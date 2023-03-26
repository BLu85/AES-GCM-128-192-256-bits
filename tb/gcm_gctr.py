import random
import re
import cocotb

from cocotb.result     import TestFailure
from cocotb.binary     import BinaryValue as bv
from cocotb.triggers   import Timer, RisingEdge

from key_exp           import aes_expand_key
from progress.bar      import ShadyBar as Bar


AES_KEY_256_WIDTH   = 256
AES_KEY_TYPES       = ['128', '192', '256']


# ======================================================================================
class gcm_gctr(object):
    def __init__(self, dut):
        self.dut            = dut
        self.aad            = {'data' : [], 'n_bytes' : 0}
        self.pt             = {'data' : [], 'n_bytes' : 0}
        self.iv_loaded      = False
        self.key_loaded     = False
        self.data           = {}
        self.config         = {}


    # ======================================================================================
    @cocotb.coroutine
    def release_rst(self, duration=10000):
        '''
        Reset the input signals and release the reset '''

        self.dut._log.debug("Reset DUT")
        self.dut.rst_i.value                      = 1
        self.dut.aes_gcm_mode_i.value             = 0
        self.dut.aes_gcm_enc_dec_i.value          = 0
        self.dut.aes_gcm_pipe_reset_i.value       = 0
        self.dut.aes_gcm_icb_stop_cnt_i.value     = 0
        self.dut.aes_gcm_iv_val_i.value           = 0
        self.dut.aes_gcm_iv_i.value               = 0
        self.dut.aes_gcm_icb_start_cnt_i.value    = 0
        self.dut.aes_gcm_key_word_i.value         = 0
        self.dut.aes_gcm_key_word_val_i.value     = 0
        self.dut.aes_gcm_ghash_pkt_val_i.value    = 0
        self.dut.aes_gcm_data_in_i.value          = 0
        self.dut.aes_gcm_data_in_bval_i.value     = 0
        self.dut.aes_gcm_ghash_aad_i.value        = 0
        self.dut.aes_gcm_ghash_aad_bval_i.value   = 0
        yield Timer(duration, 'ns')
        self.dut.rst_i.value                      = 0
        self.dut._log.debug("Reset released")


    # ======================================================================================
    @cocotb.coroutine
    def set_enc_dec(self, enc_dec):
        '''
        Determine if the AES-GCM IP is set in encryption or decryption mode. '''

        if enc_dec == 'enc':
            self.dut.aes_gcm_enc_dec_i.value = 0
        else:
            self.dut.aes_gcm_enc_dec_i.value = 1

        self.dut._log.info(f"Set the AES IP in {enc_dec}ryption mode.")

        yield RisingEdge(self.dut.clk_i)


    # ======================================================================================
    @cocotb.coroutine
    def load_iv(self, iv):
        '''
        Load the IV vector.
        After the 96 bit IV is loaded, a flag is set '''

        iv_bv = bv(n_bits=iv['n_bytes'] * 8)

        # IV is loaded right aligned
        iv_bv.assign('{:>0{width}b}'.format(int(iv['data'], 16), width=int(iv['n_bytes']) * 8))

        self.dut.aes_gcm_iv_val_i.value   = 1
        self.dut.aes_gcm_iv_i.value       = iv_bv.get_value()
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_iv_val_i.value   = 0
        self.dut.aes_gcm_iv_i.value       = 0

        self.dut._log.info(f"IV  = 0x{iv['data']}")
        self.iv_loaded = True


    # ======================================================================================
    @cocotb.coroutine
    def start_icb(self):
        '''
        Start the ICB.
        The function check that an IV has been loaded already by checking the
        correspondent flag. Also, it checks that a valid KEY has been loaded
        and that it has been expanded by checking the correspondent flag. '''

        if self.iv_loaded is False:
            raise TestFailure("IV must be loaded first")
        if self.key_loaded is False:
            raise TestFailure("KEY must be loaded first")
        else:
            self.dut.aes_gcm_icb_start_cnt_i.value = 1
            yield RisingEdge(self.dut.clk_i)
            self.dut.aes_gcm_icb_start_cnt_i.value = 0


    # ======================================================================================
    @cocotb.coroutine
    def stop_icb(self):
        '''
        Stop the ICB '''

        self.dut.aes_gcm_icb_stop_cnt_i.value = 1
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_icb_stop_cnt_i.value = 0
        self.iv_loaded = False
        self.dut._log.info("Start ICB counter")


    # ======================================================================================
    @cocotb.coroutine
    def aes_set_mode(self):
        '''
        Set the AES mode '''

        self.dut.aes_gcm_mode_i.value = AES_KEY_TYPES.index(self.config['aes_mode'])
        yield RisingEdge(self.dut.clk_i)


    # ======================================================================================
    @cocotb.coroutine
    def load_key(self, key):
        '''
        Load AES Key.
        The function checks in what mode the DUT has been set (key type 128, 192, 256).
        Key vector width is 256. Trailing zero are concatenated when the loaded key is
        128 or 192 '''

        # Select key length
        if self.config['aes_mode'] == "128":
            aes_key_mode = 0b0100
        elif self.config['aes_mode'] == "192":
            aes_key_mode = 0b0110
        else: # "256"
            aes_key_mode = 0b0111

        # Key extended with trailing zeros
        key_ext = key['data'] + str(int(AES_KEY_256_WIDTH // 4 - int(key['n_bytes']) * 2) * '0')

        key_bv = bv(n_bits=AES_KEY_256_WIDTH)

        # The Key is loaded right aligned
        key_bv.assign('{:>0{width}b}'.format(int(key_ext, 16), width=AES_KEY_256_WIDTH))

        self.dut.aes_gcm_key_word_val_i.value = aes_key_mode
        self.dut.aes_gcm_key_word_i.value     = key_bv.get_value()
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_key_word_val_i.value = 0
        self.dut.aes_gcm_key_word_i.value     = 0

        self.dut._log.info(f"KEY: {self.config['aes_mode']} bits")
        self.dut._log.info(f"KEY = 0x{key['data']}")
        self.key_loaded = True


    # ======================================================================================
    @cocotb.coroutine
    def load_pre_exp_key(self, key):
        '''
        Load a pre-expanded AES Key.
        The function checks in what mode the DUT has been set (key type 128, 192, 256).
        Key stages (128 bit) are loaded one at the time. Bits 3-0 of 'val' signal are used
        to select the index of the stage to load, while bit 7 triggers the stage to be
        loaded '''

        # Select key length
        if self.config['aes_mode'] == "128":
            exp_rnd = 11
        elif self.config['aes_mode'] == "192":
            exp_rnd = 13
        else: # "256"
            exp_rnd = 15

        exp_key = aes_expand_key(key['data'], self.config['aes_mode'])
        key_bv  = bv(n_bits=AES_KEY_256_WIDTH)

        for i in range (exp_rnd):
            # Key extended with trailing zeros
            key_ext = ''.join(str('{:0>2X}'.format(x)) for x in exp_key[:16]) + str(32 * '0')
            key_bv.assign('{:>0{width}b}'.format(int(key_ext, 16), width=AES_KEY_256_WIDTH))
            exp_key = exp_key[16:]
            # The Key is loaded left aligned
            self.dut.aes_gcm_key_word_val_i.value = (i + 1)
            self.dut.aes_gcm_key_word_i.value     = key_bv.get_value()
            yield RisingEdge(self.dut.clk_i)

        self.dut.aes_gcm_key_word_val_i.value = 0
        yield RisingEdge(self.dut.clk_i)

        self.dut._log.info(f"KEY: {self.config['aes_mode']} bits")
        self.dut._log.info(f"KEY = 0x{key['data']}")
        self.key_loaded = True


    # ======================================================================================
    @cocotb.coroutine
    def cipher_is_ready(self):
        '''
        Wait for the AES to Produce H0 and J0. This can be avoided
        if the AES pipeline has the same size of the AES number of rounds '''

        while self.dut.aes_gcm_ready_o.value == 0:
            yield RisingEdge(self.dut.clk_i)


    # ======================================================================================
    def config_data(self):
        '''
        Produce the IV, the AAD and the PT data '''

        iv  = {}
        key = {}

        _bytes = {  'aad_n_bytes' : 0,
                    'pt_n_bytes' : 0}
        _name  = [  'aad_n_bytes',
                    'pt_n_bytes']

        if self.config['aes_mode'] == "ALL":
            self.config['aes_mode'] = random.choice(AES_KEY_TYPES)

        if self.config['aes_mode'] == '128':
            key['n_bytes'] = 16
        elif self.config['aes_mode'] == '192':
            key['n_bytes'] = 24
        else:
            key['n_bytes'] = 32

        # Load the IV
        iv['n_bytes'] = 12

        if re.fullmatch(r"^[0-9a-fA-F]+$", self.config['iv']) is not None:
            iv['data'] = '{:0>{width}.{max}}'.format(self.config['iv'], width=2*iv['n_bytes'], max=2*iv['n_bytes'])
        else:
            raise TestFailure("IV is not an hexadecimal number")

        # Load the Key
        if re.fullmatch(r"^[0-9a-fA-F]+$", self.config['key']) is not None:
            # Right align, pad width 0s, {width}.{precision (max)}
            key['data'] = '{:0>{width}.{max}}'.format(self.config['key'], width=2*key['n_bytes'], max=2*key['n_bytes'])
        else:
            raise TestFailure("Key is not an hexadecimal number")

        self.data['iv']  = iv
        self.data['key'] = key

        # Number of byte for AAD and PT
        for i in range(2):
            n_bytes = int(random.betavariate(.1, .1) * self.config['max_n_byte'])
            self.dut._log.info(f"{_name[i]}: byte to generate: {n_bytes}")
            _bytes[_name[i]] = n_bytes

        self.data.update(_bytes)

        # Create random delays: 5 bits
        #   bit-0 : inserts a delay between the start of the packet and the first AAD data
        #   bit-1 : inserts a delay between an AAD data and the next one
        #   bit-2 : inserts a delay between the last AAD data and the first PT data
        #   bit-3 : inserts a delay between a Data in and the next one
        #   bit-4 : inserts a delay between the last Data in and the end of the packet
        self.data['delays'] = random.randint(0, 31)

        # N.B. When decrypting, there cannot be an overlap of the AAD and the CT.
        #      AAD+CT is the stream of data that enters the GHASH.
        #      Therefore, in this case bit-2 needs to be 0.
        if self.config['enc_dec'] == 'dec':
            self.data['delays'] &= ~(1 << 2)


    # ======================================================================================
    @cocotb.coroutine
    def encrypt_data(self, aad_n_bytes, pt_n_bytes, aad_tran, pt_tran, aad_model_tran, pt_model_tran):
        '''
        Send AAD and PT data through the pipeline '''

        # Create 128-bit AAD words
        aad_n_trans     = aad_n_bytes >> 4
        aad_last_trans  = 1 if aad_n_bytes & 0xF else 0
        aad_tot_trans   = aad_n_trans + aad_last_trans

        # Create 128-bit PT words
        pt_n_trans      = pt_n_bytes >> 4
        pt_last_trans   = 1 if pt_n_bytes & 0xF else 0
        pt_tot_trans    = pt_n_trans + pt_last_trans

        # Load the AAD data
        if aad_tot_trans:
            bar_txt = 'AAD: generating ' + str(aad_tot_trans) + ' block'
            bar_txt = (bar_txt + 's') if aad_tot_trans != 1 else bar_txt
            with Bar(bar_txt, max=aad_tot_trans) as bar:
                while aad_n_trans:
                    if len(aad_tran) < 100:
                        transaction = bytes.fromhex('{:032X}'.format(random.randint(0, (2**128)-1)))
                        aad_tran.append(transaction)
                        aad_model_tran.append(transaction)
                        aad_n_trans -= 1
                        bar.next()
                    else:
                        yield RisingEdge(self.dut.clk_i)

                # Create the last chunck of AAD shorter than a word
                if aad_last_trans:
                    n_rem_bytes = aad_n_bytes & 0xF
                    transaction = bytes.fromhex('{:0{width}X}'.format(random.randint(0, (2**(8*n_rem_bytes))-1), width=2*n_rem_bytes))
                    aad_tran.append(transaction)
                    aad_model_tran.append(transaction)
                    bar.next()
                bar.finish()

        # Load the PT data
        if pt_tot_trans:
            bar_txt = 'PT:  generating ' + str(pt_tot_trans) + ' block'
            bar_txt = (bar_txt + 's') if pt_tot_trans != 1 else bar_txt
            with Bar(bar_txt, max=pt_tot_trans) as bar:
                while pt_n_trans:
                    if len(pt_tran) < 100:
                        transaction = bytes.fromhex('{:032X}'.format(random.randint(0, (2**128)-1)))
                        pt_tran.append(transaction)
                        pt_model_tran.append(transaction)
                        pt_n_trans -= 1
                        bar.next()
                    else:
                        yield RisingEdge(self.dut.clk_i)

                # Create the last chunck of PT shorter than a word
                if pt_last_trans:
                    n_rem_bytes = pt_n_bytes & 0xF
                    transaction = bytes.fromhex('{:0{width}X}'.format(random.randint(0, (2**(8*n_rem_bytes))-1), width=2*n_rem_bytes))
                    pt_tran.append(transaction)
                    pt_model_tran.append(transaction)
                    bar.next()
                bar.finish()

