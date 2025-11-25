"""
GitHub Tools - PR automation for R.D

Provides tools for R.D to create and merge pull requests.
"""

import logging
from typing import Dict, List, Optional
from github import Github, GithubException
from app.config import GITHUB_TOKEN, GITHUB_REPO

logger = logging.getLogger(__name__)

class GitHubTools:
    """Tools for GitHub PR automation"""
    
    def __init__(self):
        """Initialize GitHub tools"""
        if not GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not configured")
        
        self.github = Github(GITHUB_TOKEN)
        self.repo = self.github.get_repo(GITHUB_REPO)
        logger.info(f"[GITHUB_TOOLS] Initialized for repo: {GITHUB_REPO}")
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        description: str,
        files: Dict[str, str]
    ) -> Dict:
        """
        Create a pull request with file changes
        
        Args:
            branch_name: Name for the new branch
            title: PR title
            description: PR description
            files: Dict mapping file paths to new content
        
        Returns:
            Dict with PR information
        """
        logger.info(f"[GITHUB_TOOLS] Creating PR: {title} (branch: {branch_name})")
        
        try:
            # Get main branch
            main_branch = self.repo.get_branch("main")
            main_sha = main_branch.commit.sha
            
            # Create new branch
            ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_sha
            )
            logger.info(f"[GITHUB_TOOLS] Created branch: {branch_name}")
            
            # Commit changes
            for file_path, content in files.items():
                try:
                    # Try to get existing file
                    file_obj = self.repo.get_contents(file_path, ref=branch_name)
                    
                    # Update existing file
                    self.repo.update_file(
                        path=file_path,
                        message=f"Update {file_path}",
                        content=content,
                        sha=file_obj.sha,
                        branch=branch_name
                    )
                    logger.info(f"[GITHUB_TOOLS] Updated file: {file_path}")
                
                except GithubException as e:
                    if e.status == 404:
                        # File doesn't exist, create it
                        self.repo.create_file(
                            path=file_path,
                            message=f"Create {file_path}",
                            content=content,
                            branch=branch_name
                        )
                        logger.info(f"[GITHUB_TOOLS] Created file: {file_path}")
                    else:
                        raise
            
            # Create pull request
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base="main"
            )
            
            logger.info(f"[GITHUB_TOOLS] Created PR #{pr.number}: {pr.html_url}")
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "branch": branch_name,
                "files_changed": len(files)
            }
        
        except Exception as e:
            logger.error(f"[GITHUB_TOOLS] Error creating PR: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def merge_pull_request(self, pr_number: int, strategy: str = "squash") -> Dict:
        """
        Merge a pull request
        
        Args:
            pr_number: PR number
            strategy: Merge strategy ("merge", "squash", "rebase")
        
        Returns:
            Dict with merge result
        """
        logger.info(f"[GITHUB_TOOLS] Merging PR #{pr_number} (strategy: {strategy})")
        
        try:
            pr = self.repo.get_pull(pr_number)
            
            # Check if PR is mergeable
            if not pr.mergeable:
                return {
                    "success": False,
                    "error": "PR is not mergeable (conflicts or checks failing)"
                }
            
            # Merge PR
            merge_result = pr.merge(
                merge_method=strategy
            )
            
            if merge_result.merged:
                logger.info(f"[GITHUB_TOOLS] Successfully merged PR #{pr_number}")
                return {
                    "success": True,
                    "pr_number": pr_number,
                    "merged": True,
                    "sha": merge_result.sha
                }
            else:
                return {
                    "success": False,
                    "error": "Merge failed (unknown reason)"
                }
        
        except Exception as e:
            logger.error(f"[GITHUB_TOOLS] Error merging PR: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pr_status(self, pr_number: int) -> Dict:
        """
        Get PR status
        
        Args:
            pr_number: PR number
        
        Returns:
            Dict with PR status
        """
        try:
            pr = self.repo.get_pull(pr_number)
            
            return {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "url": pr.html_url
            }
        
        except Exception as e:
            logger.error(f"[GITHUB_TOOLS] Error getting PR status: {e}")
            return {"error": str(e)}

# Singleton instance
_github_tools = None

def get_github_tools() -> GitHubTools:
    """Get the global GitHub tools instance"""
    global _github_tools
    if _github_tools is None:
        _github_tools = GitHubTools()
    return _github_tools
