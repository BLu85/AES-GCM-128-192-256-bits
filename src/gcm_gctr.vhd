--------------------------------------------------------------------------------
--! @File name:     gcm_gctr
--! @Date:          21/02/2019
--! @Description:   the module contains the GCM-GCTR
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.or_reduce;
use work.aes_pkg.all;
use work.gcm_pkg.all;

--------------------------------------------------------------------------------
entity gcm_gctr is
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
        gctr_plain_text_bval_i      : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        gctr_plain_text_i           : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        ghash_h_loaded_i            : in  std_logic;
        ghash_j0_loaded_i           : in  std_logic;
        aes_ecb_val_o               : out std_logic;
        aes_ecb_data_o              : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        gctr_cipher_ready_o         : out std_logic;
        gctr_cipher_text_val_o      : out std_logic;
        gctr_cipher_text_bval_o     : out std_logic_vector(NB_STAGE_C-1 downto 0);
        gctr_cipher_text_o          : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        gctr_icb_cnt_overflow_o     : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_gcm_gctr of gcm_gctr is

    --! Constants

    --! Types

    --! Signals
    signal icb_val_c                : std_logic;
    signal icb_iv_c                 : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_plain_text_val_c    : std_logic;
    signal gctr_plain_text_c        : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal aes_ecb_busy_c           : std_logic;
    signal aes_ecb_val_c            : std_logic;
    signal aes_ecb_data_c           : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_data_mask_c         : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_cipher_text_val_c   : std_logic;
    signal gctr_cipher_text_val_s   : std_logic;
    signal gctr_cipher_text_bval_c  : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal gctr_cipher_text_bval_s  : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal gctr_cipher_text_c       : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_cipher_text_s       : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_mode_c              : std_logic_vector(1 downto 0);
    signal gctr_ack_c               : std_logic;
    signal gctr_cipher_ready_c      : std_logic;

    --------------------------------------------------------------------------------
    --! Component declaration
    --------------------------------------------------------------------------------
    component aes_ecb is
        generic(
            aes_n_rounds_g              : natural range 0 to NR_256_C   := NR_128_C
        );
        port(
            rst_i                       : in  std_logic;
            clk_i                       : in  std_logic;
            aes_mode_i                  : in  std_logic_vector(1 downto 0);
            aes_key_word_val_i          : in  std_logic_vector(3 downto 0);
            aes_key_word_i              : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
            aes_pipe_reset_i            : in  std_logic;
            aes_plain_text_val_i        : in  std_logic;
            aes_plain_text_i            : in  std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            aes_cipher_text_ack_i       : in  std_logic;
            aes_cipher_text_val_o       : out std_logic;
            aes_cipher_text_o           : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            aes_ecb_busy_o              : out std_logic);
    end component;

    component aes_icb is
        port(
            rst_i                       : in  std_logic;
            clk_i                       : in  std_logic;
            icb_start_cnt_i             : in  std_logic;
            icb_stop_cnt_i              : in  std_logic;
            icb_iv_val_i                : in  std_logic;
            icb_iv_i                    : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
            aes_ecb_busy_i              : in  std_logic;
            icb_val_o                   : out std_logic;
            icb_iv_o                    : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
            icb_cnt_overflow_o          : out std_logic);
    end component;

begin

    gctr_mode_c <= gctr_mode_i when (gctr_mode_g = AES_MODE_ALL_C) else
                   gctr_mode_g;

    --------------------------------------------------------------------------------
    --! Component instantiation
    --------------------------------------------------------------------------------
    u_aes_icb : aes_icb
        port map(
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            icb_start_cnt_i             => gctr_icb_start_cnt_i,
            icb_stop_cnt_i              => gctr_icb_stop_cnt_i,
            icb_iv_val_i                => gctr_iv_val_i,
            icb_iv_i                    => gctr_iv_i,
            aes_ecb_busy_i              => aes_ecb_busy_c,
            icb_val_o                   => icb_val_c,
            icb_iv_o                    => icb_iv_c,
            icb_cnt_overflow_o          => gctr_icb_cnt_overflow_o);

    u_aes_ecb : aes_ecb
        generic map (
            aes_n_rounds_g              => gctr_n_rounds_g)
        port map (
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            aes_mode_i                  => gctr_mode_c,
            aes_key_word_val_i          => gctr_key_word_val_i,
            aes_key_word_i              => gctr_key_word_i,
            aes_pipe_reset_i            => gctr_pipe_reset_i,
            aes_plain_text_val_i        => gctr_plain_text_val_c,
            aes_plain_text_i            => gctr_plain_text_c,
            aes_cipher_text_ack_i       => gctr_ack_c,           --! Acknoledge the ECB block that a data has been read
            aes_cipher_text_val_o       => aes_ecb_val_c,
            aes_cipher_text_o           => aes_ecb_data_c,
            aes_ecb_busy_o              => aes_ecb_busy_c);

    gctr_plain_text_val_c   <= gctr_icb_start_cnt_i or icb_val_c;
    gctr_plain_text_c       <= ZERO_128_C when (gctr_icb_start_cnt_i = '1') else icb_iv_c;     --! Create H0 when starting the counter
    gctr_ack_c              <= not(ghash_h_loaded_i and ghash_j0_loaded_i) or or_reduce(gctr_plain_text_bval_i);

    --! PT can be xor-ed after H0 and J0 have been calculated
    gctr_cipher_ready_c     <= aes_ecb_val_c and ghash_h_loaded_i and ghash_j0_loaded_i;
    gctr_cipher_text_val_c  <= gctr_cipher_ready_c and or_reduce(gctr_plain_text_bval_i);

    --------------------------------------------------------------------------------
    --! Expand one bval bit to one byte
    --------------------------------------------------------------------------------
    cipher_mask_p : process(gctr_plain_text_bval_i)
    begin
        for i in 0 to NB_STAGE_C-1 loop
            for j in 0 to 7 loop
                gctr_data_mask_c((i * 8) + j) <= gctr_plain_text_bval_i(i);
            end loop;
        end loop;
    end process;

    gctr_cipher_text_c <= (gctr_plain_text_i xor aes_ecb_data_c) and gctr_data_mask_c;

    --------------------------------------------------------------------------------
    --! Sample data
    --------------------------------------------------------------------------------
    cipher_text_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_cipher_text_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(gctr_cipher_text_val_c = '1') then
                gctr_cipher_text_s <= gctr_cipher_text_c;
            end if;
        end if;
    end process;

    cipher_text_val_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_cipher_text_val_s <= '0';
        elsif(rising_edge(clk_i)) then
            gctr_cipher_text_val_s <= gctr_cipher_text_val_c;
        end if;
    end process;

    cipher_text_bval_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_cipher_text_bval_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            gctr_cipher_text_bval_s <= gctr_cipher_text_bval_c;
        end if;
    end process;

    gctr_cipher_text_bval_c <= gctr_plain_text_bval_i when (gctr_cipher_text_val_c = '1') else (others => '0');

    ---------------------------------------------------------------
    aes_ecb_val_o           <= aes_ecb_val_c;
    aes_ecb_data_o          <= aes_ecb_data_c;
    gctr_cipher_ready_o     <= gctr_cipher_ready_c;
    gctr_cipher_text_val_o  <= gctr_cipher_text_val_s;
    gctr_cipher_text_bval_o <= gctr_cipher_text_bval_s;
    gctr_cipher_text_o      <= gctr_cipher_text_s;

end architecture;
