from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import gsc_client
import gsc_mcp_server

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:  # pragma: no cover - depends on the test environment
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

@unittest.skipIf(ClientSession is None, "mcp is not installed")
class InProcessToolTests(unittest.TestCase):
    """Exercises tool bodies directly (no subprocess), so gsc_client can be mocked.

    gsc_inspect previously crashed with "Object of type InspectionResult is not
    JSON serializable" because it returned the dataclass gsc_client.inspect_url
    gives back without converting it — the CLI's own inspect report does that
    conversion itself, so this gap only showed up through the MCP tool.
    """

    def test_gsc_inspect_serializes_the_inspection_result(self):
        fake_result = gsc_client.InspectionResult(
            page_url="https://example.com/a", verdict="PASS", coverage_state="Submitted and indexed"
        )
        with (
            patch.object(gsc_client, "resolve_site_url", return_value="sc-domain:example.com"),
            patch.object(gsc_client.Settings, "from_env", return_value=gsc_client.Settings(None, None)),
            patch.object(gsc_client, "inspect_url", return_value=fake_result),
        ):
            server = gsc_mcp_server.create_server()
            content, _ = asyncio.run(
                server.call_tool("gsc_inspect", {"page_url": "https://example.com/a"})
            )
        payload = json.loads(content[0].text)
        self.assertEqual(payload["site_url"], "sc-domain:example.com")
        self.assertEqual(payload["verdict"], "PASS")
        self.assertEqual(payload["coverage_state"], "Submitted and indexed")


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
