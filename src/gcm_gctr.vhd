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
end entity;

--------------------------------------------------------------------------------
architecture arch_gcm_gctr of gcm_gctr is

    --! Constants

    --! Types

    --! Signals
    signal icb_val                  : std_logic;
    signal icb_iv                   : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_data_in_val         : std_logic;
    signal gctr_data_in             : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal aes_ecb_busy             : std_logic;
    signal aes_ecb_val              : std_logic;
    signal aes_ecb_data             : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_data_mask           : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_data_out_val        : std_logic;
    signal gctr_data_out_val_q      : std_logic;
    signal gctr_data_out_bval       : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal gctr_data_out_bval_q     : std_logic_vector(NB_STAGE_C-1 downto 0);
    signal gctr_data_out            : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_data_out_q          : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    signal gctr_mode                : std_logic_vector(1 downto 0);
    signal gctr_ack                 : std_logic;
    signal gctr_ready               : std_logic;

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

    gctr_mode <= gctr_mode_i when (gctr_mode_g = AES_MODE_ALL_C) else gctr_mode_g;

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
            aes_ecb_busy_i              => aes_ecb_busy,
            icb_val_o                   => icb_val,
            icb_iv_o                    => icb_iv,
            icb_cnt_overflow_o          => gctr_icb_cnt_overflow_o);

    u_aes_ecb : aes_ecb
        generic map (
            aes_n_rounds_g              => gctr_n_rounds_g)
        port map (
            rst_i                       => rst_i,
            clk_i                       => clk_i,
            aes_mode_i                  => gctr_mode,
            aes_key_word_val_i          => gctr_key_word_val_i,
            aes_key_word_i              => gctr_key_word_i,
            aes_pipe_reset_i            => gctr_pipe_reset_i,
            aes_plain_text_val_i        => gctr_data_in_val,
            aes_plain_text_i            => gctr_data_in,
            aes_cipher_text_ack_i       => gctr_ack,           --! Acknoledge the ECB block that a data has been read
            aes_cipher_text_val_o       => aes_ecb_val,
            aes_cipher_text_o           => aes_ecb_data,
            aes_ecb_busy_o              => aes_ecb_busy);

    gctr_data_in_val   <= gctr_icb_start_cnt_i or icb_val;
    gctr_data_in       <= ZERO_128_C when (gctr_icb_start_cnt_i = '1') else icb_iv;     --! Create H0 when starting the counter
    gctr_ack           <= not(ghash_h_loaded_i and ghash_j0_loaded_i) or or_reduce(gctr_data_in_bval_i);

    --! PT can be xor-ed after H0 and J0 have been calculated
    gctr_ready         <= aes_ecb_val and ghash_h_loaded_i and ghash_j0_loaded_i;
    gctr_data_out_val  <= gctr_ready and or_reduce(gctr_data_in_bval_i);

    --------------------------------------------------------------------------------
    --! Expand one bval bit to one byte
    --------------------------------------------------------------------------------
    cipher_mask_p : process(gctr_data_in_bval_i)
    begin
        for i in 0 to NB_STAGE_C-1 loop
            for j in 0 to 7 loop
                gctr_data_mask((i * 8) + j) <= gctr_data_in_bval_i(i);
            end loop;
        end loop;
    end process;

    gctr_data_out    <= (gctr_data_in_i xor aes_ecb_data) and gctr_data_mask;

    --------------------------------------------------------------------------------
    --! Sample data
    --------------------------------------------------------------------------------
    cipher_text_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_data_out_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(gctr_data_out_val = '1') then
                gctr_data_out_q <= gctr_data_out;
            end if;
        end if;
    end process;

    cipher_text_val_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_data_out_val_q <= '0';
        elsif(rising_edge(clk_i)) then
            gctr_data_out_val_q <= gctr_data_out_val;
        end if;
    end process;

    cipher_text_bval_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            gctr_data_out_bval_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            gctr_data_out_bval_q <= gctr_data_out_bval;
        end if;
    end process;

    gctr_data_out_bval <= gctr_data_in_bval_i when (gctr_data_out_val = '1') else (others => '0');

    ---------------------------------------------------------------
    aes_ecb_val_o           <= aes_ecb_val;
    aes_ecb_data_o          <= aes_ecb_data;
    gctr_ready_o            <= gctr_ready;
    gctr_data_out_val_o     <= gctr_data_out_val_q;
    gctr_data_out_bval_o    <= gctr_data_out_bval_q;
    gctr_data_out_o         <= gctr_data_out_q;

end architecture;
