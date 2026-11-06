import random
import unittest

from aegis_reference import NeuralEngine, dot4, signed32

class TestAegis(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(dot4(0x04030201, 0x08070605), 70)

    def test_negative(self):
        self.assertEqual(dot4(0xfc03feff, 0x05fc0302), -40)

    def test_extremes(self):
        self.assertEqual(dot4(0x80808080, 0x80808080), 65536)
        self.assertEqual(dot4(0x7f7f7f7f, 0x7f7f7f7f), 64516)

    def test_accumulate_and_clear(self):
        eng = NeuralEngine()
        self.assertEqual(eng.tick(start=True, clear_acc=True, a=0x04030201, b=0x08070605), (70, True))
        self.assertEqual(eng.tick(start=True, a=0x04030201, b=0x08070605), (140, True))
        self.assertEqual(eng.tick(), (140, False))
        self.assertEqual(eng.tick(clear_acc=True), (0, False))
        self.assertEqual(eng.tick(reset=True), (0, False))

    def test_random_dot(self):
        random.seed(2026)
        for _ in range(1000):
            aa = [random.randint(-128, 127) for _ in range(4)]
            bb = [random.randint(-128, 127) for _ in range(4)]
            packed_a = sum((v & 255) << (8*i) for i, v in enumerate(aa))
            packed_b = sum((v & 255) << (8*i) for i, v in enumerate(bb))
            self.assertEqual(dot4(packed_a, packed_b), sum(x*y for x,y in zip(aa,bb)))

    def test_wraparound(self):
        eng = NeuralEngine()
        eng.accumulator = 0x7fffffff
        self.assertEqual(eng.tick(start=True, a=0x00000001, b=0x00000001), (signed32(0x80000000), True))

if __name__ == "__main__":
    unittest.main()
