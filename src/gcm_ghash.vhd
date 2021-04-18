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
        ghash_aad_bval_i            : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_aad_i                 : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
        ghash_cipher_text_bval_i    : in  std_logic_vector(NB_STAGE_C-1 downto 0);
        ghash_cipher_text_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
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
    signal h_s                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal j0_s                 : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal x_c                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_c                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_s                  : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_val_c              : std_logic;
    signal pkt_val_s            : std_logic;
    signal eop_c                : std_logic;
    signal sop_c                : std_logic;
    signal h_loaded_s           : std_logic;
    signal load_h_c             : std_logic;
    signal j0_loaded_s          : std_logic;
    signal load_j0_c            : std_logic;
    signal aad_val_c            : std_logic;
    signal cipher_val_c         : std_logic;
    signal aad_cnt_c            : natural range 0 to 16;
    signal aad_cnt_s            : std_logic_vector((GCM_DATA_WIDTH_C / 2-3)-1 downto 0);
    signal cipher_cnt_c         : natural range 0 to 16;
    signal cipher_cnt_s         : std_logic_vector((GCM_DATA_WIDTH_C / 2-3)-1 downto 0);
    signal cnt_c                : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal x_data_c             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_prev_c             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal j0_val_s             : std_logic;
    signal cnt_val_s            : std_logic;
    signal ghash_tag_val_s      : std_logic;
    signal ghash_tag_c          : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal ghash_tag_s          : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

    signal x_part_0_c           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal x_part_1_c           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part_0_c           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part_1_c           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal h_part_0_s           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal h_part_1_s           : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
    signal y_part_c             : std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);

    --------------------------------------------------------------------------------
    --! Component declaration
    --------------------------------------------------------------------------------
    component ghash_gfmul is
        port(
            gf_mult_x_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
            gf_mult_h_i         : in  std_logic_vector(GCM_DATA_WIDTH_C-1 downto 0);
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
            h_loaded_s <= '0';
        elsif(rising_edge(clk_i)) then
            if(ghash_new_icb_i = '1') then
                h_loaded_s <= '0';
            elsif(load_h_c = '1') then
                h_loaded_s <= '1';
            end if;
        end if;
    end process;

    load_h_c <= not(h_loaded_s) and aes_ecb_val_i;

    --------------------------------------------------------------------------------
    --! Get H
    --------------------------------------------------------------------------------
    get_h_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            h_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(load_h_c = '1') then
                h_s <= aes_ecb_data_i;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Enable J0
    --------------------------------------------------------------------------------
    enable_j0_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            j0_loaded_s <= '0';
        elsif(rising_edge(clk_i)) then
            if(ghash_new_icb_i = '1') then
                j0_loaded_s <= '0';
            elsif(load_j0_c = '1') then
                j0_loaded_s <= '1';
            end if;
        end if;
    end process;

    load_j0_c <= not(j0_loaded_s) and aes_ecb_val_i and h_loaded_s;

    --------------------------------------------------------------------------------
    --! Get J0
    --------------------------------------------------------------------------------
    get_j0_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            j0_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(load_j0_c = '1') then
                j0_s <= aes_ecb_data_i;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Ghash next packet
    --------------------------------------------------------------------------------
    ghash_next_pkt_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            y_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            --! Save Y to xor with the next incoming X value
            if(y_val_c = '1') then
                y_s <= y_c;
            end if;
        end if;
    end process;

    y_val_c <= cnt_val_s or (ghash_pkt_val_i and aad_val_c) or (pkt_val_s and cipher_val_c);

    --------------------------------------------------------------------------------
    --! aad lenght
    --------------------------------------------------------------------------------
    aad_length_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            aad_cnt_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(j0_val_s = '1') then
                aad_cnt_s <= (others => '0');
            elsif(aad_val_c = '1') then
               aad_cnt_s  <= std_logic_vector(unsigned(aad_cnt_s) + to_unsigned(aad_cnt_c, aad_cnt_s'length));
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! cipher text lenght
    --------------------------------------------------------------------------------
    ct_length_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            cipher_cnt_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(j0_val_s = '1') then
                cipher_cnt_s <= (others => '0');
            elsif(cipher_val_c = '1') then
                cipher_cnt_s <= std_logic_vector(unsigned(cipher_cnt_s) + to_unsigned(cipher_cnt_c, cipher_cnt_s'length));
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Calculate the length of the aad data
    --------------------------------------------------------------------------------
    aad_len_p : process(ghash_aad_bval_i)
        variable tmp_v : std_logic_vector(NB_STAGE_C-1 downto 0);
    begin
        tmp_v     := (others => '1');
        aad_cnt_c <= 0;
        aad_val_c <= '0';
        for i in 0 to NB_STAGE_C-1 loop
            if(tmp_v = ghash_aad_bval_i) then
                aad_cnt_c <= NB_STAGE_C - i;
                aad_val_c <= '1';
            end if;
            tmp_v(i) := '0';
        end loop;
    end process;

    --------------------------------------------------------------------------------
    --! Calculate the length of the cipher data
    --------------------------------------------------------------------------------
    cipher_len_p : process(ghash_cipher_text_bval_i)
        variable tmp_v : std_logic_vector(NB_STAGE_C-1 downto 0);
    begin
        tmp_v        := (others => '1');
        cipher_cnt_c <= 0;
        cipher_val_c <= '0';
        for i in 0 to NB_STAGE_C-1 loop
            if(tmp_v = ghash_cipher_text_bval_i) then
                cipher_cnt_c <= NB_STAGE_C - i;
                cipher_val_c <= '1';
            end if;
            tmp_v(i) := '0';
        end loop;
    end process;

    --------------------------------------------------------------------------------
    --! Bit counter: minimum size increment is 1 byte
    cnt_c       <= aad_cnt_s & "000" & cipher_cnt_s & "000";

    --! Select X input
    x_data_c    <= ghash_aad_i          when (aad_val_c = '1')      else
                   ghash_cipher_text_i  when (cipher_val_c = '1')   else
                   cnt_c;

    --! Output from the previous gfmul
    y_prev_c    <= (others => '0') when (sop_c = '1') else y_s;

    --! gfmul: X input
    x_c         <= x_data_c xor y_prev_c;

    --! TAG update result
    ghash_tag_c <= y_s xor j0_s;

    --! Start/End of packet
    sop_c <= ghash_pkt_val_i and not(pkt_val_s);
    eop_c <= pkt_val_s and not(ghash_pkt_val_i);

    --------------------------------------------------------------------------------
    --! Sample the ghash tag
    --------------------------------------------------------------------------------
    sample_tag_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            ghash_tag_s <= (others => '0');
        elsif(rising_edge(clk_i)) then
            if(j0_val_s = '1') then
                ghash_tag_s <= ghash_tag_c;
            end if;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Sample valid signals
    --------------------------------------------------------------------------------
    ghash_tag_p : process(rst_i, clk_i)
    begin
        if(rst_i = '1') then
            pkt_val_s       <= '0';
            cnt_val_s       <= '0';
            j0_val_s        <= '0';
            ghash_tag_val_s <= '0';
        elsif(rising_edge(clk_i)) then
            pkt_val_s       <= ghash_pkt_val_i;
            cnt_val_s       <= eop_c;
            j0_val_s        <= cnt_val_s;
            ghash_tag_val_s <= j0_val_s;
        end if;
    end process;

    --------------------------------------------------------------------------------
    --! Component instantiation
    --------------------------------------------------------------------------------
    u_ghash_gfmul: ghash_gfmul
        port map(
            gf_mult_x_i => x_c,
            gf_mult_h_i => h_s,
            gf_mult_y_o => y_c);

    u_ghash_gfmul_0: ghash_gfmul
        port map(
            gf_mult_x_i => x_part_0_c,
            gf_mult_h_i => h_s,
            gf_mult_y_o => y_part_0_c);


            u_ghash_gfmul_1: ghash_gfmul
            port map(
                gf_mult_x_i => x_part_1_c,
                gf_mult_h_i => h_s,
                gf_mult_y_o => y_part_1_c);

    x_part_0_c <= ZERO_C & x_c(63 downto 0);
    h_part_0_s <= ZERO_C & h_s(63 downto 0);

    x_part_1_c <= x_c(127 downto 64) & ZERO_C;
    h_part_1_s <= h_s(127 downto 64) & ZERO_C;

    y_part_c   <= y_part_1_c xor y_part_0_c;

    --------------------------------------------------------------------------------
    ghash_h_loaded_o    <= h_loaded_s;
    ghash_j0_loaded_o   <= j0_loaded_s;
    ghash_tag_val_o     <= ghash_tag_val_s;
    ghash_tag_o         <= ghash_tag_s;

end architecture;
