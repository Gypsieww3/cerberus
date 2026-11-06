#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
command -v iverilog >/dev/null && command -v vvp >/dev/null || { echo "Install Icarus Verilog" >&2; exit 2; }
build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
iverilog -g2012 -Wall -s core_tb -o "$build/core.out" \
  09_HARDWARE/RV32I_TRACE/rtl/cerberus_rv32i_core.sv \
  09_HARDWARE/RV32I_TRACE/tb/core_tb.sv
vvp "$build/core.out"
