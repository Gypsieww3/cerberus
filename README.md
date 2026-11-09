> **USO RESTRITO — PROJETOS PROPRIETÁRIOS.** © 2026 Gabriel Filipe Correia, quanto às partes originais de sua titularidade. A visualização deste repositório público **não concede licença para copiar, redistribuir, revender ou usar comercialmente** os componentes proprietários. Só está permitida a interação com a [demonstração pública MOSS](demo/) no navegador, dentro das [condições de avaliação](EVALUATION_TERMS.md). Os direitos de terceiros e eventuais cotitulares legítimos mantêm-se. Consulte [LICENSE](LICENSE) e o [índice de direitos dos projetos](PROJECT_RIGHTS_INDEX.md). **Atenção:** como o repositório é público, o código já publicado é tecnicamente visível e copiável; os avisos não são proteção anticópia.

# C.E.R.B.E.R.U.S. — Engineering & Research Portfolio

**Cognitive Engineering, Robotics, Bio-inspired Evolution & Research for Unified Systems**

Experimental technology initiative in Curitiba, Brazil. The repository contains independent projects and a shared engineering roadmap. **Not all listed projects are completed or commercially validated.**

## New: local CERBERUS Control Plane (Alpha 0.1)

A **working, read-only control panel** can check the health of approved localhost APIs for MOSS Lab, Telemetry Studio and O Olho Que Tudo Vê. It does **not** execute programs or give autonomous access to the computer. Run `03_CERBERUS_CORE/ABRIR_CONTROL_PLANE.bat` on Windows, then open `http://127.0.0.1:8890/` and enter the temporary token displayed in the terminal. See [integration contract](docs/INTEGRATION_CONTRACT.md) and [product verification matrix](docs/RELEASE_MATRIX.md).

## Featured software — CERBERUS Code Guard

**Python static-analysis desktop tool | Windows | Proprietary | Supervised pilot by request**

CERBERUS Code Guard v0.10.0 scans Python source locally for selected risk patterns, supports limited input-to-shell tracing, exports JSON/SARIF/HTML reports, and compares scans across development iterations. It is a **working experimental prototype**, not certified security software. Development-PC validation: **73 tests passed, 1 skipped**; external client validation is still pending.

**For software engineering teams:** [View product overview and technical limitations](CODE_GUARD.md) · [Request a supervised pilot](https://github.com/Gypsieww3/cerberus/issues/new?template=code-guard-pilot.md) · [Read restricted rights](CODE_GUARD_RIGHTS.md)

> **No source code, downloadable executable or software-use license is published for Code Guard here.** Demonstrations and evaluations require prior written agreement. A public issue is visible to everyone; do not post confidential projects, passwords or private company information.

---

## New public demonstrations and product information (November 2026)

- [TERRA VIVA — open the browser demo](https://gypsieww3.github.io/cerberus-terra-viva-demo/) — static snapshot, not live human-level AI.
- [Telemetry Studio — product details](docs/TELEMETRY_STUDIO_PUBLIC.md) — private, usable local CSV/SQLite prototype; 11 local tests and cross-platform CI.
- [Core Commander — product details](docs/CORE_COMMANDER_PUBLIC.md) — private Windows engineering source, 104 local tests (one skipped), cross-platform delivery not certified.
- [Code Guard — product information](CODE_GUARD.md) — private 0.10 source, automated Windows CI; supervised pilots only.
- [Control Plane — read-only integration contract](docs/INTEGRATION_CONTRACT.md) — local localhost health monitoring, not unattended agent control.

Public showcase: [clickable products and demos](projects.html). Software rights, testing limitations and commercial pilot conditions are documented separately.

## Projects

| Folder | Project | Stage / existing evidence |
|---|---|---|
| [01_MOSS_KYVRAEL](01_MOSS_KYVRAEL/README.md) | MOSS / KYVRAEL | Experimental local multi-agent AI; archived v5.25.4 located |
| [02_ARKHE](02_ARKHE/README.md) | ARKHÉ ∅ | Scientific functional-concept experiments; independent archive v0.6.1 |
| [03_CERBERUS_CORE](03_CERBERUS_CORE/README.md) | Shared ecosystem | v0.6 pilot package located; validation is environment-specific |
| [04_WEBSITE](04_WEBSITE/README.md) | Website | Existing website is still hosted at repository-root `index.html` |
| [05_TRADING](05_TRADING/README.md) | KIM / Quant Lab; trading research | Paper-trading prototype v0.6.1; no live-trading promise |
| [06_LOTOFACIL](06_LOTOFACIL/README.md) | Lotofácil research | Analysis and reproducible statistics concept |
| [07_ROBOTICA](07_ROBOTICA/README.md) | TR-003 robotics | Static load modelling / independent archive v0.6.1 |
| [08_PROMETHEUS](08_PROMETHEUS/README.md) | PROMETHEUS Industrial | Synthetic PGM image inspection prototype v0.6.1 |
| [09_HARDWARE](09_HARDWARE/README.md) | RV32I-TRACE processor and GENESIS X phone | RTL design prototype v0.1 / concept-stage handset |
| [10_EMPRESA](10_EMPRESA/README.md) | Organization, partners, and planning | Public-only reference; no personal documents |
| [11_MODELOS_IA](11_MODELOS_IA/README.md) | Local AI / Ollama integration | Setup, model manifests, performance experiments |
| [12_BACKUPS](12_BACKUPS/README.md) | Backup and reproducibility | Policies and restore instructions, no personal data |
| [13_OLHO_QUE_TUDO_VE](13_OLHO_QUE_TUDO_VE/README.md) | O Olho Que Tudo Vê / FinGINT | Plataforma de simulação financeira geoespacial v1.1; apresentação pública, código proprietário não publicado |

## Important distinctions

- **Present in GitHub**: files visible in this repository, including this catalog and the existing website.
- **Located in the owner's project library**: archives identified during inventory; they are **not automatically imported to GitHub**.
- **Tests**: only explicitly recorded results count; successful tests in one environment do not prove Windows, FPGA, silicon or production readiness.
- **Public repository**: never upload API keys, tokens, SQLite personal memory, local logs, private communications, proprietary assets or unreviewed model weights.

See [import status](docs/IMPORT_STATUS.md), [roadmap](docs/ROADMAP.md) and [security policy](SECURITY.md).

The owner retains the rights applicable to original work. **No open-source license is granted by this README.**
