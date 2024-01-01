import os
import sys
import json
import argparse
import random

from config_aes_round  import generate_aes_round
from config_aes_ecb    import generate_aes_ecb
from config_aes_kexp   import generate_aes_kexp_logic
from config_aes_kprexp import generate_aes_pre_exp_key
from config_aes_top    import generate_aes_top
from argparse          import RawTextHelpFormatter


# ======================================================================================
class aes_conf(object):
    '''AES funtions for a single block
    '''
    ip_mode   = ['128', '192', '256']
    ip_ed     = ['enc', 'dec']
    ip_size   = ['XS', 'S', 'M', 'L']
    ip_pipe   = range(0, 8)
    test_size = ['short', 'medium', 'long']


    # ======================================================================================
    def __init__(self, basepath='./', config_ip_only = True):

        self.config_ip_only = config_ip_only
        self.conf_param = {}
        self.basepath = basepath
        self.parser = argparse.ArgumentParser(  add_help=False, formatter_class=RawTextHelpFormatter,
                                                description='')
        self.add_args()
        self.args = self.parser.parse_args()


    # ======================================================================================
    def add_args(self):

        self.parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                            help='Configure the AES-GCM IP')

        self.parser.add_argument('-v', '--version', action='version',
                            version='v1.7', help="Show the script version.")

        self.parser.add_argument('-m', '--mode',
                            default=None, metavar='MODE', type = lambda s : s.upper(), choices=self.ip_mode,
                            help='Set the GCM mode: choose amongst 128 (default), 192, or 256.')

        self.parser.add_argument('-b', '--ed',
                            type=str.lower, default=None, metavar='ENC DEC', choices=self.ip_ed,
                            help='Set the IP to encrypt (default) or decrypt incoming data.')

        self.parser.add_argument('-p', '--pipe',
                            type=int, default=None, metavar='N', choices=self.ip_pipe,
                            help='Set the number of pipe stages in the AES round core. E.g.: set -p 7 to get 3 pipe stages (maximum value).')

        self.parser.add_argument('-s', '--size',
                            type=str.upper, default=None, metavar='SIZE', choices=self.ip_size,
                            help='Set the size of the GCM-AES IP. It defines the number of AES rounds:\
                            \nXS = 1 AES round instance,\nS = 2 AES round instances,\
                            \nM = AES round instances are half the number of rounds needed for the specific mode,\
                            \nL = AES round instances are equal to the number of rounds needed for the specific mode.')

        self.parser.add_argument('-x', '--rmexp',
                            default=False, action='store_true',
                            help='Remove the logic that expands the key. Expanded key has to be provided externally')

        self.parser.add_argument('-f', '--ngfmul',
                            type=int, default=1, metavar='GFMUL', choices=range(1,3),
                            help='Specify 1 (default) or 2 GFMUL IP in the GHASH block.')


        if self.config_ip_only == True:
            return


        self.parser.add_argument('-w', '--wipe',
                            action='store_true',
                            help='Wipe the tmp folder from all the config files.')

        self.parser.add_argument('-c', '--compiler',
                            type=str.lower,
                            help='Define the compiler')

        self.parser.add_argument('-k', '--key',
                            type=str.upper, metavar='KEY',
                            help='Load a specific key')

        self.parser.add_argument('-i', '--iv',
                            type=str.upper, metavar='IV',
                            help='Load a specific IV')

        self.parser.add_argument('-a', '--aad',
                            type=str.upper, metavar='AAD',
                            help='Load a specific stream of AAD data; \'empty\' loads 0 AAD bytes')

        self.parser.add_argument('-d', '--data',
                            type=str.upper, metavar='DATA',
                            help='Load a specific stream of CT or PT data; \'empty\' loads 0 CT or PT bytes')

        self.parser.add_argument('-e', '--seed',
                            type=int, metavar='N',
                            help='Set the seed to re-run specific test conditions. N is an integer number')

        self.parser.add_argument('-g', '--gui',
                            type=str, nargs='?', const='aes_dump', metavar='file',
                            help='Start a GUI session. Signals are dumped in \'file\'.')

        self.parser.add_argument('-n', '--n-test',
                            type=int, default=1, metavar='N',
                            help='Run N tests.')

        self.parser.add_argument('-r', '--rand-param',
                            action='store_true',
                            help='Generate random IP parameters.')

        self.parser.add_argument('-t', '--tsize',
                            default=None, metavar='SIZE', choices=self.test_size,
                            help='Set the maximum number of byte that can be generated for the AAD and the PT: short (2^10-1), medium (2^16-1), long (2^32-1)')

        self.parser.add_argument('-z', '--verbose',
                            action='store_true',
                            help='increase output verbosity.')


    # ======================================================================================
    def create_seed(self):
        return random.randint(0, 2**32 - 1)


    # ======================================================================================
    def wipe_dir(self, dir):
        os.system('rm -rv ' + dir)
        os.system('mkdir -v ' + dir)


    # ======================================================================================
    def test_config(self):

        test_size = dict(zip(self.test_size, [2**12 - 1, 2**16 - 1, 2**32 - 1]))

        basepath = self.basepath + 'tmp/'

        if self.args.seed != None:
            # Load the test with parameter specified in the .json seed file
            if os.path.exists(basepath):
                files = [str(self.args.seed) + '.json']

                with open(basepath + files[-1], 'r') as last_config_file:
                    self.conf_param = json.load(last_config_file)
                    last_config_file.close()
            else:
                sys.exit(" >>\tError: a test must be generated before calling arg \'-l\'. File .json has not been found")
        else:
            # Create the seed
            self.conf_param['seed'] = self.create_seed()


        if self.args.key != None or self.args.seed == None:
            if self.args.key != None:
                if self.args.mode == 'ALL':
                    sys.exit(" >>\tError: Cannot supply a key when mode is set to ALL")
                if self.args.mode == None:
                    if str((len(self.args.key)//2)*8) != '128':
                        sys.exit(" >>\tError: AES mode and Key lenght don\'t match")
                elif self.args.mode != str((len(self.args.key)//2)*8):
                    sys.exit(" >>\tError: AES mode and Key lenght don\'t match")
                self.conf_param['key'] = self.args.key
            else:
                # Create a random Key
                self.conf_param['key'] = 'random'


        self.set_default_value( self.args.tsize    , self.args.seed , 'test_size' , 'short'  )
        self.set_default_value( self.args.iv       , self.args.seed , 'iv'        , 'random' )
        self.set_default_value( self.args.aad      , self.args.seed , 'aad'       , 'random' )
        self.set_default_value( self.args.data     , self.args.seed , 'data'      , 'random' )
        self.set_default_value( self.args.compiler , self.args.seed , 'compiler'  , 'ghdl'   )

        self.conf_param['max_n_byte'] = test_size[self.conf_param['test_size']]


        if self.args.verbose == True:
            self.conf_param['verbose'] = 'DEBUG'
        else:
            self.conf_param['verbose'] = 'INFO'

        if self.args.seed != None:
            self.conf_param['seed'] = self.args.seed

        return self.conf_param


    # ======================================================================================
    def gcm_ip_config(self):

        aes_n_rounds = dict(zip(self.ip_mode, [10, 12, 14]))

        if hasattr(self.args, 'seed'):
            seed = self.args.seed
        else:
            seed = None

        self.set_default_value( self.args.size   , seed , 'aes_size'      , 'XS'  )
        self.set_default_value( self.args.mode   , seed , 'aes_mode'      , '128' )
        self.set_default_value( self.args.ed     , seed , 'enc_dec'       , 'enc' )
        self.set_default_value( self.args.pipe   , seed , 'pipes_in_core' , 0     )
        self.set_default_value( self.args.ngfmul , seed , 'n_gfmul_ip'    , 1     )


        if self.conf_param['aes_size'] == 'XS':
            self.conf_param['n_rounds'] = 1
        elif self.conf_param['aes_size'] == 'S':
            self.conf_param['n_rounds'] = 2
        elif self.conf_param['aes_size'] == 'M':
            if self.conf_param['aes_mode'] == 'ALL':
                sys.exit(" >>\tError: size \'M\' is not allowed when \'-m all\' is selected")
            self.conf_param['n_rounds'] = aes_n_rounds[self.conf_param['aes_mode']]//2
        else:
            if self.conf_param['aes_mode'] == 'ALL':
                self.conf_param['n_rounds'] = aes_n_rounds['256']
            else:
                self.conf_param['n_rounds'] = aes_n_rounds[self.conf_param['aes_mode']]

        if self.args.rmexp != None or seed == None:
                self.conf_param['key_pre_exp'] = self.args.rmexp


    # ======================================================================================
    def cocotb_params(self):
        config  = ''
        config += ' COCOTB_LOG_LEVEL=' + self.conf_param['verbose']
        config += ' RANDOM_SEED=' + str(self.conf_param['seed'])
        config += ' SIM=' + self.conf_param['compiler']

        # Gui setting is not saved in the configuration file
        if self.args.gui != None:
            config += ' WAVE_ON=true'
            config += ' DUMP_FILENAME=' + self.basepath + 'tmp/' + self.args.gui + '.ghw'
        return config


    # ======================================================================================
    def save_configuration(self):
        # Save the verbosity
        store_verb = self.conf_param['verbose']

        # Do not save the verbosity
        del self.conf_param['verbose']

        if os.path.exists('./tmp') == False:
           os.system('mkdir -v tmp')

        with open(self.basepath + 'tmp/' + str(self.conf_param['seed']) + '.json', 'w') as config_file:
            json.dump(self.conf_param, config_file, indent=4)
            config_file.close()

        # Restore verbosity
        self.conf_param['verbose'] = store_verb


    # ======================================================================================
    def generate_templated_file(self):
        # Clean paths
        gen_rtl_path = str(self.basepath) + 'gen_rtl/'
        os.system('rm -rv '   + gen_rtl_path)
        os.system('mkdir -v ' + gen_rtl_path)

        # Generate the number of pipe stages in the round core file
        generate_aes_round( self.conf_param['pipes_in_core'],
                            gen_rtl_path)

        # Generate the aes_kexp file
        if self.conf_param['key_pre_exp'] == True:
            generate_aes_key = generate_aes_pre_exp_key
        else:
            generate_aes_key = generate_aes_kexp_logic

        generate_aes_key( self.conf_param['aes_mode'],
                          self.conf_param['n_rounds'],
                          gen_rtl_path)

        # Generate the ecb file
        generate_aes_ecb( self.conf_param['key_pre_exp'],
                          gen_rtl_path)

        # Generate the top entity file
        generate_aes_top( self.conf_param['aes_mode'],
                          self.conf_param['n_rounds'],
                          self.conf_param['pipes_in_core'],
                          self.conf_param['n_gfmul_ip']-1,
                          gen_rtl_path)

    # ======================================================================================
    def set_default_value(self, arg, seed, pname, value):
        # Set the default value for the configuration entry
        if arg != None or seed == None:
            if arg != None:
                self.conf_param[pname] = arg
            else:
                self.conf_param[pname] = value
