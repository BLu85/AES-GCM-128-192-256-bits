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
    signal icb_start_cnt_s      : std_logic;
    signal load_iv_c            : std_logic;
    signal cnt_val_c            : std_logic;
    signal icb_iv_val_s         : std_logic;
    signal icb_cnt_of_s         : std_logic;
    signal cnt_overflow_c       : std_logic;
    signal icb_iv_s             : std_logic_vector(GCM_ICB_WIDTH_C-1 downto 0);
    signal cnt_s                : std_logic_vector(GCM_CNT_WIDTH_C-1 downto 0);

begin

    --------------------------------------------------------------------------------
    --! Counter start/stop
    --------------------------------------------------------------------------------
    cnt_start_stop_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            icb_iv_val_s <= '0';
        elsif(rising_edge(clk_i)) then
            if(icb_stop_cnt_i = '1' or cnt_overflow_c = '1') then
                icb_iv_val_s <= '0';
            elsif(icb_start_cnt_i = '1') then
                icb_iv_val_s <= '1';
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Load IV 96-bit
    --------------------------------------------------------------------------------
    load_iv_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            icb_iv_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(load_iv_c = '1') then
                icb_iv_s <= icb_iv_i;                   --! Preload the IV base
            end if;
        end if;
    end process;

    load_iv_c <= icb_iv_val_i and not(icb_iv_val_s);    --! Valid rising edge

    --------------------------------------------------------------------------------
    --! Increment the lower 32-bit of the IV
    --------------------------------------------------------------------------------
    iv_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            cnt_s <= IV_CNT_RST_VALUE_C;
        elsif(rising_edge(clk_i)) then
            if(icb_start_cnt_i = '1') then
                cnt_s <= IV_CNT_RST_VALUE_C;
            elsif(cnt_val_c = '1') then
                cnt_s <= cnt_s + 1;
            end if;
        end if;
    end process;

    cnt_val_c <= icb_iv_val_s and not(aes_ecb_busy_i) and not(cnt_overflow_c);

    --------------------------------------------------------------------------------
    --! Counter overflow
    --------------------------------------------------------------------------------
    cnt_of_p: process(clk_i, rst_i)
    begin
        if(rst_i = '1') then
            icb_cnt_of_s <= '0';
        elsif(rising_edge(clk_i)) then
            icb_cnt_of_s <= cnt_overflow_c;
        end if;
    end process;

    cnt_overflow_c <= and_reduce(cnt_s);

    ---------------------------------------------------------------
    icb_val_o           <= icb_iv_val_s;
    icb_iv_o            <= icb_iv_s & cnt_s;
    icb_cnt_overflow_o  <= icb_cnt_of_s;

end architecture;
