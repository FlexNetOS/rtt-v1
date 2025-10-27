# MCP ↔ RTT Connector

Purpose: map MCP tools to RTT symbols and avoid duplicate agent files across providers.

## Steps
1) Project canonical agents into provider trees (symlinks or proxies):
```
python tools/project_providers.py
```
2) If your MCP server exports a tools list as JSON, generate RTT manifests:
```
python connector-mcp/mcp_to_rtt.py claude providers/claude/.claude/tools.json
```
3) Wire routes with RTT:
```
rtt scan && rtt plan && rtt apply
```

Notes:
- No duplicates: canonical agents live under `agents/common`. Provider trees hold symlinks or proxy JSON files.
- Mapping is recorded in `.rtt/linkmap.json`.
- Control sockets are in `connector-mcp/bridge.yaml`. Update per host.
