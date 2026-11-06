# RV32I-TRACE prototype core

Experimental single-cycle interpretation of a small RV32I instruction subset.
* Supported: ADDI/ANDI/ORI/XORI, ADD/SUB/AND/OR/XOR, LW/SW, BEQ/BNE, LUI, AUIPC, JAL, JALR, ECALL halt.
* Missing: shifts, compares, byte/halfword loads, exceptions/interrupts, CSR, real bus, memory protection, timing constraints, synthesis and ISA compliance testing.
* Memories are testbench-accessible arrays. Address space is limited to 256 bytes of instruction and 256 bytes of data.
* Invalid instructions and misaligned / out-of-range word accesses halt with a simulation trap flag.
* Test via \`bash 09_HARDWARE/RV32I_TRACE/sim/test_core_linux.sh\` with Icarus Verilog installed.
* This is **not** a complete processor, unique patentable microarchitecture or manufacturing-ready chip. It is a baseline for independently verified extension.
