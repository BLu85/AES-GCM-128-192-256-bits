#!/usr/bin/python

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
                            version='v1.0', help="Show the script version.")

        self.parser.add_argument('-m', '--mode',
                            default=None, metavar='MODE', type = lambda s : s.upper(), choices=['128', '192', '256', 'ALL'],
                            help='Set the GCM mode: choose among 128 (default), 192, or 256.')

        self.parser.add_argument('-p', '--pipe',
                            type=int, default=None, metavar='N', choices=range(0, 8),
                            help='Set the number of pipe stages in the AES round core. E.g.: set -p 7 to get 3 pipe stages (maximum value).')

        self.parser.add_argument('-s', '--size',
                            default=None, metavar='SIZE', choices=['XS', 'S', 'M', 'L'],
                            help='Set the size of the GCM-AES IP. It defines the number of AES rounds:\
                            \nXS = 1 AES round instance,\nS = 2 AES round instances,\
                            \nM = AES round instances are half the number of rounds needed for the specific mode,\
                            \nL = AES round instances are equal to the number of rounds needed for the specific mode.')

        self.parser.add_argument('-x', '--rmexp',
                            action='store_true',
                            help='Remove the logic that expands the key. Expanded key has to be provided externally')

        if self.config_ip_only == True:
            return

        self.parser.add_argument('-c', '--compiler',
                            type=str,
                            help='Define the compiler')

        self.parser.add_argument('-k', '--key',
                            type=str, metavar='KEY',
                            help='Load a specific key')

        self.parser.add_argument('-i', '--iv',
                            type=str, metavar='IV',
                            help='Load a specific IV')

        self.parser.add_argument('-e', '--seed',
                            type=int, metavar='N',
                            help='Set the seed to re-run specific test conditions. N is an integer number')

        self.parser.add_argument('-g', '--gui',
                            type=str, nargs='?', const='aes_dump', metavar='file',
                            help='Start a GUI session. Signals are dumped in \'file\'.')

        self.parser.add_argument('-l', '--last-test',
                            action='store_true',
                            help='Re-run the last test. It will use the same test configuration and seed of the last test run.')

        self.parser.add_argument('-t', '--tsize',
                            default=None, metavar='SIZE', choices=['small', 'medium', 'big'],
                            help='Set the maximum number of byte that can be generated for the AAD and the PT: small (2^10-1), medium (2^20-1), big (2^32-1)')

        self.parser.add_argument('-d', '--verbose',
                            action='store_true',
                            help='increase output verbosity.')


    # ======================================================================================
    def test_config(self, basepath='./'):

        test_size = {   'small'  : 2**16 - 1,
                        'medium' : 2**24 - 1,
                        'big'    : 2**28 - 1}

        basepath = self.basepath + 'tmp/'

        if self.args.last_test == True:
            # Load the last test configuration and seed
            if os.path.exists(basepath):
                files = [f for f in os.listdir(basepath) if f.endswith('.json')]
                if len(files) != 1:
                    sys.exit(" >>\tError: there should be only one .json config file when arg \'-l\' is used")

                with open(basepath + files[0], 'r') as last_config_file:
                    self.conf_param = json.load(last_config_file)
                    last_config_file.close()
            else:
                sys.exit(" >>\tError: a test must be generated before calling arg \'-l\'. File .json has not been found")
        else:
            # Create a new configuration
            os.system('rm -rv ' + basepath)
            os.system('mkdir -v ' + basepath)

            # Create the seed
            seed = random.randint(0, 2**32 - 1)
            self.conf_param['seed'] = seed

        if self.args.tsize != None or self.args.last_test == False:
            if self.args.tsize != None:
                self.conf_param['test_size'] = self.args.tsize
            else:
                self.conf_param['test_size'] = 'small'

        self.conf_param['max_n_byte'] = test_size[self.conf_param['test_size']]

        if self.args.key != None or self.args.last_test == False:
            if self.args.key != None:
                if self.args.mode == 'ALL':
                    sys.exit(" >>\tError: Cannot supply a key when mode is set to ALL")
                if self.args.mode != str((len(self.args.key)//2)*8):
                    sys.exit(" >>\tError: AES mode and Key lenght don\'t match")
                self.conf_param['key'] = self.args.key
            else:
                self.conf_param['key'] = 'random'

        if self.args.iv != None or self.args.last_test == False:
            if self.args.iv != None:
                self.conf_param['iv'] = self.args.iv
            else:
                self.conf_param['iv'] = 'random'

        if self.args.compiler != None or self.args.last_test == False:
            if self.args.compiler != None:
                self.conf_param['compiler'] = self.args.compiler
            else:
                self.conf_param['compiler'] = 'ghdl'

        if self.args.verbose == True:
            self.conf_param['verbose'] = 'DEBUG'
        else:
            self.conf_param['verbose'] = 'INFO'

        if self.args.seed != None:
            self.conf_param['seed'] = self.args.seed

        return self.conf_param


    # ======================================================================================
    def gcm_ip_config(self):

        aes_n_rounds = {    '128' : 10,
                            '192' : 12,
                            '256' : 14}

        if self.config_ip_only == True:
            last_test = False
        else:
            last_test = self.args.last_test

        if self.args.size != None or last_test == False:
            if self.args.size != None:
                self.conf_param['aes_size'] = self.args.size
            else:
                self.conf_param['aes_size'] = 'XS'

        if self.args.mode != None or last_test == False:
            if self.args.mode != None:
                self.conf_param['aes_mode'] = self.args.mode
            else:
                self.conf_param['aes_mode'] = '128'

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

        if self.args.pipe != None or last_test == False:
            if self.args.pipe != None:
                self.conf_param['pipes_in_core'] = self.args.pipe
            else:
                self.conf_param['pipes_in_core'] = 0

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
        v = self.conf_param['verbose']

        # Do not save the verbosity
        del self.conf_param['verbose']

        with open(self.basepath + 'tmp/' + str(self.conf_param['seed']) + '.json', 'w') as config_file:
            json.dump(self.conf_param, config_file, indent=4)
            config_file.close()

        # Restore verbosity
        self.conf_param['verbose'] = v


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
                          gen_rtl_path)
