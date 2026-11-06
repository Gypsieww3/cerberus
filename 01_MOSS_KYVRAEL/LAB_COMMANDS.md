# MOSS Lab — interface local (Windows / Linux)

This CLI is **not** the full MOSS engine. It provides an offline journal, read-only task previews and optional private notes. No external or OS actions are performed by the preview system.

In Windows CMD:

\`\`\`bat
cd 01_MOSS_KYVRAEL
ABRIR_MOSS_LAB.bat status
ABRIR_MOSS_LAB.bat preview "Verificar projeto" --actions inspect,validate,report
ABRIR_MOSS_LAB.bat list
ABRIR_MOSS_LAB.bat memory-add "Nota local para testes"
ABRIR_MOSS_LAB.bat memory-search "testes"
\`\`\`

On Linux/macOS: \`python 01_MOSS_KYVRAEL/cli.py status\`.

- Local data: \`~/.cerberus/moss_lab\`. Use \`--data-dir\` to choose a private folder.
- No cloud sync and no background execution.
- For preview completion, use \`complete-preview <mission_id>\`. This validates the preview, **not real actions**.
- For stale running mission recovery, use \`recover --older-than 3600\`. For an explicit retry use \`retry <mission_id> --approve\`.
- If you remove an archive or local database, keep independent backups; this tool does not include automatic restoration.
