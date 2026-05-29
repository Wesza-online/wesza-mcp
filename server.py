#!/usr/bin/env python3
"""
Wesza MCP Server
Deploy and manage apps on Wesza from Claude, Cursor, or any MCP client.

Usage:
    WESZA_API_TOKEN=your_token python server.py

Claude Desktop config (~/.config/claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "wesza": {
          "command": "python",
          "args": ["/path/to/wesza_mcp/server.py"],
          "env": { "WESZA_API_TOKEN": "your_token_here" }
        }
      }
    }
"""

import asyncio
import os
import sys

import httpx

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError:
    sys.exit("Install the MCP package first:  pip install mcp")

BASE_URL = os.environ.get("WESZA_API_URL", "https://wesza.online")
TOKEN = os.environ.get("WESZA_API_TOKEN", "")

server = Server("wesza")


async def _api(method: str, path: str, **kwargs):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        r = await client.request(method, f"/api/v1{path}", headers=headers, **kwargs)
        r.raise_for_status()
        return r.json()


def _fmt_app(a: dict) -> str:
    name   = a.get("name", "?")
    status = a.get("status", "?")
    url    = a.get("app_url") or a.get("subdomain_url") or "—"
    fw     = a.get("framework") or ""
    aid    = a.get("id", "?")
    fw_str = f" · {fw}" if fw else ""
    return f"• {name} [{status}]{fw_str}\n  URL: {url}\n  ID:  {aid}"


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_apps",
            description="List all your deployed apps with status, URL, and framework.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_app",
            description="Get full details for one app — status, URL, framework, server, last deploy time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"}
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="deploy_app",
            description="Deploy a new app from a GitHub repository URL. Returns the app ID to track progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "github_url": {"type": "string", "description": "Full GitHub repo URL (https://github.com/you/repo)"},
                    "name":       {"type": "string", "description": "Optional display name for the app"},
                    "branch":     {"type": "string", "description": "Git branch to deploy (default: main)"},
                    "server_id":  {"type": "string", "description": "Server ID to deploy to (from list_servers). Leave blank if you only have one server."},
                    "env_vars":   {"type": "object", "description": "Env vars to inject at deploy time (key → value)"},
                },
                "required": ["github_url"],
            },
        ),
        types.Tool(
            name="redeploy_app",
            description="Pull the latest code and redeploy an existing app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"}
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="restart_app",
            description="Restart a running app's process without redeploying (no code pull).",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"}
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="delete_app",
            description="Delete a deployed app and stop its process. Irreversible — requires confirm=true.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id":  {"type": "string",  "description": "App ID from list_apps"},
                    "confirm": {"type": "boolean", "description": "Must be true to confirm deletion"},
                },
                "required": ["app_id", "confirm"],
            },
        ),
        types.Tool(
            name="get_logs",
            description="Fetch recent runtime logs (stdout/stderr) from a deployed app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string",  "description": "App ID from list_apps"},
                    "lines":  {"type": "integer", "description": "Number of log lines (default 100, max 500)"},
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="set_env_vars",
            description="Set or update environment variables for an app. Changes take effect after the next redeploy.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"},
                    "vars":   {"type": "object", "description": "Key-value pairs to set (e.g. {\"SECRET_KEY\": \"abc123\"})"},
                },
                "required": ["app_id", "vars"],
            },
        ),
        types.Tool(
            name="get_env_vars",
            description="List environment variable keys for an app. Values are masked for security.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"}
                },
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="delete_env_var",
            description="Delete a specific environment variable from an app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"},
                    "key":    {"type": "string", "description": "Name of the env var to delete"},
                },
                "required": ["app_id", "key"],
            },
        ),
        types.Tool(
            name="list_servers",
            description="List all your connected VPS servers and their connection status.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_server_incidents",
            description="Get recent AI-resolved incidents and auto-fixes for a server.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Server ID from list_servers"},
                    "limit":     {"type": "integer", "description": "Max incidents to return (default 10)"},
                },
                "required": ["server_id"],
            },
        ),
        types.Tool(
            name="add_domain",
            description="Set a custom domain for an app (Builder plan or higher required).",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string", "description": "App ID from list_apps"},
                    "domain": {"type": "string", "description": "Domain (e.g. api.yourcompany.com)"},
                },
                "required": ["app_id", "domain"],
            },
        ),
        types.Tool(
            name="get_usage",
            description="Get your plan usage — deploys used, AI fixes remaining, credit balance, plan name.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="run_command",
            description="Run a whitelisted shell command on an app's server (e.g. run migrations, clear cache).",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "Server ID from list_servers"},
                    "command":   {"type": "string", "description": "Shell command to run"},
                },
                "required": ["server_id", "command"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    def txt(s: str) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=s)]

    try:
        if name == "list_apps":
            data = await _api("GET", "/deploy")
            apps = data.get("deployments", data) if isinstance(data, dict) else data
            if not apps:
                return txt("No apps deployed yet. Use deploy_app to get started.")
            return txt("\n\n".join(_fmt_app(a) for a in apps))

        elif name == "get_app":
            d = await _api("GET", f"/deploy/{arguments['app_id']}")
            lines = [
                f"Name:      {d.get('name')}",
                f"Status:    {d.get('status')}",
                f"URL:       {d.get('app_url') or d.get('subdomain_url') or '—'}",
                f"Framework: {d.get('framework') or 'unknown'}",
                f"Port:      {d.get('port') or '—'}",
                f"Server:    {d.get('server_id') or 'unassigned'}",
                f"Branch:    {d.get('branch') or 'main'}",
                f"Repo:      {d.get('github_url') or '—'}",
                f"Updated:   {d.get('updated_at') or '—'}",
                f"ID:        {d.get('id')}",
            ]
            return txt("\n".join(lines))

        elif name == "deploy_app":
            payload: dict = {"repo_url": arguments["github_url"]}
            if arguments.get("name"):      payload["name"]      = arguments["name"]
            if arguments.get("branch"):    payload["branch"]    = arguments["branch"]
            if arguments.get("server_id"): payload["server_id"] = arguments["server_id"]
            if arguments.get("env_vars"):
                payload["env"] = [{"key": k, "value": v} for k, v in arguments["env_vars"].items()]
            data = await _api("POST", "/deploy", json=payload)
            aid  = data.get("id", "?")
            url  = data.get("app_url") or data.get("subdomain_url") or "provisioning…"
            return txt(f"Deploy started!\nApp ID: {aid}\nURL:    {url}\n\nUse get_logs(app_id='{aid}') to stream the deploy log.")

        elif name == "redeploy_app":
            data = await _api("POST", f"/deploy/{arguments['app_id']}/redeploy")
            return txt(f"Redeploy triggered: {data.get('message', data)}")

        elif name == "restart_app":
            data = await _api("POST", f"/deploy/{arguments['app_id']}/restart")
            return txt(f"Restart initiated: {data.get('message', data)}")

        elif name == "delete_app":
            if not arguments.get("confirm"):
                return txt("Deletion cancelled. Pass confirm=true to permanently delete this app.")
            await _api("DELETE", f"/deploy/{arguments['app_id']}")
            return txt(f"App {arguments['app_id']} has been deleted.")

        elif name == "get_logs":
            lines = min(int(arguments.get("lines", 100)), 500)
            data  = await _api("GET", f"/deploy/{arguments['app_id']}/logs/runtime?lines={lines}")
            raw_logs = data.get("logs", [])
            status   = data.get("status", "unknown")
            pid      = data.get("pid")
            # logs may be list of strings or list of dicts {"text": "...", "ts": ...}
            log_lines = [
                (l.get("text", str(l)) if isinstance(l, dict) else str(l))
                for l in raw_logs
            ]
            header = f"[status: {status}" + (f" · pid: {pid}" if pid else "") + "]\n"
            body   = "\n".join(log_lines) if log_lines else "(no logs yet)"
            return txt(header + body)

        elif name == "set_env_vars":
            payload = {"secrets": [{"key": k, "value": v} for k, v in arguments["vars"].items()]}
            data    = await _api("POST", f"/deploy/{arguments['app_id']}/secrets", json=payload)
            return txt(f"Saved {len(arguments['vars'])} env var(s). {data.get('message', '')}\nRedeploy the app to apply changes.")

        elif name == "get_env_vars":
            data = await _api("GET", f"/deploy/{arguments['app_id']}/secrets")
            secrets = data.get("secrets", [])
            if not secrets:
                return txt("No environment variables set for this app.")
            lines = [f"  {s['key']} = {s['value']}" for s in secrets]
            return txt("Environment variables (values masked):\n" + "\n".join(lines))

        elif name == "delete_env_var":
            await _api("DELETE", f"/deploy/{arguments['app_id']}/secrets/{arguments['key']}")
            return txt(f"Deleted env var: {arguments['key']}")

        elif name == "list_servers":
            data    = await _api("GET", "/servers")
            servers = data.get("servers", data) if isinstance(data, dict) else data
            if not servers:
                return txt("No servers connected.\nRun the one-line agent install on your VPS and connect it to Wesza.")
            lines = []
            for s in servers:
                lines.append(
                    f"• {s.get('name','?')} [{s.get('status','?')}]\n"
                    f"  IP: {s.get('ip','?')} · ID: {s.get('id','?')}"
                )
            return txt("\n\n".join(lines))

        elif name == "get_server_incidents":
            limit  = int(arguments.get("limit", 10))
            data   = await _api("GET", f"/servers/{arguments['server_id']}/incidents?limit={limit}")
            incs   = data.get("incidents", data) if isinstance(data, dict) else data
            if not incs:
                return txt("No incidents recorded for this server.")
            lines = []
            for inc in incs:
                lines.append(
                    f"• [{inc.get('status','?')}] {inc.get('summary') or inc.get('title','?')}\n"
                    f"  {inc.get('created_at','?')}"
                )
            return txt("\n\n".join(lines))

        elif name == "add_domain":
            data = await _api("POST", f"/deploy/{arguments['app_id']}/domain",
                              json={"domain": arguments["domain"]})
            return txt(f"Domain configured: {data.get('message', data)}")

        elif name == "get_usage":
            data = await _api("GET", "/account/summary")
            u = data.get("usage", data)
            bal = data.get("balance", {})
            bal_str = f"${bal.get('current', '?'):.2f}" if isinstance(bal, dict) else f"${bal}"
            plan = data.get("plan") or data.get("user", {}).get("plan", "?")
            lines = [
                f"Plan:           {plan}",
                f"Deploys used:   {u.get('deploys_used', '?')} / {u.get('deploys_limit', '?')}",
                f"AI fixes used:  {u.get('fixes_used', '?')} / {u.get('fixes_limit', '?')}",
                f"Credit balance: {bal_str}",
            ]
            return txt("\n".join(lines))

        elif name == "run_command":
            data = await _api("POST", f"/servers/{arguments['server_id']}/chat",
                              json={"message": arguments["command"]})
            return txt(data.get("response") or data.get("output") or str(data))

        else:
            return txt(f"Unknown tool: {name}")

    except httpx.HTTPStatusError as e:
        return txt(f"API error {e.response.status_code}: {e.response.text[:400]}")
    except Exception as e:
        return txt(f"Error: {e}")


async def main():
    if not TOKEN:
        sys.exit(
            "Error: WESZA_API_TOKEN is not set.\n"
            "Get your token from wesza.online/dashboard → Settings → API Token\n"
            "Then run:  WESZA_API_TOKEN=your_token python server.py"
        )
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main_sync():
    """Entrypoint for `wesza-mcp` console script."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
