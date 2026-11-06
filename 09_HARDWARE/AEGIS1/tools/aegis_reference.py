"""Reference model for the AEGIS-1 signed INT8 dot4 hardware block."""
MASK = (1 << 32) - 1

def signed8(value: int) -> int:
    value &= 0xff
    return value - 256 if value & 0x80 else value

def signed32(value: int) -> int:
    value &= MASK
    return value - (1 << 32) if value & (1 << 31) else value

def dot4(a: int, b: int) -> int:
    return signed32(sum(
        signed8(a >> (8 * i)) * signed8(b >> (8 * i))
        for i in range(4)
    ))

class NeuralEngine:
    def __init__(self):
        self.accumulator = 0
        self.valid = False

    def tick(self, *, reset=False, start=False, clear_acc=False, a=0, b=0):
        self.valid = False
        if reset:
            self.accumulator = 0
        elif start:
            result = dot4(a, b)
            self.accumulator = signed32(
                result if clear_acc else self.accumulator + result
            )
            self.valid = True
        elif clear_acc:
            self.accumulator = 0
        return self.accumulator, self.valid
