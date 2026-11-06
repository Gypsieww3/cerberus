// AEGIS-1 v0.3: minimal synchronous 32-bit register-mapped neural peripheral.
// Transactions accepted on rising clock edge when bus_valid; read results after edge.
module aegis_neural_mmio (
    input wire clk, input wire rst,
    input wire bus_valid, input wire bus_write,
    input wire [7:0] bus_addr, input wire [31:0] bus_wdata,
    output wire bus_ready, output reg [31:0] bus_rdata,
    output wire bus_error
);
    localparam [7:0] REG_A=8'h00, REG_B=8'h04,
        REG_CTRL=8'h08, REG_RESULT=8'h0c,
        REG_STATUS=8'h10, REG_ID=8'h14;
    reg [31:0] operand_a, operand_b;
    reg done;
    wire signed [31:0] accumulator;
    wire engine_valid;
    wire control_write = bus_valid && bus_write && !bus_error && bus_addr == REG_CTRL;
    wire start = control_write && bus_wdata[0];
    wire clear_acc = control_write && bus_wdata[1];
    assign bus_ready = 1'b1; // no arbitration or backpressure in v0.3
    wire addr_defined = bus_addr == REG_A || bus_addr == REG_B ||
        bus_addr == REG_CTRL || bus_addr == REG_RESULT ||
        bus_addr == REG_STATUS || bus_addr == REG_ID;
    wire addr_writable = bus_addr == REG_A || bus_addr == REG_B || bus_addr == REG_CTRL;
    assign bus_error = bus_valid && (bus_addr[1:0] != 2'b00 ||
        !addr_defined || (bus_write && !addr_writable));
    always @(*) begin
        case (bus_addr)
            REG_A: bus_rdata = operand_a;
            REG_B: bus_rdata = operand_b;
            REG_CTRL: bus_rdata = 32'd0;
            REG_RESULT: bus_rdata = accumulator;
            REG_STATUS: bus_rdata = {31'd0, done};
            REG_ID: bus_rdata = 32'h41454731; // AEG1
            default: bus_rdata = 32'd0;
        endcase
    end
    always @(posedge clk) begin
        if (rst) begin
            operand_a <= 32'd0;
            operand_b <= 32'd0;
            done <= 1'b0;
        end else if (bus_valid && bus_write && !bus_error) begin
            case (bus_addr)
                REG_A: operand_a <= bus_wdata;
                REG_B: operand_b <= bus_wdata;
                REG_CTRL: begin
                    if (bus_wdata[2]) done <= 1'b0;
                    if (bus_wdata[0]) done <= 1'b1;
                end
                default: ;
            endcase
        end
    end
    aegis_dot4_int8 engine (
        .clk(clk), .rst(rst), .start(start), .clear_acc(clear_acc),
        .vector_a(operand_a), .vector_b(operand_b),
        .valid(engine_valid), .accumulator(accumulator)
    );
endmodule
