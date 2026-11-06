\`timescale 1ns/1ps
module alu_tb;
logic [31:0] a,b,result;
logic [3:0] op;
logic zero;
integer checks=0;
cerberus_alu dut(.a(a),.b(b),.op(op),.result(result),.zero(zero));
task automatic check(
  input logic [31:0] av, bv,
  input logic [3:0] operation,
  input logic [31:0] expected
);
begin
  a=av; b=bv; op=operation;
  #1;
  checks=checks+1;
  if (result!==expected || zero!==(expected==32'd0)) begin
    $display("FAIL op=%0d a=%h b=%h actual=%h expected=%h",
             operation,av,bv,result,expected);
    $fatal(1);
  end
end
endtask
initial begin
  check(20,22,0,42);
  check(20,22,1,32'hfffffffe);
  check(32'hffffffff,1,0,0);
  check(32'haa55aa55,32'h0ff00ff0,2,32'h0a500a50);
  check(32'haa55aa55,32'h0ff00ff0,3,32'haff5aff5);
  check(32'haa55aa55,32'h0ff00ff0,4,32'ha5a5a5a5);
  check(1,31,5,32'h80000000);
  check(32'h80000000,31,6,1);
  check(32'h80000000,31,7,32'hffffffff);
  check(32'hffffffff,0,8,1);
  check(32'hffffffff,0,9,0);
  check(42,42,1,0);
  check(1,33,5,2);
  check(32'hffffffff,32'hffffffff,15,0);
  $display("PASS CERBERUS_ALU %0d test cases",checks);
  $finish;
end
endmodule
