import cocotb
import random

from cocotb.triggers        import RisingEdge, Event
from cocotb_bus.monitors    import Monitor
from gcm_driver             import data_driver


# ======================================================================================
class sequencer:

    def __init__(self, pkt_drv, aad_drv, pt_drv, delay, config, aad_tran, pt_tran):

        self.pkt_drv    = pkt_drv
        self.aad_drv    = aad_drv
        self.pt_drv     = pt_drv
        self.config     = config
        self.end_aad    = Event()
        self.close_pkt  = Event()
        self.delay      = delay
        self.rnd        = lambda x : x * random.randint(0, 5)
        self.aad_tran   = aad_tran
        self.pt_tran    = pt_tran


    # ======================================================================================
    @cocotb.coroutine
    def aad(self):

        delay_in        = 1 if (self.config['delays'] & 0x01) else 0
        aad_toggle      = 1 if (self.config['delays'] & 0x02) else 0
        overlap         = 1 if (self.config['delays'] & 0x04) else 0

        aad_n_blocks    = self.config['aad_n_bytes'] >> 4
        aad_last_block  = 1 if (self.config['aad_n_bytes'] & 0xF) else 0

        # Start valid packet
        yield self.pkt_drv.start_pkt()
        yield self.delay(self.rnd(delay_in))

        # Start AAD data
        while aad_n_blocks:
            if len(self.aad_tran):
                yield self.delay(self.rnd(aad_toggle))
                data = self.aad_tran.pop(0)
                aad_n_blocks -= 1
                yield self.aad_drv.write(data)

        # Send the last AAD block
        while aad_last_block:
            if len(self.aad_tran):
                yield self.delay(self.rnd(aad_toggle))
                data = self.aad_tran.pop(0)
                aad_last_block -= 1
                if overlap == 1:
                    # Trigger the Plain Text to start
                    self.end_aad.set("AAD End of data")
                    yield self.aad_drv.write(data)
                else:
                    yield self.aad_drv.write(data)
                    yield self.delay(self.rnd(1))
                    # Trigger the Plain Text to start
                    self.end_aad.set("AAD End of data")
        else:
            self.end_aad.set("AAD End of data")

        # Send close packet trigger
        self.close_pkt.set("Close the packet")


    # ======================================================================================
    @cocotb.coroutine
    def pt(self):

        pt_toggle   = 1 if (self.config['delays'] & 0x08) else 0
        delay_out   = 1 if (self.config['delays'] & 0x10) else 0

        pt_n_blocks = self.config['pt_n_bytes'] >> 4

        if self.config['pt_n_bytes'] & 0xF:
            pt_n_blocks += 1

        yield self.end_aad.wait()

        ## Start PT data
        cnt = pt_n_blocks
        while cnt:
            if len(self.pt_tran):
                yield self.delay(self.rnd(pt_toggle))
                data = self.pt_tran.pop(0)
                cnt -= 1
                yield self.pt_drv.write(data)

        # Close Packet valid
        yield self.delay(self.rnd(delay_out))

        self.close_pkt.wait()

        if pt_n_blocks == 0:
            yield self.delay(1)

        yield self.pkt_drv.stop_pkt()


    # ======================================================================================
    def start_sequencer(self):
        cocotb.start_soon(self.pt())
        cocotb.start_soon(self.aad())


# ======================================================================================
class gcm_AAD_monitor(Monitor):
    '''
    Receive the AAD data.
    Each 'bval' bit signals a valid cipher text byte from the
    AAD data vector.
    '''

    # ======================================================================================
    def __init__(self, name, dut, callback=None, event=None):
        self.name     = name
        self.clk      = dut.clk_i
        self.aad_bval = dut.aes_gcm_ghash_aad_bval_i
        self.aad_data = dut.aes_gcm_ghash_aad_i
        Monitor.__init__(self, callback, event)

    # ======================================================================================
    @cocotb.coroutine
    def _monitor_recv(self):

        transaction = data_driver(self.clk, self.aad_bval, self.aad_data)
        while True:
            if self.aad_bval.value.integer != 0:

                cocotb.log.debug(f"\tAAD {self.aad_bval.value.integer:04X} " + \
                                    f"{self.aad_data.value.integer:032X}")
                aad_block = transaction.read()
                self._recv(aad_block)

            yield RisingEdge(self.clk)


# ======================================================================================
class gcm_PT_monitor(Monitor):
    '''
    Receive the plain text data.
    Each 'bval' bit signals a valid cipher text byte from the
    plain text data vector.
    '''

    # ======================================================================================
    def __init__(self, name, dut, callback=None, event=None):
        self.name    = name
        self.clk     = dut.clk_i
        self.pt_bval = dut.aes_gcm_data_in_bval_i
        self.pt_data = dut.aes_gcm_data_in_i
        self.rdy     = dut.aes_gcm_ready_o
        Monitor.__init__(self, callback, event)

    # ======================================================================================
    @cocotb.coroutine
    def _monitor_recv(self):

        transaction = data_driver(self.clk, self.pt_bval, self.pt_data)
        while True:
            if self.pt_bval.value.integer != 0 and self.rdy.value.integer == 1:

                cocotb.log.debug(f"\tPT {self.pt_bval.value.integer:04X} " + \
                                    f"{self.pt_data.value.integer:032X}")
                pt_block = transaction.read()
                self._recv(pt_block)

            yield RisingEdge(self.clk)


# ======================================================================================
class gcm_CT_monitor(Monitor):
    '''
    Receive the cipher data.
    Each 'bval' bit signals a valid cipher text byte from the
    cipher data vector.
    '''

    # ======================================================================================
    def __init__(self, name, dut, callback=None, event=None):
        self.name    = name
        self.clk     = dut.clk_i
        self.ct_bval = dut.aes_gcm_data_out_bval_o
        self.ct_data = dut.aes_gcm_data_out_o
        Monitor.__init__(self, callback, event)

    # ======================================================================================
    @cocotb.coroutine
    def _monitor_recv(self):

        transaction = data_driver(self.clk, self.ct_bval, self.ct_data)
        while True:
            if self.ct_bval.value.integer != 0:

                cocotb.log.debug(f"\tCT {self.ct_bval.value.integer:04X} " + \
                                    f"{self.ct_data.value.integer:032X}")
                ct_block = transaction.read()
                self._recv(ct_block)

            yield RisingEdge(self.clk)


# ======================================================================================
class gcm_TAG_monitor(Monitor):
    '''
    Receive the TAG data.
    '''

    # ======================================================================================
    def __init__(self, name, dut, callback=None, event=None):
        self.name       = name
        self.clk        = dut.clk_i
        self.tag_val    = dut.aes_gcm_ghash_tag_val_o
        self.tag_data   = dut.aes_gcm_ghash_tag_o
        Monitor.__init__(self, callback, event)

    # ======================================================================================
    @cocotb.coroutine
    def _monitor_recv(self):

        while True:
            if self.tag_val.value.integer == 1:

                tag = self.tag_data.value.integer
                cocotb.log.info(f"DUT\tTAG {tag:032X}")
                self._recv(tag.to_bytes(16, 'big'))

            yield RisingEdge(self.clk)
