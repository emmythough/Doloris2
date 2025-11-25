"""
Test Tools - Run and validate tests for R.D

Provides tools for R.D to run pytest and validate fixes.
"""

import subprocess
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TestTools:
    """Tools for running and analyzing tests"""
    
    def __init__(self, repo_path: str = None):
        """
        Initialize test tools
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path or "."
        logger.info(f"[TEST_TOOLS] Initialized with repo: {self.repo_path}")
    
    def run_tests(self, scope: str, timeout: int = 60) -> Dict:
        """
        Run pytest with specific scope
        
        Args:
            scope: Test scope (file path, class, or specific test)
            timeout: Timeout in seconds
        
        Returns:
            Dict with test results
        """
        logger.info(f"[TEST_TOOLS] Running tests: {scope} (timeout: {timeout}s)")
        
        try:
            # Run pytest with JSON output
            cmd = [
                "python", "-m", "pytest",
                scope,
                "-v",
                "--tb=short",
                "--no-header",
                f"--timeout={timeout}"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout + 5  # Add buffer to subprocess timeout
            )
            
            # Parse output
            output = result.stdout + result.stderr
            exit_code = result.returncode
            
            # Determine status
            if exit_code == 0:
                status = "passed"
            elif exit_code == 1:
                status = "failed"
            else:
                status = "error"
            
            # Parse test results
            test_results = self._parse_pytest_output(output)
            
            logger.info(f"[TEST_TOOLS] Tests {status}: {len(test_results)} tests")
            
            return {
                "status": status,
                "exit_code": exit_code,
                "output": output,
                "tests": test_results,
                "summary": self._generate_summary(test_results)
            }
        
        except subprocess.TimeoutExpired:
            logger.error(f"[TEST_TOOLS] Tests timed out after {timeout}s")
            return {
                "status": "timeout",
                "error": f"Tests timed out after {timeout} seconds"
            }
        
        except Exception as e:
            logger.error(f"[TEST_TOOLS] Error running tests: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _parse_pytest_output(self, output: str) -> List[Dict]:
        """Parse pytest output to extract test results"""
        tests = []
        
        # Simple parsing - look for PASSED/FAILED lines
        for line in output.split('\n'):
            if '::' in line and ('PASSED' in line or 'FAILED' in line):
                parts = line.split('::')
                if len(parts) >= 2:
                    test_file = parts[0].strip()
                    test_name = parts[1].split()[0].strip()
                    status = "passed" if "PASSED" in line else "failed"
                    
                    tests.append({
                        "file": test_file,
                        "name": test_name,
                        "status": status
                    })
        
        return tests
    
    def _generate_summary(self, test_results: List[Dict]) -> str:
        """Generate summary of test results"""
        total = len(test_results)
        passed = sum(1 for t in test_results if t["status"] == "passed")
        failed = total - passed
        
        return f"{passed}/{total} passed, {failed} failed"
    
    def find_related_tests(self, path: str) -> List[str]:
        """
        Find test files related to a module
        
        Args:
            path: Module path
        
        Returns:
            List of test file paths
        """
        from app.dev_brain.code_tools import get_code_tools
        
        code_tools = get_code_tools(self.repo_path)
        return code_tools.find_related_tests(path)

# Singleton instance
_test_tools = None

def get_test_tools(repo_path: str = None) -> TestTools:
    """Get the global test tools instance"""
    global _test_tools
    if _test_tools is None:
        _test_tools = TestTools(repo_path)
    return _test_tools
