# Import status — 2026-11-06

This document explicitly distinguishes **inventory** from **published source**.

## Existing GitHub content

- `index.html` at the repository root was present before this organization update and is preserved.
- The folders added in this update contain project descriptions and import notes, not an assertion that all archive source code is online.

## Archives located in the owner's ChatGPT file library

| Archive | Contents (approx.) | Publication |
|---|---:|---|
| MOSS_KYVRAEL_v5_25_4_VERIFICACAO_AMPLIADA.zip | 377 files incl. runtime data, SQLite and logs | **review before source upload** |
| CERBERUS_RV32I_TRACE_v0_1_PROTO.zip | 7 source/test/docs files | **source import pending** |
| ARKHE_INDEPENDENTE_v0_6_1.zip | 28 files incl. sample data | **source import pending** |
| PROMETHEUS_INDEPENDENTE_v0_6_1.zip | 22 files | **source import pending** |
| TR003_INDEPENDENTE_v0_6_1.zip | 20 files | **source import pending** |
| KIM_INDEPENDENTE_v0_6_1.zip | 102 files; paper trading by default | **source import pending** |
| CERBERUS_ECOSYSTEM_v0_6_PILOTOS.zip | 696 files incl. duplicated components / runtime state | **selective merge pending** |

**Warning:** these archives are in the owner's file library, NOT on GitHub. Automatic bulk attachment transfer to the GitHub connector is unavailable in this session. Do not call them published until files actually appear in GitHub.

## Safe import principles

1. Import each independent project's own source, not redundant copies from the ecosystem ZIP.
2. Keep runtime state, secrets, logs, personal files and model weights outside Git.
3. Review license / commercialization implications before making novel processor IP public.
4. Compare checksums against source archives, run static checks, then tests.
5. Maintain separate project directories.
