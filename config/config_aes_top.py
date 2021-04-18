#!/usr/bin/env python3

import sys

def generate_aes_top(aes_mode = '128', aes_n_rounds = 1, pipe_stage=0, filepath='./'):
    filename = filepath + 'top_aes_gcm.vhd'

    file_lines = []
    file_lines.append(
    '''--------------------------------------------------------------------------------
--! @File name:     top_aes_gcm
--! @Date:          01/10/2019
--! @Description:   this module is the top entity
--! @Reference:     NIST Special Publication 800-38D, November, 2007
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.gcm_pkg.all;
use work.aes_pkg.all;

-- This IP has been configured with:
--   AES Mode:    ''' + aes_mode + '''
--   # rounds:    ''' + str(aes_n_rounds) + '''
--   pipe stages: ''' + str(pipe_stage) + '''

--------------------------------------------------------------------------------
entity top_aes_gcm is
    port(
        rst_i                           : in  std_logic;
        clk_i                           : in  std_logic;
        aes_gcm_mode_i                  : in  std_logic_vector(1 downto 0);
        aes_gcm_pipe_reset_i            : in  std_logic;
        aes_gcm_key_word_val_i          : in  std_logic_vector(3 downto 0);
        aes_gcm_key_word_i              : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
        aes_gcm_iv_val_i                : in  std_logic;
        aes_gcm_iv_i                    : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
        aes_gcm_icb_start_cnt_i         : in  std_logic;
        aes_gcm_icb_stop_cnt_i          : in  std_logic;
        aes_gcm_ghash_pkt_val_i         : in  std_logic;
        aes_gcm_ghash_aad_bval_i        : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_ghash_aad_i             : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        aes_gcm_plain_text_bval_i       : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_plain_text_i            : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        aes_gcm_cipher_ready_o          : out std_logic;
        aes_gcm_cipher_text_val_o       : out std_logic;
        aes_gcm_cipher_text_bval_o      : out std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_cipher_text_o           : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        aes_gcm_icb_cnt_overflow_o      : out std_logic;
        aes_gcm_ghash_tag_val_o         : out std_logic;
        aes_gcm_ghash_tag_o             : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0));
end entity;

--------------------------------------------------------------------------------
architecture arch_top_aes_gcm of top_aes_gcm is

    component aes_gcm is
        generic(
            aes_gcm_mode_g                  : std_logic_vector(1 downto 0)  := AES_MODE_128_C;
            aes_gcm_n_rounds_g              : natural range 0 to NR_256_C   := NR_128_C);
        port(
            rst_i                           : in  std_logic;
            clk_i                           : in  std_logic;
            aes_gcm_mode_i                  : in  std_logic_vector(1 downto 0);
            aes_gcm_pipe_reset_i            : in  std_logic;
            aes_gcm_key_word_val_i          : in  std_logic_vector(3 downto 0);
            aes_gcm_key_word_i              : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
            aes_gcm_iv_val_i                : in  std_logic;
            aes_gcm_iv_i                    : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
            aes_gcm_icb_start_cnt_i         : in  std_logic;
            aes_gcm_icb_stop_cnt_i          : in  std_logic;
            aes_gcm_ghash_pkt_val_i         : in  std_logic;
            aes_gcm_ghash_aad_bval_i        : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            aes_gcm_ghash_aad_i             : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            aes_gcm_plain_text_bval_i       : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            aes_gcm_plain_text_i            : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            aes_gcm_cipher_ready_o          : out std_logic;
            aes_gcm_cipher_text_val_o       : out std_logic;
            aes_gcm_cipher_text_bval_o      : out std_logic_vector(NB_STAGE_C-1 downto 0);
            aes_gcm_cipher_text_o           : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            aes_gcm_icb_cnt_overflow_o      : out std_logic;
            aes_gcm_ghash_tag_val_o         : out std_logic;
            aes_gcm_ghash_tag_o             : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0));
    end component;

begin

    u_aes_gcm: aes_gcm
        generic map(
            aes_gcm_mode_g                  => AES_MODE_''' + aes_mode + '''_C,
            aes_gcm_n_rounds_g              => ''' + str(aes_n_rounds) + ''')
        port map(
            rst_i                           => rst_i,
            clk_i                           => clk_i,
            aes_gcm_mode_i                  => aes_gcm_mode_i,
            aes_gcm_pipe_reset_i            => aes_gcm_pipe_reset_i,
            aes_gcm_key_word_val_i          => aes_gcm_key_word_val_i,
            aes_gcm_key_word_i              => aes_gcm_key_word_i,
            aes_gcm_iv_val_i                => aes_gcm_iv_val_i,
            aes_gcm_iv_i                    => aes_gcm_iv_i,
            aes_gcm_icb_start_cnt_i         => aes_gcm_icb_start_cnt_i,
            aes_gcm_icb_stop_cnt_i          => aes_gcm_icb_stop_cnt_i,
            aes_gcm_ghash_pkt_val_i         => aes_gcm_ghash_pkt_val_i,
            aes_gcm_ghash_aad_bval_i        => aes_gcm_ghash_aad_bval_i,
            aes_gcm_ghash_aad_i             => aes_gcm_ghash_aad_i,
            aes_gcm_plain_text_bval_i       => aes_gcm_plain_text_bval_i,
            aes_gcm_plain_text_i            => aes_gcm_plain_text_i,
            aes_gcm_cipher_ready_o          => aes_gcm_cipher_ready_o,
            aes_gcm_cipher_text_val_o       => aes_gcm_cipher_text_val_o,
            aes_gcm_cipher_text_bval_o      => aes_gcm_cipher_text_bval_o,
            aes_gcm_cipher_text_o           => aes_gcm_cipher_text_o,
            aes_gcm_icb_cnt_overflow_o      => aes_gcm_icb_cnt_overflow_o,
            aes_gcm_ghash_tag_val_o         => aes_gcm_ghash_tag_val_o,
            aes_gcm_ghash_tag_o             => aes_gcm_ghash_tag_o);

end architecture;
''')

    try:
        with open(filename, 'w') as fp:
            fp = open(filename, 'w')
            fp.write("\n".join(file_lines).expandtabs(4))
            fp.close()
            print(' >>\tOK   : File ' + filename + ' has been successfully generated')
    except:
        print(' >>\tError: File ' + filename + ' could not be generated')
        sys.exit()
