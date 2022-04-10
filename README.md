# AES-GCM 128-192-256 bits

This repository contains a highly configurable **AES-GCM** IP, using keys at 128, 192 or 256 bits.
The configuration parameters can be combined so to obtain an IP that suits the user requirements.

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
    │   └── verilog             #   *.v only (TBD)
    ├── tb                      # Cocotb tests and Makefile
    └── doc                     # Documentation files

## Requirements

* GHDL
* Python3.5+
* Cocotb (`pip3 install cocotb`)
* Cocotb-bus (`pip3 install cocotb-bus`)
* pycryptodome (`pip3 install pycryptodome`)
* progressbar (`pip3 install progress`)

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

The **ECB** (**E**lectronic **C**ode**B**ook) is the block that contains the _AES_ algorithm and performs the transformation of the input data. The input **KEY** is internally expanded and its stages used for encryption. The **ICB** (**I**nitial **C**ounter **B**lock) receives the 96-bits **IV** (**I**nitialization **V**ector), concatenates the value of a 32-bit counter and supplies the 128-bits to the **ECB**. The counter is incremented at every clock. The encrypted data produced by the **ECB** are xor-ed with the incoming _**P**lain**T**ext_ (**PT**) data. The data produced by the _xor_ operation are the so called _**C**ipher**T**ext_ (**CT**).
The **GHASH** block receives the _**A**dditional **A**uthenticated **D**ata_ (**AAD**) and the **CT** and produces a **TAG** to authenticate the entire stream of encrypted data.

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
        └── gcm_ghash
            │
            └── ghash_gfmul

### IP blocks: short description

* **aes_gcm**: is the top-module and comtains blocks **gcm_gctr** and **gcm_ghash**.
* **gcm_gctr**: the module performs the encryption and produces the **CT** data. It is composed by the **aes_icb** and the **aes_ecb** blocks.
* **aes_icb**: it receives the **IV**, appends the value of the counter and supplies it as input to the **aes_ecb**.
* **aes_ecb**: it receives as inputs the **key** and the counter vector and produces its encrypted version. The module is composed by **aes_kexp**, **aes_first_round** and a configurable number of **aes_round** submodules.
* **aes_kexp**: this module can receive the expanded key stages or receive the **key** and perform its expansion. The key stages are supplied to the **aes_round**.
* **aes_round**: it performs one round of encryption. The user can decide how many **aes_round** blocks to instantiate in order to increase performance or to save logic area and power. This setting can be configured by setting the _aes ecb size_.
* **aes_last_round**: the module performs the last encryption round.
* **gcm_ghash**: the module receives the **AAD** and the **CT** and computes the **TAG** used to authenticate the message. It is composed by the **gcm_gf_mul** submodule.
* **gcm_gf_mul**: the module performs the multiplication in a binary _Galois Field_.

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

This option sets the size of block **aes_ecb**. This module receives the **PT** and the **key** stages and performs the _N_ rounds necessary to produce the **CT** , where _N_ can be 10, 12 or 14 for _AES_ modes equal to 128, 192 or 256-bits respectively.

![aes_core](doc/core.png?style=centerme)

This IP is composed by a number _k_ of **aes_round** instances. In order to meet the required performance in terms of throughput, area and power saving, the user can configure _k_ by running the following command:

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

If the **aes_ecb** size is set to **XS**, **S** or **M**, the pipeline is composed by _k_ < _N_ **aes_round** instances. In these configurations, when data arrive at the last **aes_round** instance, they are looped back at the beginning of the pipeline in order to be processed _N_ times. A multiplexer is inserted in order to select the new data or the data looped back from the last **aes_round** instance.


In both the configurations (_One-way_ or _Loop-back_ _pipeline_) backpressure can be applied at the end of the pipeline if the produced encrypted data are not consumed. Despite backpressure is applied, data keep moving if the next stage in the pipeline is not busy and stalled. So, for example, in the case of a _One-Way pipeline_ configuration, if the last **aes_round** instance contains data that are not consumed, new data can still be injected at the beginning of the pipeline. They will travel inside the pipeline and will stop at the last but one **aes_round** instance, as the last is busy and stalled. When the entire pipeline if filled and data are not consumed at its end, backpressure is propagated up to the **IV** module, in order to stop the counter.

**Example 1:** the following command sets the **AES-GCM** for keys of size 256 and a number of **aes_round** instances equal to 7.
```
python gcm_config -m 256 -s M
```
**Example 2:** the following command sets the number of **aes_round** instances equal to 2, independently from the _mode_ (in this case _mode_ will be 128 as this is the _default_ value if not explicited.)
```
python gcm_config -s S
```

### Parameter: _pipe_

This parameter sets the number of registered stages in each of the **aes_round** instances.
The figure below shows a single **aes_round** module.

![round_pipe_stages](doc/round_pipe.png?style=centerme)

It is composed by the blocks: _ByteSub_, _ShiftRow_, _MixColum_ and _AddRoundKey_. Each block perfoms purely combinatorial operations. The module output data are registered before being sent to the next **aes_round** instance. The first three block outputs can be singularly registered as well or can be fed directly into the next one in order to save logic and reduce the data latency. The user can decide which output to register by executing the command:

```
python gcm_config -p PIPE
```

where _PIPE_ is a number composed by 3 bits, each of whom enable or disable a flip-flop vector to register the output of the first three blocks of the pipe. When a bit is set ('1') the ouput of the corresponent block is registered.

**Example:** the following command adds a registered stage after the _MixColumn_ block:
```
python gcm_config -p 4
```
In binary 4 = '_100_', so the output of the block _MixColumn_ is registered.
It is worth notice that all the _MixColum_ blocks inside each of the **aes_round** instances in the **aes_ecb** module will have a registered output and the data latency will increase. So, if the user configures the **AES-GCM** for a 256-bits **key** and a **aes_ecb** _size_ equal to **L**, there will be 14 **aes_round** instances. The latency of the entire pipeline will be 28 clock cycles, 2 for each **aes_round** instance.


## Timing diagrams

In this section timing diagram to perform a data encryption is shown.

![aes_gcm_timing_diagram](doc/aes_gcm_timing_diagram.png?style=centerme)

Steps to perfrom the data encryption are:
  1) **Key loading**: Key must be left align in the _gcm_key_word_i_ vector.
  2) **IV loading**: IV can be loaded from the clock after _gcm_key_val_i_ falling edge onwards.
  3) **Start IV counter**: it can be started while loading the **IV** or at any clock cycle after it.
  4) **Packet valid**: signal _gcm_ghash_pkt_val_i_ must be high while loading **AAD** and **PT** data. A falling edge of this signal triggers the calculation of the final **TAG**.
  5) **Load AAD**: when the _gcm_cipher_ready_o_ is high, **AAD** data can be loaded. Each high bit in the _gcm_ghash_aad_bval_i_ vector indicates a valid byte in the _gcm_ghash_aad_data_i_. **AAD** data must be left align and contiguous inside the vector (E.g.: _gcm_ghash_aad_bval_i_ = 0xF802 is not a accepted, as 1's are not contiguos. 0xF800 or 0xFFFF are accepted.)
  6) **Load PT**: **PT** data can be loaded after **AAD** data have been loaded. If there are no **AAD** data to load, **PT** can be sent into the pipeline as soon as **IV** counter is started. Each high bit in the _gcm_plain_text_bval_i_ vector indicates a valid byte in the _gcm_plain_text_data_i_. **PT** data must be left align and contiguous inside the vector. The first **PT** data block can be loaded while the last **AAD** data block is loaded.
  7) **Get CT**: when signal _gcm_cipher_text_val_o_ is valid, **CT** can be read. Each high bit in the _gcm_cipher_text_bval_i_ vector indicates a valid byte in the _gcm_cipher_text_data_i_. In general, a **CT** data block is ready on the next cycle of each loaded **PT** data block.
  9) **Get TAG**: The **TAG** is produced 3 cycles after the _gcm_ghash_pkt_val_i_ signal falling edge. Signal _gcm_ghash_tag_val_o determines a valid **TAG**.

In order to feed the **AES-GCM** module with data to encrypt, the **IV** and the **Key** have to be loaded.


## How to configure the testbench

The testbench block diagram is shown in the picture below.

![aes_core](doc/tb.png?style=centerme)


The testbench uses **cocotb** to interact with the DUT.
The testbench shares the same parameters used by the configuration script and introduces a few more to run the tests.

The following command creates an **AES-GCM** DUT with a key size of 192-bits, 6 **aes_round** instances (_Medium_ size), 2 pipe stages registered (_ByteSub_, _MixColumn_) and load 500028340 as the seed test. It also saves the signals in file _aes_dump.ghw_ (```-g``` option).
```
python gcm_testbench.py -m 192 -p 5 -s M -e 500028340 -g
```

To re-run the test, the ```--last-test``` parameter can be used:
```
python gcm_testbench.py -l
```
To show the other parameters, run the script with ```--help``` option.
At the end of the test the **cocotb** table reports tests that passed or failed.


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
[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate?hosted_button_id=YVAFM39DE9UTL)

