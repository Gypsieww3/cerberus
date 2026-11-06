// Smoke simulation against the checked-in 9-word reference program.
`timescale 1ns/1ps
module core_tb;
  reg clk=1'b0;
  reg rst=1'b1;
  wire [31:0] pc, retired;
  wire halted, illegal_instruction, retire_valid;
  wire [31:0] retire_pc, retire_instruction, retire_value;
  wire [4:0] retire_rd;
  integer i;
  always #5 clk=~clk;
  cerberus_rv32i_core dut(
    .clk(clk),.rst(rst),.pc(pc),.halted(halted),.illegal_instruction(illegal_instruction),
    .retired(retired),.retire_valid(retire_valid),.retire_pc(retire_pc),
    .retire_instruction(retire_instruction),.retire_rd(retire_rd),.retire_value(retire_value));
  initial begin
    for(i=0;i<64;i=i+1) dut.imem[i]=32'h00000013;
    $readmemh("09_HARDWARE/RV32I_TRACE/tb/program.hex",dut.imem);
    repeat(2) @(negedge clk);
    rst=1'b0;
    repeat(20) @(negedge clk);
    if (!halted || illegal_instruction) $fatal(1,"CPU failed to halt at ECALL");
    if (pc !== 32'd32 || retired !== 32'd7) $fatal(1,"Unexpected retirement: pc=%0d count=%0d",pc,retired);
    if (dut.x[0] !== 0 || dut.x[1] !== 5 || dut.x[2] !== 7 || dut.x[3] !== 12 ||
        dut.x[4] !== 12 || dut.x[5] !== 0 || dut.x[6] !== 1 || dut.dmem[0] !== 12)
      $fatal(1,"Program final state mismatch");
    $display("PASS: CERBERUS RV32I subset core reference program, retired=%0d",retired);
    rst=1'b1;
    @(negedge clk);
    dut.imem[0]=32'hffffffff;
    rst=1'b0;
    repeat(3) @(negedge clk);
    if (!halted || !illegal_instruction || retired !== 0)
      $fatal(1,"Illegal instruction should trap without retirement");
    $display("PASS: illegal instruction trap");
    $finish;
  end
endmodule
