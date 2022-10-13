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
    signal stage_val_q          : std_logic;
    signal stage_val_d          : std_logic;
    signal stage_data_q         : state_t;
    signal stage_data_d         : state_t;
    signal stage_stall_c        : std_logic;
    signal last_rnd_busy        : std_logic;
    signal stage_val_en         : std_logic;

begin

    --------------------------------------------------------------------------------
    --! Sample data valid
    --------------------------------------------------------------------------------
    sample_dval_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            stage_val_q  <= '0';
        elsif(rising_edge(clk_i)) then
            stage_val_q <= stage_val_d;
        end if;
    end process;

    last_rnd_busy <= stage_val_q and not(last_rnd_ack_i);
    stage_val_d   <= not(last_rnd_reset_i) and ((stage_val_q and last_rnd_busy) or (last_rnd_val_i and not(last_rnd_busy)));

    --------------------------------------------------------------------------------
    --! Sample data
    --------------------------------------------------------------------------------
    sample_data_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            stage_data_q <= (others => (others => (others => '0')));
        elsif(rising_edge(clk_i)) then
            if(stage_val_en = '1') then
                stage_data_q <= stage_data_d;
            end if;
        end if;
    end process;

    stage_val_en <= not(last_rnd_busy) and last_rnd_val_i;
    stage_data_d <= add_round_key(last_rnd_data_i, kexp_last_stage_i);

    --------------------------------------------------------------------------------
    --! Data have completed all the rounds
    last_rnd_val_o  <= stage_val_q;

    --! Last round data
    last_rnd_data_o <= stage_data_q;

    --! Last round is busy
    last_rnd_busy_o <= last_rnd_busy;

end architecture;
