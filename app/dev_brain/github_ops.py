import os
import logging
from github import Github
from app.config import GITHUB_TOKEN, GITHUB_REPO

logger = logging.getLogger(__name__)

def create_repair_pr(ticket_id: str, analysis: dict) -> str:
    """
    Creates a Pull Request with the fix.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        logger.warning("GitHub credentials not set. Skipping PR creation.")
        return "http://mock-github-url/pr/1"
        
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # 1. Create Branch
        base_branch = repo.get_branch("main")
        branch_name = f"fix/repair-{ticket_id}"
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_branch.commit.sha)
        except Exception:
            # Branch might already exist
            pass
            
        # 2. Commit Test
        try:
            repo.create_file(
                path=analysis["test_file"],
                message=f"test: reproduce issue #{ticket_id}",
                content=analysis["test_code"],
                branch=branch_name
            )
        except Exception:
            # File might exist, update it?
            pass
            
        # 3. Commit Fix
        # For simplicity, we assume we are replacing the file or patching. 
        # Real implementation needs to handle reading existing content and patching.
        # Here we just try to update if exists or create.
        try:
            contents = repo.get_contents(analysis["patch_file"], ref=branch_name)
            repo.update_file(
                path=analysis["patch_file"],
                message=f"fix: {analysis['explanation']}",
                content=analysis["patch_code"],
                sha=contents.sha,
                branch=branch_name
            )
        except Exception:
            repo.create_file(
                path=analysis["patch_file"],
                message=f"fix: {analysis['explanation']}",
                content=analysis["patch_code"],
                branch=branch_name
            )
            
        # 4. Create PR
        pr = repo.create_pull(
            title=f"Fix: Issue #{ticket_id}",
            body=f"Auto-generated repair for ticket #{ticket_id}.\n\n{analysis['explanation']}",
            head=branch_name,
            base="main"
        )
        
        return pr.html_url
        
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        return "error-creating-pr"
