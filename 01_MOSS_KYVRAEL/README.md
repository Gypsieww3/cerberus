# MOSS / KYVRAEL

**Canonical archive located:** `MOSS_KYVRAEL_v5_25_4_VERIFICACAO_AMPLIADA.zip` (v5.25.4).

Experimental multi-agent AI platform with local model interaction, tasks, plans, memory and verification. The archived README reports fixes around SQLite connection closure; other Windows/Ollama problems **are not assumed fixed**.

**Status here:** project documentation; source import awaiting security filtering and comparison with canonical ZIP.

**Next validation:** Python syntax/imports, independent tests, Windows CLI smoke test, lifecycle of SQLite connections, Ollama integration and permission gates. Exclude `data/*.sqlite3*`, logs, workspace snapshots, local settings and secrets from Git. Run only in a sandbox with a copy of data.
