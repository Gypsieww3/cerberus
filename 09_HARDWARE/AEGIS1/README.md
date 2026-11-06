# AEGIS-1 Neural Engine v0.2 (experimental)
Independent hardware development while MOSS/KYVRAEL continues separately.

## Implemented
- `aegis_dot4_int8`: 4 signed INT8 multipliers, 32-bit signed sum, accumulates on each accepted `start`.
- `clear_acc`: clears accumulator when idle; with `start`, replaces accumulator with current dot product.
- `valid` pulses high on every `start` clock edge; result registers on that same edge.
- Wraparound 32-bit signed arithmetic (no overflow flag or saturation).
- Standalone testbench covering positive, negative, accumulated, cleared and reset cases.

## Simulation (from repo root)
```sh
iverilog -g2012 -s aegis_dot4_tb -o aegis_dot4_tb.vvp 09_HARDWARE/AEGIS1/rtl/aegis_dot4_int8.sv 09_HARDWARE/AEGIS1/tb/aegis_dot4_tb.sv
vvp aegis_dot4_tb.vvp
```

## Explicit limitations
This is *not* a complete NPU, chip, FPGA prototype, driver, inference runtime, or RISC-V instruction extension. It has no backpressure, bus interface, DMA, interrupt, memory subsystem or clock-domain crossing. `start` is sampled every cycle (throughput one 4-lane dot product/clock in this behavioral RTL; no timing or silicon performance claim).

## Next engineering milestones
1. Add a register-mapped peripheral wrapper with a documented ready/valid contract.
2. Add randomized tests against a software reference and overflow tests.
3. Integrate with the existing RV32I experiment using a non-conflicting memory map.
4. Build sensor I/O, privilege boundary, and low-power interfaces as independently testable modules.
5. Use synthesis and timing reports before making FPGA, energy, or speed claims.
