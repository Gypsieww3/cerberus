// AEGIS-1 register interface directed simulation
`timescale 1ns/1ps
module aegis_mmio_tb;
    reg clk=0, rst=1, bus_valid=0, bus_write=0;
    reg [7:0] bus_addr=0;
    reg [31:0] bus_wdata=0;
    wire bus_ready, bus_error;
    wire [31:0] bus_rdata;
    always #5 clk=~clk;
    aegis_neural_mmio dut(.*);
    task write_reg(input [7:0] addr, input [31:0] value);
    begin
        @(negedge clk);
        bus_addr=addr; bus_wdata=value; bus_write=1; bus_valid=1;
        #1;
        if (!bus_ready || bus_error) $fatal(1,"Write rejected at %h",addr);
        @(posedge clk); #1;
        bus_valid=0; bus_write=0;
    end
    endtask
    task expect_reg(input [7:0] addr, input [31:0] expected);
    begin
        @(negedge clk);
        bus_addr=addr; bus_write=0; bus_valid=1;
        #1;
        if (bus_error || !bus_ready || bus_rdata !== expected)
            $fatal(1,"Read at %h expected %h got %h",addr,expected,bus_rdata);
        @(posedge clk); #1; bus_valid=0;
    end
    endtask
    initial begin
        repeat(2) @(negedge clk);
        rst=0;
        expect_reg(8'h14,32'h41454731);
        write_reg(8'h00,32'h04030201);
        write_reg(8'h04,32'h08070605);
        write_reg(8'h08,32'h00000003); // start and replace
        expect_reg(8'h0c,32'd70);
        expect_reg(8'h10,32'd1);
        write_reg(8'h08,32'h00000001); // accumulate
        expect_reg(8'h0c,32'd140);
        write_reg(8'h08,32'h00000004); // acknowledge done
        expect_reg(8'h10,32'd0);
        write_reg(8'h08,32'h00000002); // clear accumulator
        expect_reg(8'h0c,32'd0);
        write_reg(8'h00,32'hfc03feff);
        write_reg(8'h04,32'h05fc0302);
        write_reg(8'h08,32'h00000003);
        expect_reg(8'h0c,32'hffffffd8); // signed result -40
        @(negedge clk);
        bus_valid=1; bus_write=1; bus_addr=8'h0c; bus_wdata=32'h12345678;
        #1;
        if (!bus_error) $fatal(1,"Read-only register write accepted");
        @(posedge clk); #1; bus_valid=0;
        expect_reg(8'h0c,32'hffffffd8);
        @(negedge clk);
        bus_valid=1; bus_write=0; bus_addr=8'h03;
        #1;
        if (!bus_error) $fatal(1,"Unaligned register accepted");
        @(posedge clk); #1; bus_valid=0;
        $display("PASS: AEGIS-1 MMIO register, signed dot, accumulation, errors");
        $finish;
    end
endmodule
