# C.E.R.B.E.R.U.S. — Product and verification matrix

Updated 2026-11-09. Only recorded evidence counts. Internal tests are **not** external client or production certification.

| Project | Source and distribution | Verified evidence | Missing for commercial readiness |
| --- | --- | --- | --- |
| [MOSS Lab](../01_MOSS_KYVRAEL/README.md) | Public experimental local API/CLI; historical MOSS engine separately stored | Repository-level Windows/Linux tests, local HTTP tests | Canonical historical integration, controlled agent runtime, packaged installation, external user acceptance |
| [Core Commander](CORE_COMMANDER_PUBLIC.md) | Private curated source repository; separate from public Control Plane | 104 local Windows tests (one skipped) and private GitHub Actions Windows CI passed 2026-11-09 | Installer, independent client pilot, integration contract and rollback |
| [Code Guard](../CODE_GUARD.md) | Proprietary Windows prototype v0.10.0, source and executable withheld from public repository | 73 passed + 1 skipped in earlier Windows tests, **not independently revalidated on client devices** | Independent tests, verified installer/signature, customer pilot |
| [Telemetry Studio](https://github.com/Gypsieww3/cerberus-telemetry-studio) | Private source, owner-only ZIP release v1.0.0 | 11 tests passed locally on Windows (2026-11-09) | CI checks across systems, installer/signature, real-sensor adapters, external pilot |
| [O Olho Que Tudo Vê](../13_OLHO_QUE_TUDO_VE/README.md) | Private source v1.1.0 | Self-tests documented in private README; external/browser validation incomplete | Dependable live authorized data sources, HTTPS deployment, security review |
| [TERRA VIVA public demo](https://gypsieww3.github.io/cerberus-terra-viva-demo/) | Public, static, Alpha 0.8 snapshot | GitHub Pages deployment succeeded 2026-11-09 | Authenticated simulation backend, interactive evolution, scientific benchmarks |
| [TERRA VIVA programs](https://github.com/Gypsieww3/cerberus-terra-viva-programs) | Private documentation and ZIP release v0.1.0-alpha | Reported offline Docker tests for small telemetry CLI; source on main not yet published | Audited private source, reproducible tests in CI, provenance |
| [RV32I-TRACE](../09_HARDWARE/RV32I_TRACE/CORE_STATUS.md) | Public experimental SystemVerilog RTL | GitHub Icarus Verilog ALU and core testbenches passed 2026-11-08 | Full ISA compliance, synthesis, FPGA test, IP/legal review |

## Definition of done for a pilot

1. Versioned source and repeatable installation/build instructions.
2. Automated tests on supported operating systems and negative-case fixtures.
3. Review of third-party component licenses and provenance.
4. No secret, PII, binary state or proprietary unpublished core in public commits.
5. Explicit known limitations, risk controls and support requirements.
6. A supervised external evaluation with written consent before a commercial claim.

## Separation of responsibilities

The new [read-only Control Plane](INTEGRATION_CONTRACT.md) checks only approved local health endpoints.
It **does not** run agent tasks, control hardware, execute trading orders, or turn static TERRA VIVA data into a live simulation.
