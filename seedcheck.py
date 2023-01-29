#!/usr/bin/env python3

from electrum import bitcoin
from electrum import keystore
from electrum import mnemonic
import urllib.request
import requests
import json
from hdwallet import HDWallet
from hdwallet.symbols import BTC, ETH, LTC, ZEC, DASH
import blockcypher
import os
import time
from hdwallet.symbols import BTC
from hdwallet.utils import is_mnemonic

#Editi this line if you need to use a specific working directory
#os.chdir('/home/working_path')

blockcypherAPI = None   # if available, put your blockcypher API key here

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# check if online or apis will not be available
def is_connected(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False


def check_lang(mnemo_word):
    f = open('Wordlists/b39en')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'english'
    f = open('Wordlists/elen')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'english'
    f = open('Wordlists/b39it')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'italian'
    f = open('Wordlists/b39cn')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'chinese_traditional'
    f = open('Wordlists/elcn')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'chinese_traditional'
    f = open('Wordlists/b39cn2')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'chinese_simplified'
    f = open('Wordlists/b39cz')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'czech'
    f = open('Wordlists/b39es')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'spanish'
    f = open('Wordlists/b39fr')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'french'
    f = open('Wordlists/b39jp')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'japanese'
    f = open('Wordlists/b39kr')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'korean'
    f = open('Wordlists/b39pr')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'portuguese'
    f = open('Wordlists/eles')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'spanish'
    f = open('Wordlists/eljp')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'japanese'
    f = open('Wordlists/elpr')
    if ('\n' + mnemo_word + '\n') in f.read():
        f.close()
        return 'portuguese'

def electrum_derive(seedl, passw, address_index, dertype):
    # derives addresses with electrum's derivation
    change = False
    is_p2sh = False
    k = keystore.from_seed(seedl, passw, is_p2sh)  # '' for passphrase
    l = k.derive_pubkey(change, address_index)
    if dertype == 'p2wpkh':
        addr = bitcoin.public_key_to_p2wpkh(l)
        return addr
    elif dertype == 'p2pkh':
        addr = bitcoin.public_key_to_p2pkh(l)
        return addr
#    elif dertype == 'p2wpkh-p2sh':      implement


def electrum_change_derive(seedl, passw, address_index, dertype):
    # derives addresses with electrum's derivation
    change = True
    is_p2sh = False
    k = keystore.from_seed(seedl, passw, is_p2sh)  # '' for passphrase
    l = k.derive_pubkey(change, address_index)
    if dertype == 'p2wpkh':
        addr = bitcoin.public_key_to_p2wpkh(l)
        return addr
    elif dertype == 'p2pkh':
        addr = bitcoin.public_key_to_p2pkh(l)
        return addr
#    elif dertype == 'p2wpkh-p2sh':      implement


print(color.YELLOW + '\n=====================\n===   SeedCheck   ===\n=====================\n' + color.END)
print('The tool tries to identify how a mnemonic phrase has been used to generate a ')
print('crypto wallet. It checks if the seed was used with Electrum (BTC) or if it was used')
print('with a wallet using a BIP39 wordlist or if it was used with a Monero wallet.')
print('It is also able to check online if the addresses have been used to determinate which')
print('derivation path was used with the given seed. It supports BIP44, BIP49 and BIP84 derivation')
print('(also for Samourai postmix wallets). It checks BTC, ETH, LTC, DASH and ZEC')
print('with Monero it tries to determinate if the seed is associated with a Monero wallet,')
print('a MyMonero wallet or a Feather wallet')
print(color.RED + '\nDISCLAIMER:' + color.END + ' This tool is designed to help identifying a mnemonic seed but it should not be ')
print('considered as exhaustive. Always check the seeds with many wallets to be sure about them')
print('\nPlease use only correct inputs. This tool was designed for serious persons\n')

# Check if connection is available and ask user for authorisation to query APIs
conn = is_connected()
if conn:
    print(color.GREEN + 'Internet connection is available' + color.END)
    print('the tool will query apis about found addresses')
    tour0 = True
    while tour0:
        agree = input('do you agree with that? (y/n)\n')
        if agree == 'y':
            print('Addresses will be checked\n')
            online_check = True
            tour0 = False
        elif agree == 'n':
            print('addresses will not be checked\n')
            online_check = False
            tour0 = False
        else:
            print(color.RED + '\nUnallowed answer, closing!\n' + color.END)
else:
    print(color. RED + 'Internet connection is not available' + color.END)
    print('Found addresses will not be checked\n')
    online_check = False

seed_str = input(color.DARKCYAN + 'Please paste (Ctrl + Shift + V) or type mnemonic to check (excluding passphrase)\n' + color.END)
seed_l = seed_str.split(' ')
language = check_lang(seed_l[0])
language1 = check_lang(seed_l[-1])
lang_false = False # to use to handle exit if language check fails
if language == language1:
    print(color.GREEN + f'Detected {language} language' + color.END)
else:
    print(color.RED + 'could not detect language' + color.END)
    lang_false = True
wn = len(seed_l) # words number, length of the mnemonic
if wn == 25:
    print(color.GREEN + 'seed could have been used with Monero Wallet (GUI or CLI)' + color.END)
elif wn == 13:
    print(color.GREEN + 'seed could have been used with MyMonero' + color.END)
elif wn == 14 and seed_l[1] == 'poem':
    print(color.GREEN + 'seed could have been used with Feather Wallet 1.x' + color.END)
elif wn == 16:
    print(color.GREEN + 'seed could have been used with Feather Wallet 2.x' + color.END)
elif wn % 3 != 0:
    exit(color.RED + 'Something seems to be wrong with the number of words' + color.END)

if lang_false:
    exit()

# Check if provided mnemonic is valid as BIP39 mnemonic or Electrum mnemonic
electrum_type = mnemonic.seed_type(seed_str)
is_electrum = False
if electrum_type == 'segwit':
    print(color.GREEN + 'The provided mnemonic is related to and Electrum segwit wallet' + color.END)
    is_electrum = True
if electrum_type == 'standard':
    print(color.GREEN + 'The provided mnemonic is related to and Electrum legacy wallet' + color.END)
    is_electrum = True
    
if (is_electrum == False and language == 'portuguese') or (language == 'czech'):
    exit(color.RED + f'Sorry, {language} is not supported at the moment :(' + color.END)
    
is_bip39 = is_mnemonic(seed_str, language)
if is_bip39:
    print(color.GREEN + 'The provided mnemonic respects the BIP39 standard' + color.END)
    
if (is_bip39 is False) and (is_electrum is False):
    exit(color.RED + 'The provided mnemonic phrase is not valid' + color.END)

# How many addresses does user want to print and check
print(color.DARKCYAN + 'How many addresses do you want to check for each derivation path?' + color.END)
tour1 = True
while tour1:
    der = input()
    if der.isdigit():
        tour1 = False
        der = int(der)
        if der > 15:
            der = 15
            print(color.YELLOW + 'Sorry! Value has been set to 15 to avoid overloading APIs and reduce execution time' + color.END)
            print('Please comment this lines if you have an API key available')
        elif der < 1:
            der = 1
            print(color.YELLOW + 'Minimum value is 1! Your answer has been set to 1' + color.END)
    else:
        print(color.RED + 'Only numbers allowed! Try again' + color.END)

print(color.DARKCYAN + 'Do you want to add a passphrase to your mnemonic? (y/n)' + color.END)
tour2 = True
while tour2:
    ans = input()
    if ans.lower() == 'y':
        passphr = input(color.DARKCYAN + 'Enter passphrase: ' + color.END)
        tour2 = False
    elif ans.lower() == 'n':
        tour2 = False
        passphr = ''
    else:
        print(color.RED + 'Please type y for yes or n for no' + color.END)

# create list of addresses from the BIP39 mnemonic phrase
btc_list = []
eth_list = []
ltc_list = []
dash_list = []
zec_list = []
elec_addr = []
if is_bip39:
    # Bitcoin derivation
    index = 0
    print(color.GREEN + '=== BITCOIN ADDRESSES ===' + color.END)
    print(color.CYAN + '+++ Legacy BIP44 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=BTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path(f"m/44'/0'/0'/0/{str(index)}")
        btc_list.append(hdwallet.p2pkh_address())
        print(btc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=BTC) # add first change address
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path(f"m/44'/0'/0'/1/0")
    btc_list.append(hdwallet.p2pkh_address())
    print('First change address: ' + btc_list[-1])
    index = 0
    print(color.CYAN + '+++ Segwit BIP49 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=BTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path(f"m/49'/0'/0'/0/{str(index)}")
        btc_list.append(hdwallet.p2wpkh_in_p2sh_address())
        print(btc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=BTC) # add first change address
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path(f"m/49'/0'/0'/1/0")
    btc_list.append(hdwallet.p2wpkh_in_p2sh_address())
    print('First change address: ' + btc_list[-1])
    index = 0
    print(color.CYAN + '+++ Native segwit BIP84 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=BTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path(f"m/84'/0'/0'/0/{str(index)}")
        btc_list.append(hdwallet.p2wpkh_address())
        print(btc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=BTC) # add first change address
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path(f"m/84'/0'/0'/1/0")
    btc_list.append(hdwallet.p2wpkh_address())
    print('First change address: ' + btc_list[-1])
    index = 0
    print(color.CYAN + '+++ Native segwit BIP84 (Samourai postmix) +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=BTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/84'/0'/0'/0/" + str(2147483646 + index)) # Samourai postmix
        btc_list.append(hdwallet.p2wpkh_address())
        print(btc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=BTC) # add first change address
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path(f"m/84'/0'/0'/1/2147483646")
    btc_list.append(hdwallet.p2wpkh_address())
    print('First change address: ' + btc_list[-1])

    # Ethereum derivation
    index = 0
    print(color.GREEN + '=== ETHEREUM ADDRESSES ===' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=ETH)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/44'/60'/0'/0/" + str(index))
        eth_list.append(hdwallet.p2pkh_address())
        print(eth_list[-1])
        index += 1

    # Litecoin derivation
    index = 0
    print(color.GREEN + '=== LITECOIN ADDRESSES ===' + color.END)
    print(color.CYAN + '+++ Legacy BIP44 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=LTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/44'/2'/0'/0/" + str(index))
        ltc_list.append(hdwallet.p2pkh_address())
        print(ltc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=LTC)
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path("m/44'/2'/0'/1/0")
    ltc_list.append(hdwallet.p2pkh_address())
    print('First change address: ' + ltc_list[-1])
    index = 0
    print(color.CYAN + '+++ Segwit BIP49 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=LTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/49'/2'/0'/0/" + str(index))
        ltc_list.append(hdwallet.p2wpkh_in_p2sh_address())
        print(ltc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=LTC)
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path("m/49'/2'/0'/1/0")
    ltc_list.append(hdwallet.p2wpkh_in_p2sh_address())
    print('First change address: ' + ltc_list[-1])
    index = 0
    print(color.CYAN + '+++ Native segwit BIP84 +++' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=LTC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/84'/2'/0'/0/" + str(index))
        ltc_list.append(hdwallet.p2wpkh_address())
        print(ltc_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=LTC)
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path("m/84'/2'/0'/1/0")
    ltc_list.append(hdwallet.p2wpkh_address())
    print('First change address: ' + ltc_list[-1])

    # Dash derivation
    index = 0
    print(color.GREEN + '=== DASH ADDRESSES ===' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=DASH)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/44'/5'/0'/0/" + str(index))
        dash_list.append(hdwallet.p2pkh_address())
        print(dash_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=DASH)
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path("m/44'/5'/0'/1/0")
    dash_list.append(hdwallet.p2pkh_address())
    print('First change address: ' + dash_list[-1])

    # Zcash derivation
    index = 0
    print(color.GREEN + '=== ZCASH ===' + color.END)
    while index < der:
        hdwallet: HDWallet = HDWallet(symbol=ZEC)
        hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
        hdwallet.from_path("m/133'/60'/0'/0/" + str(index))
        zec_list.append(hdwallet.p2pkh_address())
        print(zec_list[-1])
        index += 1
    hdwallet: HDWallet = HDWallet(symbol=ZEC)
    hdwallet.from_mnemonic(mnemonic=seed_str, passphrase=passphr, language=language)
    hdwallet.from_path("m/133'/60'/0'/1/0")
    zec_list.append(hdwallet.p2pkh_address())
    print('First change address: ' + zec_list[-1])

# create list of addresses from the electrum mnemonic phrase
if is_electrum:
    print(color.GREEN + '=== Electrum Bitcoin addresses ===' + color.END)
    if electrum_type == 'segwit':
        index = 0
        print(color.GREEN + 'Found Electrum addresses:' + color.END)
        while index < der:
            elec_addr.append(electrum_derive(seed_str, passphr, index, 'p2wpkh'))
            print(elec_addr[index])
            index += 1
        elec_addr.append(electrum_change_derive(seed_str, passphr, index, 'p2wpkh'))
        print('First change address: ' + elec_addr[-1])
    elif electrum_type == 'standard':
        index = 0
        while index < der:
            elec_addr.append(electrum_derive(seed_str, passphr, index, 'p2pkh'))
            print(elec_addr[index])
            index += 1
        elec_addr.append(electrum_change_derive(seed_str, passphr, index, 'p2pkh'))
        print('First change address: ' + elec_addr[-1])

# Check addresses online
online_found = False  # if True address was found used and a message will be shown
elec_found = False
if online_check:
    if is_bip39 == True:
        print(color.DARKCYAN + '\nchecking bip39 derived addresses online' + color.END)
    # check BTC
    i = 0
    while i < len(btc_list):
        link = 'https://blockchain.info/q/addressfirstseen/' + btc_list[i]
        time.sleep(400/1000)
        used = requests.get(link)
        data = used.text    # gives a string
        if data != '0':
            if i < (der + 1):
                print(color.GREEN + '--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0 ---' + color.END)
                i = der + 1
            elif i < ((der + 1) * 2):
                print(color.GREEN + '--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0\' ---' + color.END)
                i = (der + 1) * 2
            elif i < ((der + 1) * 3):
                print(color.GREEN + '--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0 ---' + color.END)
                i = (der + 1) * 3
            elif i < ((der + 1) * 4):
                print(color.GREEN + '--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0\' ---' + color.END)
                i = (der + 1) * 4
        i += 1
    # check ETH
    i = 0
    while i < len(eth_list):
        link = 'https://api.blockcypher.com/v1/eth/main/addrs/' + eth_list[i]
        eth_resp = requests.get(link)
        time.sleep(400/1000)
        eth_resp = eth_resp.text
        eth_resp_dict = json.loads(eth_resp)
        if eth_resp_dict['n_tx'] != 0:
            online_found = True
            print(color.GREEN + '--- The given seed was used to derive Ethereum addresses with derivation path m/44\'/60\'/0\'/0 ---' + color.END)
            break
        i += 1

    # check LTC
    i = 0
    while i < len(ltc_list):
        ltc_tx = blockcypher.get_total_num_transactions(ltc_list[i], coin_symbol='ltc', api_key=blockcypherAPI)
        if blockcypherAPI is None:
            time.sleep(400/1000)
        if ltc_tx != 0:
            online_found = True
            if i < (der + 1):
                print(color.GREEN + '--- The given seed was used to derive Litecoin addresses with derivation path m/44\'/2\'/0\'/0 ---' + color.END)
                i = (der + 1)
            elif i < ((der + 1) * 2):
                print(color.GREEN + '--- The given seed was used to derive Litecoin addresses with derivation path m/49\'/2\'/0\'/0 ---' + color.END)
                i = ((der + 1) * 2)
            elif i < ((der + 1) * 3):
                print(color.GREEN + '--- The given seed was used to derive Litecoin addresses with derivation path m/84\'/2\'/0\'/0 ---' + color.END)
                i = (der + 1) * 3
        else:
            i += 1
    # Check DASH
    i = 0
    while i < len(dash_list):
        dash_tx = blockcypher.get_total_num_transactions(dash_list[i], coin_symbol='dash', api_key=blockcypherAPI)
        if blockcypherAPI is None:
            time.sleep(400/1000)
        if dash_tx != 0:
            online_found = True
            print(color.GREEN + '--- The given seed was used to derive Dash addresses with derivation path m/44\'/5\'/0\'/0 ---' + color.END)
            break
        else:
            i += 1
    # Check ZEC
    i = 0
    while i < len(zec_list):
        link = 'https://api.zcha.in/v2/mainnet/accounts/' + zec_list[i]
        zec_resp = requests.get(link)
        time.sleep(400/1000)
        zec_resp = zec_resp.text
        zec_resp_dict = json.loads(zec_resp)
        if zec_resp_dict['firstSeen'] != 0:
            online_found = True
            print(color.GREEN + '--- The given seed was used to derive ZCash addresses with derivation path m/44\'/133\'/0\'/0 ---' + color.END)
            break
        else:
            i += 1

    # check Electrum BTC addresses
    i = 0
    if len(elec_addr) > 0:
        print(color.DARKCYAN + '\nchecking Electrum derived addresses online' + color.END)
    while i < len(elec_addr):
        link = 'https://blockchain.info/q/addressfirstseen/' + elec_addr[i]
        time.sleep(400 / 1000)
        used = requests.get(link)
        data = used.text  # gives a string
        if data != '0':
            print(color.GREEN + '--- The given seed has been used with an Electrum Bitcoin wallet ---' + color.END)
            elec_found = True
            break
        i += 1

if (online_found == False and is_bip39 == True):
    print(color.RED + 'Bip39 derivation path not found')
    print('Maybe you should try with some multi-currency desktop wallet or with some custom derivation path or adding a passphrase' + color.END)

if (elec_found == False and is_electrum == True):
    print(color.RED + 'The seed is related to an Electrum wallet but seems to be unused')
    print('Maybe you should try it with some altcoin Electrum version' + color.END)
    
