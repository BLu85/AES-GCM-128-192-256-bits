#!/usr/bin/env python3

import sys

def generate_aes_ecb(pre_expanded = True, filepath='./'):
    filename = filepath + 'aes_ecb.vhd'

    state_type = 'state_arr_t(aes_n_rounds_g-1 downto 0);' if pre_expanded == False else 'state_t;'
    key_idx    = 'rnd_key_index_next(i),'                  if pre_expanded == False else 'open,'
    trg_key    = 'rnd_stage_trg_key(i),'                   if pre_expanded == False else 'open,'
    idx        = '(aes_n_rounds_g-1)'                      if pre_expanded == False else ''

    file_lines = []
    file_lines.append(
    '''--------------------------------------------------------------------------------
--! @File name:     aes_ecb
--! @Date:          20/05/2016
--! @Description:   the module performs the AES encryption
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;
use work.aes_func.all;

--------------------------------------------------------------------------------
entity aes_ecb is
    generic(
        aes_n_rounds_g              : natural range 0 to NR_256_C   := NR_128_C);
    port(
        rst_i                       : in  std_logic;
        clk_i                       : in  std_logic;
        aes_mode_i                  : in  std_logic_vector(1 downto 0);
        aes_key_word_val_i          : in  std_logic_vector(3 downto 0);
        aes_key_word_i              : in  std_logic_vector(AES_256_KEY_WIDTH_C-1 downto 0);
        aes_pipe_reset_i            : in  std_logic;
        aes_plain_text_val_i        : in  std_logic;
        aes_plain_text_i            : in  std_logic_vector(aes_DATA_WIDTH_C-1 downto 0);
        aes_cipher_text_ack_i       : in  std_logic;
        aes_cipher_text_val_o       : out std_logic;
        aes_cipher_text_o           : out std_logic_vector(aes_DATA_WIDTH_C-1 downto 0);
        aes_ecb_busy_o              : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_ecb of aes_ecb is

    --! Constants''')

    if (pre_expanded == False):
        file_lines.append(
    '''\tconstant RCON_START_VALUE_C         : std_logic_vector(7 downto 0) := x"01";''')

    file_lines.append('''
    --! Types

    --! Signals
    signal rnd_loop_back              : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_i_am_last              : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_next_stage_busy        : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_val_prev         : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_cnt_prev         : round_cnt_arr_t(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_data_prev        : state_arr_t(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_val_next         : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_cnt_next         : round_cnt_arr_t(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_data_next        : state_arr_t(aes_n_rounds_g-1 downto 0);
    signal rnd_stage_trg_key          : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_next_stage_val         : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal rnd_busy                   : std_logic;
    signal rnd_i_am_busy              : std_logic_vector(aes_n_rounds_g-1 downto 0);
    signal loop_back_cnt              : round_cnt_t;
    signal loop_back_data             : state_t;
    signal loop_back                  : std_logic;
    signal kexp_key_next_stage        : state_arr_t(aes_n_rounds_g-1 downto 0);
    signal kexp_key_last_stage        : ''' + state_type + '''
    signal last_rnd_busy              : std_logic;
    signal aes_plain_text             : state_t;
    signal aes_cipher_text_val        : std_logic;
    signal aes_cipher_text            : state_t;''')

    if (pre_expanded == False):
        file_lines.append('''
    signal kexp_key_next_part         : key_vec_arr_t(aes_n_rounds_g-1 downto 0);
    signal rnd_key_index_next         : round_cnt_arr_t(aes_n_rounds_g-1 downto 0);
    signal kexp_rcon_exp              : byte_arr_t(aes_n_rounds_g-1 downto 0);
    signal kexp_rcon                  : byte_arr_t(aes_n_rounds_g-1 downto 0);
    signal kexp_key_part              : key_vec_arr_t(aes_n_rounds_g-1 downto 0);
    signal start_first_stage          : std_logic;
    signal key_origin_q               : key_vec_t;''')

    file_lines.append('''

    --------------------------------------------------------------------------------
    --! Component declaration
    --------------------------------------------------------------------------------''')
    if (pre_expanded == True):
        file_lines.append('''
    component aes_kexp is
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
    end component;''')

    else:
        file_lines.append('''
    component aes_kexp is
        generic(
            core_num_g              : natural := 0);
        port(
            rst_i                   : in  std_logic;
            clk_i                   : in  std_logic;
            aes_mode_i              : in  std_logic_vector(1 downto 0);
            kexp_dval_i             : in  std_logic;
            kexp_cnt_i              : in  round_cnt_t;
            kexp_rcon_i             : in  byte_t;
            kexp_key_part_i         : in  key_vec_t;
            kexp_rcon_o             : out byte_t;
            kexp_key_next_part_o    : out key_vec_t;
            kexp_key_next_stage_o   : out state_t;
            kexp_key_last_stage_o   : out state_t);
    end component;''')

    file_lines.append('''

    component aes_round is
        port(
            rst_i                   : in  std_logic;
            clk_i                   : in  std_logic;
            aes_mode_i              : in  std_logic_vector(1 downto 0);
            rnd_i_am_last_inst_i    : in  std_logic;
            kexp_part_key_i         : in  state_t;
            rnd_stage_reset_i       : in  std_logic;
            rnd_next_stage_busy_i   : in  std_logic;
            rnd_stage_val_i         : in  std_logic;
            rnd_stage_cnt_i         : in  round_cnt_t;
            rnd_stage_data_i        : in  state_t;
            rnd_stage_val_o         : out std_logic;
            rnd_key_index_o         : out round_cnt_t;
            rnd_stage_cnt_o         : out round_cnt_t;
            rnd_stage_data_o        : out state_t;
            rnd_stage_trg_key_o     : out std_logic;
            rnd_next_stage_val_o    : out std_logic;
            rnd_loop_back_o         : out std_logic;
            rnd_i_am_busy_o         : out std_logic);
    end component;

    component aes_last_round is
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
            last_rnd_busy_o         : out std_logic);
    end component;

begin

    --------------------------------------------------------------------------------
    --! Get and store the key
    --------------------------------------------------------------------------------''')
    if (pre_expanded == False):
        file_lines.append('''
    get_key_p: process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            key_origin_q <= (others => (others => (others => '0')));
        elsif(rising_edge(clk_i)) then
            --! Load the key words in the key vector
            if (aes_key_word_val_i(2) = '1') then
                key_origin_q(7) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (7+1)-1 downto WORD_WIDTH_C * 7));
                key_origin_q(6) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (6+1)-1 downto WORD_WIDTH_C * 6));
                key_origin_q(5) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (5+1)-1 downto WORD_WIDTH_C * 5));
                key_origin_q(4) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (4+1)-1 downto WORD_WIDTH_C * 4));
            end if;
            if (aes_key_word_val_i(1) = '1') then
                key_origin_q(3) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (3+1)-1 downto WORD_WIDTH_C * 3));
                key_origin_q(2) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (2+1)-1 downto WORD_WIDTH_C * 2));
            end if;
            if (aes_key_word_val_i(0) = '1') then
                key_origin_q(1) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (1+1)-1 downto WORD_WIDTH_C * 1));
                key_origin_q(0) <= vec_to_word(aes_key_word_i(WORD_WIDTH_C * (0+1)-1 downto WORD_WIDTH_C * 0));
            end if;
            if (aes_mode_i = AES_MODE_192_C or aes_mode_i = AES_MODE_128_C) then
                key_origin_q(1) <= (others => (others => '0'));
                key_origin_q(0) <= (others => (others => '0'));
            end if;
            if (aes_mode_i = AES_MODE_128_C) then
                key_origin_q(3) <= (others => (others => '0'));
                key_origin_q(2) <= (others => (others => '0'));
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Component instantiation
    --------------------------------------------------------------------------------
    gen_key_stack: for i in 0 to aes_n_rounds_g-1 generate
        u_aes_kexp: aes_kexp
            generic map(
                core_num_g              => i
            )
            port map(
                rst_i                   => rst_i,
                clk_i                   => clk_i,
                aes_mode_i              => aes_mode_i,
                kexp_dval_i             => rnd_stage_trg_key(i),
                kexp_cnt_i              => rnd_key_index_next(i),
                kexp_rcon_i             => kexp_rcon(i),
                kexp_key_part_i         => kexp_key_part(i),
                kexp_rcon_o             => kexp_rcon_exp(i),
                kexp_key_next_part_o    => kexp_key_next_part(i),
                kexp_key_next_stage_o   => kexp_key_next_stage(i),
                kexp_key_last_stage_o   => kexp_key_last_stage(i)
            );
    end generate gen_key_stack;''')

    else:
        file_lines.append('''

    u_aes_kexp: aes_kexp
        generic map(
            core_num_g              => aes_n_rounds_g
        )
        port map(
            rst_i                   => rst_i,
            clk_i                   => clk_i,
            kexp_key_word_val_i     => aes_key_word_val_i,
            kexp_key_word_i         => aes_key_word_i,
            kexp_cnt_i              => rnd_stage_cnt_i,
            kexp_key_next_stage_o   => kexp_key_next_stage,
            kexp_key_last_stage_o   => kexp_key_last_stage
        );''')

    file_lines.append('''

    --! Plain text conversion
    aes_plain_text <= vec_to_state(aes_plain_text_i);

    gen_round_stack: for i in 0 to aes_n_rounds_g-1 generate
        u_aes_round: aes_round
            port map(
                rst_i                   => rst_i,
                clk_i                   => clk_i,
                aes_mode_i              => aes_mode_i,
                rnd_i_am_last_inst_i    => rnd_i_am_last(i),
                kexp_part_key_i         => kexp_key_next_stage(i),
                rnd_stage_reset_i       => aes_pipe_reset_i,
                rnd_next_stage_busy_i   => rnd_next_stage_busy(i),
                rnd_stage_val_i         => rnd_stage_val_prev(i),
                rnd_stage_cnt_i         => rnd_stage_cnt_prev(i),
                rnd_stage_data_i        => rnd_stage_data_prev(i),
                rnd_key_index_o         => ''' + key_idx + '''
                rnd_stage_val_o         => rnd_stage_val_next(i),
                rnd_stage_cnt_o         => rnd_stage_cnt_next(i),
                rnd_stage_data_o        => rnd_stage_data_next(i),
                rnd_stage_trg_key_o     => ''' + trg_key + '''
                rnd_next_stage_val_o    => rnd_next_stage_val(i),
                rnd_loop_back_o         => rnd_loop_back(i),
                rnd_i_am_busy_o         => rnd_i_am_busy(i)
            );

        gen_others: if i < aes_n_rounds_g-1 generate
            rnd_i_am_last(i)     <= '0';
            rnd_next_stage_busy(i) <= rnd_i_am_busy(i + 1);
        end generate gen_others;

        gen_last: if i = aes_n_rounds_g-1 generate
            rnd_i_am_last(i)     <= '1';
            rnd_next_stage_busy(i) <= last_rnd_busy;
        end generate gen_last;

    end generate gen_round_stack;''')

    if (pre_expanded == False):
        file_lines.append('''
    --! Key chain signals
    start_first_stage <= not(rnd_busy) and rnd_stage_val_prev(0);
    kexp_key_part(0)  <= key_origin_q       when (start_first_stage = '1') else kexp_key_next_part(aes_n_rounds_g-1);
    kexp_rcon(0)      <= RCON_START_VALUE_C when (start_first_stage = '1') else kexp_rcon_exp(aes_n_rounds_g-1);

    gen_rcon_chain: for i in 1 to aes_n_rounds_g-1 generate
        kexp_key_part(i)  <= kexp_key_next_part(i-1);
        kexp_rcon(i)      <= kexp_rcon_exp(i-1);
    end generate gen_rcon_chain;''')

    file_lines.append('''

    rnd_busy              <= rnd_i_am_busy(0) or loop_back;

    --! Round chain signals
    loop_back             <= rnd_loop_back(aes_n_rounds_g-1);
    loop_back_cnt         <= rnd_stage_cnt_next(aes_n_rounds_g-1);
    loop_back_data        <= rnd_stage_data_next(aes_n_rounds_g-1);

    rnd_stage_val_prev(0)   <= loop_back or aes_plain_text_val_i;
    rnd_stage_cnt_prev(0)   <= loop_back_cnt  when (loop_back = '1') else   0;
    rnd_stage_data_prev(0)  <= loop_back_data when (loop_back = '1') else   aes_plain_text;

    gen_rnd_chain: for i in 1 to aes_n_rounds_g-1 generate
        rnd_stage_val_prev(i)  <= rnd_next_stage_val(i-1);
        rnd_stage_cnt_prev(i)  <= rnd_stage_cnt_next(i-1);
        rnd_stage_data_prev(i) <= rnd_stage_data_next(i-1);
    end generate gen_rnd_chain;

    u_aes_last_round: aes_last_round
        port map(
            rst_i               => rst_i,
            clk_i               => clk_i,
            kexp_last_stage_i   => kexp_key_last_stage''' + idx + ''',
            last_rnd_reset_i    => aes_pipe_reset_i,
            last_rnd_val_i      => rnd_stage_val_next(aes_n_rounds_g-1),
            last_rnd_data_i     => rnd_stage_data_next(aes_n_rounds_g-1),
            last_rnd_ack_i      => aes_cipher_text_ack_i,
            last_rnd_val_o      => aes_cipher_text_val,
            last_rnd_data_o     => aes_cipher_text,
            last_rnd_busy_o     => last_rnd_busy);

    --! Outptus
    aes_ecb_busy_o          <= rnd_busy;
    aes_cipher_text_val_o   <= aes_cipher_text_val;
    aes_cipher_text_o       <= state_to_vec(aes_cipher_text);

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
