--------------------------------------------------------------------------------
--! @File name:     ghash_gfmul
--! @Date:          29/04/2019
--! @Description:   The module performs the GF multiplication
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.xor_reduce;
use work.gcm_pkg.all;

--------------------------------------------------------------------------------
entity ghash_gfmul is
    port(
        gf_mult_h_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        gf_mult_x_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        gf_mult_y_o         : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0));
end entity;

--------------------------------------------------------------------------------
architecture arch_ghash_gfmul of ghash_gfmul is

    --! Constants

    --! Types
    type gf_array_t is array ((GCM_DATA_WIDTH_C-1) downto 0) of std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

    --! Signals
    signal gf_z : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

begin

    --------------------------------------------------------------------------------
    --! GF Multiplications
    --------------------------------------------------------------------------------
    gf_mult_p   : process(gf_mult_x_i, gf_mult_h_i)
        variable tmp_v : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        variable vec_v : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        variable acc_v : gf_array_t;
    begin
        tmp_v := gf_mult_h_i;

        for i in GCM_DATA_WIDTH_C-1 downto 0 loop
            --! Save tmp_v vertically in the array
            for j in GCM_DATA_WIDTH_C-1 downto 0 loop
                acc_v(j)(i) := gf_mult_x_i(i) and tmp_v(j);
            end loop;

            vec_v := tmp_v;
            --! (V_i >> 1) xor R = ('11100001 || 0^120')
            tmp_v(127)              := vec_v(0);
            tmp_v(126)              := vec_v(127) xor vec_v(0);
            tmp_v(125)              := vec_v(126) xor vec_v(0);
            tmp_v(124 downto 121)   := vec_v(125 downto 122);
            tmp_v(120)              := vec_v(121) xor vec_v(0);
            tmp_v(119 downto 0)     := vec_v(120 downto 1);
        end loop;

        --! Z_i xor V_i
        for i in 0 to GCM_DATA_WIDTH_C-1 loop
            gf_z(i) <= xor_reduce(acc_v(i));
        end loop;
    end process;

    ---------------------------------------------------------------
    gf_mult_y_o <= gf_z;

end architecture;
