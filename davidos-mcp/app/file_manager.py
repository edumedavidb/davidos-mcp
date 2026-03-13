"""Safe file operations with security guardrails."""

import logging
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import settings, ALLOWED_READ_FILES, ALLOWED_WRITE_FILES

logger = logging.getLogger("davidos-mcp")


class FileManagerError(Exception):
    """Custom error for file operations."""
    pass


class PathTraversalError(FileManagerError):
    """Path traversal attempt detected."""
    pass


class FileAccessError(FileManagerError):
    """File not in allowlist."""
    pass


class FileManager:
    """Manages safe file operations within DavidOS directory."""
    
    def __init__(self, root_path: Optional[Path] = None):
        self.root = root_path or settings.davidos_root
        self.root = self.root.resolve()
        
    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path within the DavidOS root.
        
        Raises:
            PathTraversalError: If path attempts to escape root directory
        """
        # Normalize the input
        clean_path = relative_path.replace("\\", "/").strip("/")
        
        # Reject absolute paths
        if clean_path.startswith("/") or clean_path.startswith("~"):
            raise PathTraversalError(f"Absolute paths not allowed: {relative_path}")
        
        # Reject path traversal attempts
        if ".." in clean_path.split("/"):
            raise PathTraversalError(f"Path traversal detected: {relative_path}")
        
        # Resolve within root
        target = (self.root / clean_path).resolve()
        
        # Verify the resolved path is within root
        try:
            target.relative_to(self.root)
        except ValueError:
            raise PathTraversalError(f"Path escapes root directory: {relative_path}")
        
        return target
    
    def read_file(self, relative_path: str) -> str:
        """Read a file from the DavidOS directory.
        
        Args:
            relative_path: Path relative to DavidOS root
            
        Returns:
            File contents as string
            
        Raises:
            FileAccessError: If file not in allowlist
            FileNotFoundError: If file doesn't exist
        """
        # Check allowlist
        if relative_path not in ALLOWED_READ_FILES:
            logger.warning(f"Attempt to read non-allowed file: {relative_path}")
            raise FileAccessError(f"File not in read allowlist: {relative_path}")
        
        target = self._resolve_path(relative_path)
        
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        logger.info(f"Reading file: {relative_path}")
        return target.read_text(encoding="utf-8")
    
    def append_to_file(self, relative_path: str, content: str) -> None:
        """Append content to a file.
        
        Args:
            relative_path: Path relative to DavidOS root
            content: Content to append
            
        Raises:
            FileAccessError: If file not in write allowlist
        """
        if relative_path not in ALLOWED_WRITE_FILES:
            logger.warning(f"Attempt to write non-allowed file: {relative_path}")
            raise FileAccessError(f"File not in write allowlist: {relative_path}")
        
        target = self._resolve_path(relative_path)
        
        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Appending to file: {relative_path}")
        
        with open(target, "a", encoding="utf-8") as f:
            f.write(content)
    
    def update_section(self, relative_path: str, section_heading: str, content: str) -> None:
        """Update or replace a markdown section.
        
        Args:
            relative_path: Path relative to DavidOS root
            section_heading: The section heading (without #)
            content: New content for the section
            
        Raises:
            FileAccessError: If file not in write allowlist
            FileManagerError: If section not found and strict mode
        """
        if relative_path not in ALLOWED_WRITE_FILES:
            logger.warning(f"Attempt to update non-allowed file: {relative_path}")
            raise FileAccessError(f"File not in write allowlist: {relative_path}")
        
        target = self._resolve_path(relative_path)
        
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        file_content = target.read_text(encoding="utf-8")
        
        # Find section by heading pattern
        escaped_heading = re.escape(section_heading)
        # Match heading at various levels
        pattern = rf"(^|\n)(#{{1,6}}\s+{escaped_heading}\s*\n)(.*?)(?=\n#{{1,6}}\s|\Z)"
        
        match = re.search(pattern, file_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Replace existing section
            new_content = (
                file_content[:match.start(2)] +
                match.group(2) +  # Keep the heading
                content.rstrip() + "\n\n" +
                file_content[match.end():]
            )
            logger.info(f"Updated section '{section_heading}' in {relative_path}")
        else:
            # Append new section at end
            new_content = file_content.rstrip() + f"\n\n## {section_heading}\n\n{content}\n"
            logger.info(f"Added new section '{section_heading}' to {relative_path}")
        
        target.write_text(new_content, encoding="utf-8")
    
    def search_files(self, query: str) -> list[dict]:
        """Search for query text across all markdown files.
        
        Args:
            query: Search string
            
        Returns:
            List of matches with file path and context
        """
        results = []
        query_lower = query.lower()
        
        for rel_path in ALLOWED_READ_FILES:
            try:
                content = self.read_file(rel_path)
                if query_lower in content.lower():
                    # Find context around match
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            context_start = max(0, i - 2)
                            context_end = min(len(lines), i + 3)
                            context = "\n".join(lines[context_start:context_end])
                            results.append({
                                "file": rel_path,
                                "line": i + 1,
                                "context": context.strip()
                            })
            except (FileNotFoundError, FileAccessError):
                continue
        
        logger.info(f"Search for '{query}' found {len(results)} matches")
        return results
    
    def list_files(self) -> list[dict]:
        """Return list of all known DavidOS files."""
        files = []
        for rel_path in sorted(ALLOWED_READ_FILES):
            try:
                target = self._resolve_path(rel_path)
                stat = target.stat() if target.exists() else None
                files.append({
                    "path": rel_path,
                    "exists": target.exists(),
                    "size": stat.st_size if stat else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None
                })
            except PathTraversalError:
                continue
        return files
    
    def resource_to_path(self, uri: str) -> Optional[str]:
        """Convert a resource URI to a file path."""
        from .config import RESOURCE_URIS
        return RESOURCE_URIS.get(uri)
