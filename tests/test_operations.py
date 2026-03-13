"""Tests for DavidOS MCP Server operations."""

import sys
import pytest
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'davidos-mcp'))

from fastapi.testclient import TestClient

# Set up test environment before imports
os.environ["DAVIDOS_ROOT"] = "/tmp/test-davidos"
os.environ["DAVIDOS_LOG_LEVEL"] = "debug"

from app.mcp_server import app, file_manager
from app.file_manager import FileManager, PathTraversalError, FileAccessError
from app.config import ALLOWED_READ_FILES, ALLOWED_WRITE_FILES


client = TestClient(app)


@pytest.fixture
def temp_davidos():
    """Create temporary DavidOS structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create directory structure
        (root / "strategy").mkdir()
        (root / "organisation").mkdir()
        (root / "execution").mkdir()
        
        # Create test files
        (root / "context.md").write_text("# Test Context\n\nTest content.")
        (root / "index.md").write_text("# Test Index\n\nNavigation.")
        (root / "strategy" / "product-vision.md").write_text("# Vision\n\nFuture state.")
        (root / "strategy" / "strategic-bets.md").write_text("# Bets\n\nOur bets.")
        (root / "strategy" / "risks.md").write_text("# Risks\n\nKnown risks.")
        (root / "strategy" / "open-questions.md").write_text("# Questions\n\nOpen items.")
        (root / "organisation" / "product-org.md").write_text("# Org\n\nStructure.")
        (root / "execution" / "decision-log.md").write_text("# Decisions\n\nLog.")
        (root / "execution" / "weekly-notes.md").write_text("# Weekly\n\nNotes.")
        
        # Update file manager to use temp directory
        original_root = file_manager.root
        file_manager.root = root
        
        yield root
        
        # Restore original root
        file_manager.root = original_root


class TestHealth:
    """Health check endpoint tests."""
    
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["server"] == "davidos-mcp"


class TestReadOperations:
    """File reading operation tests."""
    
    def test_read_context(self, temp_davidos):
        response = client.post("/read", params={"path": "context.md"})
        assert response.status_code == 200
        assert "Test Context" in response.json()["content"]
    
    def test_read_allowed_file(self, temp_davidos):
        response = client.post("/read", params={"path": "strategy/risks.md"})
        assert response.status_code == 200
        assert "Known risks" in response.json()["content"]
    
    def test_read_nonexistent_file(self, temp_davidos):
        response = client.post("/read", params={"path": "nonexistent.md"})
        assert response.status_code == 403  # Not in allowlist
    
    def test_read_blocked_path_traversal(self, temp_davidos):
        response = client.post("/read", params={"path": "../../../etc/passwd"})
        assert response.status_code == 403


class TestListFiles:
    """File listing tests."""
    
    def test_list_files_returns_known_files(self, temp_davidos):
        response = client.get("/files")
        assert response.status_code == 200
        files = response.json()
        paths = [f["path"] for f in files]
        assert "context.md" in paths
        assert "strategy/risks.md" in paths


class TestSearchMemory:
    """Search operation tests."""
    
    def test_search_finds_content(self, temp_davidos):
        response = client.post("/search", params={"query": "Test Context"})
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        assert any("context.md" in r["file"] for r in results)
    
    def test_search_no_results(self, temp_davidos):
        response = client.post("/search", params={"query": "xyznonexistent"})
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestAppendOperations:
    """Append operation tests."""
    
    def test_append_decision(self, temp_davidos):
        # Test via file manager directly (tools are async)
        import asyncio
        
        from app.mcp_server import append_decision
        result = asyncio.run(append_decision(
            context="Test context",
            decision="Test decision",
            options_considered=["Option 1", "Option 2"],
            implications="Test implications",
            review_date="2026-12-01"
        ))
        
        assert "Decision recorded" in result
        
        # Verify file was updated
        content = (temp_davidos / "execution" / "decision-log.md").read_text()
        assert "Test decision" in content
        assert "Option 1" in content
    
    def test_append_open_question(self, temp_davidos):
        import asyncio
        from app.mcp_server import append_open_question
        
        result = asyncio.run(append_open_question(
            question="What is the test question?",
            category="Test Category"
        ))
        
        assert "Added question" in result
        
        content = (temp_davidos / "strategy" / "open-questions.md").read_text()
        assert "What is the test question?" in content
    
    def test_append_weekly_note(self, temp_davidos):
        import asyncio
        from app.mcp_server import append_weekly_note
        
        result = asyncio.run(append_weekly_note(
            note="Test weekly progress",
            week_date="2026-W10"
        ))
        
        assert "Note added" in result
        
        content = (temp_davidos / "execution" / "weekly-notes.md").read_text()
        assert "Test weekly progress" in content


class TestUpdateSection:
    """Section update tests."""
    
    def test_update_existing_section(self, temp_davidos):
        import asyncio
        from app.mcp_server import update_section
        
        # First ensure file exists with section
        risks_file = temp_davidos / "strategy" / "risks.md"
        risks_file.write_text("# Risks\n\n## Product evolution risk\n\nOld content.\n")
        
        result = asyncio.run(update_section(
            file="strategy/risks.md",
            section_heading="Product evolution risk",
            content="Updated risk description."
        ))
        
        assert "Updated section" in result
        
        content = risks_file.read_text()
        assert "Updated risk description" in content
        assert "Old content" not in content
    
    def test_update_adds_new_section(self, temp_davidos):
        import asyncio
        from app.mcp_server import update_section
        
        result = asyncio.run(update_section(
            file="strategy/risks.md",
            section_heading="New Section",
            content="New section content."
        ))
        
        assert "Added new section" in result
        
        content = (temp_davidos / "strategy" / "risks.md").read_text()
        assert "New Section" in content
        assert "New section content" in content


class TestGenerateBrief:
    """Brief generation tests."""
    
    def test_generate_brief_finds_content(self, temp_davidos):
        import asyncio
        from app.mcp_server import generate_brief
        
        brief = asyncio.run(generate_brief(
            topic="Test Context",
            context="testing"
        ))
        
        assert "Strategic Brief: Test Context" in brief
        assert "context.md" in brief


class TestFileManagerSecurity:
    """File manager security tests."""
    
    def test_path_traversal_blocked(self, temp_davidos):
        fm = FileManager(temp_davidos)
        
        with pytest.raises(PathTraversalError):
            fm._resolve_path("../../../etc/passwd")
        
        with pytest.raises(PathTraversalError):
            fm._resolve_path("/absolute/path")
    
    def test_write_allowlist_enforced(self, temp_davidos):
        fm = FileManager(temp_davidos)
        
        with pytest.raises(FileAccessError):
            fm.append_to_file("../../outside.md", "content")


class TestContainerStartup:
    """Container startup simulation tests."""
    
    def test_all_essential_files_accessible(self, temp_davidos):
        """Verify all expected files can be read."""
        for rel_path in ALLOWED_READ_FILES:
            try:
                content = file_manager.read_file(rel_path)
                assert content is not None
            except FileNotFoundError:
                # Some files may not exist in test environment
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
