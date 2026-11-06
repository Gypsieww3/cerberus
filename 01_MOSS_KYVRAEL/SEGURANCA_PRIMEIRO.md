# MOSS — segurança antes de executar

The source v5.25.4 archive contains an existing `config.json` with
`auto_approve_all: true`, `pc_control_enabled: true` and
`risk_auto_approve` including `execute` and `network`.
These settings are **not appropriate for first-run testing** on a personal computer.

Before running code:
1. Create a copy in an isolated working directory.
2. Set `auto_approve_all` to `false`.
3. Set `pc_control_enabled` and `web_research_enabled` to `false` during initial smoke tests.
4. Set each sensitive `approval_required` action to `true`: file writes/deletes/moves, execute, install, downloads, PC input, publish, messages, payments.
5. Limit `risk_auto_approve` to `["read"]`; keep live self-improvement disabled.
6. Keep passwords and local memory out of version control.
7. Test in a sandbox with disposable data; do not run autonomy with real credentials or external brokerage/hardware accounts.

These are safety recommendations, **not proof that the program enforces them correctly**. Verify the actual authorization paths before trusting the configuration.
