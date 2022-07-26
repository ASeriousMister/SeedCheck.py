# SeedCheck.py
SeedCheck.py is a Python tool that tries  to determinate the derivation path a mnemonic seed was used with.
It is part of the bigger project Anu₿itux: more info at https://anubitux.org.
V2 relased: now user is able to decide how many addresses to derive and check.

## Overview
It allows the user to insert a mnemonic seed with an eventual passphrase and generates addresses with many derivation algorithms.
After deriving the addresses, it tries to look them up using apis of public block explorers, to verify if they were involved in transactions and determinate the correct derivation path. This feature is optional because users may not trust public block explorers and prefer to look up addresses in a different way.

## Supported derivations
The tool supports the following coins with the indicated derivation paths:
### Bitcoin
- Electrum
--* Standard wallet
--* Segwit wallet
- BIP39
  * m/44'/0'/0'/0
  * m/44'/0'/0'/0' (hardened addresses)
  * m/49'/0'/0'/0
  * m/49'/0'/0'/0' (hardened addresses)
  * m/84'/0'/0'/0
  * m/84'/0'/0'/0' (hardened addresses)
  * m/84'/00/2147483645'/0'/0 (Samourai wallet Premix)
  * m/84'/00/2147483646'/0'/0 (Samourai wallet Postmix)
### Ethereum
- BIP39
  * m/44'/60'/0'/0
  * m/44'/60'/0'/0' (hardened addresses)
### Litecoin
- BIP39
  * m/44'/2'/0'/0
  * m/44'/2'/0'/0' (hardened addresses)
  * m/49'/2'/0'/0
  * m/49'/2'/0'/0' (hardened addresses)
  * m/84'/2'/0'/0
  * m/84'/2'/0'/0' (hardened addresses)
### Dash
- BIP39
  * m/44'/5'/0'/0
  * m/44'/5'/0'/0' (hardened addresses)
### ZCash
- BIP39
  * m/44'/133'/0'/0
  * m/44'/133'/0'/0' (hardened addresses)
### Monero
- Monero wallet (GUI or CLI)
- MyMonero wallet
- Feather wallet

## Installation
The tool was tested in Ubuntu 20.04 with Python3.8.
I suggest tu run the tool in his own virtual enviroment.
Python shoul be installed by default. If not so, update your repositories
```
sudo apt update
```
and type
```
sudo apt install python3
```
Then install pip, to easily install the dependencies
```
sudo apt install python3-pip
```
Now clone the github repository
```
git clone https://github.com/ASeriousMister/SeedCheck.py
```
and install python virtual enviroments
```
pip3 install virtualenv
```
Now move to SeedCheck.py's directory,
```
cd SeedCheck.py
```
create a virtual enviroment (in the example named scve, but you can choose your preferred name)
```
virtualenv scve
```
and activate it
```
source scve/bin/activate
```
The name of the virtual enviroment should appear, in brackets, on the left of your command line. 
Now you can install the dependencies
```
sudo apt install python3-pyqt5 libsecp256k1-0 python3-cryptography
pip3 install -r requirements.txt
```
Finally, you are ready to run the tool
```
python3 seedcheck.py
```
Sometimes pip may not install the packages listed in requirements.txt in the proper way.
In this case, just install the missing package shown in the error message with
```
pip3 install {missing_package_name}
```

## Additional tips
If you want to launch the tool as a single command in your terminal adding it to your PATH, you need to specify the tools folder changing the working directory of the tool in the seedcheck.py file. Go to line 16-17, edit the chdir command and uncomment it.

## Disclaimer
SeedCheck.py aims to help who finds a seed to determinate how it was used without the need of checking it with many clients. Of course, there are a lot of possibilities not handled by SeedCheck.py, so do not only rely of its output. There could be custom derivation paths used by skilled users or with some kind of client. The seed could also be related to different coins not checked by the tool.
When a derivation path is found, I suggest to try it with some kind of multicurrency client, because the mnemonic seed could derive addresses for many different coins.

## Read more
- [BIPs](https://github.com/bitcoin/bips)
- [Electrum wallet](https://github.com/spesmilo/electrum)
- [Monero](https://github.com/monero-project/monero)
- [HD wallet](https://pypi.org/project/hdwallet/)
- [Monero Python](https://monero-python.readthedocs.io/en/latest/)

## To do list
- add support for Electrum forks for different coin
- add support for Electrum Slip39
- add support for Taproot Bitcoin addresses
- check Monero addresses' activity
- add support to new Feather Wallet's seeds using Polyseed based on BIP 39


