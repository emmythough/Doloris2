import json
import logging
import os
import redis
from rq import Worker
from app.core.system_logger import system_logger
from app.openai_client import openai_client
from app.dev_brain.github_ops import create_repair_pr
from app.db import DB

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def process_repair_job(job_data):
    """
    Process a repair job for the Dev Brain.
    """
    trace_id = job_data.get("trace_id")
    payload = job_data.get("payload")
    ticket_id = payload.get("ticket_id")
    
    logger.info(f"Processing repair job for ticket {ticket_id}")
    
    try:
        system_logger.log_event(trace_id, "dev_brain", "repair_start", "info", {"ticket_id": ticket_id})
        
        # 1. Fetch Ticket & Errors
        ticket = DB.supabase.table("repair_tickets").select("*").eq("id", ticket_id).single().execute()
        ticket_data = ticket.data
        
        # 2. Analyze with o3-mini (using o1-mini as proxy if o3 not available)
        # We use a specialized prompt for reasoning
        analysis_prompt = f"""
You are R.D, an expert software engineer.
Analyze the following bug report and propose a fix.

Bug Description: {ticket_data['description']}
Error IDs: {ticket_data['error_ids']}

You have access to the codebase via tools.
1. Read relevant files.
2. Reproduce the issue with a test case.
3. Create a patch.

Return a JSON object with:
- test_file: path to new test file
- test_code: content of test file
- patch_file: path to file to fix
- patch_code: content of fixed file
- explanation: summary of fix
"""
        
        # Mocking the reasoning loop for now
        # In real implementation, this would be a loop calling tools (read_file, etc.)
        # Here we just simulate a response for demonstration
        
        # response = await openai_client.chat_completion(...)
        
        logger.info("Dev Brain analyzing...")
        
        # Simulate Analysis Result
        analysis = {
            "test_file": "tests/reproduce_issue.py",
            "test_code": "def test_fail(): assert False",
            "patch_file": "app/main.py",
            "patch_code": "# Fixed",
            "explanation": "Simulated fix"
        }
        
        # 3. Create PR
        pr_url = create_repair_pr(ticket_id, analysis)
        
        # 4. Update Ticket
        DB.supabase.table("repair_tickets").update({
            "status": "pr_created",
            "pr_url": pr_url
        }).eq("id", ticket_id).execute()
        
        system_logger.log_event(trace_id, "dev_brain", "repair_complete", "success", {"pr_url": pr_url})
        
    except Exception as e:
        logger.error(f"Error processing repair job {ticket_id}: {e}", exc_info=True)
        system_logger.log_event(trace_id, "dev_brain", "repair_error", "error", {"error": str(e)})
        raise e

if __name__ == "__main__":
    conn = redis.from_url(REDIS_URL)
    qs = ['dev_brain']
    w = Worker(qs, connection=conn)
    w.work()
