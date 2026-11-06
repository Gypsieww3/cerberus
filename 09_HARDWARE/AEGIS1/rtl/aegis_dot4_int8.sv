// C.E.R.B.E.R.U.S. AEGIS-1 Neural Engine v0.2
// Four signed INT8 multipliers, summed into a 32-bit wrapping accumulator.
// Standalone experimental accelerator; not an integrated RISC-V extension.
module aegis_dot4_int8 (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire        clear_acc,
    input  wire [31:0] vector_a,
    input  wire [31:0] vector_b,
    output reg         valid,
    output reg signed [31:0] accumulator
);
    wire signed [7:0] a0 = vector_a[7:0];
    wire signed [7:0] a1 = vector_a[15:8];
    wire signed [7:0] a2 = vector_a[23:16];
    wire signed [7:0] a3 = vector_a[31:24];
    wire signed [7:0] b0 = vector_b[7:0];
    wire signed [7:0] b1 = vector_b[15:8];
    wire signed [7:0] b2 = vector_b[23:16];
    wire signed [7:0] b3 = vector_b[31:24];
    wire signed [15:0] p0 = a0 * b0;
    wire signed [15:0] p1 = a1 * b1;
    wire signed [15:0] p2 = a2 * b2;
    wire signed [15:0] p3 = a3 * b3;
    wire signed [31:0] dot_product =
        {{16{p0[15]}}, p0} + {{16{p1[15]}}, p1} +
        {{16{p2[15]}}, p2} + {{16{p3[15]}}, p3};

    always @(posedge clk) begin
        if (rst) begin
            accumulator <= 32'sd0;
            valid <= 1'b0;
        end else begin
            valid <= start;
            if (start) begin
                if (clear_acc)
                    accumulator <= dot_product;
                else
                    accumulator <= accumulator + dot_product;
            end else if (clear_acc) begin
                accumulator <= 32'sd0;
            end
        end
    end
endmodule
