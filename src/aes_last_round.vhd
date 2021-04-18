--------------------------------------------------------------------------------
--! @File name:     gcm_gctr
--! @Date:          21/02/2019
--! @Description:   the module performs the last round of the encryption chain
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;
use work.aes_func.all;

--------------------------------------------------------------------------------
entity aes_last_round is
    port(
        rst_i                   : in  std_logic;
        clk_i                   : in  std_logic;
        kexp_last_stage_i       : in  state_t;
        last_rnd_reset_i        : in  std_logic;
        last_rnd_val_i          : in  std_logic;
        last_rnd_data_i         : in  state_t;
        last_rnd_ack_i          : in  std_logic;
        last_rnd_val_o          : out std_logic;
        last_rnd_data_o         : out state_t;
        last_rnd_busy_o         : out std_logic
    );
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_last_round of aes_last_round is

    --! Constants

    --! Types

    --! Signals
    signal stage_val_s          : std_logic;
    signal stage_data_s         : state_t;
    signal stage_data_c         : state_t;
    signal stage_stall_c        : std_logic;
    signal last_rnd_busy_c      : std_logic;
    signal stage_val_c          : std_logic;

begin

    --------------------------------------------------------------------------------
    --! Sample data valid
    --------------------------------------------------------------------------------
    sample_dval_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            stage_val_s  <= '0';
        elsif(rising_edge(clk_i)) then
            if(last_rnd_reset_i = '1') then
                stage_val_s <= '0';
            elsif(last_rnd_busy_c = '0') then
                stage_val_s <= last_rnd_val_i;
            end if;
        end if;
    end process;

    last_rnd_busy_c <= stage_val_s and not(last_rnd_ack_i);

    --------------------------------------------------------------------------------
    --! Sample data
    --------------------------------------------------------------------------------
    sample_data_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            stage_data_s <= (others => (others => (others => '0')));
        elsif(rising_edge(clk_i)) then
            if(stage_val_c = '1') then
                stage_data_s <= stage_data_c;
            end if;
        end if;
    end process;

    stage_val_c  <= not(last_rnd_busy_c) and last_rnd_val_i;
    stage_data_c <= add_round_key(last_rnd_data_i, kexp_last_stage_i);

    --------------------------------------------------------------------------------
    --! Data have completed all the rounds
    last_rnd_val_o  <= stage_val_s;

    --! Last round data
    last_rnd_data_o <= stage_data_s;

    --! Last round is busy
    last_rnd_busy_o <= last_rnd_busy_c;

end architecture;
