# Security and publication policy

This is a **public** GitHub repository. Source review is required before publishing research code, particularly the MOSS agent, optional external providers, trading adapters and processor IP.

Do not commit passwords, API keys, private phone numbers, identity documents, private email, trading credentials, Ollama model weights, personal chat history, live SQLite memory, logs, backups, or unpublished commercial partner proposals.

Public examples should default to **simulation / paper / dry-run**. Commands with live trading, hardware actuation or unrestricted PC control must never be enabled by documentation examples.

If a secret is discovered in a commit, rotate or revoke the secret immediately and assess whether public history needs cleanup. A .gitignore does not erase secrets already committed.

## Control Plane supervised Docker tasks (Alpha 0.2)

The Control Plane accepts only predefined task identifiers, not shell commands, source paths, URLs, docker images, environment variables or arguments from the browser. Each mission requires a short-lived one-time approval ticket and authenticated second confirmation. The Docker CLI enforces `--pull=never`, `--network none`, read-only repository and root filesystem, non-root UID, dropped capabilities, CPU/memory/PID bounds and a timeout. There is no host command fallback if Docker is not available.

The local audit SQLite database is stored outside the Git repository at `~/.cerberus/control_plane/missions.sqlite3` and is **not encrypted at rest**. Summarized output may contain repository filenames or test data; never feed it private client code. Unclean process termination can leave an orphaned Docker container despite the recovery of SQLite records. This environment is **not** independently hardened or certified for untrusted customer code.
