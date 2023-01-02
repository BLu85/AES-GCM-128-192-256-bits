#!/usr/bin/python

import os
import sys
import argparse
import random
import cocotb

sys.path.append('../config/')
import gcm_utils as gu


if __name__ == "__main__":

    gen_base_path = './'

    # Show args for the IP and the testbench
    conf = gu.aes_conf(gen_base_path, False)

    if conf.args.wipe == True:
        conf.wipe_dir(gen_base_path + 'tmp/')

    for i in range(conf.args.n_test):

        # Randomise the IP paramters
        if conf.args.rand_param is True:
            conf.args.last_test = False
            if conf.args.mode == None:
                conf.args.mode  = random.choice(conf.ip_mode)
            if conf.args.pipe == None:
                conf.args.pipe  = random.choice(conf.ip_pipe)
            if conf.args.size == None:
                conf.args.size  = random.choice(conf.ip_size)
            if conf.args.tsize == None:
                conf.args.tsize = random.choice(conf.test_size)

        # Configure the test
        conf.test_config()

        # Configure the IP
        conf.gcm_ip_config()

        # Generate the files from the python templates
        conf.generate_templated_file()

        # Save the configuration parameters in the file _seed_.json
        conf.save_configuration()

        # Generate the parameters for the cocotb makefile and run the test
        a = os.system('make ' + conf.cocotb_params())
