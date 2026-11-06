#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v iverilog >/dev/null || ! command -v vvp >/dev/null; then
  echo "Icarus Verilog required" >&2; exit 2
fi
build="$(mktemp -d)"
trap 'rm -rf "$build"' EXIT
iverilog -g2012 -s alu_tb -o "$build/a.out" rtl/cerberus_alu.sv tb/alu_tb.sv
vvp "$build/a.out"
