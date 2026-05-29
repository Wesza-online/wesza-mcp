# Wesza MCP Server

Deploy and manage your apps from inside **Claude**, **Cursor**, or **Windsurf** — no terminal switching needed.

## What it does

Once connected, you can say things like:

> *"Deploy my GitHub repo to Wesza"*
> *"Show me the logs for my Flask app"*
> *"Set DATABASE_URL for my backend and redeploy"*
> *"What apps do I have running?"*

And the AI handles it.

## Tools available

| Tool | What it does |
|------|-------------|
| `list_apps` | Show all your deployed apps with status and URL |
| `get_app` | Full details for one app |
| `deploy_app` | Deploy a new app from a GitHub URL |
| `redeploy_app` | Pull latest code and redeploy |
| `restart_app` | Restart without redeploying |
| `delete_app` | Delete an app (requires confirm=true) |
| `get_logs` | Read runtime stdout/stderr logs |
| `set_env_vars` | Set environment variables |
| `get_env_vars` | List env var keys (values masked) |
| `delete_env_var` | Remove an env var |
| `list_servers` | Show connected VPS servers |
| `get_server_incidents` | See AI-resolved incidents |
| `add_domain` | Set a custom domain |
| `get_usage` | Plan usage and credit balance |
| `run_command` | Run a shell command on a server |

## Setup

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (Mac/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "wesza": {
      "command": "python",
      "args": ["-m", "wesza_mcp.server"],
      "env": {
        "WESZA_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project (or the global `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "wesza": {
      "command": "python",
      "args": ["-m", "wesza_mcp.server"],
      "env": {
        "WESZA_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Get your API token

1. Go to [wesza.online/dashboard](https://wesza.online/dashboard)
2. Settings → API Token → Copy

## Install

```bash
pip install wesza-mcp
```

Or run without installing:

```bash
pip install mcp httpx
WESZA_API_TOKEN=your_token python -m wesza_mcp.server
```
