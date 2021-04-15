# SDFEC-PYNQ

This design offers an environment to evaluate the Soft Decision Forward Error
Correction (SD-FEC) IPs using PYNQ and a ZCU111 or RFSoC2x2 board. Based on work by Andy Dow
(Xilinx; Edinburgh), it allows us to explore the RFSoC SDFEC with a configurable data path
including:

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

This repository is compatible with several [PYNQ releases](https://github.com/Xilinx/PYNQ/releases) for the [ZCU111](https://www.xilinx.com/products/boards-and-kits/zcu111.html) and [RFSoC2x2](http://www.rfsoc-pynq.io/) boards.

We supply pre-built wheels with all tagged releases. These can be installed
directly with pip.

```sh
# PYNQ v2.4.1, v2.5
pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v1.0_$BOARD/rfsoc_sdfec-1.0-py3-none-any.whl

# PYNQ v2.6
pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v2.0_$BOARD/rfsoc_sdfec-2.0-py3-none-any.whl


```

The wheel is just a self-contained archive, so we must ask the module to copy
its notebooks to the filesystem after installation.

```sh
python3 -c 'import rfsoc_sdfec; rfsoc_sdfec.install_notebooks()'
```

The notebook should now be available in `rfsoc_sdfec/`.

## Building the wheel

> NOTE: Build this on an x86 machine that has Vivado on the path and a license for the SD-FEC IP. You can generate the required license by following [this link](https://www.xilinx.com/products/intellectual-property/sd-fec.html).


We release pre-built wheels for every tagged release. If you want to build your
own wheel, this can be done from a Linux PC with Python3 and Vivado 2020.1
installed. Clone this repo and use make to build the wheel:

```sh
git clone https://github.com/Xilinx/SDFEC-PYNQ.git
cd SDFEC-PYNQ

BOARD=ZCU111 make wheel
# or
BOARD=RFSoC2x2 make wheel
```

The wheel is built in the `dist` folder.

## License 
[BSD 3-Clause](https://github.com/Xilinx/SDFEC-PYNQ/blob/master/LICENSE)
