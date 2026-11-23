# ContextOps MCP server

This package is intentionally reserved for the authenticated remote MCP transport.

When implemented, its tool handlers must call the same service layer as `services/api/app/services`; tools must not duplicate retrieval, authorization, or action logic.

Initial tool contract:

```text
contextops_search
contextops_get_citation
contextops_run_agent
contextops_create_action_preview
contextops_execute_approved_action
```

All tools require workspace-scoped authentication and audit logging. Any write-capable tool must be split into preview and explicit approval/execution stages.
