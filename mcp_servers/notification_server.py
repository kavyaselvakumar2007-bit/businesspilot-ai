import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mcp.server.fastmcp import FastMCP

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import logger

# Initialize FastMCP Server for Notifications
mcp = FastMCP("Notification Server")

@mcp.tool()
def send_notification(recipient: str, subject: str, body: str) -> str:
    """
    Sends email or slack notification to a stakeholder.
    If SMTP variables are provided, sends a real email. Otherwise, falls back to a simulated log.
    
    Args:
        recipient (str): Email address of the stakeholder.
        subject (str): Title of the message.
        body (str): Text content of the notification.
        
    Returns:
        str: Status message indicating success or simulation details.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    # Check if SMTP is configured
    if smtp_server and smtp_port and smtp_username and smtp_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient, msg.as_string())
            server.quit()
            
            logger.info(f"Notification successfully sent via SMTP to {recipient}")
            return json.dumps({
                "success": True, 
                "channel": "email",
                "message": f"Real email sent successfully to {recipient} via SMTP."
            })
        except Exception as e:
            logger.error(f"Failed to send real email via SMTP: {str(e)}")
            # Fall back to simulation instead of crashing
            return json.dumps({
                "success": False,
                "error": str(e),
                "message": f"Real email send failed. Fallback simulation: Logged dispatch to {recipient}."
            })
    else:
        # Secure simulation logging
        logger.info(f"[SIMULATION] Dispatching Notification to {recipient}...")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body[:300]}...")  # Truncate for log neatness
        
        return json.dumps({
            "success": True,
            "channel": "simulation",
            "message": f"Notification simulated in logs. Recipient: {recipient}. SMTP details not fully configured in env."
        })

if __name__ == "__main__":
    mcp.run()
