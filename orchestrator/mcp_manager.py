import os
import sys
import json
import asyncio
from contextlib import AsyncExitStack
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import ClientSession

from config.settings import logger

class MCPManager:
    """
    Manages spawning, lifecycle, and tool dispatching for multiple MCP servers
    running as Python subprocesses over standard input/output (stdio).
    """
    def __init__(self):
        self.servers_config = {
            "Lead Data Server": "mcp_servers/lead_data_server.py",
            "Business Knowledge Server": "mcp_servers/business_knowledge_server.py",
            "Reporting Server": "mcp_servers/reporting_server.py",
            "Notification Server": "mcp_servers/notification_server.py"
        }
        self.exit_stack = AsyncExitStack()
        self.sessions = {}
        self.discovered_tools = {}

    async def start_all(self):
        """
        Starts all configured MCP servers as subprocesses, initializes client sessions,
        and discovers available tools dynamically.
        """
        logger.info("Starting MCP Servers...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for name, relative_path in self.servers_config.items():
            server_script = os.path.join(base_dir, relative_path)
            if not os.path.exists(server_script):
                logger.error(f"MCP server script not found: {server_script}")
                continue
                
            # Use sys.executable to ensure we run in the same python environment (venv, etc.)
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_script],
                env=os.environ.copy()
            )
            
            logger.info(f"Connecting to MCP Server: '{name}' using {sys.executable}...")
            
            try:
                # Establish stdio transport
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                
                # Establish ClientSession
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                
                # Initialize connection with server
                await session.initialize()
                self.sessions[name] = session
                
                # Retrieve and list tools
                tools_response = await session.list_tools()
                # FastMCP list_tools returns an object containing 'tools'
                tools_list = tools_response.tools if hasattr(tools_response, "tools") else tools_response
                
                self.discovered_tools[name] = [t.name for t in tools_list]
                logger.info(f"Server '{name}' initialized with tools: {self.discovered_tools[name]}")
                
            except Exception as e:
                logger.error(f"Failed to launch MCP Server '{name}': {str(e)}")
                raise e

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict = None) -> dict:
        """
        Invokes a tool on a specific MCP server.
        
        Args:
            server_name (str): Name of the target server.
            tool_name (str): Name of the tool.
            arguments (dict): Inputs for the tool.
            
        Returns:
            dict: The result payload of the tool execution.
        """
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"MCP Session '{server_name}' is not running.")
            
        arguments = arguments or {}
        
        # Invoke tool via protocol
        response = await session.call_tool(tool_name, arguments)
        
        # Parse result: response.content holds text block
        # FastMCP returns a CallToolResult which contains a list of contents
        if hasattr(response, "content") and response.content:
            first_block = response.content[0]
            if hasattr(first_block, "text"):
                text_val = first_block.text
            else:
                text_val = str(first_block)
                
            logger.info(f"Raw tool response (truncated): {text_val[:500]}")
            # Try parsing JSON if applicable
            try:
                return json.loads(text_val)
            except json.JSONDecodeError:
                return text_val
                
        return {"success": False, "error": "Empty response from tool"}

    async def stop_all(self):
        """
        Gracefully terminates all running MCP client sessions and subprocesses.
        """
        logger.info("Stopping MCP client sessions...")
        try:
            await self.exit_stack.aclose()
            self.sessions.clear()
            self.discovered_tools.clear()
            logger.info("All MCP servers terminated successfully.")
        except Exception as e:
            logger.error(f"Error while shutting down MCP servers: {str(e)}")
