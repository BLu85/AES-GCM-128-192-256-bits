import gcm_utils as gu

if __name__ == "__main__":

    gen_base_path = '../src/'

    # Show args for the IP only
    conf = gu.aes_conf(gen_base_path)

    # Set the IP parameters
    conf.gcm_ip_config()

    # Generate the files from the python templates
    conf.generate_templated_file()

    # Write the parameter in the gcm top file
    print(' >>\tOK   : AES-GCM IP configured as:')
    for key, value in conf.conf_param.items():
        print(' >>\tOK   : ' + key + ':\t' + str(value))
