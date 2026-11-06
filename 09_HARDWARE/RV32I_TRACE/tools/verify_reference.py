"""Independent Python check for the smoke-test program's machine-code words.

Important: this checks the *test program*, not the SystemVerilog RTL. RTL must
be compiled and simulated with Icarus Verilog or another HDL simulator.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = [int(x, 16) for x in (ROOT / 'tb' / 'program.hex').read_text().split()]


def sign_extend(n: int, width: int) -> int:
    return n - (1 << width) if n & (1 << (width - 1)) else n


def simulate(program: list[int]) -> tuple[list[int], list[int], int, int]:
    pc = 0
    gpr = [0] * 32
    mem = [0] * 64
    retired = 0
    for _ in range(32):
        assert 0 <= pc // 4 < len(program), 'Unexpected PC beyond program'
        word = program[pc // 4]
        opcode, rd, f3 = word & 127, (word >> 7) & 31, (word >> 12) & 7
        rs1, rs2 = (word >> 15) & 31, (word >> 20) & 31
        next_pc = pc + 4
        if word == 0x00000073:
            return gpr, mem, retired, pc
        if opcode == 0x13 and f3 == 0:  # addi
            imm = sign_extend(word >> 20, 12)
            gpr[rd] = (gpr[rs1] + imm) & 0xFFFFFFFF
        elif opcode == 0x33 and f3 == 0 and word >> 25 == 0:  # add
            gpr[rd] = (gpr[rs1] + gpr[rs2]) & 0xFFFFFFFF
        elif opcode == 0x23 and f3 == 2:  # sw
            imm = sign_extend(((word >> 25) << 5) | ((word >> 7) & 31), 12)
            address = gpr[rs1] + imm
            assert address % 4 == 0 and address // 4 < len(mem)
            mem[address // 4] = gpr[rs2]
        elif opcode == 0x03 and f3 == 2:  # lw
            imm = sign_extend(word >> 20, 12)
            address = gpr[rs1] + imm
            assert address % 4 == 0 and address // 4 < len(mem)
            gpr[rd] = mem[address // 4]
        elif opcode == 0x63 and f3 == 0:  # beq
            imm = (((word >> 31) & 1) << 12) | (((word >> 7) & 1) << 11)
            imm |= (((word >> 25) & 63) << 5) | (((word >> 8) & 15) << 1)
            if gpr[rs1] == gpr[rs2]:
                next_pc = pc + sign_extend(imm, 13)
        else:
            raise AssertionError(f'Unsupported smoke-program instruction 0x{word:08x}')
        gpr[0] = 0
        retired += 1
        pc = next_pc
    raise AssertionError('ECALL not reached within 32 steps')


def main() -> None:
    assert len(PROGRAM) == 9
    regs, memory, retired, trap_pc = simulate(PROGRAM)
    assert (regs[1], regs[2], regs[3], regs[4], regs[5], regs[6]) == (5, 7, 12, 12, 0, 1)
    assert memory[0] == 12
    assert retired == 7 and trap_pc == 32
    print('PASS: independent instruction-program reference check (not RTL simulation)')


if __name__ == '__main__':
    main()
