import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.notification_agent import NotificationAgent

@pytest.fixture
def mock_context():
    return {
        "metrics": {"total_leads": 10, "hot_leads": 2, "total_revenue": 150000.0, "avg_score": 55},
        "leads": [{"company_name": "Hot SaaS", "priority_tier": "Hot"}],
        "tasks": [{"lead_company": "Hot SaaS", "task_description": "Review requirements", "assignee": "John", "priority": "High"}],
        "recipient": "test@example.com"
    }

def test_notification_agent_fallback_on_unconfigured_smtp(mock_context):
    """
    Test that NotificationAgent switches to simulation mode when the Notification MCP server returns
    a simulation response (signaling SMTP is not configured).
    """
    agent = NotificationAgent()
    
    # Mock call_mcp_tool to return a simulation response
    agent.call_mcp_tool = AsyncMock(return_value={
        "success": True,
        "channel": "simulation",
        "message": "Notification simulated in logs. Recipient: test@example.com. SMTP details not fully configured in env."
    })
    
    result = asyncio.run(agent.execute(mock_context))
    
    assert result["success"] is True
    assert result["channel"] == "simulation"
    assert result["message"] == "Email dispatch simulated because SMTP is not configured."
    assert result["dispatch_message"] == "Email dispatch simulated because SMTP is not configured."

def test_notification_agent_fallback_on_smtp_error(mock_context):
    """
    Test that NotificationAgent switches to simulation mode when email sending fails (returns success: False).
    """
    agent = NotificationAgent()
    
    # Mock call_mcp_tool to return success: False representing an SMTP error
    agent.call_mcp_tool = AsyncMock(return_value={
        "success": False,
        "error": "ConnectionRefusedError",
        "message": "Real email send failed. Fallback simulation: Logged dispatch."
    })
    
    result = asyncio.run(agent.execute(mock_context))
    
    assert result["success"] is True
    assert result["channel"] == "simulation"
    assert result["message"] == "Email dispatch simulated because SMTP is not configured."
    assert result["dispatch_message"] == "Email dispatch simulated because SMTP is not configured."

def test_notification_agent_fallback_on_exception(mock_context):
    """
    Test that NotificationAgent switches to simulation mode if calling the MCP tool raises an exception.
    """
    agent = NotificationAgent()
    
    # Mock call_mcp_tool to raise an Exception
    agent.call_mcp_tool = AsyncMock(side_effect=Exception("MCP server crash"))
    
    result = asyncio.run(agent.execute(mock_context))
    
    assert result["success"] is True
    assert result["channel"] == "simulation"
    assert result["message"] == "Email dispatch simulated because SMTP is not configured."
    assert result["dispatch_message"] == "Email dispatch simulated because SMTP is not configured."

def test_notification_agent_real_email_success(mock_context):
    """
    Test that NotificationAgent returns real email delivery status when valid credentials are present and SMTP succeeds.
    """
    agent = NotificationAgent()
    
    # Mock call_mcp_tool to return a successful email delivery status
    agent.call_mcp_tool = AsyncMock(return_value={
        "success": True,
        "channel": "email",
        "message": "Real email sent successfully to test@example.com via SMTP."
    })
    
    result = asyncio.run(agent.execute(mock_context))
    
    assert result["success"] is True
    assert result["channel"] == "email"
    assert "Real email sent successfully" in result["message"]
    assert "Real email sent successfully" in result["dispatch_message"]
