#from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Crypto.Cipher import AES
from cocotb import log

# ======================================================================================
class gcm:

    # ======================================================================================
    def __init__(self, key, icb):

        self.ct  = []
        self.tag = []

        _key = int(key['data'], 16).to_bytes(key['n_bytes'], byteorder='big')
        _icb = int(icb['data'], 16).to_bytes(icb['n_bytes'], byteorder='big')
        self.model = AES.new(_key, mode=AES.MODE_GCM, nonce=_icb)

    # ======================================================================================
    def load_aad(self, aad):
        self.model.update(aad)

    # ======================================================================================
    def load_plain_text(self, pt):
        self.ct.append(self.model.encrypt(pt))

    # ======================================================================================
    def get_tag(self, aad):
        tag = self.model.digest()
        self.tag.append(tag)
        log.info('Model\tTAG '  + '{:032X}'.format(int.from_bytes(tag, 'big')))

