# AES-GCM 128-192-256 bits

This repository contains a highly configurable encryption and decryption **AES-GCM** IP, using keys at 128, 192 or 256 bits.
The configuration parameters can be combined in order to obtain an IP that suits the user requirements.

## IP features
- 4 IP sizes:
  - _smallest_ IP configuration (12.8 bits/clk @ _key_ = 128)
  - _biggest_ IP configuration (128 bits/clk @ _key_ = Any)
- Key size: 128, 192, 256 bits
- Key expansion: the IP can expand the key or can receive a pre-expanded key
- Up to 3 pipeline stages can be inserted in order to help the timing closure and the place and route
- Configurable testbench with the possibility to add other tests

## Directory structure

    ├── config                  # Python scripts to configure the IP
    ├── src                     # Source files
    │   ├── vhdl                #   *.vhd only
    │   └── SystemVerilog       #   *.sv only (TBD)
    ├── tb                      # Cocotb tests and Makefile
    └── doc                     # Documentation files

## Requirements

### To produce the source files
* Python3.5+

### To run the testbench
* Python3.5+
* GHDL
* Cocotb (`pip install cocotb`)
* Cocotb-bus (`pip install cocotb-bus`)
* pycryptodome (`pip install pycryptodome`)
* progressbar (`pip install progress`)

## Quick start

This short section is for those who don't like to read the documentation and just want to play around or use the IP in some configuration.

### Run the IP configuration

Move first to the _config_ folder:
```
cd config
```
then run:
```
python gcm_config.py --mode 256 --size L --pipe 0
```
All the IP files have been exported in the folder _src_. To get **help** from the script, just run:
```
python gcm_config --help
```

### Run the testbench

Move first to the _tb_ folder:
```
cd tb
```
then run:
```
python gcm_testbench.py -m 128 -p 0 -s M -g
```

## IP description

The main sub-blocks that compose the **AES-GCM** IP are shown in the following figure.

![ip_blocks](doc/ip_blocks.png?style=centerme)

The **ECB** (**E**lectronic **C**ode**B**ook) is the block that contains the _AES_ algorithm and performs the transformation of the input data. The **ICB** (**I**nitial **C**ounter **B**lock) receives the 96-bits **IV** (**I**nitialization **V**ector) and concatenates it with the value of an internal 32-bits counter that is incremented at every clock. The LSb of the formed 128-bits vector corresponds to the LSb of the counter. This vector is supplied to the **ECB**. The input **Key** can be loaded pre-expanded or can be expanded internally. The expanded key stages are used to encrypt the 128-bits vectors incoming from the **ICB**. The encrypted data produced from the **ECB** are xor-ed with the incoming data.
The **GHASH** block receives the _**A**dditional **A**uthenticated **D**ata_ (**AAD**) and the _**C**ipher**T**ext_ (**CT**) and produces a **TAG** to authenticate the entire stream of encrypted data.
If the **AES-GCM** is set in encryption mode, the incoming data are treated as _**P**lain**T**ext_ (**PT**). In this case the **CT** data produced from the _xor_ operation are supplied to the **GHASH** block. Vice versa, if the **AES-GCM** is set in decryption mode, the incoming data are treated as **CT**. These data are directly supplied to the **GHASH** block (dashed line) and also to the _xor_ operator to produce the **PT** data.

### IP structure

    └── aes_gcm
        │
        ├── gcm_gctr
        │   │
        │   ├── aes_icb
        │   └── aes_ecb
        │       │
        │       ├── aes_kexp
        │       ├── aes_round
        │       └── aes_last_round
        │
        ├── gcm_ghash
        |   │
        |   └── ghash_gfmul
        │
        └── aes_enc_dec_ctrl

### IP blocks: short description

* **aes_gcm**: it is the top-module. It contains the blocks **gcm_gctr** and **gcm_ghash**.
* **gcm_gctr**: the module performs the encryption of the **ICB** vectors that are then _xor-ed_ with the incoming data. It is composed of the **aes_icb** and the **aes_ecb** blocks.
* **aes_icb**: it receives the **IV**, concatenates the value of the counter and supplies it to the **aes_ecb**.
* **aes_ecb**: it produces the encrypted version of the incoming **ICB** vectors using a pre-expanded **Key** or a **Key** expanded internally. The module contains the **aes_kexp**, the **aes_first_round** and a configurable number of **aes_round** sub-modules.
* **aes_kexp**: this module can receive the expanded **Key** stages or can receive the **Key** and perform its expansion. The key stages are supplied to the **aes_round**.
* **aes_round**: it performs one round of encryption. The user can set how many **aes_round** blocks to instantiate in order to increase performance or to save logic area and power. This option can be configured by setting the _aes ecb size_.
* **aes_last_round**: the module performs the last encryption round.
* **gcm_ghash**: the module receives the **AAD** and the **CT** and computes the **TAG** used to authenticate the message. It is composed of the **gcm_gf_mul** sub-module.
* **gcm_gf_mul**: the module performs the multiplication in a binary _Galois Field_.
* **aes_enc_dec_ctrl**: the module drives the _data valid_ signals for the  **GHASH** module.

## IP configuration

The **AES-GCM** IP can be configured in order to set the _AES_ key size, control the logic area used, tweak the data throughput and their latency.
To configure the **AES-GCM** IP the user has to type the command ```./gcm_config [OPTION]``` in the _config_ folder.
To know how the IP can be configured, run the command:
```
python gcm_config --help
```

The IP _parameters_ are discussed in the following sub-sections.

### Parameter: _mode_

This parameter sets the size of the key the **AES-GCM** IP is expecting to receive.
To set it, run the command:
```
python gcm_config -m MODE
```

where _MODE_ can be one of the following values: 128, 192 or 256.

**Example:** the following command sets the IP to receive keys of size 192-bits.
```
python gcm_config -m 192
```

### Parameter: _size_

This option sets the size of block **aes_ecb**. This module receives the **ICB** vectors and the **Key** stages and performs the _N_ rounds necessary to produce the encrypted data to xor with the incoming **PT** (**CT**) in order to obtain the **CT** (**PT**); _N_ can be 10, 12 or 14 for _AES_ modes equal to 128, 192 or 256-bits respectively.

![aes_core](doc/core.png?style=centerme)

This IP is composed of a number _k_ of **aes_round** instances. In order to meet the required performance in terms of throughput, area and power saving, the user can configure _k_ by running the following command:

```
python gcm_config -s SIZE
```

where _SIZE_ can get the values:
* **XS** (eXtra-Small):
  - _k_ = 1 **aes_round** IP,
  - _throughput_ = 12,8 bit/clk @ key = 128 bit
* **S** (Small):
  - _k_ = 2 **aes_round** IP,
  - _throughput_ = 25,6 bit/clk @ key = 128 bit
* **M** (Medium):
  - _k_ = _N_/2 **aes_round** IP,
  - _throughput_ = 64 bit/clk @ key = 128 bit
* **L** (Large):
  - _k_ = _N_ **aes_round** IP,
  - _throughput_ = 128 bit/clk @ key = 128, 192, 256 bit

#### One-way pipeline

If the **aes_ecb** size is set to **L** (_k_ = _N_) the **IV + counter** vectors, 128-bits wide, walk throughout the _k_ **aes_round** instances and are collected encrypted at the **aes_core** output. Input data can be injected into the pipeline as a continuous flow.

#### Loop-back pipeline

If the **aes_ecb** size is set to **XS**, **S** or **M**, the pipeline is composed of _k_ < _N_ **aes_round** instances. In these configurations, when the data arrive at the last **aes_round** instance, they are looped back at the beginning of the pipeline in order to be processed _N_ times. A multiplexer is inserted in order to select the new data or the data looped back from the last **aes_round** instance.

In both the configurations (_One-way_ or _Loop-back_ _pipeline_) back pressure can be applied at the end of the pipeline if the produced encrypted data are not consumed. Despite back pressure being applied, the data keep moving if the next stage in the pipeline is not busy and stalled. For example, in the case of a _One-Way pipeline_ configuration, if the last **aes_round** instance contains data that are not consumed, new data can still be injected at the beginning of the pipeline. They will travel inside the pipeline and will stop at the last but one **aes_round** instance, as the last is busy and stalled. When the entire pipeline if filled and the data are not consumed at its end, the back pressure is propagated up to the **ICB** module, in order to stop the counter.

**Example 1:** the following command sets the **AES-GCM** with key size of 256 bits and a number of **aes_round** instances equal to 7.
```
python gcm_config -m 256 -s M
```
**Example 2:** the following command sets the number of **aes_round** instances equal to 2, independently from the _mode_ (in this case the _mode_ will be 128 as this is the _default_ value when not explicited.)
```
python gcm_config -s S
```

### Parameter: _pipe_

This parameter sets the number of registered stages in each of the **aes_round** instances.
The figure below shows a single **aes_round** module.

![round_pipe_stages](doc/round_pipe.png?style=centerme)

It is composed of the blocks: _ByteSub_, _ShiftRow_, _MixColum_ and _AddRoundKey_. Each block perfoms purely combinatorial operations. The module output data are registered before being sent to the next **aes_round** instance. The first three block outputs can be singularly registered as well or can be fed directly into the next one in order to save logic and reduce the data latency. The user can decide which output to register by executing the command:

```
python gcm_config -p PIPE
```

where _PIPE_ is a 3 bits number, each of whom enables or disables a flip-flop vector to register the output of the first three blocks of the pipe. When a bit is set, the ouput of the corresponent block is registered.

**Example:** the following command adds a registered stage after the _MixColumn_ block:
```
python gcm_config -p 4
```
In binary 4 = '_100_', so the output of the block _MixColumn_ is registered.
It is worth notice that all the _MixColum_ blocks inside each of the **aes_round** instances in the **aes_ecb** module will have a registered output and the data latency will increase. So, if the user configures the **AES-GCM** for a 256-bits **Key** and a **aes_ecb** _size_ equal to **L**, there will be 14 **aes_round** instances. The latency of the entire pipeline will be 28 clock cycles, 2 for each **aes_round** instance.


## Timing diagrams

In this section timing diagram to perform a data encryption is shown.

![aes_gcm_timing_diagram](doc/aes_gcm_timing_diagram.png?style=centerme)

Steps to perfrom the data encryption are:
  1) **Key loading**: the **Key** must be left aligned in the _aes_gcm_key_word_i_ vector.
  2) **IV loading**: the **IV** can be loaded from the clock after _aes_gcm_key_val_i_ falling edge onwards.
  3) **Start IV counter**: it can be started while loading the **IV** or at any clock cycle after it.
  4) **Packet valid**: the signal _aes_gcm_ghash_pkt_val_i_ must be set while loading the **AAD** and the **PT** data. A falling edge of this signal triggers the calculation of the final **TAG**.
  5) **Load AAD**: when the _aes_gcm_ready_o_ is set, the **AAD** data can be loaded. Each set bit in the _aes_gcm_ghash_aad_bval_i_ vector indicates a valid byte in the _aes_gcm_ghash_aad_data_i_. The **AAD** data must be left aligned and contiguous inside the vector (E.g.: _aes_gcm_ghash_aad_bval_i_ = 0xF802 is not a accepted, as 1's are not contiguous. 0xF800 or 0xFFFF are accepted).
  6) **Load the PT**: the **PT** data can be loaded after the **AAD** data have been loaded. If there are no **AAD** data to load, the **PT** can be sent into the pipeline as soon as the **ICB** counter is started. Each set bit in the _aes_gcm_data_in_bval_i_ vector indicates a valid byte in the _gcm_data_in_data_i_. The **PT** data must be left aligned and contiguous inside the vector. The first **PT** data block can be loaded while the last **AAD** data block is loaded.
  7) **Get the CT**: when the signal _aes_gcm_data_out_val_o_ is valid, the **CT** can be read. Each set bit in the _aes_gcm_data_out_bval_i_ vector indicates a valid byte in the _aes_gcm_data_out_data_i_. In general a **CT** data block is ready on the next cycle of each loaded **PT** data block.
  9) **Get the TAG**: the **TAG** is produced 3 cycles after the _aes_gcm_ghash_pkt_val_i_ signal falling edge. The signal _aes_gcm_ghash_tag_val_o_ determines a valid **TAG**.

In order to feed the **AES-GCM** module with data to encrypt, the **IV** and the **Key** have to be loaded.


## How to configure the testbench

The testbench block diagram is shown in the picture below.

![aes_core](doc/tb.png?style=centerme)


The testbench uses **cocotb** to interact with the DUT.
The testbench shares the same parameters used to configure the IP and introduces a few more to run the tests.

The following command creates an **AES-GCM** DUT with a key size of 192-bits, 6 **aes_round** instances (_Medium_ size), 2 pipe stages registered (_ByteSub_, _MixColumn_) and load 500028340 as the seed test. It also saves the signals in file _aes_dump.ghw_ (```-g``` option).
```
python gcm_testbench.py -m 192 -p 5 -s M -e 500028340 -g
```

To re-run a specific test, the ```--seed``` parameter can be used:
```
python gcm_testbench.py -e 912237129 -s L
```

The parameters can be overridden when explicited (_-s L_ in the command above).

It is also possible to load a specific _key_, _iv_, _aad_ and _data_ stream. For example the test could be configured in a particular mode with a particular _key_:
```
python gcm_testbench.py -m 256 -k 92E11DCDAA866F5CE790FD24501F92509AACF4CB8B1339D50C9C1240935DD08B
```

or it can be tested with the [NIST test vectors](https://www.ieee802.org/1/files/public/docs2011/bn-randall-test-vectors-0511-v1.pdf) to check it returns the expected data:
```
python gcm_testbench.py -m 128 -k AD7A2BD03EAC835A6F620FDCB506B345 -d 08000F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A0002 -a D609B1F056637A0D46DF998D88E52E00B2C2846512153524C0895E81 -i 12153524C0895E81B2C28465
```

or

```
python gcm_testbench.py -m256 -k 691D3EE909D7F54167FD1CA0B5D769081F2BDE1AEE655FDBAB80BD5295AE6BE7 -d empty -a E20106D7CD0DF0761E8DCD3D88E5400076D457ED08000F101112131415161718191A1B1C1D1E1F202122232425262728292A2B2C2D2E2F303132333435363738393A0003 -i F0761E8DCD3D000176D457ED
```

The test seed is the name of the file with extension _.json_ located at the directory ```tb/tmp/```.
To show the other parameters, run the script with ```--help``` option.
At the end of the test the **cocotb** table reports the test result.


## Implementation results

The **AES-GCM** IP has been implemented on a *Xilinx xcku035-ffva1156-3*. The table below shows different test configurations:

| Test # | Mode    | Size  | # Pipe stages | Freq. [MHz]   | Throughput [MB/s]   | Key expansion logic |
|:------:|:-------:|:-----:|:-------------:|:-------------:|:-------------------:|:------------:|
| (1)    | 256     | L     | 0             | 100           | 1600                | Yes          |
| (2)    | 192     | L     | 0             | 100           | 1600                | Yes          |
| (3)    | 128     | L     | 0             | 100           | 1600                | Yes          |
| (4)    | 256     | XS    | 0             | 100           | 114                 | Yes          |
| (5)    | 128     | XS    | 0             | 125           | 200                 | Yes          |
| (6)    | 128     | XS    | 1             | 125           | 200                 | Yes          |
| (7)    | 128     | XS    | 0             | 125           | 200                 | No           |

The following table shows the results in terms of number of resurces occupied and slack for the tests shown in the previous table.

|Tests  | LUTs    | FFs    | WNS [ns] | WHS [ns] |
|:-----:| --------|:------:| ---------| ---------|
| (1)   | 26898   | 7025   | 0.522    | 0.013    |
| (2)   | 23978   | 5399   | 0.380    | 0.013    |
| (3)   | 22463   | 4029   | 0.232    | 0.013    |
| (4)   | 12935   | 1864   | 0.502    | 0.013    |
| (5)   | 12841   | 1608   | 0.550    | 0.013    |
| (6)   | 11918   | 1629   | 0.833    | 0.013    |
| (7)   | 11607   | 2831   | 1.191    | 0.013    |


## Authors

Luca Berghella

## License

All the files in this repository are licensed under [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Donate
[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=7UGKAU37P3Y48)

