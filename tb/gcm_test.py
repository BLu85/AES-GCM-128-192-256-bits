import json
import random
import cocotb
import gcm_model
import gcm_gctr as gctr

from cocotb.clock          import Clock
from gcm_driver            import pkt_driver, aad_driver, pt_driver, wait_for
from gcm_sequencer         import sequencer, gcm_AAD_monitor, gcm_PT_monitor, gcm_CT_monitor, gcm_TAG_monitor
from cocotb.triggers       import RisingEdge, FallingEdge, ClockCycles
from cocotb_bus.scoreboard import Scoreboard

CLK_PERIOD = 10
RST_WINDOW = CLK_PERIOD + (CLK_PERIOD * 3 // 4)


# ======================================================================================
@cocotb.test()
def test_dut(dut):
    '''
    The testbench:
      * Binds the interfaces
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

    tb = gctr.gcm_gctr(dut)

    # Open config file
    with open('./tmp/' + str(cocotb.RANDOM_SEED) + '.json', 'r') as config_file:
        tb.config = dict(json.load(config_file))

    # Generate configuration data
    tb.config_data()

    # Initialise GCM model
    dut_model = gcm_model.gcm(tb.data['key'], tb.data['iv'], tb.config['enc_dec'])

    # Create drivers
    pkt_drv = pkt_driver(dut.clk_i, dut.aes_gcm_ghash_pkt_val_i)
    aad_drv = aad_driver(dut.clk_i, dut.aes_gcm_ghash_aad_bval_i,  dut.aes_gcm_ghash_aad_i)
    pt_drv  = pt_driver( dut.clk_i, dut.aes_gcm_data_in_bval_i, dut.aes_gcm_data_in_i, dut.aes_gcm_ready_o)

    # Create delay function
    delay   = wait_for(dut.clk_i, RisingEdge)

    # Get the AES mode
    dut._log.info('AES mode: ' + tb.config['aes_mode'])

    # Get AES key size
    dut._log.info('AES size: ' + tb.config['aes_size'])

    # Release the Reset
    cocotb.start_soon(tb.release_rst(RST_WINDOW))

    # Start the Clock
    cocotb.start_soon(Clock(dut.clk_i, CLK_PERIOD, 'ns').start())

    # Wait for the Reset falling edge event
    yield FallingEdge(dut.rst_i)

    # Wait few clocks
    yield ClockCycles(dut.clk_i, random.randint(10, 20))

    # Create the sequencer
    seq = sequencer(pkt_drv, aad_drv, pt_drv, delay.n_clk, tb.data, aad_tran, pt_tran)

    if tb.config['enc_dec'] == 'enc':
        data_in_callback = dut_model.load_plain_text
    else:
        data_in_callback = dut_model.load_cipher_text

    # Create monitors
    mon_aad      = gcm_AAD_monitor("Get AAD", dut, dut_model.load_aad)
    mon_data_in  = gcm_PT_monitor("Get PT", dut, data_in_callback)
    mon_data_out = gcm_CT_monitor("Get CT", dut)
    mon_tag      = gcm_TAG_monitor("Get TAG", dut, dut_model.get_tag)

    # Create scoreboard
    scoreboard = Scoreboard(dut)

    # Add scoreboard interfaces
    scoreboard.add_interface(mon_aad, aad_model_tran)
    scoreboard.add_interface(mon_data_in, pt_model_tran)
    scoreboard.add_interface(mon_data_out, dut_model.data_out)
    scoreboard.add_interface(mon_tag, dut_model.tag)

    # Set the AES in encryption or decryption mode
    yield tb.set_enc_dec(tb.config['enc_dec'])

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
    dut._log.info(f"\nAAD:\t{n_transaction}\ttransactions to read")

    # Set the number of PT transactions
    n_transaction = tb.data['pt_n_bytes'] >> 4
    if tb.data['pt_n_bytes'] & 0xF:
        n_transaction += 1
    dut._log.info(f"DATA:\t{n_transaction}\ttransactions to read\n")

    # Start the sequencer
    seq.start_sequencer()

    # Encrypt data
    yield tb.encrypt_data(tb.data['aad_n_bytes'], tb.data['pt_n_bytes'], aad_tran, pt_tran, aad_model_tran, pt_model_tran)

    # Wait for the test to finish
    while dut.aes_gcm_ghash_tag_val_o.value == 0:
        yield RisingEdge(dut.clk_i)

    last_cycles = ClockCycles(dut.clk_i, 20)
    yield last_cycles

