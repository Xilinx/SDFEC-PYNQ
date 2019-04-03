#   Copyright (c) 2019, Xilinx, Inc.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import xsdfec

import signal
import plotly.io as pio
import os
from typing import Tuple
from enum import Enum
from pynq import Overlay, MMIO

def install_notebooks(notebook_dir=None):
    """Copy SDFEC notebooks to the filesystem

    notebook_dir: str
        An optional destination filepath. If None, assume PYNQ's default
        jupyter_notebooks folder.
    """
    import shutil
    from distutils.dir_util import copy_tree

    if notebook_dir == None:
        notebook_dir = os.environ['PYNQ_JUPYTER_NOTEBOOKS']
        if not os.path.isdir(notebook_dir):
            raise ValueError(
            f'Directory {notebook_dir} does not exist. Please supply a `notebook_dir` argument.')

    src_nb_dir = os.path.join(os.path.dirname(__file__), 'notebooks')
    dst_nb_dir = os.path.join(notebook_dir, 'rfsoc_sdfec')
    if os.path.exists(dst_nb_dir):
        shutil.rmtree(dst_nb_dir)
    copy_tree(src_nb_dir, dst_nb_dir)


class ModType(Enum):
    """Enum for modulation type"""
    BPSK  = 0
    QPSK  = 1
    QAM16 = 2
    QAM64 = 3

    
class _SuppressedSIGINT(object):
    def __enter__(self):
        self._caught_sig = None
        self._orig_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self._caught_sig = (sig, frame)

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self._orig_handler)
        if not self._caught_sig == None:
            self._orig_handler(*self._signal_buf)
            

class SdFecOverlay(Overlay):
    """Overlay for SD FEC evaluation demo"""
    
    def __init__(self, bitfile_name=None, dark_theme=False, **kwargs):
        """Construct a new SdFecOverlay
        
        bitfile_name: str
            Optional bitstream filename. If None, we use the bitstream supplied with this package.
        """
        
        # Generate default bitfile name
        if bitfile_name is None:
            this_dir = os.path.dirname(__file__)
            bitfile_name = os.path.join(this_dir, 'bitstreams', 'sdfec_pynq.bit')
        
        # Build a default plotly template for our log plots
        log_template = pio.templates['plotly_dark' if dark_theme else 'plotly_white']
        log_template.layout.yaxis.exponentformat = 'power'
        log_template.layout.yaxis.type = 'log'
        log_template.layout.scene.yaxis.exponentformat = 'power'
        log_template.layout.scene.yaxis.type = 'log'
        log_template.layout.width = 1000
        log_template.layout.height = 400
        log_template.layout.autosize = False
        log_template.layout.legend.x = 1.1
        pio.templates['log_plot'] = log_template

        # Create Overlay
        super().__init__(bitfile_name, **kwargs)

        
    def _collect_monitor_stats(self, mon, sys_clk=300e6):
        first   = int(mon.register_map.first_V)
        last    = int(mon.register_map.last_V)
        stalled = int(mon.register_map.stalled_V)
        iters   = int(self.stats.register_map.iter_cnt_V)
        blocks  = int(self.stats.register_map.block_cnt_V)
        k       = int(self.stats.register_map.k_V)
        return dict(
            throughput = ((blocks-1) * k) / (last - first) * sys_clk / (2**30),
            avg_iter   = iters / blocks,
            stalled    = stalled
        )
    
    
    def run_block(self, source_params, fec_params, channel_params):
        """Run the SD FEC test given source, FEC, and channel parameters.
        
        See the `default_params` method for a reasonable set of default arguments.
        
        source_params : dict
            Configuration for number of blocks (num_blocks), zeroization (zero_data), and modulation type (mod_type).
        
        fec_params : dict
            Configuration for LDPC codes (code_name), max iterations (max_iter), and early termination (term_on_pass).
            
        channel_params : dict
            Configuration for SNR (snr), and chanel model bypass (skip_chan).
            
        return : dict
            A dict populated with test stats including BER, FER, and throughput.
        """
        
        # Check input parameter ranges
        assert 0 <= channel_params['snr'] <= 16, "Argument 'channel_params['snr']' out of range"
        assert 0 <= source_params['num_blocks'], "Argument 'source_params['num_blocks']' out of range"
        assert 0 <= fec_params['max_iter']     , "Argument 'fec_params['max_iter']' out of range"
        
        # Starting critical section, so delay any keyboard interrupts
        with _SuppressedSIGINT():
        
            # Setup SDFEC blocks
            self.sd_fec_enc.CORE_ORDER = 0
            self.sd_fec_dec.CORE_ORDER = 0
            self.data_source.register_map.fec_type_V = 0 # LDPC = 0

            k = self.sd_fec_dec._code_params.ldpc[fec_params['code_name']]['k']
            n = self.sd_fec_dec._code_params.ldpc[fec_params['code_name']]['n']

            self.sd_fec_enc.CORE_AXIS_ENABLE = 0
            self.sd_fec_dec.CORE_AXIS_ENABLE = 0

            self.sd_fec_enc.add_ldpc_params(0,0,0,0, fec_params['code_name'])
            self.sd_fec_dec.add_ldpc_params(0,0,0,0, fec_params['code_name'])

            self.sd_fec_enc.CORE_AXIS_ENABLE = 63
            self.sd_fec_dec.CORE_AXIS_ENABLE = 63

            # Setup data source
            self.data_source.register_map.zero_data_V    = source_params['zero_data']
            self.data_source.register_map.mod_type_V     = source_params['mod_type'].value
            self.data_source.register_map.skip_chan_V    = channel_params['skip_chan']
            self.data_source.register_map.snr_V          = int(channel_params['snr']*2048)
            self.data_source.register_map.inv_sigma_sq_V = int(pow(10.0,channel_params['snr']/10)*1024)

            word1, word2 = self._to_64bit_tuple(1<<14)
            self.data_source.register_map.enc_ctrl_word_V_1 = word1
            self.data_source.register_map.enc_ctrl_word_V_2 = word2
            word1, word2 = self._to_64bit_tuple((1<<14) + (fec_params['term_on_pass'] << 16) + (fec_params['max_iter'] << 18))
            self.data_source.register_map.dec_ctrl_word_V_1 = word1
            self.data_source.register_map.dec_ctrl_word_V_2 = word2

            self.data_source.register_map.num_blocks_V = source_params['num_blocks']
            self.data_source.register_map.source_words_V = int((k+127)/128)
            self.data_source.register_map.source_keep_V = 0xFFFFFFFF & self._calc_tkeep(k, 128)
            word1, word2 = self._to_64bit_tuple(self._calc_tkeep(n, 96))
            self.data_source.register_map.enc_keep_V_1 = word1
            self.data_source.register_map.enc_keep_V_2 = word2
            word1, word2 = self._to_64bit_tuple(self._calc_tkeep(k, 128))
            self.data_source.register_map.dec_keep_V_1 = word1
            self.data_source.register_map.dec_keep_V_2 = word2

            self.data_source.register_map.chan_symbls_V = self._get_chan_symbols(source_params['mod_type'], n)
            self.data_source.register_map.chan_rem_V = self._get_chan_rem(source_params['mod_type'], n)

            # Setup stats block
            self.stats.register_map.num_blocks_V = source_params['num_blocks']
            self.stats.register_map.k_V = k
            self.stats.register_map.n_V = n
            self.stats.register_map.mask_V_1 = self._calc_stats_mask(k)[0]
            self.stats.register_map.mask_V_2 = self._calc_stats_mask(k)[1]
            self.stats.register_map.mask_V_3 = self._calc_stats_mask(k)[2]
            self.stats.register_map.mask_V_4 = self._calc_stats_mask(k)[3]
            self.stats.register_map.src_inc_parity_V = 0

            # Setup stream monitors
            self.enc_ip_mon.register_map.num_blocks_V = source_params['num_blocks']
            self.enc_op_mon.register_map.num_blocks_V = source_params['num_blocks']
            self.dec_ip_mon.register_map.num_blocks_V = source_params['num_blocks']
            self.dec_op_mon.register_map.num_blocks_V = source_params['num_blocks']

            # Start all blocks
            self.enc_ip_mon.register_map.CTRL.AP_START = 1
            self.enc_op_mon.register_map.CTRL.AP_START = 1
            self.dec_ip_mon.register_map.CTRL.AP_START = 1
            self.dec_op_mon.register_map.CTRL.AP_START = 1
            self.stats.register_map.CTRL.AP_START = 1
            self.data_source.register_map.CTRL.AP_START = 1

            # Wait for end of test
            while (self.stats.register_map.CTRL.AP_IDLE == 0):
                pass

            # Recover stats
            block_cnt      = int(self.stats.register_map.block_cnt_V)
            bit_errs       = int(self.stats.register_map.cor_berr_V)
            frame_errs     = int(self.stats.register_map.cor_blerr_V)
            raw_bit_errs   = int(self.stats.register_map.raw_berr_V)
            raw_frame_errs = int(self.stats.register_map.raw_blerr_V)
            k              = int(self.stats.register_map.k_V)

            enc_stats = self._collect_monitor_stats(self.enc_op_mon)
            dec_stats = self._collect_monitor_stats(self.dec_op_mon)
            
        return dict(
            snr = channel_params['snr'],
            mod_type = source_params['mod_type'].name, 
            code_name = fec_params['code_name'],
            ber = bit_errs   / (block_cnt * k),
            fer = frame_errs /  block_cnt,
            raw_ber = raw_bit_errs   / (block_cnt * k),
            raw_fer = raw_frame_errs /  block_cnt,
            enc_throughput = enc_stats['throughput'],
            enc_avg_iters = enc_stats['avg_iter'],
            dec_throughput = dec_stats['throughput'],
            dec_avg_iters = dec_stats['avg_iter'],
            _bit_errors = bit_errs,
        )


    @staticmethod
    def default_params():
        source_params = dict(
            mod_type   = ModType.BPSK,
            zero_data  = False,
            num_blocks = 10000,
        )

        fec_params = dict(
            code_name    = 'docsis_short',
            max_iter     = 8,
            term_on_pass = False,
        )

        channel_params = dict(
            snr       = 5.0,
            skip_chan = False,
        )
        return (source_params, fec_params, channel_params)

    @staticmethod
    def fold_stat_list(stats: list) -> dict:
        """Fold/reduce a list of stat dicts into a single stat dict.
        
        stats : list of dicts
            A list of stat dicts. Each element is likely obtained from a `run_block` call
        
        return : dict
            A single dict with the combined stats
        """
        sum_stat = lambda key: sum(map(lambda s:s[key], stats))
        avg_stat = lambda key: sum_stat(key) / len(stats)
        return dict(
            snr = stats[0]['snr'],
            mod_type = stats[0]['mod_type'], 
            code_name = stats[0]['code_name'],
            ber = avg_stat('ber'),
            fer = avg_stat('fer'),
            raw_ber = avg_stat('raw_ber'),
            raw_fer = avg_stat('raw_fer'),
            enc_throughput = avg_stat('enc_throughput'),
            enc_avg_iters = avg_stat('enc_avg_iters'),
            dec_throughput = avg_stat('dec_throughput'),
            dec_avg_iters = avg_stat('dec_avg_iters'),
            _bit_errors = sum_stat('_bit_errors'),
        )
    
    @staticmethod
    def _calc_stats_mask(k: int) -> Tuple[int, int, int, int]:
        bits = k % 128

        # Short-circuit on zero bits
        if bits == 0:
            return (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)

        masks = [0,0,0,0]
        for i in range(4):
            if bits >= 32:
                masks[i] = 0xFFFFFFFF
                bits -= 32
            else:
                masks[i] = 0x7FFFFFFF >> (31-bits)
                bits = 0
        return (masks[0], masks[1], masks[2], masks[3])


    @staticmethod
    def _calc_tkeep(pkt_size: int, per_trans: int, is_bits: bool = True) -> int:
        rem = pkt_size % per_trans
        if is_bits:
            rem = int((rem + 7) / 8)
        if rem == 0:
            return 0xFFFFFFFF
        else:
            return (1 << rem) - 1

        
    @staticmethod
    def _to_64bit_tuple(val: int) -> Tuple[int, int]:
        return (val & 0xFFFFFFFF, (val >> 32) & 0xFFFFFFFF)

    
    @staticmethod
    def _get_mod_n(mod_type: ModType) -> int:
        return {
            'BPSK':  4,
            'QPSK':  8,
            'QAM16': 12,
            'QAM64': 24,
        }[mod_type.name]

    
    @staticmethod
    def _get_chan_symbols(mod_type: ModType, n: int) -> int:
        x = SdFecOverlay._get_mod_n(mod_type)
        return int((n+x-1) / x)
    
    @staticmethod
    def _get_chan_rem(mod_type: ModType, n: int) -> int:
        return int(n % SdFecOverlay._get_mod_n(mod_type))

