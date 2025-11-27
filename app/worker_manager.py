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
        """Worker thread function - manually polls queue"""
        import time
        
        try:
            logger.info("Connecting to Redis...")
            conn = redis.from_url(REDIS_URL)
            conn.ping()
            logger.info("Redis connection successful")
            
            logger.info("Setting up queue...")
            queue = Queue('conversation', connection=conn)
            logger.info(f"Queue '{queue.name}' ready")
            
            # Import the worker function
            from app.workers.conversation_worker import process_conversation_job
            logger.info("Worker function imported")
            
            logger.info("Worker polling started (checking every 2 seconds)...")
            
            while self.running:
                try:
                    # Manually dequeue and process jobs
                    job = queue.dequeue()
                    
                    if job:
                        logger.info(f"Processing job: {job.id}")
                        try:
                            # Execute the job
                            result = job.perform()
                            job.set_status('finished')
                            logger.info(f"Job {job.id} completed successfully")
                        except Exception as e:
                            job.set_status('failed')
                            logger.error(f"Job {job.id} failed: {e}", exc_info=True)
                    else:
                        # No job available, sleep briefly
                        time.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Worker polling error: {e}", exc_info=True)
                    time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Worker crashed during setup: {e}", exc_info=True)
            self.running = False
            
    def stop_worker(self):
        """Stop the worker (called on shutdown)"""
        self.running = False
        logger.info("Worker shutdown requested")

# Global instance
worker_manager = WorkerManager()
