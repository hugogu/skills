from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:  # pragma: no cover - depends on the test environment
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


@unittest.skipIf(ClientSession is None, "mcp is not installed")
class MCPProtocolTests(unittest.TestCase):
    def test_stdio_server_lists_tools(self):
        async def run_check():
            server_path = Path(__file__).resolve().parents[1] / "gsc_mcp_server.py"
            parameters = StdioServerParameters(command=sys.executable, args=[str(server_path)], env={})
            async with stdio_client(parameters) as (read_stream, write_stream), ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return {tool.name for tool in result.tools}

        self.assertEqual(
            asyncio.run(run_check()),
            {
                "gsc_properties",
                "gsc_search",
                "gsc_performance",
                "gsc_page_queries",
                "gsc_compare",
                "gsc_sitemaps",
                "gsc_inspect",
                "gsc_indexing",
                "gsc_site_audit",
            },
        )

    def test_stdio_server_returns_clean_error_without_credentials(self):
        async def run_check():
            server_path = Path(__file__).resolve().parents[1] / "gsc_mcp_server.py"
            parameters = StdioServerParameters(
                command=sys.executable, args=[str(server_path)], env={"GSC_CREDENTIALS_PATH": ""}
            )
            async with stdio_client(parameters) as (read_stream, write_stream), ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("gsc_properties", {})
                return result.content[0].text

        self.assertIn("No credentials configured", asyncio.run(run_check()))


if __name__ == "__main__":
    unittest.main()
