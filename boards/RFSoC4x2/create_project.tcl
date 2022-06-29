# Copyright (C) 2021 Xilinx, Inc
# SPDX-License-Identifier: BSD-3-Clause

set proj_name "sdfec_pynq"
set exdes_name "sd_fec_gen_ex"
set exdes_dir "${proj_name}/sdfec_exdes/${exdes_name}"

create_project -force $proj_name ./$proj_name -part xczu48dr-ffvg1517-2-e

create_ip -name sd_fec -vendor xilinx.com -library ip -version 1.1 -module_name sd_fec_gen
set_property -dict [list CONFIG.Standard "Custom" \
                         CONFIG.LDPC_Decode "true" \
                         CONFIG.LDPC_Decode_Code_Definition "[pwd]/srcs/all_codes.txt" \
                         CONFIG.DIN_Lanes 2 \
                         CONFIG.Include_PS_Example_Design "true" \
                         CONFIG.Example_Design_PS_Type "ZYNQ_UltraScale+_RFSoC" \
                         CONFIG.Include_Encoder "true" \
                         CONFIG.Build_SDK_Project "false"] [get_ips sd_fec_gen]

open_example_project -in_process -force -dir ./${proj_name}/sdfec_exdes [get_ips sd_fec_gen]

# Change PS Master AXI width to 128 to conform with PYNQ requirements
set_property -dict [list CONFIG.PSU__MAXIGP0__DATA_WIDTH {128}] [get_bd_cells zynq_ultra_ps]

# Board config
set_property -dict [list CONFIG.PSU__QSPI__PERIPHERAL__ENABLE {0}] [get_bd_cells zynq_ultra_ps]
set_property -dict [list CONFIG.PSU__PSS_REF_CLK__FREQMHZ {33.33333} CONFIG.PSU__DDRC__CL {16} CONFIG.PSU__DDRC__CWL {12} CONFIG.PSU__DDRC__DEVICE_CAPACITY {16384 MBits} CONFIG.PSU__DDRC__ROW_ADDR_COUNT {17} CONFIG.PSU__DDRC__SPEED_BIN {DDR4_2400R} CONFIG.PSU__DDRC__T_RAS_MIN {32} CONFIG.PSU__DDRC__T_RC {45.32} CONFIG.PSU__DDRC__T_RCD {16} CONFIG.PSU__DDRC__T_RP {16} CONFIG.PSU__DDRC__COMPONENTS {Components} CONFIG.PSU__CRF_APB__APLL_CTRL__FBDIV {79} CONFIG.PSU__CRF_APB__DPLL_CTRL__FBDIV {72} CONFIG.PSU__CRF_APB__DPLL_TO_LPD_CTRL__DIVISOR0 {3} CONFIG.PSU__DISPLAYPORT__PERIPHERAL__ENABLE {0} CONFIG.PSU__SATA__PERIPHERAL__ENABLE {0} CONFIG.PSU__CRL_APB__AMS_REF_CTRL__DIVISOR0 {30} CONFIG.PSU__CRF_APB__TOPSW_MAIN_CTRL__DIVISOR0 {3} CONFIG.PSU__CRL_APB__IOPLL_CTRL__FBDIV {90} CONFIG.PSU__CRL_APB__RPLL_CTRL__FBDIV {63} CONFIG.PSU__CRL_APB__IOPLL_TO_FPD_CTRL__DIVISOR0 {3} CONFIG.PSU__CRL_APB__RPLL_TO_FPD_CTRL__DIVISOR0 {2} CONFIG.PSU__CRL_APB__UART0_REF_CTRL__DIVISOR0 {15} CONFIG.PSU__CRL_APB__I2C0_REF_CTRL__DIVISOR0 {15} CONFIG.PSU__CRL_APB__I2C1_REF_CTRL__DIVISOR0 {15} CONFIG.PSU__CRL_APB__CPU_R5_CTRL__DIVISOR0 {3} CONFIG.PSU__CRL_APB__PCAP_CTRL__DIVISOR0 {8} CONFIG.PSU__CRL_APB__LPD_LSBUS_CTRL__DIVISOR0 {15} CONFIG.PSU__CRL_APB__DBG_LPD_CTRL__DIVISOR0 {6} CONFIG.PSU__CRF_APB__DDR_CTRL__SRCSEL {DPLL} CONFIG.PSU__CRF_APB__GDMA_REF_CTRL__SRCSEL {DPLL} CONFIG.PSU__CRF_APB__DPDMA_REF_CTRL__SRCSEL {DPLL} CONFIG.PSU__CRL_APB__IOU_SWITCH_CTRL__SRCSEL {RPLL} CONFIG.PSU__CRL_APB__LPD_SWITCH_CTRL__SRCSEL {RPLL} CONFIG.PSU__CRL_APB__ADMA_REF_CTRL__SRCSEL {RPLL} CONFIG.PSU__CRL_APB__TIMESTAMP_REF_CTRL__SRCSEL {PSS_REF_CLK} CONFIG.PSU__OVERRIDE__BASIC_CLOCK {1} CONFIG.PSU__CRF_APB__ACPU_CTRL__FREQMHZ {1333.333} CONFIG.PSU__CRF_APB__DDR_CTRL__FREQMHZ {1200}] [get_bd_cells zynq_ultra_ps]
# RFSoC4x2 alterations
delete_bd_objs [get_bd_intf_nets diff_clock_rtl_0_1] [get_bd_intf_ports sys_diff_clock]
set_property -dict [list CONFIG.PRIM_SOURCE {Single_ended_clock_capable_pin}] [get_bd_cells clk_wiz]
connect_bd_net [get_bd_pins clk_wiz/clk_in1] [get_bd_pins zynq_ultra_ps/pl_clk0]
# Set reset port as active low
set_property -dict [list CONFIG.POLARITY {ACTIVE_LOW}] [get_bd_ports reset]
set_property -dict [list CONFIG.RESET_TYPE {ACTIVE_LOW} CONFIG.RESET_PORT {resetn}] [get_bd_cells clk_wiz]
connect_bd_net [get_bd_ports reset] [get_bd_pins clk_wiz/resetn]
# Change the LED GPIO to active low
create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 util_vector_logic_0
set_property -dict [list CONFIG.C_SIZE {5} CONFIG.C_OPERATION {not} CONFIG.LOGO_FILE {data/sym_notgate.png}] [get_bd_cells util_vector_logic_0]
delete_bd_objs [get_bd_intf_nets axi_gpio_GPIO]
delete_bd_objs [get_bd_intf_ports led_bits]
connect_bd_net [get_bd_pins axi_gpio/gpio_io_o] [get_bd_pins util_vector_logic_0/Op1]
make_bd_pins_external  [get_bd_pins util_vector_logic_0/Res]
set_property name led_bits [get_bd_ports Res_0]

validate_bd_design
save_bd_design

add_files -fileset constrs_1 -norecurse ./srcs/rfsoc4x2_constraints.xdc
set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]

# change number of threads to suit your cpu
launch_runs impl_1 -to_step write_bitstream -jobs 3
wait_on_run impl_1

#get bitstream and hwh files
if {![file exists ./bitstreams/]} {
	file mkdir ./bitstreams/
}

file copy -force ./${exdes_dir}/${exdes_name}.runs/impl_1/ps_example_wrapper.bit ./bitstreams/${proj_name}.bit                    
file copy -force ./${exdes_dir}/${exdes_name}.gen/sources_1/bd/ps_example/hw_handoff/ps_example.hwh ./bitstreams/${proj_name}.hwh	
