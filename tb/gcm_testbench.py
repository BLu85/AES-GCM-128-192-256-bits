#!/usr/bin/python

import os
import sys
import argparse

sys.path.append('../config/')
import gcm_utils as gu


if __name__ == "__main__":

    gen_base_path = './'
    gen_tmp_path  = gen_base_path + 'tmp/'

    # Show args for the IP and the testbench
    conf = gu.aes_conf(gen_base_path, False)

    # Configure the test
    conf.test_config()

    # Configure the IP
    conf.gcm_ip_config()

    # Generate the files from the python templates
    conf.generate_templated_file()

    # Save the configuration parameters in the file _seed_.json
    conf.save_configuration()

    # Generate the parameters for the cocotb makefile and run the test
    os.system('make ' + conf.cocotb_params())

