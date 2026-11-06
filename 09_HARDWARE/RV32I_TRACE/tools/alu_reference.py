"""Independent Python reference for the generic RV32I ALU module."""
MASK=0xffffffff
def signed(x):
    x=x&MASK
    return x-(1<<32) if x&(1<<31) else x
def alu(a,b,op):
    if any(type(v) is not int for v in (a,b,op)) or not 0<=op<16:
        raise ValueError("Invalid integer operands/opcode")
    a,b=a&MASK,b&MASK
    operations={
        0:lambda:a+b,1:lambda:a-b,2:lambda:a&b,
        3:lambda:a|b,4:lambda:a^b,5:lambda:a<<(b&31),
        6:lambda:a>>(b&31),7:lambda:signed(a)>>(b&31),
        8:lambda:int(signed(a)<signed(b)),
        9:lambda:int(a<b),
    }
    result=(operations[op]()&MASK) if op in operations else 0
    return result,result==0
def self_check():
    examples=[
        (20,22,0,42),(20,22,1,0xfffffffe),(0xffffffff,1,0,0),
        (0xaa55aa55,0x0ff00ff0,2,0x0a500a50),
        (0xaa55aa55,0x0ff00ff0,3,0xaff5aff5),
        (0xaa55aa55,0x0ff00ff0,4,0xa5a5a5a5),
        (1,31,5,0x80000000),(0x80000000,31,6,1),
        (0x80000000,31,7,0xffffffff),
        (0xffffffff,0,8,1),(0xffffffff,0,9,0),
        (42,42,1,0),(1,33,5,2),(0xffffffff,0xffffffff,15,0)]
    for a,b,op,expected in examples:
        actual,_=alu(a,b,op)
        assert actual==expected,(a,b,op,actual,expected)
    return len(examples)
if __name__=="__main__":
    print("PASS",self_check(),"Python ALU reference vectors (not HDL simulation)")
