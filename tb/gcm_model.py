from Crypto.Cipher import AES
from cocotb import log

# ======================================================================================
class gcm:

    # ======================================================================================
    def __init__(self, key, icb, ed):

        # encryption/decryption
        self.ed = ed

        self.data_out = []
        self.tag = []

        _key = int(key['data'], 16).to_bytes(key['n_bytes'], byteorder='big')
        _icb = int(icb['data'], 16).to_bytes(icb['n_bytes'], byteorder='big')
        self.model = AES.new(_key, mode=AES.MODE_GCM, nonce=_icb)

    # ======================================================================================
    def load_aad(self, aad):
        self.model.update(aad)

    # ======================================================================================
    def load_plain_text(self, pt):
        self.data_out.append(self.model.encrypt(pt))

    # ======================================================================================
    def load_cipher_text(self, ct):
        self.data_out.append(self.model.decrypt(ct))

    # ======================================================================================
    def get_tag(self, tag):
        if self.ed == 'enc':
            model_tag = self.model.digest()
            self.tag.append(model_tag)
            log.info('Model\tTAG '  + '{:032X}'.format(int.from_bytes(model_tag, 'big')))
            if tag == model_tag:
                log.info('\33[92m' + "OK:\tTAGs match. " + '\33[00m')
            else:
                log.error('ERROR: TAGs mismatch')
        else:
            try:
                self.model.verify(tag)
                self.tag.append(tag)
                log.info('\33[92m' + "OK:\tTAGs match. " + '\33[00m' + "the message is authentic!")
            except ValueError:
                log.error("ERROR:\tKEY or IV incorrect, or message corrupted")
                # Force TAG error: invert received TAG
                not_tag = ~(int.from_bytes(tag, 'big'))
                self.tag.append((not_tag & ((1 << 128)-1)).to_bytes(16, 'big'))

