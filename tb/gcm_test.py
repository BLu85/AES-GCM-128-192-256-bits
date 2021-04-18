import json
import random
import re
import os
import gcm_model
import cocotb

from cocotb.result     import TestFailure
from cocotb.binary     import BinaryValue as bv
from cocotb.clock      import Clock
from cocotb.triggers   import Timer, Event, RisingEdge, FallingEdge, ClockCycles
from cocotb.scoreboard import Scoreboard

from key_exp           import aes_expand_key
from gcm_driver        import pkt_driver, aad_driver, pt_driver, wait_for
from gcm_sequencer     import sequencer, gcm_AAD_monitor, gcm_PT_monitor, gcm_CT_monitor, gcm_TAG_monitor

from progress.bar      import ShadyBar as Bar


AES_KEY_256_WIDTH   = 256
CLK_PERIOD          = 10
RST_WINDOW          = CLK_PERIOD + (CLK_PERIOD * 3 // 4)
AES_KEY_TYPES       = ['128', '192', '256']


# ======================================================================================
class gcm_gctr(object):
    def __init__(self, dut, debug=False):
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
        self.dut.rst_i                      <= 1
        self.dut.aes_gcm_mode_i             <= 0
        self.dut.aes_gcm_pipe_reset_i       <= 0
        self.dut.aes_gcm_icb_stop_cnt_i     <= 0
        self.dut.aes_gcm_iv_val_i           <= 0
        self.dut.aes_gcm_iv_i               <= 0
        self.dut.aes_gcm_icb_start_cnt_i    <= 0
        self.dut.aes_gcm_key_word_i         <= 0
        self.dut.aes_gcm_key_word_val_i     <= 0
        self.dut.aes_gcm_ghash_pkt_val_i    <= 0
        self.dut.aes_gcm_plain_text_i       <= 0
        self.dut.aes_gcm_plain_text_bval_i  <= 0
        self.dut.aes_gcm_ghash_aad_i        <= 0
        self.dut.aes_gcm_ghash_aad_bval_i   <= 0
        yield Timer(duration, 'ns')
        self.dut.rst_i                      <= 0
        self.dut._log.debug("Reset released")


    # ======================================================================================
    @cocotb.coroutine
    def load_iv(self, iv):
        '''
        Load the IV vector.
        After the 96 bit IV is loaded, a flag is set '''

        iv_bv = bv(n_bits=iv['n_bytes'] * 8)

        # IV is loaded right aligned
        iv_bv.assign('{:>0{width}b}'.format(int(iv['data'], 16), width=int(iv['n_bytes']) * 8))

        self.dut.aes_gcm_iv_val_i   <= 1
        self.dut.aes_gcm_iv_i       <= iv_bv.get_value()
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_iv_val_i   <= 0
        self.dut.aes_gcm_iv_i       <= 0

        self.dut._log.info("IV  = 0x%s", iv['data'])
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
            self.dut.aes_gcm_icb_start_cnt_i <= 1
            yield RisingEdge(self.dut.clk_i)
            self.dut.aes_gcm_icb_start_cnt_i <= 0


    # ======================================================================================
    @cocotb.coroutine
    def stop_icb(self):
        '''
        Stop the ICB '''

        self.dut.aes_gcm_icb_stop_cnt_i <= 1
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_icb_stop_cnt_i <= 0
        self.iv_loaded = False
        self.dut._log.info("Start ICB counter")


    # ======================================================================================
    @cocotb.coroutine
    def aes_set_mode(self):
        '''
        Set the AES mode '''

        self.dut.aes_gcm_mode_i <= AES_KEY_TYPES.index(self.config['aes_mode'])
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

        self.dut.aes_gcm_key_word_val_i <= aes_key_mode
        self.dut.aes_gcm_key_word_i     <= key_bv.get_value()
        yield RisingEdge(self.dut.clk_i)
        self.dut.aes_gcm_key_word_val_i <= 0
        self.dut.aes_gcm_key_word_i     <= 0

        self.dut._log.info("KEY: %s bits", self.config['aes_mode'])
        self.dut._log.info("KEY = 0x%s", key['data'])
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
            self.dut.aes_gcm_key_word_val_i <= (i + 1)
            self.dut.aes_gcm_key_word_i     <= key_bv.get_value()
            yield RisingEdge(self.dut.clk_i)

        self.dut.aes_gcm_key_word_val_i <= 0
        yield RisingEdge(self.dut.clk_i)

        self.dut._log.info("KEY: %s bits", self.config['aes_mode'])
        self.dut._log.info("KEY = 0x%s", key['data'])
        self.key_loaded = True


    # ======================================================================================
    @cocotb.coroutine
    def cipher_is_ready(self):
        '''
        Wait for the AES to Produce H0 and J0. This can be avoided
        if the AES pipeline has the same size of the AES number of rounds '''

        while self.dut.aes_gcm_cipher_ready_o.value == 0:
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

        # Create the IV or load it
        iv['n_bytes'] = 12
        if self.config['iv'] == 'random':
            iv['data'] = '{:0{width}X}'.format(random.randint(0, (2**(8*iv['n_bytes']))-1), width =2*iv['n_bytes'])
        else:
            if re.fullmatch(r"^[0-9a-fA-F]+$", self.config['iv']) is not None:
                iv['data'] = '{:0>{width}.{max}}'.format(self.config['iv'], width = 2*iv['n_bytes'], max =2*iv['n_bytes'])
            else:
                raise TestFailure("IV is not an hexadecimal number")

        # Create the Key or load it
        if self.config['key'] == 'random':
            key['data'] = '{:0{width}X}'.format(random.randint(0, 2**(8 * key['n_bytes']) - 1), width =2*key['n_bytes'])
        else:
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
            self.dut._log.info("\n" + _name[i] + ": byte to generate: " + str(n_bytes))
            _bytes[_name[i]] = n_bytes

        self.data.update(_bytes)

        # Create random delays: 5 bits
        #   bit-0 : inserts a delay between the start of the packet and the first AAD data
        #   bit-1 : inserts a delay between an AAD data and the next one
        #   bit-2 : inserts a delay between the last AAD data and the first PT data
        #   bit-3 : inserts a delay between the last AAD data and the first PT data
        #   bit-4 : inserts a delay between the last PT data and the end of the packet
        self.data['delays'] = random.randint(0, 31)


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


# ======================================================================================
@cocotb.test()
def test_dut(dut):
    '''
    The testbench:
      * binds the interfaces
      * Loads the Key
      * Loads the IV in the ICB
      * Sends the AAD data through the pipeline
      * Sends the PT data through the pipeline
      * Checks the CT and the MAC match the model '''

    # Create the lists of transactions
    aad_tran        = []
    pt_tran         = []
    aad_model_tran  = []
    pt_model_tran   = []

    tb = gcm_gctr(dut)

    # Open config file
    with open('./tmp/' + str(cocotb.RANDOM_SEED) + '.json', 'r') as config_file:
        tb.config = dict(json.load(config_file))

    # Generate configuration data
    tb.config_data()

    # Initialise GCM model
    dut_model = gcm_model.gcm(tb.data['key'], tb.data['iv'])

    # Create drivers
    pkt_drv = pkt_driver(dut.clk_i, dut.aes_gcm_ghash_pkt_val_i)
    aad_drv = aad_driver(dut.clk_i, dut.aes_gcm_ghash_aad_bval_i,  dut.aes_gcm_ghash_aad_i)
    pt_drv  = pt_driver( dut.clk_i, dut.aes_gcm_plain_text_bval_i, dut.aes_gcm_plain_text_i, dut.aes_gcm_cipher_ready_o)

    # Create delay function
    delay   = wait_for(dut.clk_i, RisingEdge)

    # Get the AES mode
    dut._log.info('AES mode: ' + tb.config['aes_mode'])

    # Get AES key size
    dut._log.info('AES size: ' + tb.config['aes_size'])

    # Release the Reset
    cocotb.fork(tb.release_rst(RST_WINDOW))

    # Start the Clock
    cocotb.fork(Clock(dut.clk_i, CLK_PERIOD, 'ns').start())

    # Wait for the Reset falling edge event
    yield FallingEdge(dut.rst_i)

    # Wait few clocks
    yield ClockCycles(dut.clk_i, random.randint(10, 20))

    # Create the sequencer
    seq = sequencer(pkt_drv, aad_drv, pt_drv, delay.n_clk, tb.data, str(tb.config['seed']), aad_tran, pt_tran)

    # Create monitors
    mon_aad = gcm_AAD_monitor("Get AAD", dut, dut_model.load_aad)
    mon_pt  = gcm_PT_monitor("Get PT", dut, dut_model.load_plain_text)
    mon_ct  = gcm_CT_monitor("Get CT", dut)
    mon_tag = gcm_TAG_monitor("Get TAG", dut, dut_model.get_tag)

    # Create scoreboard
    scoreboard = Scoreboard(dut)

    # Add scoreboard interfaces
    scoreboard.add_interface(mon_aad, aad_model_tran)
    scoreboard.add_interface(mon_pt,  pt_model_tran)
    scoreboard.add_interface(mon_ct,  dut_model.ct)
    scoreboard.add_interface(mon_tag, dut_model.tag)

    # Set AES key mode
    yield tb.aes_set_mode()

    # Load the KEY
    if (tb.config['key_pre_exp'] == True):
        yield tb.load_pre_exp_key(tb.data['key'])
    else:
        yield tb.load_key(tb.data['key'])

    # Load the ICB
    yield tb.load_iv(tb.data['iv'])

    # Start The ICB
    yield tb.start_icb()

    # Wait the AES to produce cipher data
    yield tb.cipher_is_ready()

     # Set the number of AAD transactions
    n_transaction = tb.data['aad_n_bytes'] >> 4
    if tb.data['aad_n_bytes'] & 0xF:
        n_transaction += 1
    dut._log.info('\n' + str(n_transaction) + " AAD transactions to read")

    # Set the number of PT transactions
    n_transaction = tb.data['pt_n_bytes'] >> 4
    if tb.data['pt_n_bytes'] & 0xF:
        n_transaction += 1
    dut._log.info(str(n_transaction) + " PT transactions to read\n")

    # Start the sequencer
    seq.start_sequencer()

    # Encrypt data
    yield tb.encrypt_data(tb.data['aad_n_bytes'], tb.data['pt_n_bytes'], aad_tran, pt_tran, aad_model_tran, pt_model_tran)

    # Wait for the test to finish
    while dut.aes_gcm_ghash_tag_val_o.value == 0:
        yield RisingEdge(dut.clk_i)

    last_cycles = ClockCycles(dut.clk_i, 20)
    yield last_cycles

