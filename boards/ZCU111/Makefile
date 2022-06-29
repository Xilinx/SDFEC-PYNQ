# Copyright (C) 2021 Xilinx, Inc
# SPDX-License-Identifier: BSD-3-Clause

SHELL := /bin/bash
design_name := sdfec_pynq
bitfile := bitstreams/sdfec_pynq.bit

all: $(bitfile) clean

$(bitfile):
	# some bash magic to retrieve LDPC codes and get them in a format required by the demo
	$(shell cat $(XILINX_VIVADO)/data/ip/xilinx/sd_fec_v1_1/common_tcl/{docsis,wifi,5g_demo}_decode.yml | sed 's/_decode:/:/g' | sed '/skip_enc_compatibility: 1/d' | sed '/encode: false/d' > srcs/all_codes.txt)

	vivado -mode batch -source create_project.tcl -notrace

clean:
	rm -rf $(design_name) ./srcs/all_codes.txt *.jou *.log NA
