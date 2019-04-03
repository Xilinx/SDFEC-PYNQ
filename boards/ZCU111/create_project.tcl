set proj_name "sdfec_pynq"
set exdes_name "sd_fec_gen_ex"
set exdes_dir "${proj_name}/sdfec_exdes/${exdes_name}"

create_project -force $proj_name ./$proj_name -part xczu28dr-ffvg1517-2L-e

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

# change PS Master AXI width to 128 to conform with PYNQ requirements
set_property -dict [list CONFIG.PSU__MAXIGP0__DATA_WIDTH {128}] [get_bd_cells zynq_ultra_ps]

validate_bd_design
save_bd_design

add_files -fileset constrs_1 -norecurse ./srcs/zcu111_constraints.xdc

set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]

# change number of threads to suit your cpu
launch_runs impl_1 -to_step write_bitstream -jobs 16
wait_on_run impl_1

# get bitstream and hwh files
if {![file exists ./bitstreams/]} {
	file mkdir ./bitstreams/
	}

file copy -force ./${exdes_dir}/${exdes_name}.runs/impl_1/ps_example_wrapper.bit ./bitstreams/${proj_name}.bit
file copy -force ./${exdes_dir}/${exdes_name}.srcs/sources_1/bd/ps_example/hw_handoff/ps_example.hwh ./bitstreams/${proj_name}.hwh