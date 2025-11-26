"""
Telegram Adapter - Handles Telegram-specific logic including file downloads

Acts as the interface between Telegram Webhook and Doloris Core.
"""

import logging
import httpx
import os
from typing import Dict, Optional, Tuple
from app.config import TELEGRAM_BOT_TOKEN
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """Handles Telegram interactions"""
    
    API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    FILE_API_URL = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}"
    
    def __init__(self):
        self.storage = StorageService()
    
    async def process_update(self, update: Dict) -> Tuple[int, str, Optional[str], Optional[Dict]]:
        """
        Process a Telegram update and extract content
        
        Returns:
            (user_id, text, file_url, file_metadata)
        """
        logger.info("[ADAPTER] 🔍 Starting update processing...")
        logger.debug(f"[ADAPTER] Update keys: {update.keys()}")
        
        message = update.get("message", {})
        logger.debug(f"[ADAPTER] Message keys: {message.keys()}")
        
        user_id = message.get("from", {}).get("id")
        logger.info(f"[ADAPTER] 👤 Extracted user_id: {user_id}")
        
        text = message.get("text", "")
        caption = message.get("caption", "")
        logger.info(f"[ADAPTER] 💬 Text: '{text}', Caption: '{caption}'")
        
        # Use caption as text if present
        final_text = text or caption or ""
        logger.info(f"[ADAPTER] 📝 Final text: '{final_text}'")
        
        # Check for files
        file_url = None
        file_metadata = None
        
        # Priority: Document > Photo > Video
        if "document" in message:
            logger.info("[ADAPTER] 📄 Document detected")
            doc = message["document"]
            file_id = doc["file_id"]
            file_name = doc.get("file_name", "document")
            mime_type = doc.get("mime_type", "application/octet-stream")
            file_size = doc.get("file_size", 0)
            
            logger.info(f"[ADAPTER] Document details: {file_name} ({mime_type}, {file_size} bytes)")
            
            file_url = await self._handle_file(user_id, file_id, file_name, mime_type, file_size)
            file_metadata = {"name": file_name, "type": mime_type, "size": file_size}
            
        elif "photo" in message:
            logger.info("[ADAPTER] 📷 Photo detected")
            # Get largest photo
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            file_name = f"photo_{file_id[:8]}.jpg"
            mime_type = "image/jpeg"
            file_size = photo.get("file_size", 0)
            
            logger.info(f"[ADAPTER] Photo details: {file_name} ({mime_type}, {file_size} bytes)")
            
            file_url = await self._handle_file(user_id, file_id, file_name, mime_type, file_size)
            file_metadata = {"name": file_name, "type": mime_type, "size": file_size}
        else:
            logger.info("[ADAPTER] ℹ️ No file attached")
        
        logger.info(f"[ADAPTER] ✅ Processing complete: user_id={user_id}, text_len={len(final_text)}, has_file={file_url is not None}")
        return user_id, final_text, file_url, file_metadata

    async def _handle_file(
        self, 
        user_id: int, 
        file_id: str, 
        file_name: str, 
        mime_type: str,
        file_size: int
    ) -> Optional[str]:
        """
        Download file from Telegram and upload to Supabase
        """
        try:
            # 1. Get file path from Telegram
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.API_URL}/getFile?file_id={file_id}")
                if res.status_code != 200:
                    logger.error(f"Failed to get file info: {res.text}")
                    return None
                
                file_path = res.json()["result"]["file_path"]
                
                # 2. Download file content
                file_res = await client.get(f"{self.FILE_API_URL}/{file_path}")
                if file_res.status_code != 200:
                    logger.error("Failed to download file content")
                    return None
                
                file_content = file_res.content
                
                # 3. Ensure user has a bucket
                bucket_res = self.storage.create_user_bucket(user_id, is_public=True)
                bucket_id = bucket_res.get("bucket_id")
                
                if not bucket_id:
                    logger.error("Failed to get/create bucket")
                    return None
                
                # 4. Upload to Supabase
                # Note: In a real app, we'd stream this. For MVP, in-memory is okay for small files.
                # We need to use the Supabase client to upload
                from app.db import DB
                
                path = f"{file_name}"
                DB.supabase.storage.from_(bucket_id).upload(
                    path=path,
                    file=file_content,
                    file_options={"content-type": mime_type}
                )
                
                # 5. Get Public URL
                public_url_res = DB.supabase.storage.from_(bucket_id).get_public_url(path)
                public_url = public_url_res
                
                # 6. Store metadata
                self.storage.store_file_metadata(user_id, {
                    "bucket_id": bucket_id,
                    "file_name": file_name,
                    "file_url": public_url,
                    "file_type": mime_type,
                    "file_size": file_size
                })
                
                return public_url
                
        except Exception as e:
            logger.error(f"Error handling file: {e}", exc_info=True)
            return None

    async def send_message(self, chat_id: int, text: str):
        """Send message back to Telegram with fallback for formatting errors"""
        logger.info(f"[ADAPTER] 📤 Sending message to chat_id={chat_id}")
        logger.debug(f"[ADAPTER] Message length: {len(text)} chars")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try with Markdown first
            payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            
            try:
                logger.info(f"[ADAPTER] 🌐 POSTing to {self.API_URL}/sendMessage (Markdown)")
                response = await client.post(f"{self.API_URL}/sendMessage", json=payload)
                
                if response.status_code == 200:
                    logger.info("[ADAPTER] ✅ Message sent successfully!")
                    return {"success": True, "response": response.json()}
                
                # If Markdown fails (400), retry as plain text
                if response.status_code == 400:
                    logger.warning(f"[ADAPTER] ⚠️ Markdown failed ({response.text}). Retrying as plain text...")
                    
                    # Remove parse_mode to send as plain text
                    payload.pop("parse_mode")
                    response = await client.post(f"{self.API_URL}/sendMessage", json=payload)
                    
                    if response.status_code == 200:
                        logger.info("[ADAPTER] ✅ Message sent successfully (Plain Text fallback)!")
                        return {"success": True, "response": response.json(), "fallback": True}
                
                # If still failing
                logger.error(f"[ADAPTER] ❌ Failed to send message: {response.status_code}")
                logger.error(f"[ADAPTER] ❌ Error response: {response.text}")
                return {"success": False, "status": response.status_code, "error": response.text}
                    
            except Exception as e:
                logger.error(f"[ADAPTER] ❌ Exception sending message: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
