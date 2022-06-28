# SDFEC-PYNQ

This design offers an environment to evaluate the Soft Decision Forward Error Correction (SD-FEC) IPs using PYNQ and a ZCU111, RFSoC2x2, or RFSoC4x2 board. Based on work by Andy Dow (Xilinx; Edinburgh), it allows us to explore the RFSoC SDFEC with a configurable data path including:

  1. A data source including BPSK, QPSK, QAM-16, and QAM-64 modulation schemes
  2. An encoding/decoding pair of SD-FEC blocks with a set of different LDPC
     codes
  3. An AWGN channel model with configurable noise power

<div align="center">
    <a href="https://github.com/Xilinx/SDFEC-PYNQ/blob/master/boards/ZCU111/notebooks/assets/notebook_preview.png">
      <img src="https://github.com/Xilinx/SDFEC-PYNQ/blob/master/boards/ZCU111/notebooks/assets/notebook_preview.png" width="750px"/>
    </a>
</div>

## Getting started

This repository is compatible with several [PYNQ releases](https://github.com/Xilinx/PYNQ/releases) for the [ZCU111](https://www.xilinx.com/products/boards-and-kits/zcu111.html), [RFSoC2x2](http://www.rfsoc-pynq.io/), and [RFSoC4x2](http://www.rfsoc-pynq.io) boards.

We supply pre-built tarballs with all tagged releases. These can be installed directly with pip.

```sh
pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v3.1/rfsoc_sdfec-3.1.tar.gz
```

The notebook should now be available in `rfsoc_sdfec`.

## Building the project 

> NOTE: Build this on an x86 machine that has Vivado on the path and a license for the SD-FEC IP. You can generate the required license by following [this link](https://www.xilinx.com/products/intellectual-property/sd-fec.html).


If you want to rebuild the overlay yourself, this can be done from a Linux PC with Python3 and Vivado 2020.2 installed. Clone this repo and use make to build the overlays for all supported boards.:

```sh
git clone https://github.com/Xilinx/SDFEC-PYNQ.git
cd SDFEC-PYNQ
make
```

This will result in a tarball at the top directory named `rfsoc_sdfec.tar.gz`. Copy this onto your board and run the following command to install:

```sh
pip install -I <path-to-tarball>
```

## License 
[BSD 3-Clause](https://github.com/Xilinx/SDFEC-PYNQ/blob/master/LICENSE)
