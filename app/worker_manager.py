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
            logger.info("Connecting to Redis...")
            conn = redis.from_url(REDIS_URL)
            conn.ping()  # Test connection
            logger.info("Redis connection successful")
            
            logger.info("Setting up queue...")
            queue = Queue('conversation', connection=conn)
            logger.info(f"Queue created: {queue.name}")
            
            # Import the worker function to ensure it's available
            logger.info("Importing worker function...")
            from app.workers.conversation_worker import process_conversation_job
            logger.info("Worker function imported successfully")
            
            logger.info("Creating RQ Worker...")
            worker = Worker([queue], connection=conn)
            logger.info("Worker created successfully")
            
            # Use burst mode with a loop to keep checking for jobs
            logger.info("Worker starting in continuous burst mode...")
            while self.running:
                try:
                    worker.work(burst=True, with_scheduler=False)
                    # Sleep briefly between bursts to avoid CPU spinning
                    import time
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Worker burst error: {e}", exc_info=True)
                    time.sleep(5)  # Wait longer on error
                    
        except Exception as e:
            logger.error(f"Worker crashed during setup: {e}", exc_info=True)
            self.running = False
            
    def stop_worker(self):
        """Stop the worker (called on shutdown)"""
        self.running = False
        logger.info("Worker shutdown requested")

# Global instance
worker_manager = WorkerManager()
