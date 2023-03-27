--------------------------------------------------------------------------------
--! @File name:     gcm_ghash
--! @Date:          29/04/2019
--! @Description:   The module performs GHASH TAG calculation
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.std_logic_misc.or_reduce;
use work.aes_pkg.NB_STAGE_C;
use work.gcm_pkg.all;

--------------------------------------------------------------------------------
entity gcm_ghash is
    port(
        rst_i                       : in  std_logic;
        clk_i                       : in  std_logic;
        ghash_pkt_val_i             : in  std_logic;
        ghash_new_icb_i             : in  std_logic;
        aes_ecb_val_i               : in  std_logic;
        aes_ecb_data_i              : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        ghash_aad_val_i             : in  std_logic;
        ghash_aad_bval_i            : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_aad_i                 : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        ghash_ct_val_i              : in  std_logic;
        ghash_ct_bval_i             : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_ct_i                  : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        ghash_h_loaded_o            : out std_logic;
        ghash_j0_loaded_o           : out std_logic;
        ghash_tag_val_o             : out std_logic;
        ghash_tag_o                 : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0));
end entity;

--------------------------------------------------------------------------------
architecture arch_gcm_ghash of gcm_ghash is

    --! Constants
    constant ZERO_C : std_logic_vector(63 downto 0) := (others => '0');

    --! Types


    --! Signals
    signal h_q                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal J0_q                 : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal gf_x                 : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal gf_y                 : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_q                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_val                : std_logic;
    signal pkt_val_q            : std_logic;
    signal eop                  : std_logic;
    signal sop                  : std_logic;
    signal h_loaded             : std_logic;
    signal h_loaded_q           : std_logic;
    signal load_h               : std_logic;
    signal j0_loaded            : std_logic;
    signal j0_loaded_q          : std_logic;
    signal load_j0              : std_logic;

    signal aad_val              : std_logic;
    signal aad_len              : natural range 0 to 16;
    signal aad_cnt_q            : std_logic_vector((GCM_DATA_WIDTH_C / 2 - 3)-1 downto 0);
    signal aad_cnt              : std_logic_vector((GCM_DATA_WIDTH_C / 2 - 3)-1 downto 0);
    signal aad_cnt_en           : std_logic;

    signal ct_val               : std_logic;
    signal ct_len               : natural range 0 to 16;
    signal ct_cnt               : std_logic_vector((GCM_DATA_WIDTH_C / 2 - 3)-1 downto 0);
    signal ct_cnt_q             : std_logic_vector((GCM_DATA_WIDTH_C / 2 - 3)-1 downto 0);

    signal ct_cnt_en            : std_logic;
    signal bit_cnt              : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal x_data               : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_prev               : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal j0_val_q             : std_logic;
    signal cnt_val_q            : std_logic;
    signal ghash_tag_val_q      : std_logic;
    signal ghash_tag            : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal ghash_tag_q          : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

    signal x_part_0             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal x_part_1             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part_0             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part_1             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal h_part_0             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal h_part_1             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part               : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

    --------------------------------------------------------------------------------
    --! Component declaration
    --------------------------------------------------------------------------------
    component ghash_gfmul is
        port(
            gf_mult_h_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            gf_mult_x_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            gf_mult_y_o         : out std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0)
        );
    end component;

begin

    --------------------------------------------------------------------------------
    --! Enable H
    --------------------------------------------------------------------------------
    enable_h_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            h_loaded_q <= '0';
        elsif(rising_edge(clk_i)) then
            h_loaded_q <= h_loaded;
        end if;
    end process;

    h_loaded <= not(ghash_new_icb_i) and (h_loaded_q or load_h);

    --------------------------------------------------------------------------------
    --! Get H
    --------------------------------------------------------------------------------
    get_h_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            h_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(load_h = '1') then
                h_q <= aes_ecb_data_i;
            end if;
        end if;
    end process;

    load_h <= not(h_loaded_q) and aes_ecb_val_i;

    --------------------------------------------------------------------------------
    --! Enable J0
    --------------------------------------------------------------------------------
    enable_j0_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            j0_loaded_q <= '0';
        elsif(rising_edge(clk_i)) then
            j0_loaded_q <= j0_loaded;
        end if;
    end process;

    j0_loaded <= not(ghash_new_icb_i) and (j0_loaded_q or load_j0);

    --------------------------------------------------------------------------------
    --! Get J0
    --------------------------------------------------------------------------------
    get_j0_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            J0_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(load_j0 = '1') then
                J0_q <= aes_ecb_data_i;
            end if;
        end if;
    end process;

    load_j0 <= not(j0_loaded_q) and aes_ecb_val_i and h_loaded_q;

    --------------------------------------------------------------------------------
    --! Ghash next packet
    --------------------------------------------------------------------------------
    ghash_next_pkt_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            y_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            --! Save Y to xor with the next incoming X value
            if(y_val = '1') then
                y_q <= gf_y;
            end if;
        end if;
    end process;

    y_val <= cnt_val_q or (ghash_aad_val_i and aad_val) or (ghash_ct_val_i and ct_val);

    --------------------------------------------------------------------------------
    --! aad lenght
    --------------------------------------------------------------------------------
    aad_length_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            aad_cnt_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(aad_cnt_en = '1') then
                aad_cnt_q <= aad_cnt;
            end if;
        end if;
    end process;

    aad_cnt_en <= (j0_val_q or aad_val);

    aad_cnt    <= (others => '0') when (j0_val_q = '1') else std_logic_vector(unsigned(aad_cnt_q) +
                                                                to_unsigned(aad_len, aad_cnt_q'length));

    --------------------------------------------------------------------------------
    --! cipher text lenght
    --------------------------------------------------------------------------------
    ct_length_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            ct_cnt_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(ct_cnt_en = '1') then
                ct_cnt_q <= ct_cnt;
            end if;
        end if;
    end process;

    ct_cnt_en <= (j0_val_q or ct_val);

    ct_cnt    <= (others => '0') when (j0_val_q = '1') else std_logic_vector(unsigned(ct_cnt_q) +
                                                                to_unsigned(ct_len, ct_cnt_q'length));

    --------------------------------------------------------------------------------
    --! Calculate the length of the aad data
    --------------------------------------------------------------------------------
    aad_len_p : process(ghash_aad_bval_i)
        variable tmp_v : std_logic_vector(NB_STAGE_C-1 downto 0);
    begin
        tmp_v   := (others => '1');
        aad_len <= 0;
        aad_val <= '0';
        for i in 0 to NB_STAGE_C-1 loop
            if(tmp_v = ghash_aad_bval_i) then
                aad_len <= NB_STAGE_C - i;
                aad_val <= '1';
            end if;
            tmp_v(i) := '0';
        end loop;
    end process;

    --------------------------------------------------------------------------------
    --! Calculate the length of the cipher data
    --------------------------------------------------------------------------------
    ct_len_p : process(ghash_ct_bval_i)
        variable tmp_v : std_logic_vector(NB_STAGE_C-1 downto 0);
    begin
        tmp_v      := (others => '1');
        ct_len <= 0;
        ct_val <= '0';
        for i in 0 to NB_STAGE_C-1 loop
            if(tmp_v = ghash_ct_bval_i) then
                ct_len <= NB_STAGE_C - i;
                ct_val <= '1';
            end if;
            tmp_v(i) := '0';
        end loop;
    end process;

    --------------------------------------------------------------------------------
    --! Bit counter: minimum size increment is 1 byte
    bit_cnt <= aad_cnt_q & "000" & ct_cnt_q & "000";

    --! Select X input
    x_data  <= ghash_aad_i when (aad_val = '1')  else
               ghash_ct_i  when (ct_val = '1')   else
               bit_cnt;

    --! Output from the previous gfmul
    y_prev  <= (others => '0') when (sop = '1') else y_q;

    --! gfmul: X input
    gf_x    <= x_data xor y_prev;

    --! Start/End of packet
    sop     <= ghash_pkt_val_i and not(pkt_val_q);
    eop     <= pkt_val_q and not(ghash_pkt_val_i);

    --------------------------------------------------------------------------------
    --! Sample the ghash tag
    --------------------------------------------------------------------------------
    sample_tag_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            ghash_tag_q <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(j0_val_q = '1') then
                ghash_tag_q <= ghash_tag;
            end if;
        end if;
    end process;

    --! TAG update result
    ghash_tag <= y_q xor J0_q;

    --------------------------------------------------------------------------------
    --! Sample valid signals
    --------------------------------------------------------------------------------
    ghash_tag_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            pkt_val_q       <= '0';
            cnt_val_q       <= '0';
            j0_val_q        <= '0';
            ghash_tag_val_q <= '0';
        elsif(rising_edge(clk_i)) then
            pkt_val_q       <= ghash_pkt_val_i;
            cnt_val_q       <= eop;
            j0_val_q        <= cnt_val_q;
            ghash_tag_val_q <= j0_val_q;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Component instantiation
    --------------------------------------------------------------------------------
    u_ghash_gfmul: ghash_gfmul
        port map(
            gf_mult_h_i => h_q,
            gf_mult_x_i => gf_x,
            gf_mult_y_o => gf_y);

    u_ghash_gfmul_0: ghash_gfmul
        port map(
            gf_mult_h_i => h_q,
            gf_mult_x_i => x_part_0,
            gf_mult_y_o => y_part_0);


    u_ghash_gfmul_1: ghash_gfmul
        port map(
            gf_mult_h_i => h_q,
            gf_mult_x_i => x_part_1,
            gf_mult_y_o => y_part_1);

    x_part_0 <= ZERO_C & gf_x(63 downto 0);
    x_part_1 <= ZERO_C & gf_x(127 downto 64);

    h_part_0 <= ZERO_C & h_q(63 downto 0);
    h_part_1 <= ZERO_C & h_q(127 downto 64);

    y_part   <= y_part_1 xor y_part_0;

    --------------------------------------------------------------------------------
    ghash_h_loaded_o    <= h_loaded_q;
    ghash_j0_loaded_o   <= j0_loaded_q;
    ghash_tag_val_o     <= ghash_tag_val_q;
    ghash_tag_o         <= ghash_tag_q;

end architecture;
