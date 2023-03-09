--------------------------------------------------------------------------------
--! @File name:     gcm_icb
--! @Date:          01/02/2019
--! @Description:   the module contains the IV and the counter to form the ICB
--! @Reference:     NIST Special Publication 800-38D, November, 2007
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_misc.and_reduce;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.aes_pkg.all;
use work.gcm_pkg.all;

--------------------------------------------------------------------------------
entity aes_icb is
    port(
        rst_i                   : in  std_logic;
        clk_i                   : in  std_logic;
        icb_start_cnt_i         : in  std_logic;
        icb_stop_cnt_i          : in  std_logic;
        icb_iv_val_i            : in  std_logic;
        icb_iv_i                : in  std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
        aes_ecb_busy_i          : in  std_logic;
        icb_val_o               : out std_logic;
        icb_iv_o                : out std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
        icb_cnt_overflow_o      : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_icb of aes_icb is

    --! Constants
    constant IV_CNT_RST_VALUE_C : std_logic_vector(GCM_CNT_WIDTH_C-1 downto 0) := x"00000001";

    --! Types

    --! Signals
    signal iv_load_en        : std_logic;
    signal iv_cnt_val        : std_logic;
    signal iv_cnt_val_en     : std_logic;
    signal iv_val            : std_logic;
    signal iv_val_q          : std_logic;
    signal iv_cnt_of         : std_logic;
    signal iv_cnt_of_q       : std_logic;
    signal iv_q              : std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
    signal iv_cnt            : std_logic_vector(GCM_CNT_WIDTH_C-1 downto 0);
    signal iv_cnt_q          : std_logic_vector(GCM_CNT_WIDTH_C-1 downto 0);
    signal iv_cnt_inc        : std_logic_vector(GCM_CNT_WIDTH_C-1 downto 0);

begin

    --------------------------------------------------------------------------------
    --! Counter start/stop
    --------------------------------------------------------------------------------
    cnt_start_stop_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            iv_val_q <= '0';
        elsif(rising_edge(clk_i)) then
            iv_val_q <= iv_val;
        end if;
    end process;

    iv_val <= not(icb_stop_cnt_i or iv_cnt_of) and (iv_val_q or icb_start_cnt_i);

    --------------------------------------------------------------------------------
    --! Load IV 96-bit
    --------------------------------------------------------------------------------
    load_iv_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            iv_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(iv_load_en = '1') then
                iv_q <= icb_iv_i;                   --! Preload the IV base
            end if;
        end if;
    end process;

    iv_load_en <= icb_iv_val_i and not(iv_val_q);   --! Valid rising edge

    --------------------------------------------------------------------------------
    --! Increment the lower 32-bit of the IV
    --------------------------------------------------------------------------------
    iv_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            iv_cnt_q <= IV_CNT_RST_VALUE_C;
        elsif(rising_edge(clk_i)) then
            if(iv_cnt_val_en = '1') then
                iv_cnt_q <= iv_cnt;
            end if;
        end if;
    end process;

    iv_cnt_val_en <= (icb_start_cnt_i or iv_cnt_val);
    iv_cnt_val    <= iv_val_q and not(aes_ecb_busy_i) and not(iv_cnt_of);
    iv_cnt        <= IV_CNT_RST_VALUE_C when (icb_start_cnt_i = '1') else iv_cnt_inc;
    iv_cnt_inc    <= iv_cnt_q + 1;

    --------------------------------------------------------------------------------
    --! Counter overflow
    --------------------------------------------------------------------------------
    cnt_of_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            iv_cnt_of_q <= '0';
        elsif(rising_edge(clk_i)) then
            iv_cnt_of_q <= iv_cnt_of;
        end if;
    end process;

    iv_cnt_of <= and_reduce(iv_cnt_q);

    ---------------------------------------------------------------
    icb_val_o           <= iv_val_q;
    icb_iv_o            <= iv_q & iv_cnt_q;
    icb_cnt_overflow_o  <= iv_cnt_of_q;

end architecture;
