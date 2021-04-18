--------------------------------------------------------------------------------
--! @File name:     aes_pkg
--! @Date:          04/03/2016
--! @Description:   the package contains the constant for the AES algorithm
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--------------------------------------------------------------------------------
--! package: aes_pkg
--------------------------------------------------------------------------------
package aes_pkg is


    --! Constants;
    constant AES_DATA_WIDTH_C       : natural   := 128;         --! AES port width

    constant AES_256_KEY_WIDTH_C    : natural   := 256;         --! AES key widths
    constant AES_128_KEY_WIDTH_C    : natural   := 128;

    constant NB_C                   : natural   := 4;           --! AES number of bytes in a word
    constant NB_STAGE_C             : natural   := 16;          --! AES number of bytes in AES stage

    constant NK_128_C               : natural   := 4;           --! AES number of words in AES keys
    constant NK_192_C               : natural   := 6;
    constant NK_256_C               : natural   := 8;

    constant NR_128_C               : natural   := 10;          --! AES number of rounds
    constant NR_192_C               : natural   := 12;
    constant NR_256_C               : natural   := 14;

    constant WORD_WIDTH_C           : natural   := 32;          --! Nummber of bits in a word

    constant ZERO_128_C             : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0) := (others => '0');

    --! Types
    subtype byte_t                  is std_logic_vector(7 downto 0);
    type    word_t                  is array (0 to NB_C-1) of byte_t;

    type    byte_arr_t              is array (natural range <>) of byte_t;

    type    state_t                 is array (0 to NB_C-1) of word_t;
    type    state_arr_t             is array (natural range <>) of state_t;

    subtype round_cnt_t             is natural range 0 to 15;
    type    round_cnt_arr_t         is array (natural range <>) of round_cnt_t;

    type    key_vec_t               is array (NK_256_C-1 downto 0) of word_t;
    type    key_vec_arr_t           is array (natural range <>) of key_vec_t;


    --! AES number of core instances
    type    aes_core_size_t         is (AES_XS_SIZE_C, AES_S_SIZE_C, AES_M_SIZE_C, AES_L_SIZE_C);


    --! AES modes
    constant AES_MODE_128_C : std_logic_vector(1 downto 0) := "00";
    constant AES_MODE_192_C : std_logic_vector(1 downto 0) := "01";
    constant AES_MODE_256_C : std_logic_vector(1 downto 0) := "10";
    constant AES_MODE_ALL_C : std_logic_vector(1 downto 0) := "11";


end;

package body aes_pkg is
end package body;
