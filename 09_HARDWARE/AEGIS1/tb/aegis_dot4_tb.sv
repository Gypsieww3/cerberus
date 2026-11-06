// Run: iverilog -g2012 -s aegis_dot4_tb -o /tmp/aegis_tb
//      09_HARDWARE/AEGIS1/rtl/aegis_dot4_int8.sv
//      09_HARDWARE/AEGIS1/tb/aegis_dot4_tb.sv
//      && vvp /tmp/aegis_tb
`timescale 1ns/1ps
module aegis_dot4_tb;
    reg clk = 0, rst = 1, start = 0, clear_acc = 0;
    reg [31:0] vector_a = 0, vector_b = 0;
    wire valid;
    wire signed [31:0] accumulator;
    always #5 clk = ~clk;
    aegis_dot4_int8 dut (
        .clk(clk), .rst(rst), .start(start), .clear_acc(clear_acc),
        .vector_a(vector_a), .vector_b(vector_b),
        .valid(valid), .accumulator(accumulator)
    );
    task check(input signed [31:0] expected, input expected_valid);
        begin
            #1;
            if (accumulator !== expected || valid !== expected_valid)
                $fatal(1, "Expected %0d valid=%b; got %0d valid=%b",
                       expected, expected_valid, accumulator, valid);
        end
    endtask
    initial begin
        @(negedge clk); rst = 0;
        // Dot([1,2,3,4],[5,6,7,8]) = 70.
        vector_a = 32'h04030201;
        vector_b = 32'h08070605;
        start = 1; clear_acc = 1;
        @(posedge clk); check(32'sd70, 1'b1);
        @(negedge clk); clear_acc = 0;
        @(posedge clk); check(32'sd140, 1'b1);
        @(negedge clk); start = 0;
        @(posedge clk); check(32'sd140, 1'b0);
        // Signed: [-1,-2,3,-4] dot [2,3,-4,5] = -40.
        @(negedge clk);
        vector_a = 32'hfc03feff;
        vector_b = 32'h05fc0302;
        start = 1; clear_acc = 1;
        @(posedge clk); check(-32'sd40, 1'b1);
        @(negedge clk); start = 0; clear_acc = 1;
        @(posedge clk); check(32'sd0, 1'b0);
        @(negedge clk); clear_acc = 0; rst = 1;
        @(posedge clk); check(32'sd0, 1'b0);
        $display("PASS: AEGIS-1 dot4 INT8 arithmetic, accumulation and reset");
        $finish;
    end
endmodule
