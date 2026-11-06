# AEGIS-1 v0.3 — Neural Peripheral Integration Specification

Independent of MOSS/KYVRAEL development. This is a *prototype local 32-bit slave*, not AMBA AXI, Wishbone, PCIe, or a complete SoC.

## Interface
- Synchronous, single-clock and active-high synchronous reset.
- Always ready: `bus_ready=1`. Request is accepted at rising clock if `bus_valid` and not `bus_error`.
- `bus_error` combinationally flags unaligned, unmapped and read-only writes during valid requests.
- 32-bit data, 8-bit byte offset, no byte strobes. Accesses are aligned words only.
- Reads are combinational. CPU or master samples `bus_rdata` while holding a valid address.
- Write A and B first, then write CONTROL with START. Read RESULT after the following rising edge.
- All register addresses are *offsets inside this slave*, not system physical addresses. System interconnect must decode a base address later.

## Register map

| Offset | Register | R/W | Meaning |
|---|---|---|---|
| 0x00 | A | R/W | Four packed signed INT8 input elements, little-endian lane order |
| 0x04 | B | R/W | Four packed signed INT8 input elements |
| 0x08 | CONTROL | W | bit0 START, bit1 CLEAR_ACC, bit2 CLEAR_DONE; read returns zero |
| 0x0C | RESULT | R | 32-bit signed accumulator with wraparound |
| 0x10 | STATUS | R | bit0 DONE sticky, clear by CONTROL bit2 |
| 0x14 | ID | R | 0x41454731 = ASCII AEG1 |

Writing CONTROL 0x3 replaces the current accumulator with the dot product of A and B.
Writing CONTROL 0x1 adds the dot product to the running accumulator.
Writing CONTROL 0x2 zeros the accumulator without performing a dot product.
Writing CONTROL 0x4 clears DONE. START takes priority if START and CLEAR_DONE are both set.

## Integration constraints
- Not connected to existing RV32I core yet; no memory mapped access through CPU is claimed.
- No CDC, interrupts, permissions, physical protection, bus stalls, DMA or direct model inference.
- No silicon measurements, FPGA synthesis, timing closure or power measurements.
- No completed smartphone, robot or computer processor exists yet.
- Do not integrate MOSS code until the hardware bridge and ABI are stable.

## Validation
GitHub Actions workflow `.github/workflows/aegis1.yml` is configured to install Icarus Verilog, compile/test both RTL modules and execute Python model tests. Check the GitHub Actions result before marking RTL simulation as passing.

## Roadmap
1. Passing CI and testbench/RTL consistency.
2. CPU-compatible address decoder and SoC integration test.
3. Randomized RTL vs reference vectors and overflow/edge-case coverage.
4. Robot sensor/event FIFO with a safe host software interface.
5. Security controls and clock/energy domains; FPGA feasibility evaluation.
