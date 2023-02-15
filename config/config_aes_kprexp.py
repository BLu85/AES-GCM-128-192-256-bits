import sys

def generate_aes_pre_exp_key(key_n_bits = '128', n_rounds = 1, filepath='./'):
    filename = filepath + 'aes_kexp.vhd'


    if key_n_bits == '128':
        n_stages = 10
    elif key_n_bits == '192':
        n_stages = 12
    else:
        n_stages = 14

    rounds = [None] * n_rounds

    for i in range (n_rounds):
        rounds[i] = [j for j in range(i, n_stages, n_rounds)]

    file_lines = []
    file_lines.append(
    '''--------------------------------------------------------------------------------
--! @File name:     aes_kexp
--! @Date:          13/01/2021
--! @Description:   the module supplies the user-loaded key portion
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.aes_pkg.all;
use work.aes_func.all;

--------------------------------------------------------------------------------
entity aes_kexp is
    generic(
        core_num_g              : natural := 0);
    port(
        rst_i                   : in  std_logic;
        clk_i                   : in  std_logic;
        kexp_key_word_val_i     : in  std_logic_vector(3 downto 0);
        kexp_key_word_i         : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
        kexp_cnt_i              : in  round_cnt_arr_t(core_num_g-1 downto 0);
        kexp_key_next_stage_o   : out state_arr_t(core_num_g-1 downto 0);
        kexp_key_last_stage_o   : out state_t);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_kexp of aes_kexp is

    --! Constants

    --! Types

    --! Signals

    signal key_idx             : natural range 0 to ''' + str(n_stages + 1) + ''';
    signal key_idx_q           : natural range 0 to ''' + str(n_stages + 1) + ''';
    signal kexp_key_word_q     : std_logic_vector(AES_128_KEY_WIDTH_C-1 downto 0);
    signal kexp_key_next_stage : state_arr_t(core_num_g downto 0);
    signal kexp_vec_q          : state_arr_t (''' + str(n_stages) + ''' downto 0);

begin


    key_idx <= to_integer(unsigned(kexp_key_word_val_i));

    --------------------------------------------------------------------------------
    --! Sample key inputs
    --------------------------------------------------------------------------------
    sample_key_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            key_idx_q       <= 0;
            kexp_key_word_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            key_idx_q       <= key_idx;
            kexp_key_word_q <= kexp_key_word_i(AES_256_KEY_WIDTH_C-1 downto AES_128_KEY_WIDTH_C);
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Get and store the key
    --------------------------------------------------------------------------------
    get_key_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            kexp_vec_q <= (others => (others => ( others => (others => '0'))));
        elsif(rising_edge(clk_i)) then
            --! Load the key words in the key vector
            if(key_idx_q /= 0) then
                kexp_vec_q(key_idx_q - 1) <= vec_to_state(kexp_key_word_q);
            end if;
        end if;
    end process;


    ''')

    for i in range(n_rounds):
        file_lines.append('\tkexp_key_next_stage(' + str(i) + ')   <= ')
        for n in range(len(rounds[i][:-1])):
            p = str(rounds[i][n])
            file_lines.append('\t\t\tkexp_vec_q(' + p + ')\twhen (kexp_cnt_i(' + str(i) + ') = ' + p + ')\telse')
        q = str(rounds[i][-1])
        file_lines.append('\t\t\tkexp_vec_q(' + q + ');\n')

    file_lines.append(
    '''

    --! Outpus
    kexp_key_next_stage_o   <= kexp_key_next_stage(core_num_g-1 downto 0);
    kexp_key_last_stage_o   <= kexp_vec_q(''' + str(n_stages) + ''');

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
