"""
Code Tools - Repository manipulation and code analysis for R.D

Provides tools for R.D to understand and modify the codebase.
"""

import os
import ast
import logging
import difflib
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeTools:
    """Tools for code analysis and manipulation"""
    
    def __init__(self, repo_path: str = None):
        """
        Initialize code tools
        
        Args:
            repo_path: Path to repository root (defaults to current working directory)
        """
        self.repo_path = repo_path or os.getcwd()
        logger.info(f"[CODE_TOOLS] Initialized with repo: {self.repo_path}")
    
    def code_map_search(self, query: str, search_type: str = "text") -> List[Dict]:
        """
        Search codebase for symbols or text
        
        Args:
            query: Search query
            search_type: "symbol" or "text"
        
        Returns:
            List of search results with file, line, and content
        """
        logger.info(f"[CODE_TOOLS] Searching for '{query}' (type: {search_type})")
        
        results = []
        
        if search_type == "symbol":
            # Search for Python symbols (functions, classes)
            results = self._search_symbols(query)
        else:
            # Text search
            results = self._search_text(query)
        
        logger.info(f"[CODE_TOOLS] Found {len(results)} results")
        return results[:20]  # Limit to 20 results
    
    def _search_symbols(self, symbol_name: str) -> List[Dict]:
        """Search for Python symbols (functions, classes)"""
        results = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content, filename=file_path)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            if symbol_name.lower() in node.name.lower():
                                results.append({
                                    "file": rel_path,
                                    "line": node.lineno,
                                    "type": type(node).__name__,
                                    "name": node.name,
                                    "context": f"{type(node).__name__} {node.name}"
                                })
                
                except Exception as e:
                    logger.debug(f"Error parsing {file_path}: {e}")
                    continue
        
        return results
    
    def _search_text(self, query: str) -> List[Dict]:
        """Search for text in files"""
        results = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if not file.endswith(('.py', '.md', '.txt', '.yaml', '.yml', '.json')):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        if query.lower() in line.lower():
                            results.append({
                                "file": rel_path,
                                "line": line_num,
                                "content": line.strip()
                            })
                
                except Exception as e:
                    logger.debug(f"Error reading {file_path}: {e}")
                    continue
        
        return results
    
    def find_references(self, symbol: str, file_path: Optional[str] = None) -> List[Dict]:
        """
        Find all references to a symbol
        
        Args:
            symbol: Symbol name to find
            file_path: Optional file path to limit search
        
        Returns:
            List of references
        """
        logger.info(f"[CODE_TOOLS] Finding references to '{symbol}'")
        
        # For now, use text search
        # TODO: Implement proper AST-based reference finding
        return self._search_text(symbol)
    
    def read_file_smart(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict:
        """
        Read file with optional line range
        
        Args:
            path: Relative path from repo root
            start_line: Optional start line (1-indexed)
            end_line: Optional end line (1-indexed)
        
        Returns:
            Dict with file content and metadata
        """
        full_path = os.path.join(self.repo_path, path)
        
        if not os.path.exists(full_path):
            return {"error": f"File not found: {path}"}
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            if start_line is not None and end_line is not None:
                # Return specific range
                start_idx = max(0, start_line - 1)
                end_idx = min(total_lines, end_line)
                content = ''.join(lines[start_idx:end_idx])
                
                return {
                    "path": path,
                    "total_lines": total_lines,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": content
                }
            else:
                # Return full file
                content = ''.join(lines)
                
                return {
                    "path": path,
                    "total_lines": total_lines,
                    "content": content
                }
        
        except Exception as e:
            logger.error(f"[CODE_TOOLS] Error reading {path}: {e}")
            return {"error": str(e)}
    
    def write_file(self, path: str, content: str) -> Dict:
        """
        Write file and compute diff
        
        Args:
            path: Relative path from repo root
            content: New file content
        
        Returns:
            Dict with success status and diff
        """
        full_path = os.path.join(self.repo_path, path)
        
        # Read existing content if file exists
        old_content = ""
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
            except Exception as e:
                logger.error(f"[CODE_TOOLS] Error reading existing file: {e}")
        
        # Write new content
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Compute diff
            diff = self._compute_diff(old_content, content, path)
            
            logger.info(f"[CODE_TOOLS] Wrote {len(content)} bytes to {path}")
            
            return {
                "success": True,
                "path": path,
                "bytes_written": len(content),
                "diff": diff
            }
        
        except Exception as e:
            logger.error(f"[CODE_TOOLS] Error writing {path}: {e}")
            return {"error": str(e)}
    
    def _compute_diff(self, old_content: str, new_content: str, filename: str) -> str:
        """Compute unified diff between old and new content"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def find_related_tests(self, path: str) -> List[str]:
        """
        Find test files related to a module
        
        Args:
            path: Module path
        
        Returns:
            List of test file paths
        """
        logger.info(f"[CODE_TOOLS] Finding tests for {path}")
        
        # Extract module name
        module_name = Path(path).stem
        
        # Search for test files
        test_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                # Look for test_<module>.py or <module>_test.py
                if file.startswith('test_') and module_name in file:
                    test_files.append(os.path.relpath(os.path.join(root, file), self.repo_path))
                elif file.endswith('_test.py') and module_name in file:
                    test_files.append(os.path.relpath(os.path.join(root, file), self.repo_path))
        
        logger.info(f"[CODE_TOOLS] Found {len(test_files)} test files")
        return test_files

# Singleton instance
_code_tools = None

def get_code_tools(repo_path: str = None) -> CodeTools:
    """Get the global code tools instance"""
    global _code_tools
    if _code_tools is None:
        _code_tools = CodeTools(repo_path)
    return _code_tools
