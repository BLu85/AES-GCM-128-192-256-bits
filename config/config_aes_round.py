import sys

def generate_aes_round(pipe_stage=0, filepath='./'):

    AES_CORE_PIPE = pipe_stage | 0x8
    filename = filepath + 'aes_round.vhd'

    indent = ' ' * 4

    file_lines = []
    file_lines.append(
    '''-------------------------------------------------------------------------------
--! @File name:     aes_round
--! @Date:          27/03/2016
--! @Description:   the module performs one of the rounds of the encryption.
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.aes_pkg.all;
use work.aes_func.all;

--------------------------------------------------------------------------------
entity aes_round is
    port(
        rst_i                       : in  std_logic;
        clk_i                       : in  std_logic;
        aes_mode_i                  : in  std_logic_vector(1 downto 0);
        rnd_i_am_last_inst_i        : in  std_logic;
        kexp_part_key_i             : in  state_t;
        rnd_stage_reset_i           : in  std_logic;
        rnd_next_stage_busy_i       : in  std_logic;
        rnd_stage_val_i             : in  std_logic;
        rnd_stage_cnt_i             : in  round_cnt_t;
        rnd_stage_data_i            : in  state_t;
        rnd_stage_val_o             : out std_logic;
        rnd_key_index_o             : out round_cnt_t;
        rnd_stage_cnt_o             : out round_cnt_t;
        rnd_stage_data_o            : out state_t;
        rnd_stage_trg_key_o         : out std_logic;
        rnd_next_stage_val_o        : out std_logic;
        rnd_loop_back_o             : out std_logic;
        rnd_i_am_busy_o             : out std_logic);
end entity;

--------------------------------------------------------------------------------
architecture arch_aes_round of aes_round is

    --! Constants

    --! Types

    --! Signals
'''
    )

    for i in range(4):
        if AES_CORE_PIPE & (1 << i):
            tmp_str = str(i) + '_q             '
            file_lines.append(indent + 'signal dval_' + tmp_str + ': std_logic;')
            file_lines.append(indent + 'signal cnt_' + tmp_str + ' : round_cnt_t;')
            file_lines.append(indent + 'signal data_' + tmp_str + ': state_t;')
            file_lines.append(  '')
        tmp_str = str(i) + '             '
        file_lines.append(indent + 'signal dval_' + tmp_str + '  : std_logic;')
        file_lines.append(indent + 'signal cnt_' + tmp_str + '   : round_cnt_t;')
        file_lines.append(indent + 'signal data_' + tmp_str + '  : state_t;')
        file_lines.append(indent + 'signal rnd_stage_data_' + str(i) + '     : state_t;')
        file_lines.append(  '')

    file_lines.append(
    '''    signal next_stage_val       : std_logic;
    signal thr                  : natural range 0 to 15;
    signal last_loop            : std_logic;
    signal stage_val            : std_logic;
    signal loop_back            : std_logic;

    signal stage_stall          : std_logic_vector(3 downto 0);
    signal stage_busy           : std_logic;
    signal rnd_stage_trg_key    : std_logic;
    signal key_var_en           : std_logic_vector(1 downto 0);

begin

    --! Sets the number of pipeline rounds to perform
    thr <=  NR_192_C    when (aes_mode_i = AES_MODE_192_C) else
            NR_256_C    when (aes_mode_i = AES_MODE_256_C) else
            NR_128_C;   --! aes_mode_i = AES_MODE_128_C

    last_loop_p : process(cnt_3_q, thr, rnd_i_am_last_inst_i)
    begin
        --! When '1' data have executed all the AES rounds
        last_loop <= '1';
        if(rnd_i_am_last_inst_i = '1') then
            if(cnt_3_q /= thr) then
                last_loop <= '0';
            end if;
        end if;
    end process;

    --! Loop data back in the round stage
    loop_back         <= dval_3_q and not(last_loop);

    --! When '1' the data are valid for the next stage
    next_stage_val    <= '0' when (rnd_i_am_last_inst_i = '1' and last_loop = '1') else dval_3_q;

    --! Data are valid and can exit the pipeline
    stage_val         <= dval_3_q and last_loop;

    --! Stall the current pipeline stage if the next stage is stalled and the current stage has valid data
    stage_stall(3)    <= dval_3_q and rnd_next_stage_busy_i and last_loop;
    stage_stall(2)    <= dval_3   and stage_stall(3);
    stage_stall(1)    <= dval_2   and stage_stall(2);
    stage_stall(0)    <= dval_1   and stage_stall(1);
    stage_busy        <= stage_stall(0);
''')

    # Create the AES stages
    file_lines.append(indent + '--! Create the AES stages')
    tmp_str =   'data_0            <= add_round_key(rnd_stage_data_0, kexp_part_key_i);'
    file_lines.append(indent + tmp_str)
    tmp_str =   'data_1            <= sub_byte(rnd_stage_data_1);'
    file_lines.append(indent + tmp_str)
    tmp_str =   'data_2            <= shift_row(rnd_stage_data_2);'
    file_lines.append(indent + tmp_str)
    tmp_str =   'data_3            <= rnd_stage_data_3 when (cnt_3 = thr) else mix_columns(rnd_stage_data_3);'
    file_lines.append(indent + tmp_str)
    file_lines.append('')


    # Create the data connection
    file_lines.append(indent + '--! Create the data connection')
    file_lines.append(indent + 'rnd_stage_data_0  <= rnd_stage_data_i;')
    for i in range(3):
        tmp_str  = 'rnd_stage_data_' + str(i + 1) + '  <= data_' + str(i)
        tmp_str += '_q;' if AES_CORE_PIPE & (1 << i) else ';'
        file_lines.append(indent + tmp_str)
    file_lines.append('')

    # Create counter connections
    file_lines.append(indent + '--! Create the counter connection')
    file_lines.append(indent + 'cnt_0             <= rnd_stage_cnt_i + 1;')
    for i in range(3):
        tmp_str  = 'cnt_' + str(i + 1) + '             <= cnt_' + str(i)
        tmp_str += '_q;' if AES_CORE_PIPE & (1 << i) else ';'
        file_lines.append(indent + tmp_str)
    file_lines.append('')

    # Create dval connections
    file_lines.append(indent + '--! Create the dval connection')
    file_lines.append(indent + 'dval_0            <= rnd_stage_val_i;')
    for i in range(3):
        tmp_str  = 'dval_' + str(i + 1) + '            <= dval_' + str(i)
        tmp_str += '_q;' if AES_CORE_PIPE & (1 << i) else ';'
        file_lines.append(indent + tmp_str)
    file_lines.append('')

    file_lines.append(indent + 'rnd_stage_trg_key <= \'1\' when ((cnt_3 /= cnt_3_q) and (stage_stall(3) = \'0\') and (rnd_stage_val_i = \'1\')) else \'0\';')

    file_lines.append(
'''
    --------------------------------------------------------------------------------
    --! process: sample_data_p
    --------------------------------------------------------------------------------
    sample_data_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
'''
    )

    for i in range(4):
        if AES_CORE_PIPE & (1 << i):
            tmp_str = str(i) + '_q'
            file_lines.append( '            dval_' + tmp_str + '   <= \'0\';')
            file_lines.append( '            cnt_' + tmp_str + '    <= 0;')
            file_lines.append( '            data_' + tmp_str + '   <= (others => (others => (others => \'0\')));')
            file_lines.append( '')

    file_lines.append(         '')
    file_lines.append(         '        elsif(rising_edge(clk_i)) then')
    file_lines.append(         '')

    # Sample the pipeline stages
    for i in range(4):
        if AES_CORE_PIPE & (1 << i):
            tmp_str = str(i)
            file_lines.append(     '            if(stage_stall(' + tmp_str + ') = \'0\') then')
            file_lines.append(     '                if(dval_' + tmp_str + ' = \'1\') then')
            file_lines.append(     '                    cnt_' + tmp_str + '_q  <= cnt_' + tmp_str + ';')
            file_lines.append(     '                    data_' + tmp_str + '_q <= data_' + tmp_str + ';')
            file_lines.append(     '                end if;')
            file_lines.append(     '                dval_' + tmp_str + '_q <= dval_' + tmp_str + ';')
            file_lines.append(     '            end if;')
            file_lines.append(     '')

    # Reset the pipe
    file_lines.append(         '            --! Reset the whole pipe')
    file_lines.append(         '            if(rnd_stage_reset_i = \'1\') then')
    for i in range(4):
        if AES_CORE_PIPE & (1 << i):
            tmp_str = str(i)
            file_lines.append( '                cnt_' + tmp_str + '_q  <= 0;')
            file_lines.append( '                dval_' + tmp_str + '_q <= \'0\';')
            file_lines.append( '')
    file_lines.append(         '            end if;')
    file_lines.append(         '        end if;')

    file_lines.append(
    '''
    end process;
    ''')

    file_lines.append(
    '''

    --------------------------------------------------------------------------------
    --! Loop back data in the round stage
    rnd_loop_back_o      <= loop_back;

    --! Data are ready for the last round
    rnd_stage_val_o      <= stage_val;

    --! Index to key expansion
    rnd_key_index_o      <= cnt_0;

    --! Next stage index
    rnd_stage_cnt_o      <= cnt_3_q;

    --! Input data for the final round
    rnd_stage_data_o     <= data_3_q;

    --! Read request to get the partial key block
    rnd_stage_trg_key_o  <= rnd_stage_trg_key;

    --! Loop data once again
    rnd_next_stage_val_o <= next_stage_val;

    --! Prevent to read new input data when busy is high
    rnd_i_am_busy_o      <= stage_busy;

end architecture;
''')

    try:
        with open(filename, 'w') as fp:
            fp = open(filename, 'w')
            fp.write("\n".join(file_lines))
            fp.close()
            print(' >>\tOK   : File ' + filename + ' has been successfully generated')
    except:
        print(' >>\tError: File ' + filename + ' could not be generated')
        sys.exit()
