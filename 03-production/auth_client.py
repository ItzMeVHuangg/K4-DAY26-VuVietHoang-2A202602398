"""MCP Client có Authentication — kết nối tới auth_server.py qua HTTP.

Client tạo HTTP client bằng create_mcp_http_client(headers=...) của MCP SDK
(đúng thư viện HTTP mà SDK dùng bên dưới, kèm timeout khuyến nghị). Header
Authorization được gắn vào mọi request HTTP (POST, GET, DELETE) tới server.

Cách chạy (cần auth_server.py đang chạy ở terminal khác):
    cd 03-production
    python auth_server.py            # terminal 1
    python auth_client.py            # terminal 2
"""

from __future__ import annotations

import asyncio

import os

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.shared.exceptions import MCPError

SERVER_URL = "http://localhost:8000/mcp"
TOKEN = os.environ.get("MCP_AUTH_TOKEN", "dev-token-abc123")


async def main() -> None:
    http_client = create_mcp_http_client(
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    async with http_client:
        async with streamable_http_client(SERVER_URL, http_client=http_client) as (
            read,
            write,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools = await session.list_tools()
                print("Tools (có auth):")
                for t in tools.tools:
                    print(f"  - {t.name}: {t.description}")

                result = await session.call_tool("get_weather", {"city": "Hanoi"})
                print(f"\nKết quả: {result.content[0].text}")


def _find_mcp_error(exc: BaseException) -> MCPError | None:
    """Tìm MCPError nằm sâu trong các lớp ExceptionGroup của anyio."""
    if isinstance(exc, MCPError):
        return exc
    for sub in getattr(exc, "exceptions", ()):
        found = _find_mcp_error(sub)
        if found:
            return found
    return None


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException as exc:
        err = _find_mcp_error(exc)
        if err is None:
            raise
        print(f"Token đang dùng: {TOKEN!r}")
        print(f"Xác thực thất bại: server từ chối request ({err})")
        raise SystemExit(1)
