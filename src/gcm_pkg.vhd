--------------------------------------------------------------------------------
--! @File name:     gcm_pkg
--! @Date:          10/02/2019
--! @Description:   the package contains the constant for the AES algorithm
--! @Reference:     FIPS PUB 197, November 26, 2001
--! @Source:        https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf
--------------------------------------------------------------------------------
library ieee;
use work.aes_pkg.all;

--------------------------------------------------------------------------------
package gcm_pkg is

    --! Constants
    constant GCM_CNT_WIDTH_C    : natural   := 32;
    constant GCM_DATA_WIDTH_C   : natural   := AES_DATA_WIDTH_C;
    constant GCM_ICB_WIDTH_C    : natural   := AES_DATA_WIDTH_C - GCM_CNT_WIDTH_C;

    --! Types

end;

package body gcm_pkg is
end package body;
