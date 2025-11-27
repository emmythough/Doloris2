"""
Worker Manager - Runs RQ worker as a background thread
This allows the worker to run inside the web service without needing a separate process
"""
import threading
import logging
import os
import redis
from rq import Worker, Queue

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class WorkerManager:
    """Manages background RQ workers"""
    
    def __init__(self):
        self.worker_thread = None
        self.running = False
        
    def start_worker(self):
        """Start the RQ worker in a background thread"""
        if self.running:
            logger.warning("Worker already running")
            return
            
        try:
            logger.info("Starting embedded RQ worker...")
            self.running = True
            self.worker_thread = threading.Thread(target=self._run_worker, daemon=True)
            self.worker_thread.start()
            logger.info("Embedded RQ worker started successfully")
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            self.running = False
            
    def _run_worker(self):
        """Worker thread function"""
        try:
            conn = redis.from_url(REDIS_URL)
            queues = [Queue('conversation', connection=conn)]
            
            # Import the worker function to ensure it's available
            from app.workers.conversation_worker import process_conversation_job
            
            worker = Worker(queues, connection=conn)
            logger.info("Worker listening on 'conversation' queue...")
            worker.work(with_scheduler=False)
        except Exception as e:
            logger.error(f"Worker crashed: {e}", exc_info=True)
            self.running = False
            
    def stop_worker(self):
        """Stop the worker (called on shutdown)"""
        self.running = False
        logger.info("Worker shutdown requested")

# Global instance
worker_manager = WorkerManager()
