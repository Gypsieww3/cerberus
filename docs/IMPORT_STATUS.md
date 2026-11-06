# GitHub source import status — 2026-11-06

## Confirmed published on main

- Original website: `index.html` at root, preserved and deployed by GitHub Pages.
- Independent project folders: 01 through 12, each with descriptive README.
- Real source code from owner-provided archives:
  - `07_ROBOTICA/calcular.py`, `07_ROBOTICA/load_model.py` (TR-003 static torque model)
  - `08_PROMETHEUS/inspection.py` (synthetic grayscale inspection)
  - `09_HARDWARE/RV32I_TRACE/tools/verify_reference.py` and `tb/program.hex` (reference checker only; RTL not published)
- `.github/workflows/engineering-smoke.yml`: GitHub Actions **passed** on 2026-11-06 for Python reference/smoke checks. These are not end-to-end project validations.

## Located and prepared for source import

A separate **CERBERUS_PROJETOS_FONTE_ORGANIZADO.zip** package was prepared from source archives in the user's ChatGPT Library (464 files, including Python, documentation and independent tests; 112 archive entries omitted as runtime state / likely sensitive material). It contains an import script that asks for an explicit confirmation **before publishing**.

The package is available from the conversation attachment and **is not automatically available on GitHub**.

| Source archive | Import status |
|---|---|
| `MOSS_KYVRAEL_v5_25_4_VERIFICACAO_AMPLIADA.zip` | Full code staged in package; not yet online |
| `ARKHE_INDEPENDENTE_v0_6_1.zip` | Full selected code staged; not yet online |
| `PROMETHEUS_INDEPENDENTE_v0_6_1.zip` | Inspection module online; remaining selected code staged |
| `TR003_INDEPENDENTE_v0_6_1.zip` | Load estimate + CLI online; remaining code staged |
| `KIM_INDEPENDENTE_v0_6_1.zip` | Selected paper-trading code staged; not yet online |
| `CERBERUS_RV32I_TRACE_v0_1_PROTO.zip` | Reference checker online; RTL, simulation files staged |
| `CERBERUS_ECOSYSTEM_v0_6_PILOTOS.zip` | Selected integration scripts staged; duplicated runtimes omitted |

## Local checks already performed

- 239 Python source files in staging: **no compile-time syntax errors found**.
- RISC-V instruction-program reference checker: **passed**, but not a simulation of RTL.
- TR-003 static example: **passed**; no physical motor has been tested.
- MOSS independent packaging test: **did not finish within the 20-second local check window**; result is inconclusive, not a success or a diagnosed defect.
- Full MOSS 240+ reported runtime/test problems: **not verified fixed**.

## Security and engineering constraints

1. GitHub repository is **public**. Unreviewed proprietary processor RTL should not be published without considering IP/licensing strategy.
2. Never commit API keys, personal or financial data, databases, local logs or model binaries.
3. MOSS archive includes permissive autonomous-control settings; use a reviewed and restrictive local config for all tests.
4. Independent project code remains in separate project folders, not mixed into the ecosystem directory.
