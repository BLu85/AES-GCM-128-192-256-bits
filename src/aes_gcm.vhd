--------------------------------------------------------------------------------
--! @File name:     aes_gcm
--! @Date:          10/02/2019
--! @Description:   the module performs the AES-GCM encryption and uthentication
--! @Reference:     NIST Special Publication 800-38D, November, 2007
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.gcm_pkg.all;
use work.aes_pkg.all;

--------------------------------------------------------------------------------
entity aes_gcm is

    generic(
        aes_gcm_mode_g              : std_logic_vector(1 downto 0)  := AES_MODE_128_C;
        aes_gcm_n_rounds_g          : natural range 0 to NR_256_C   := NR_128_C);
    port(
        rst_i                       : in  std_logic;
        clk_i                       : in  std_logic;
        aes_gcm_mode_i              : in  std_logic_vector(1 downto 0);
        aes_gcm_enc_dec_i           : in  std_logic;
        aes_gcm_pipe_reset_i        : in  std_logic;
        aes_gcm_key_word_val_i      : in  std_logic_vector(3 downto 0);
        aes_gcm_key_word_i          : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
        aes_gcm_iv_val_i            : in  std_logic;
        aes_gcm_iv_i                : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
        aes_gcm_icb_start_cnt_i     : in  std_logic;
        aes_gcm_icb_stop_cnt_i      : in  std_logic;
        aes_gcm_ghash_pkt_val_i     : in  std_logic;
        aes_gcm_ghash_aad_bval_i    : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_ghash_aad_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        aes_gcm_data_in_bval_i      : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_data_in_i           : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        aes_gcm_ready_o             : out std_logic;
        aes_gcm_data_out_val_o      : out std_logic;
        aes_gcm_data_out_bval_o     : out std_logic_vector(NB_STAGE_C-1 downto 0);
        aes_gcm_data_out_o          : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        aes_gcm_ghash_tag_val_o     : out std_logic;
        aes_gcm_ghash_tag_o         : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        aes_gcm_icb_cnt_overflow_o  : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_gcm of aes_gcm is

    --! Constants

    --! Types

    --! Signals
    signal aes_ecb_val            : std_logic;
    signal aes_ecb_data           : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal aes_gcm_ready          : std_logic;
    signal gctr_data_out_bval     : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal gctr_data_out          : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal ghash_data_in_bval     : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal ghash_data_in          : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal ghash_h_loaded         : std_logic;
    signal ghash_j0_loaded        : std_logic;
    signal ghash_aad_val          : std_logic;
    signal ghash_ct_val           : std_logic;

    --------------------------------------------------------------------------------
    --! Component declaration
    --------------------------------------------------------------------------------
    component gcm_gctr is
        generic(
            gctr_mode_g                 : std_logic_vector(1 downto 0)  := AES_MODE_128_C;
            gctr_n_rounds_g             : natural range 0 to NR_256_C   := NR_128_C);
        port(
            rst_i                       : in  std_logic;
            clk_i                       : in  std_logic;
            gctr_mode_i                 : in  std_logic_vector(1 downto 0);
            gctr_key_word_val_i         : in  std_logic_vector(3 downto 0);
            gctr_key_word_i             : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
            gctr_iv_val_i               : in  std_logic;
            gctr_iv_i                   : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
            gctr_icb_start_cnt_i        : in  std_logic;
            gctr_icb_stop_cnt_i         : in  std_logic;
            gctr_pipe_reset_i           : in  std_logic;
            gctr_data_in_bval_i         : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            gctr_data_in_i              : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            ghash_h_loaded_i            : in  std_logic;
            ghash_j0_loaded_i           : in  std_logic;
            aes_ecb_val_o               : out std_logic;
            aes_ecb_data_o              : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            gctr_ready_o                : out std_logic;
            gctr_data_out_val_o         : out std_logic;
            gctr_data_out_bval_o        : out std_logic_vector(NB_STAGE_C-1 downto 0);
            gctr_data_out_o             : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            gctr_icb_cnt_overflow_o     : out std_logic);
    end component;

    component gcm_ghash is
        port(
            rst_i                       : in  std_logic;
            clk_i                       : in  std_logic;
            ghash_pkt_val_i             : in  std_logic;
            ghash_new_icb_i             : in  std_logic;
            aes_ecb_val_i               : in  std_logic;
            aes_ecb_data_i              : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            ghash_aad_val_i             : in  std_logic;
            ghash_aad_bval_i            : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            ghash_aad_i                 : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            ghash_ct_val_i              : in  std_logic;
            ghash_ct_bval_i             : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            ghash_ct_i                  : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            ghash_h_loaded_o            : out std_logic;
            ghash_j0_loaded_o           : out std_logic;
            ghash_tag_val_o             : out std_logic;
            ghash_tag_o                 : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0));
    end component;

    component aes_enc_dec_ctrl is
        port(
            rst_i                       : in  std_logic;
            clk_i                       : in  std_logic;
            aes_gcm_enc_dec_i           : in  std_logic;
            ghash_pkt_val_i             : in  std_logic;
            ghash_aad_bval_i            : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            ghash_ct_bval_i             : in  std_logic_vector(NB_STAGE_C-1 downto 0);
            ghash_aad_val_o             : out std_logic;
            ghash_ct_val_o              : out std_logic);
    end component;

begin

    --------------------------------------------------------------------------------
    --! Component instantiation
    --------------------------------------------------------------------------------
    u_gcm_gctr: gcm_gctr
        generic map(
            gctr_mode_g                 => aes_gcm_mode_g,
            gctr_n_rounds_g             => aes_gcm_n_rounds_g
        )
        port map(
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            gctr_mode_i                 => aes_gcm_mode_i,
            gctr_key_word_val_i         => aes_gcm_key_word_val_i,
            gctr_key_word_i             => aes_gcm_key_word_i,
            gctr_iv_val_i               => aes_gcm_iv_val_i,
            gctr_iv_i                   => aes_gcm_iv_i,
            gctr_icb_start_cnt_i        => aes_gcm_icb_start_cnt_i,
            gctr_icb_stop_cnt_i         => aes_gcm_icb_stop_cnt_i,
            gctr_pipe_reset_i           => aes_gcm_pipe_reset_i,
            gctr_data_in_bval_i         => aes_gcm_data_in_bval_i,
            gctr_data_in_i              => aes_gcm_data_in_i,
            ghash_h_loaded_i            => ghash_h_loaded,
            ghash_j0_loaded_i           => ghash_j0_loaded,
            aes_ecb_val_o               => aes_ecb_val,
            aes_ecb_data_o              => aes_ecb_data,
            gctr_ready_o                => aes_gcm_ready,
            gctr_data_out_val_o         => aes_gcm_data_out_val_o,
            gctr_data_out_bval_o        => gctr_data_out_bval,
            gctr_data_out_o             => gctr_data_out,
            gctr_icb_cnt_overflow_o     => aes_gcm_icb_cnt_overflow_o
        );

    u_gcm_ghash: gcm_ghash
        port map(
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            ghash_pkt_val_i             => aes_gcm_ghash_pkt_val_i,
            ghash_new_icb_i             => aes_gcm_iv_val_i,
            aes_ecb_val_i               => aes_ecb_val,
            aes_ecb_data_i              => aes_ecb_data,
            ghash_aad_val_i             => ghash_aad_val,
            ghash_aad_bval_i            => aes_gcm_ghash_aad_bval_i,
            ghash_aad_i                 => aes_gcm_ghash_aad_i,
            ghash_ct_val_i              => ghash_ct_val,
            ghash_ct_bval_i             => ghash_data_in_bval,
            ghash_ct_i                  => ghash_data_in,
            ghash_h_loaded_o            => ghash_h_loaded,
            ghash_j0_loaded_o           => ghash_j0_loaded,
            ghash_tag_val_o             => aes_gcm_ghash_tag_val_o,
            ghash_tag_o                 => aes_gcm_ghash_tag_o
        );

    u_aes_enc_dec_ctrl: aes_enc_dec_ctrl
        port map(
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            aes_gcm_enc_dec_i           => aes_gcm_enc_dec_i,
            ghash_pkt_val_i             => aes_gcm_ghash_pkt_val_i,
            ghash_aad_bval_i            => aes_gcm_ghash_aad_bval_i,
            ghash_ct_bval_i             => aes_gcm_data_in_bval_i,
            ghash_aad_val_o             => ghash_aad_val,
            ghash_ct_val_o              => ghash_ct_val
        );


    ghash_data_in_bval <= gctr_data_out_bval     when (aes_gcm_enc_dec_i = '0') else
                          aes_gcm_data_in_bval_i when (aes_gcm_ready = '1')     else
                          (others => '0');

    ghash_data_in      <= gctr_data_out when (aes_gcm_enc_dec_i = '0') else aes_gcm_data_in_i;


    --------------------------------------------------------------------------------
    aes_gcm_ready_o         <= aes_gcm_ready;
    aes_gcm_data_out_bval_o <= gctr_data_out_bval;
    aes_gcm_data_out_o      <= gctr_data_out;

end architecture;
