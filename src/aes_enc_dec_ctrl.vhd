--------------------------------------------------------------------------------
--! @File name:     aes_enc_dec_ctrl
--! @Date:          26/03/2023
--! @Description:   the module contains the control logic for to manage the
--!                 encryption or the deciption of the incoming data
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;
use ieee.std_logic_misc.or_reduce;

--------------------------------------------------------------------------------
entity aes_enc_dec_ctrl is
    port(
        rst_i                       : in  std_logic;
        clk_i                       : in  std_logic;
        aes_gcm_enc_dec_i           : in  std_logic;
        ghash_pkt_val_i             : in  std_logic;
        ghash_aad_bval_i            : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_ct_bval_i             : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_aad_val_o             : out std_logic;
        ghash_ct_val_o              : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_enc_dec_ctrl of aes_enc_dec_ctrl is

    signal ghash_aad_val           : std_logic;
    signal ghash_aad_val_q         : std_logic;
    signal ghash_ct_or             : std_logic;
    signal ghash_ct_or_val         : std_logic;
    signal ghash_ct_or_val_q       : std_logic;
    signal ghash_ct_val            : std_logic;
    signal ghash_ct_val_q          : std_logic;

begin

    --------------------------------------------------------------------------------
    --! GHASH AAD valid
    --------------------------------------------------------------------------------
    ghash_aad_dval_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            ghash_aad_val_q <= '0';
        elsif(rising_edge(clk_i)) then
            ghash_aad_val_q <= ghash_aad_val;
        end if;
    end process;

    ghash_aad_val <= ghash_pkt_val_i and (or_reduce(ghash_aad_bval_i) or
                                            (ghash_aad_val_q and not(ghash_ct_val)));


    --------------------------------------------------------------------------------
    --! GHASH CT data valid
    --------------------------------------------------------------------------------
    ghash_ct_val_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            ghash_ct_or_val_q <= '0';
        elsif(rising_edge(clk_i)) then
            ghash_ct_or_val_q <= ghash_ct_or_val;
        end if;
    end process;

    ghash_ct_or_val <= (ghash_ct_or and ghash_pkt_val_i);

    ghash_ct_val <= ghash_ct_or_val_q when (aes_gcm_enc_dec_i = '0') else
                        (ghash_pkt_val_i and (ghash_ct_or or ghash_ct_or_val_q));

    ghash_ct_or  <= or_reduce(ghash_ct_bval_i);

    --------------------------------------------------------------------------------
    ghash_ct_val_o  <= ghash_ct_val;
    ghash_aad_val_o <= ghash_aad_val;

end architecture;
