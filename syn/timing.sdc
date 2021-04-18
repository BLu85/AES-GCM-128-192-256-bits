# 100 Mhz clock
create_clock -period 10.0 [get_ports clk_i]

# Set the maximum clock source latency
set_clock_latency -source -max 0.7 [get_clocks clk_i]

# Set the maximum clock network latency
set_clock_latency -max 0.3 [get_clocks clk_i]

# Add a total uncertainty
set_clock_uncertainty -setup 0.15 [get_clocks clk_i]

# The maximum clock transition
#set_clock_transition -max 0.12 [get_clocks clk_i]


# Set max and min input delay
set_input_delay -max  4 -clock clk_i [all_inputs]
set_input_delay -min  3 -clock clk_i [all_inputs]

# Set max and min output delay
set_output_delay -max  2 -clock clk_i [all_outputs]
set_output_delay -min  1 -clock clk_i [all_outputs]
