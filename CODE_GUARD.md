# C.E.R.B.E.R.U.S. CODE GUARD

**Proprietary software — public product information only.**

**Status (8 November 2026):** Version 0.10.0, Windows desktop prototype available **only for a supervised evaluation after written authorization**. Source code, executable binaries, internal tests, commercial contacts and private reports are **not distributed in this public repository**.

## What it does

CERBERUS Code Guard is an experimental, local, read-only Python static-analysis tool developed under the C.E.R.B.E.R.U.S. initiative.

- Examines Python AST for selected API usage patterns requiring review.
- Highlights certain uses of `eval`, `exec`, `os.system`, subprocess, pickle and YAML loaders.
- Includes limited, intra-function tracing of simple `input()` flows to shell commands. **Not comprehensive data-flow analysis.**
- Exports JSON, SARIF and standalone HTML findings.
- Compares two scan reports to show new, persistent and not-seen findings. Not-seen findings are **not** proof of remediation.
- Scans source files locally; the scanner does not execute code under analysis.

## Technical validation

The developer's Windows PC passed 73 of 74 automated tests (one skipped because of Windows symlink privileges); a local Tk GUI smoke test and synthetic acceptance test also passed. Results are limited to the cases tested, **not an independent security audit or enterprise certification**.

The Windows executable is currently **unsigned**. It must not be run by bypassing corporate antivirus, SmartScreen or security policies. Compatibility with independent client machines has not yet been confirmed.

## Request a demonstration

**Engineering, QA and security teams:** [Open a Code Guard pilot inquiry](https://github.com/Gypsieww3/cerberus/issues/new?template=code-guard-pilot.md) to describe, in public and non-confidential terms, what your team would like to evaluate.

The first demonstration uses **synthetic Python examples only**. Any software delivery, evaluation license or commercial discussion is arranged separately under explicit written terms. Do not share internal repositories, sensitive information, passwords, phone numbers or private company records in a public issue.

## Pilot availability

A supervised pilot and demonstration can be discussed with authorized engineering/QA teams. Any evaluation requires a **separate written agreement** specifying scope, duration, recipients, rights and support. No license is granted by this public description.

## Ownership and permitted use

**© 2026 Gabriel Filipe Correia — C.E.R.B.E.R.U.S. All rights reserved.**

No permission is granted to use, reproduce, modify, host, distribute, sublicense, repackage, sell or commercially exploit CERBERUS Code Guard, its source code, binaries or protected original documentation, except as expressly authorized in advance in writing by the rightsholder, subject to mandatory legal exceptions.

**This page is not an open-source license, a free software offer, or an authorization to download/run the product.** The product is not included here.

Read the [Code Guard rights and licensing notice](CODE_GUARD_RIGHTS.md).

> Note: A public notice is not an absolute technical barrier to copying. Publicly posted text can be read and quoted where applicable law permits. Product rights and third-party component licenses remain subject to applicable law.
