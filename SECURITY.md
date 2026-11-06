# Security and publication policy

This is a **public** GitHub repository. Source review is required before publishing research code, particularly the MOSS agent, optional external providers, trading adapters and processor IP.

Do not commit passwords, API keys, private phone numbers, identity documents, private email, trading credentials, Ollama model weights, personal chat history, live SQLite memory, logs, backups, or unpublished commercial partner proposals.

Public examples should default to **simulation / paper / dry-run**. Commands with live trading, hardware actuation or unrestricted PC control must never be enabled by documentation examples.

If a secret is discovered in a commit, rotate or revoke the secret immediately and assess whether public history needs cleanup. A .gitignore does not erase secrets already committed.
