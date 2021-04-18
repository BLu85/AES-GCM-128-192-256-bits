#!/usr/bin/env python3

import sys

N_RND_128 = 11
N_RND_192 = 13
N_RND_256 = 15

def generate_aes_kexp_logic(key_n_bits = 128, n_rounds = 1, filepath='./'):
    filename = filepath + 'aes_kexp.vhd'

    #                               kexp_var_en(0) valid rounds                         kexp_var_en(1) valid rounds                         kexp_var_en(2) valid rounds
    round_variation =   {   '128' : [[],                                                [],                                                 []                                              ],
                            '192' : [[i for i in range(1, N_RND_192) if i % 3 == 1],    [i for i in range(1, N_RND_192) if i % 3 == 2],     []                                              ],
                            '256' : [[],                                                [],                                                 [i for i in range(1, N_RND_256) if i % 2 == 0]  ]
                        }

    file_lines = []
    file_lines.append(
    '''--------------------------------------------------------------------------------
--! @File name:     aes_kexp
--! @Date:          12/02/2016
--! @Description:   the module performs the key expansion
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;
use work.aes_func.all;

--------------------------------------------------------------------------------
entity aes_kexp is
    generic(
        core_num_g              : natural := 0);
    port(
        rst_i                   : in  std_logic;
        clk_i                   : in  std_logic;
        aes_mode_i              : in  std_logic_vector(1 downto 0);
        kexp_cnt_i              : in  round_cnt_t;
        kexp_dval_i             : in  std_logic;
        kexp_rcon_i             : in  byte_t;
        kexp_key_part_i         : in  key_vec_t;
        kexp_rcon_o             : out byte_t;
        kexp_key_next_part_o    : out key_vec_t;
        kexp_key_next_stage_o   : out state_t;
        kexp_key_last_stage_o   : out state_t);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_kexp of aes_kexp is

    --! Constants
    constant RST_WORD_C          : word_t := (x"00", x"00", x"00", x"00");

    --! Types

    --! Signals

    signal w_in_0_c              : word_t;
    signal w_in_1_c              : word_t;
    signal w_in_2_c              : word_t;
    signal w_in_3_c              : word_t;
    signal w_in_4_c              : word_t;
    signal w_in_5_c              : word_t;
    signal w_in_6_c              : word_t;
    signal w_in_7_c              : word_t;

    signal w_0_s                 : word_t;
    signal w_1_s                 : word_t;
    signal w_2_s                 : word_t;
    signal w_3_s                 : word_t;
    signal w_4_s                 : word_t;
    signal w_5_s                 : word_t;
    signal w_6_s                 : word_t;
    signal w_7_s                 : word_t;

    signal tmp_0_c               : word_t;
    signal tmp_1_c               : word_t;
    signal tmp_2_c               : word_t;
    signal tmp_3_c               : word_t;

    signal opa_0_c               : word_t;
    signal opa_1_c               : word_t;
    signal opa_2_c               : word_t;
    signal opa_3_c               : word_t;

    signal opb_0_c               : word_t;
    signal opb_1_c               : word_t;
    signal opb_2_c               : word_t;
    signal opb_3_c               : word_t;

    signal rcon_next_c           : byte_t;
    signal rcon_byte_c           : byte_t;
    signal kexp_rcon_s           : byte_t;
    signal rcon_c                : word_t;

    signal tmp_c                 : word_t;
    signal rotw_c                : word_t;
    signal subw_c                : word_t;
    signal elabw_c               : word_t;

    signal skip_192_c            : std_logic;
    signal skip_256_c            : std_logic;

    signal kexp_key_next_part_c  : key_vec_t;
    signal kexp_key_next_stage_c : state_t;
    signal kexp_key_last_stage_c : state_t;

    signal kexp_var_en           : std_logic_vector(2 downto 0);

begin

    w_in_7_c    <= kexp_key_part_i(7);
    w_in_6_c    <= kexp_key_part_i(6);
    w_in_5_c    <= kexp_key_part_i(5);
    w_in_4_c    <= kexp_key_part_i(4);
    w_in_3_c    <= kexp_key_part_i(3);
    w_in_2_c    <= kexp_key_part_i(2);
    w_in_1_c    <= kexp_key_part_i(1);
    w_in_0_c    <= kexp_key_part_i(0);

    opb_0_c     <= w_in_7_c;
    opb_1_c     <= w_in_6_c;
    opb_2_c     <= w_in_5_c;
    opb_3_c     <= w_in_4_c;

    --! Word to be expanded
    tmp_c       <=  w_in_4_c    when ( aes_mode_i = AES_MODE_128_C) else
                    w_in_0_c    when ( aes_mode_i = AES_MODE_256_C) else
                    w_in_2_c    when ((aes_mode_i = AES_MODE_192_C) and (kexp_var_en(0) = '1')) else
                    w_xor(w_xor(w_in_6_c, w_in_7_c), w_in_2_c);

    opa_0_c     <=  w_in_2_c    when ((aes_mode_i = AES_MODE_192_C) and (kexp_var_en(0) = '0')) else elabw_c;

    opa_2_c     <=  elabw_c     when ((aes_mode_i = AES_MODE_192_C) and (kexp_var_en(1) = '1')) else tmp_1_c;

    opa_1_c     <=  tmp_0_c;
    opa_3_c     <=  tmp_2_c;


    --! Shift, Rotate, Substitute and xor operations
    skip_192_c  <=  '1' when ((aes_mode_i = AES_MODE_192_C) and (kexp_var_en(1 downto 0) = "00"))   else '0';
    skip_256_c  <=  '1' when ((aes_mode_i = AES_MODE_256_C) and (kexp_var_en(2) = '1')) else '0';

    --! introduce skip_192 and skip_256

    rcon_byte_c <=  kexp_rcon_i when (skip_256_c = '0') else x"00";
    rcon_c      <=  (rcon_byte_c, x"00", x"00", x"00");

    rcon_next_c <=  kexp_rcon_i             when (skip_256_c = '1' or skip_192_c = '1') else    xtime2(kexp_rcon_i);
    rotw_c      <=  tmp_c                   when (skip_256_c = '1')                     else    rot_word(tmp_c);
    subw_c      <=  sub_word(rotw_c);
    elabw_c     <=  w_xor(rcon_c, subw_c);

    --! Execute Xor between expanded and incoming key
    tmp_0_c     <= w_xor(opa_0_c, opb_0_c);
    tmp_1_c     <= w_xor(opa_1_c, opb_1_c);
    tmp_2_c     <= w_xor(opa_2_c, opb_2_c);
    tmp_3_c     <= w_xor(opa_3_c, opb_3_c);

    --------------------------------------------------------------------------------
    --! process: Sample new rcon
    --------------------------------------------------------------------------------
    new_rcon_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            kexp_rcon_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(kexp_dval_i = '1') then
                kexp_rcon_s <= rcon_next_c;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! process: Sample key
    --------------------------------------------------------------------------------
    sample_key_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            w_0_s   <= RST_WORD_C;
            w_1_s   <= RST_WORD_C;
            w_2_s   <= RST_WORD_C;
            w_3_s   <= RST_WORD_C;
            w_4_s   <= RST_WORD_C;
            w_5_s   <= RST_WORD_C;
            w_6_s   <= RST_WORD_C;
            w_7_s   <= RST_WORD_C;
        elsif(rising_edge(clk_i)) then
            if(kexp_dval_i = '1') then
                if(aes_mode_i = AES_MODE_128_C) then
                    w_7_s <= tmp_0_c;
                    w_6_s <= tmp_1_c;
                    w_5_s <= tmp_2_c;
                    w_4_s <= tmp_3_c;
                elsif(aes_mode_i = AES_MODE_192_C) then
                    w_7_s <= w_in_3_c;
                    w_6_s <= w_in_2_c;
                    w_5_s <= tmp_0_c;
                    w_4_s <= tmp_1_c;
                    w_3_s <= tmp_2_c;
                    w_2_s <= tmp_3_c;
                else
                    w_7_s <= w_in_3_c;
                    w_6_s <= w_in_2_c;
                    w_5_s <= w_in_1_c;
                    w_4_s <= w_in_0_c;
                    w_3_s <= tmp_0_c;
                    w_2_s <= tmp_1_c;
                    w_1_s <= tmp_2_c;
                    w_0_s <= tmp_3_c;
                end if;
            end if;
        end if;
    end process;

    kexp_key_next_part_c    <= (w_7_s, w_6_s, w_5_s, w_4_s, w_3_s, w_2_s, w_1_s, w_0_s);
    kexp_key_next_stage_c   <= (kexp_key_part_i(7), kexp_key_part_i(6), kexp_key_part_i(5), kexp_key_part_i(4));
    kexp_key_last_stage_c   <= (w_7_s, w_6_s, w_5_s, w_4_s);

    ''')

    if key_n_bits == '128':
        r = N_RND_128
    elif key_n_bits == '192':
        r = N_RND_192
    else:
        r = N_RND_256

    r = r - 1

    # Create an empty array for each round core
    a = [[] for i in range(n_rounds)]

    # Add to the list the round number each round core will receive
    for i in range(r):
        a[i % n_rounds].append(i+1)

    if key_n_bits == 'ALL':
        for key in ['128', '192', '256']:
            list0 = list(round_variation[key][0])
            list1 = list(round_variation[key][1])
            list2 = list(round_variation[key][2])
    else:
        list0 = list(round_variation[key_n_bits][0])
        list1 = list(round_variation[key_n_bits][1])
        list2 = list(round_variation[key_n_bits][2])

    for i in range(n_rounds):
        var0 = list(set(a[i]).intersection(list0))
        var1 = list(set(a[i]).intersection(list1))
        var2 = list(set(a[i]).intersection(list2))

        file_lines.append('\tgen_key_var_' + str(i) + ': if core_num_g = ' + str(i) + ' generate')
        file_lines.append('\t\tprocess(kexp_cnt_i)')
        file_lines.append('\t\tbegin')
        file_lines.append('\t\t\tkexp_var_en <= \"000\";')
        if len(var0) != 0:
            tmp = list(set(var0))
            file_lines.append('\t\t\tcase kexp_cnt_i is')
            file_lines.append('\t\t\t\twhen ' + ' | '.join(str(n) for n in sorted(tmp)) + ' => kexp_var_en(0) <= \'1\';')
            file_lines.append('\t\t\t\twhen others => kexp_var_en(0) <= \'0\';')
            file_lines.append('\t\t\tend case;')

        if len(var1) != 0 and (key_n_bits == '192' or key_n_bits == 'ALL'):
            tmp = list(set(var1))
            file_lines.append('\t\t\tcase kexp_cnt_i is')
            file_lines.append('\t\t\t\twhen ' + ' | '.join(str(n) for n in sorted(tmp)) + ' => kexp_var_en(1) <= \'1\';')
            file_lines.append('\t\t\t\twhen others => kexp_var_en(1) <= \'0\';')
            file_lines.append('\t\t\tend case;')
        if len(var2) != 0 and (key_n_bits == '256' or key_n_bits == 'ALL'):
            tmp = list(set(var2))
            file_lines.append('\t\t\tcase kexp_cnt_i is')
            file_lines.append('\t\t\t\twhen ' + ' | '.join(str(n) for n in sorted(tmp)) + ' => kexp_var_en(2) <= \'1\';')
            file_lines.append('\t\t\t\twhen others => kexp_var_en(2) <= \'0\';')
            file_lines.append('\t\t\tend case;')
        file_lines.append('\t\tend process;')
        file_lines.append('\tend generate;\n')

    file_lines.append(
    '''
    --! Outpus
    kexp_key_next_stage_o   <= kexp_key_next_stage_c;
    kexp_key_last_stage_o   <= kexp_key_last_stage_c;
    kexp_rcon_o             <= kexp_rcon_s;
    kexp_key_next_part_o    <= kexp_key_next_part_c;

end architecture;
''')

    try:
        with open(filename, 'w') as fp:
            fp = open(filename, 'w')
            fp.write("\n".join(file_lines).expandtabs(4))
            fp.close()
            print(' >>\tOK   : File ' + filename + ' has been successfully generated')
    except:
        print(' >>\tError: File ' + filename + ' could not be generated')
        sys.exit()
