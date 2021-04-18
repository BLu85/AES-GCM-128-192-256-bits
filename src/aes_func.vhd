--------------------------------------------------------------------------------
--! @File name:     aes_func
--! @Date:          04/03/2016
--! @Description:   the package contains AES and data conversion functions
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
---------------------------------------------------------------------------------
library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;

--------------------------------------------------------------------------------
--! List of function contained in this package:
--!     + word_to_vec
--!     + vec_to_word
--!     + vec_to_state
--!     + state_to_vec
--!     + sub_byte
--!     + add_round_key
--!     + rot_word
--!     + shift_row
--!     + mix_columns
--!     + w_xor
--!     + xtime2
--!     + sub_word
--!     + xtime3
--!     + sbox

--------------------------------------------------------------------------------
package aes_func is

    --! Constants

    --! Functions prototypes
    function word_to_vec(w_in : word_t) return std_logic_vector;
    function vec_to_word(v_in : std_logic_vector(31 downto 0)) return word_t;
    function vec_to_state(v_in : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0)) return state_t;
    function state_to_vec(s_in : state_t) return std_logic_vector;
    function sub_byte(state_in : state_t) return state_t;
    function add_round_key(data_in, key : state_t) return state_t;
    function rot_word(data_in : word_t) return word_t;
    function shift_row(state_in : state_t) return state_t;
    function mix_columns(state_in : state_t) return state_t;
    function w_xor(w_a_in, w_b_in : word_t) return word_t;
    function xtime2(data_in : byte_t) return byte_t;
    function sub_word(data_in : word_t) return word_t;
    function xtime3(data_in : byte_t) return byte_t;
    function sbox(data_in : byte_t) return byte_t;

end package aes_func;

--------------------------------------------------------------------------------
package body aes_func is

    --------------------------------------------------------------------------------
    --! Function: convert word to vector
    --------------------------------------------------------------------------------
    function word_to_vec(w_in : word_t) return std_logic_vector is
        variable tmp_v : std_logic_vector(31 downto 0);
    begin
        tmp_v(31 downto 24) := w_in(0);
        tmp_v(23 downto 16) := w_in(1);
        tmp_v(15 downto 8)  := w_in(2);
        tmp_v(7  downto 0)  := w_in(3);
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: convert vector to word
    --------------------------------------------------------------------------------
    function vec_to_word(v_in : std_logic_vector(31 downto 0)) return word_t is
        variable tmp_v : word_t;
    begin
        tmp_v(0) := v_in(31 downto 24);
        tmp_v(1) := v_in(23 downto 16);
        tmp_v(2) := v_in(15 downto 8);
        tmp_v(3) := v_in(7  downto 0);
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: convert vector to state
    --------------------------------------------------------------------------------
    function vec_to_state(v_in : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0)) return state_t is
        variable tmp_v : state_t;
    begin
        tmp_v(0) := vec_to_word(v_in((WORD_WIDTH_C * 4) - 1 downto WORD_WIDTH_C * 3));
        tmp_v(1) := vec_to_word(v_in((WORD_WIDTH_C * 3) - 1 downto WORD_WIDTH_C * 2));
        tmp_v(2) := vec_to_word(v_in((WORD_WIDTH_C * 2) - 1 downto WORD_WIDTH_C * 1));
        tmp_v(3) := vec_to_word(v_in((WORD_WIDTH_C * 1) - 1 downto WORD_WIDTH_C * 0));
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: convert state to vector
    --------------------------------------------------------------------------------
    function state_to_vec(s_in : state_t) return std_logic_vector is
        variable tmp_v  : std_logic_vector(AES_DATA_WIDTH_C-1 downto 0);
    begin
        tmp_v := (word_to_vec(s_in(0)) & word_to_vec(s_in(1)) & word_to_vec(s_in(2)) & word_to_vec(s_in(3)));
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: SubByte()
    --------------------------------------------------------------------------------
    function sub_byte(state_in : state_t) return state_t is
        variable tmp_v : state_t;
    begin
        for i in 0 to (NB_C-1) loop
            for j in 0 to (NB_C-1) loop
                tmp_v(i)(j) := sbox(state_in(i)(j));
            end loop;
        end loop;
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: AddRoundKey()
    --------------------------------------------------------------------------------
    function add_round_key(data_in, key : state_t) return state_t is
        variable tmp_v : state_t;
    begin
         for i in 0 to (NB_C-1) loop
            for j in 0 to (NB_C-1) loop
                tmp_v(i)(j) := data_in(i)(j) xor key(i)(j);
            end loop;
        end loop;
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: RotWord()
    --------------------------------------------------------------------------------
    function rot_word(data_in : word_t) return word_t is
        variable tmp_v : word_t;
    begin
        tmp_v := (data_in(1), data_in(2), data_in(3), data_in(0));
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: ShiftRow()
    --------------------------------------------------------------------------------
    function shift_row(state_in : state_t) return state_t is
        variable tmp_v : state_t;
    begin
        tmp_v(0) := (state_in(0)(0), state_in(1)(1), state_in(2)(2), state_in(3)(3));
        tmp_v(1) := (state_in(1)(0), state_in(2)(1), state_in(3)(2), state_in(0)(3));
        tmp_v(2) := (state_in(2)(0), state_in(3)(1), state_in(0)(2), state_in(1)(3));
        tmp_v(3) := (state_in(3)(0), state_in(0)(1), state_in(1)(2), state_in(2)(3));
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: MixColumns()
    --------------------------------------------------------------------------------
    function mix_columns(state_in : state_t) return state_t is
        variable tmp_v : state_t;
    begin
        for i in 0 to (NB_C-1) loop
            tmp_v(i)(0) :=  xtime2(state_in(i)(0)) xor xtime3(state_in(i)(1)) xor state_in(       i)(2)  xor state_in(       i)(3);
            tmp_v(i)(1) :=  state_in(       i)(0)  xor xtime2(state_in(i)(1)) xor xtime3(state_in(i)(2)) xor state_in(       i)(3);
            tmp_v(i)(2) :=  state_in(       i)(0)  xor state_in(       i)(1)  xor xtime2(state_in(i)(2)) xor xtime3(state_in(i)(3));
            tmp_v(i)(3) :=  xtime3(state_in(i)(0)) xor state_in(       i)(1)  xor state_in(       i)(2)  xor xtime2(state_in(i)(3));
        end loop;
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: word xor
    --------------------------------------------------------------------------------
    function w_xor(w_a_in, w_b_in : word_t) return word_t is
        variable tmp_v : word_t;
    begin
        tmp_v(0) := w_a_in(0) xor w_b_in(0);
        tmp_v(1) := w_a_in(1) xor w_b_in(1);
        tmp_v(2) := w_a_in(2) xor w_b_in(2);
        tmp_v(3) := w_a_in(3) xor w_b_in(3);
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: xtime2(): polynomial multiplication by 2
    --------------------------------------------------------------------------------
    function xtime2(data_in : byte_t) return byte_t is
        variable tmp_v : byte_t;
    begin
        --! IRREDUCIBLE_POLY_C = x"1B"
        tmp_v(7) := data_in(6);
        tmp_v(6) := data_in(5);
        tmp_v(5) := data_in(4);
        tmp_v(4) := data_in(3) xor data_in(7);
        tmp_v(3) := data_in(2) xor data_in(7);
        tmp_v(2) := data_in(1);
        tmp_v(1) := data_in(0) xor data_in(7);
        tmp_v(0) := data_in(7);
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: xtime3(): polynomial multiplication by 3
    --------------------------------------------------------------------------------
    function xtime3(data_in : byte_t) return byte_t is
        variable tmp_v : byte_t;
    begin
        tmp_v := xtime2(data_in) xor data_in;
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: SubWord()
    --------------------------------------------------------------------------------
    function sub_word(data_in : word_t) return word_t is
        variable tmp_v: word_t;
    begin
        tmp_v(0) := sbox(data_in(0));
        tmp_v(1) := sbox(data_in(1));
        tmp_v(2) := sbox(data_in(2));
        tmp_v(3) := sbox(data_in(3));
        return tmp_v;
    end function;

    --------------------------------------------------------------------------------
    --! Function: sBox()
    --------------------------------------------------------------------------------
    function sbox(data_in : byte_t) return byte_t is
        variable tmp_v: byte_t;
    begin
        case(data_in) is
            when x"00" => tmp_v := x"63";   when x"40" => tmp_v := x"09";   when x"80" => tmp_v := x"cd";   when x"c0" => tmp_v := x"ba";
            when x"01" => tmp_v := x"7c";   when x"41" => tmp_v := x"83";   when x"81" => tmp_v := x"0c";   when x"c1" => tmp_v := x"78";
            when x"02" => tmp_v := x"77";   when x"42" => tmp_v := x"2c";   when x"82" => tmp_v := x"13";   when x"c2" => tmp_v := x"25";
            when x"03" => tmp_v := x"7b";   when x"43" => tmp_v := x"1a";   when x"83" => tmp_v := x"ec";   when x"c3" => tmp_v := x"2e";
            when x"04" => tmp_v := x"f2";   when x"44" => tmp_v := x"1b";   when x"84" => tmp_v := x"5f";   when x"c4" => tmp_v := x"1c";
            when x"05" => tmp_v := x"6b";   when x"45" => tmp_v := x"6e";   when x"85" => tmp_v := x"97";   when x"c5" => tmp_v := x"a6";
            when x"06" => tmp_v := x"6f";   when x"46" => tmp_v := x"5a";   when x"86" => tmp_v := x"44";   when x"c6" => tmp_v := x"b4";
            when x"07" => tmp_v := x"c5";   when x"47" => tmp_v := x"a0";   when x"87" => tmp_v := x"17";   when x"c7" => tmp_v := x"c6";
            when x"08" => tmp_v := x"30";   when x"48" => tmp_v := x"52";   when x"88" => tmp_v := x"c4";   when x"c8" => tmp_v := x"e8";
            when x"09" => tmp_v := x"01";   when x"49" => tmp_v := x"3b";   when x"89" => tmp_v := x"a7";   when x"c9" => tmp_v := x"dd";
            when x"0a" => tmp_v := x"67";   when x"4a" => tmp_v := x"d6";   when x"8a" => tmp_v := x"7e";   when x"ca" => tmp_v := x"74";
            when x"0b" => tmp_v := x"2b";   when x"4b" => tmp_v := x"b3";   when x"8b" => tmp_v := x"3d";   when x"cb" => tmp_v := x"1f";
            when x"0c" => tmp_v := x"fe";   when x"4c" => tmp_v := x"29";   when x"8c" => tmp_v := x"64";   when x"cc" => tmp_v := x"4b";
            when x"0d" => tmp_v := x"d7";   when x"4d" => tmp_v := x"e3";   when x"8d" => tmp_v := x"5d";   when x"cd" => tmp_v := x"bd";
            when x"0e" => tmp_v := x"ab";   when x"4e" => tmp_v := x"2f";   when x"8e" => tmp_v := x"19";   when x"ce" => tmp_v := x"8b";
            when x"0f" => tmp_v := x"76";   when x"4f" => tmp_v := x"84";   when x"8f" => tmp_v := x"73";   when x"cf" => tmp_v := x"8a";

            when x"10" => tmp_v := x"ca";   when x"50" => tmp_v := x"53";   when x"90" => tmp_v := x"60";   when x"d0" => tmp_v := x"70";
            when x"11" => tmp_v := x"82";   when x"51" => tmp_v := x"d1";   when x"91" => tmp_v := x"81";   when x"d1" => tmp_v := x"3e";
            when x"12" => tmp_v := x"c9";   when x"52" => tmp_v := x"00";   when x"92" => tmp_v := x"4f";   when x"d2" => tmp_v := x"b5";
            when x"13" => tmp_v := x"7d";   when x"53" => tmp_v := x"ed";   when x"93" => tmp_v := x"dc";   when x"d3" => tmp_v := x"66";
            when x"14" => tmp_v := x"fa";   when x"54" => tmp_v := x"20";   when x"94" => tmp_v := x"22";   when x"d4" => tmp_v := x"48";
            when x"15" => tmp_v := x"59";   when x"55" => tmp_v := x"fc";   when x"95" => tmp_v := x"2a";   when x"d5" => tmp_v := x"03";
            when x"16" => tmp_v := x"47";   when x"56" => tmp_v := x"b1";   when x"96" => tmp_v := x"90";   when x"d6" => tmp_v := x"f6";
            when x"17" => tmp_v := x"f0";   when x"57" => tmp_v := x"5b";   when x"97" => tmp_v := x"88";   when x"d7" => tmp_v := x"0e";
            when x"18" => tmp_v := x"ad";   when x"58" => tmp_v := x"6a";   when x"98" => tmp_v := x"46";   when x"d8" => tmp_v := x"61";
            when x"19" => tmp_v := x"d4";   when x"59" => tmp_v := x"cb";   when x"99" => tmp_v := x"ee";   when x"d9" => tmp_v := x"35";
            when x"1a" => tmp_v := x"a2";   when x"5a" => tmp_v := x"be";   when x"9a" => tmp_v := x"b8";   when x"da" => tmp_v := x"57";
            when x"1b" => tmp_v := x"af";   when x"5b" => tmp_v := x"39";   when x"9b" => tmp_v := x"14";   when x"db" => tmp_v := x"b9";
            when x"1c" => tmp_v := x"9c";   when x"5c" => tmp_v := x"4a";   when x"9c" => tmp_v := x"de";   when x"dc" => tmp_v := x"86";
            when x"1d" => tmp_v := x"a4";   when x"5d" => tmp_v := x"4c";   when x"9d" => tmp_v := x"5e";   when x"dd" => tmp_v := x"c1";
            when x"1e" => tmp_v := x"72";   when x"5e" => tmp_v := x"58";   when x"9e" => tmp_v := x"0b";   when x"de" => tmp_v := x"1d";
            when x"1f" => tmp_v := x"c0";   when x"5f" => tmp_v := x"cf";   when x"9f" => tmp_v := x"db";   when x"df" => tmp_v := x"9e";

            when x"20" => tmp_v := x"b7";   when x"60" => tmp_v := x"d0";   when x"a0" => tmp_v := x"e0";   when x"e0" => tmp_v := x"e1";
            when x"21" => tmp_v := x"fd";   when x"61" => tmp_v := x"ef";   when x"a1" => tmp_v := x"32";   when x"e1" => tmp_v := x"f8";
            when x"22" => tmp_v := x"93";   when x"62" => tmp_v := x"aa";   when x"a2" => tmp_v := x"3a";   when x"e2" => tmp_v := x"98";
            when x"23" => tmp_v := x"26";   when x"63" => tmp_v := x"fb";   when x"a3" => tmp_v := x"0a";   when x"e3" => tmp_v := x"11";
            when x"24" => tmp_v := x"36";   when x"64" => tmp_v := x"43";   when x"a4" => tmp_v := x"49";   when x"e4" => tmp_v := x"69";
            when x"25" => tmp_v := x"3f";   when x"65" => tmp_v := x"4d";   when x"a5" => tmp_v := x"06";   when x"e5" => tmp_v := x"d9";
            when x"26" => tmp_v := x"f7";   when x"66" => tmp_v := x"33";   when x"a6" => tmp_v := x"24";   when x"e6" => tmp_v := x"8e";
            when x"27" => tmp_v := x"cc";   when x"67" => tmp_v := x"85";   when x"a7" => tmp_v := x"5c";   when x"e7" => tmp_v := x"94";
            when x"28" => tmp_v := x"34";   when x"68" => tmp_v := x"45";   when x"a8" => tmp_v := x"c2";   when x"e8" => tmp_v := x"9b";
            when x"29" => tmp_v := x"a5";   when x"69" => tmp_v := x"f9";   when x"a9" => tmp_v := x"d3";   when x"e9" => tmp_v := x"1e";
            when x"2a" => tmp_v := x"e5";   when x"6a" => tmp_v := x"02";   when x"aa" => tmp_v := x"ac";   when x"ea" => tmp_v := x"87";
            when x"2b" => tmp_v := x"f1";   when x"6b" => tmp_v := x"7f";   when x"ab" => tmp_v := x"62";   when x"eb" => tmp_v := x"e9";
            when x"2c" => tmp_v := x"71";   when x"6c" => tmp_v := x"50";   when x"ac" => tmp_v := x"91";   when x"ec" => tmp_v := x"ce";
            when x"2d" => tmp_v := x"d8";   when x"6d" => tmp_v := x"3c";   when x"ad" => tmp_v := x"95";   when x"ed" => tmp_v := x"55";
            when x"2e" => tmp_v := x"31";   when x"6e" => tmp_v := x"9f";   when x"ae" => tmp_v := x"e4";   when x"ee" => tmp_v := x"28";
            when x"2f" => tmp_v := x"15";   when x"6f" => tmp_v := x"a8";   when x"af" => tmp_v := x"79";   when x"ef" => tmp_v := x"df";

            when x"30" => tmp_v := x"04";   when x"70" => tmp_v := x"51";   when x"b0" => tmp_v := x"e7";   when x"f0" => tmp_v := x"8c";
            when x"31" => tmp_v := x"c7";   when x"71" => tmp_v := x"a3";   when x"b1" => tmp_v := x"c8";   when x"f1" => tmp_v := x"a1";
            when x"32" => tmp_v := x"23";   when x"72" => tmp_v := x"40";   when x"b2" => tmp_v := x"37";   when x"f2" => tmp_v := x"89";
            when x"33" => tmp_v := x"c3";   when x"73" => tmp_v := x"8f";   when x"b3" => tmp_v := x"6d";   when x"f3" => tmp_v := x"0d";
            when x"34" => tmp_v := x"18";   when x"74" => tmp_v := x"92";   when x"b4" => tmp_v := x"8d";   when x"f4" => tmp_v := x"bf";
            when x"35" => tmp_v := x"96";   when x"75" => tmp_v := x"9d";   when x"b5" => tmp_v := x"d5";   when x"f5" => tmp_v := x"e6";
            when x"36" => tmp_v := x"05";   when x"76" => tmp_v := x"38";   when x"b6" => tmp_v := x"4e";   when x"f6" => tmp_v := x"42";
            when x"37" => tmp_v := x"9a";   when x"77" => tmp_v := x"f5";   when x"b7" => tmp_v := x"a9";   when x"f7" => tmp_v := x"68";
            when x"38" => tmp_v := x"07";   when x"78" => tmp_v := x"bc";   when x"b8" => tmp_v := x"6c";   when x"f8" => tmp_v := x"41";
            when x"39" => tmp_v := x"12";   when x"79" => tmp_v := x"b6";   when x"b9" => tmp_v := x"56";   when x"f9" => tmp_v := x"99";
            when x"3a" => tmp_v := x"80";   when x"7a" => tmp_v := x"da";   when x"ba" => tmp_v := x"f4";   when x"fa" => tmp_v := x"2d";
            when x"3b" => tmp_v := x"e2";   when x"7b" => tmp_v := x"21";   when x"bb" => tmp_v := x"ea";   when x"fb" => tmp_v := x"0f";
            when x"3c" => tmp_v := x"eb";   when x"7c" => tmp_v := x"10";   when x"bc" => tmp_v := x"65";   when x"fc" => tmp_v := x"b0";
            when x"3d" => tmp_v := x"27";   when x"7d" => tmp_v := x"ff";   when x"bd" => tmp_v := x"7a";   when x"fd" => tmp_v := x"54";
            when x"3e" => tmp_v := x"b2";   when x"7e" => tmp_v := x"f3";   when x"be" => tmp_v := x"ae";   when x"fe" => tmp_v := x"bb";
            when x"3f" => tmp_v := x"75";   when x"7f" => tmp_v := x"d2";   when x"bf" => tmp_v := x"08";   when others => tmp_v := x"16"; --! x"ff"
        end case;
        return tmp_v;
    end function;

end package body;
