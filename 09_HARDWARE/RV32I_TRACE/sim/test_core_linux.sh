#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."/..
out="$(mktemp)"
trap 'rm -f "$out"' EXIT
iverilog -g2012 -Wall -s core_tb -o "$out" \
  09_HARDWARE/RV32I_TRACE/rtl/cerberus_rv32i_core.sv \
  09_HARDWARE/RV32I_TRACE/tb/core_tb.sv
vvp "$out"
