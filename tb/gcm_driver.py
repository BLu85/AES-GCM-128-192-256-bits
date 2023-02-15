import cocotb
from cocotb.triggers    import RisingEdge
from cocotb.binary      import BinaryValue as bv


# ======================================================================================
class aad_driver:
    def __init__(self, clk, bval, data):

        self.clk  = clk
        self.bval = bval
        self.data = data

    # ======================================================================================
    @cocotb.coroutine
    def write(self, aad):
        '''
        Load the AAD data.
        The function assert the packet valid and starts loading data in
        chuncks of 128 bit wide
        '''
        self.aad_data = bv(n_bits=128)
        self.aad_bval = bv(n_bits=16)

        # Load the AAD
        n_bits = len(aad) * 8
        self.aad_data.assign('{:0{width}b}'.format(int.from_bytes(aad, "big"), width=n_bits))
        self.aad_bval.assign((n_bits // 8) * '1')

        self.data.value = self.aad_data.get_value()
        self.bval.value = self.aad_bval.get_value()
        yield RisingEdge(self.clk)
        self.bval.value = 0

# ======================================================================================
class pkt_driver:
    def __init__(self, clk, pkt):
        self.clk = clk
        self.pkt = pkt

    @cocotb.coroutine
    def start_pkt(self):
        yield RisingEdge(self.clk)
        self.pkt.value = 1

    @cocotb.coroutine
    def stop_pkt(self):
        self.pkt.value = 0
        yield RisingEdge(self.clk)


# ======================================================================================
class pt_driver:
    def __init__(self, clk, bval, data, ready):

        self.clk   = clk
        self.bval  = bval
        self.data  = data
        self.ready = ready

    # ======================================================================================
    @cocotb.coroutine
    def write(self, pt):
        '''
        Load the PT to encrypt.
        The function waits for the AAD data to be loaded. This is triggered by an event.
        A random delay could be inserted between the last loaded AAD data and the loading
        of the first PT block. Another delay could be inserted between the last
        loaded PT block and the falling edge of the packet valid.
        '''
        self.pt_data = bv(n_bits=128)
        self.pt_dval = bv(n_bits=16)

        n_bits = len(pt) * 8
        self.pt_data.assign('{:0{width}b}'.format(int.from_bytes(pt, "big"), width=n_bits))
        self.pt_dval.assign((n_bits // 8) * '1')

        self.data.value = self.pt_data.get_value()
        self.bval.value = self.pt_dval.get_value()
        yield RisingEdge(self.clk)
        while (self.ready.value != 1):
            yield RisingEdge(self.clk)
        self.bval.value = 0


# ======================================================================================
class wait_for:
    def __init__(self, clk, edge):
        self.clk  = clk
        self.edge = edge

    # ======================================================================================
    @cocotb.coroutine
    def n_clk(self, n):
        for _ in range(n):
            yield self.edge(self.clk)


# ======================================================================================
class data_driver:
    def __init__(self, clk, bval, data):
        self.clk  = clk
        self.bval = bval
        self.data = data


    # ======================================================================================
    def read(self):
        val  = self.bval.value.integer
        data = self.data.value.integer
        '''
        Example:
                val  = 0xFFC0 <- 10 bits = '1'
                data = 0x756A9E2C1904DF026D35000000000000
                -----------------------------------------
                Only the first 10 bytes from the left are valid
        '''
        sel_byte = 0
        for _ in range(16):
            if val & 0x8000:
                sel_byte += 1
                val <<= 1
            else:
                break

        shift   = 16 - sel_byte
        data  >>= (shift * 8)
        block   = data.to_bytes(sel_byte, 'big')
        return(block)
