// C.E.R.B.E.R.U.S. educational RV32I subset: simulation-focused prototype.
// No interrupts/CSR, MMU, timing closure, external bus or silicon validation.
// Separate instruction/data memories are exposed for a controlled testbench.
module cerberus_rv32i_core (
  input wire clk,
  input wire rst,
  output reg [31:0] pc,
  output reg halted,
  output reg illegal_instruction,
  output reg [31:0] retired,
  output reg retire_valid,
  output reg [31:0] retire_pc,
  output reg [31:0] retire_instruction,
  output reg [4:0] retire_rd,
  output reg [31:0] retire_value
);
  reg [31:0] imem [0:63];
  reg [31:0] dmem [0:63];
  reg [31:0] x [0:31];
  reg [31:0] insn, a, b, next_pc, value, address;
  reg [31:0] imm_i, imm_s, imm_b, imm_j;
  reg write_rd, invalid;
  integer i;

  always @(posedge clk) begin
    retire_valid <= 1'b0;
    if (rst) begin
      pc <= 32'd0;
      halted <= 1'b0;
      illegal_instruction <= 1'b0;
      retired <= 32'd0;
      retire_pc <= 32'd0;
      retire_instruction <= 32'd0;
      retire_rd <= 5'd0;
      retire_value <= 32'd0;
      for (i=0; i<32; i=i+1) x[i] <= 32'd0;
      for (i=0; i<64; i=i+1) dmem[i] <= 32'd0;
    end else if (!halted) begin
      if (pc[1:0] != 2'b00 || pc >= 32'd256) begin
        halted <= 1'b1;
        illegal_instruction <= 1'b1;
      end else begin
        insn = imem[pc[7:2]];
        a = x[insn[19:15]];
        b = x[insn[24:20]];
        imm_i = {{20{insn[31]}}, insn[31:20]};
        imm_s = {{20{insn[31]}}, insn[31:25], insn[11:7]};
        imm_b = {{19{insn[31]}}, insn[31], insn[7], insn[30:25], insn[11:8], 1'b0};
        imm_j = {{11{insn[31]}}, insn[31], insn[19:12], insn[20], insn[30:21], 1'b0};
        next_pc = pc + 32'd4;
        address = 32'd0;
        value = 32'd0;
        write_rd = 1'b0;
        invalid = 1'b0;
        if (insn == 32'h00000073) begin  // ECALL: program stop in this prototype
          halted <= 1'b1;
        end else begin
          case (insn[6:0])
            7'b0010011: begin  // ADDI, ANDI, ORI, XORI
              write_rd = 1'b1;
              case (insn[14:12])
                3'b000: value = a + imm_i;
                3'b111: value = a & imm_i;
                3'b110: value = a | imm_i;
                3'b100: value = a ^ imm_i;
                default: invalid = 1'b1;
              endcase
            end
            7'b0110011: begin  // ADD, SUB, AND, OR, XOR
              write_rd = 1'b1;
              case ({insn[31:25], insn[14:12]})
                {7'b0000000,3'b000}: value = a + b;
                {7'b0100000,3'b000}: value = a - b;
                {7'b0000000,3'b111}: value = a & b;
                {7'b0000000,3'b110}: value = a | b;
                {7'b0000000,3'b100}: value = a ^ b;
                default: invalid = 1'b1;
              endcase
            end
            7'b0000011: begin  // LW (aligned)
              address = a + imm_i;
              if (insn[14:12] != 3'b010 || address[1:0] != 2'b00 || address >= 32'd256)
                invalid = 1'b1;
              else begin
                value = dmem[address[7:2]];
                write_rd = 1'b1;
              end
            end
            7'b0100011: begin  // SW (aligned)
              address = a + imm_s;
              if (insn[14:12] != 3'b010 || address[1:0] != 2'b00 || address >= 32'd256)
                invalid = 1'b1;
              else dmem[address[7:2]] <= b;
            end
            7'b1100011: begin
              if (insn[14:12] == 3'b000) begin // BEQ
                if (a == b) next_pc = pc + imm_b;
              end else if (insn[14:12] == 3'b001) begin // BNE
                if (a != b) next_pc = pc + imm_b;
              end else invalid = 1'b1;
            end
            7'b0110111: begin write_rd = 1'b1; value = {insn[31:12], 12'b0}; end // LUI
            7'b0010111: begin write_rd = 1'b1; value = pc + {insn[31:12], 12'b0}; end // AUIPC
            7'b1101111: begin write_rd = 1'b1; value = pc + 32'd4; next_pc = pc + imm_j; end // JAL
            7'b1100111: begin // JALR
              if (insn[14:12] != 3'b000) invalid = 1'b1;
              else begin write_rd = 1'b1; value = pc + 32'd4; next_pc = (a + imm_i) & 32'hfffffffe; end
            end
            default: invalid = 1'b1;
          endcase
          if (invalid) begin
            halted <= 1'b1;
            illegal_instruction <= 1'b1;
          end else begin
            if (write_rd && insn[11:7] != 0) x[insn[11:7]] <= value;
            pc <= next_pc;
            retired <= retired + 32'd1;
            retire_valid <= 1'b1;
            retire_pc <= pc;
            retire_instruction <= insn;
            retire_rd <= write_rd ? insn[11:7] : 5'd0;
            retire_value <= (write_rd && insn[11:7] != 0) ? value : 32'd0;
          end
        end
      end
    end
  end
endmodule
