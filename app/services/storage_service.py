"""
Storage Service - Manages Supabase Storage buckets and files

Handles autonomous bucket creation and file metadata storage.
"""

import logging
from typing import Dict, Optional
from app.db import DB
import uuid

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing user storage"""
    
    def __init__(self):
        self.db = DB
    
    def create_user_bucket(self, user_id: int, is_public: bool = False) -> Dict:
        """
        Create a storage bucket for a user if it doesn't exist
        
        Args:
            user_id: Telegram User ID
            is_public: Whether the bucket should be public
            
        Returns:
            Dict with success status and bucket_id
        """
        try:
            # Check if user already has a bucket
            existing = self.db.supabase.table("storage_spaces").select("bucket_id").eq("user_id", user_id).execute()
            if existing.data:
                return {"success": True, "bucket_id": existing.data[0]["bucket_id"], "message": "Bucket already exists"}
            
            # Generate unique bucket ID
            bucket_id = f"user-{user_id}-{str(uuid.uuid4())[:8]}"
            
            # Create bucket via Supabase Storage API
            # Note: This requires the Service Role Key to be set in DB client
            res = self.db.supabase.storage.create_bucket(
                bucket_id,
                options={"public": is_public}
            )
            
            # Record in database
            self.db.supabase.table("storage_spaces").insert({
                "user_id": user_id,
                "bucket_id": bucket_id,
                "is_public": is_public
            }).execute()
            
            logger.info(f"Created bucket {bucket_id} for user {user_id}")
            return {"success": True, "bucket_id": bucket_id}
            
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
            return {"success": False, "error": str(e)}
    
    def store_file_metadata(self, user_id: int, file_info: Dict) -> Dict:
        """
        Store metadata for an uploaded file
        
        Args:
            user_id: Telegram User ID
            file_info: Dict containing file_name, file_url, bucket_id, etc.
            
        Returns:
            Dict with success status and file_id
        """
        try:
            data = {
                "user_id": user_id,
                "bucket_id": file_info.get("bucket_id"),
                "file_name": file_info.get("file_name"),
                "file_url": file_info.get("file_url"),
                "file_type": file_info.get("file_type"),
                "file_size": file_info.get("file_size"),
                "summary": file_info.get("summary")
            }
            
            res = self.db.supabase.table("files").insert(data).execute()
            
            if res.data:
                return {"success": True, "file_id": res.data[0]["id"]}
            return {"success": False, "error": "No data returned"}
            
        except Exception as e:
            logger.error(f"Error storing file metadata: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_bucket(self, user_id: int) -> Optional[str]:
        """Get user's bucket ID"""
        try:
            res = self.db.supabase.table("storage_spaces").select("bucket_id").eq("user_id", user_id).execute()
            if res.data:
                return res.data[0]["bucket_id"]
            return None
        except Exception as e:
            logger.error(f"Error getting user bucket: {e}")
            return None
