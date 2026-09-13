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
            server_path = Path(__file__).resolve().parents[1] / "ga_mcp_server.py"
            parameters = StdioServerParameters(
                command=sys.executable,
                args=[str(server_path)],
                env={},
            )
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return {tool.name for tool in result.tools}

        self.assertEqual(
            asyncio.run(run_check()),
            {
                "ga_list_properties",
                "ga_get_metadata",
                "ga_run_report",
                "ga_overview",
                "ga_pages",
                "ga_sources",
                "ga_countries",
                "ga_devices",
                "ga_daily",
                "ga_realtime",
            },
        )


if __name__ == "__main__":
    unittest.main()
