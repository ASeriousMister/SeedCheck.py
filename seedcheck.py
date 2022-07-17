#!/usr/bin/env python3
from electrum import bitcoin
from electrum import keystore
from electrum import mnemonic
import urllib.request
import requests
import json
from hdwallet import BIP44HDWallet, BIP84HDWallet, BIP49HDWallet, HDWallet
from hdwallet.cryptocurrencies import BitcoinMainnet, EthereumMainnet, LitecoinMainnet, ZcashMainnet, DashMainnet
from hdwallet.utils import generate_mnemonic, is_mnemonic
from hdwallet.symbols import BTC, ETH, LTC, ZEC, DASH
import blockcypher
from monero.seed import Seed
import os

#Editi this line if you need to use a specific working directory
#os.chdir('/home/working_path')


# checks if given seed's words are in the available wordlist
def checklist(path, lenght, language, kind, seedl):
    f = open(path, 'r')
#    print(f'===Starting with {kind} {language} wordlist===')
    it = 0
    while (it < lenght):
        f.seek(0)
        if seedl[i] in f.read():
            it += 1
            if (it == lenght):
                f.close()
                return True
        else:
            f.close()
            return False


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

#returns address receiving coin as sym, language, seed, passphrase, bip version, coin number, address index and if address is hardened


def add_der(sym, lang, seedl, psph, bip, coin, num, is_hardened):
    hdwallet: HDWallet = HDWallet(symbol=sym)
    hdwallet.from_mnemonic(mnemonic=seedl, passphrase=psph, language=lang)
    hdwallet.from_index(bip, hardened=True)
    hdwallet.from_index(coin, hardened=True)
    hdwallet.from_index(0, hardened=True)
    hdwallet.from_index(0)
    hdwallet.from_index(num, hardened=is_hardened)
    if bip == 44:
        return hdwallet.p2pkh_address()
    if bip == 84:
        return hdwallet.p2wpkh_address()
    if bip == 49:
        return hdwallet.p2wpkh_in_p2sh_address()


# uses custom derivation paths used by samourai wallet
def sam_der(lang, seedl, psph, mix, num, is_hardened):
    hdwallet: HDWallet = HDWallet(symbol=BTC)
    hdwallet.from_mnemonic(mnemonic=seedl, passphrase=psph, language=lang)
    hdwallet.from_index(84, hardened=True)
    hdwallet.from_index(0, hardened=True)
    # sam premix= 2147483645' postmix= 2147483646'
    hdwallet.from_index(mix, hardened=True)
    hdwallet.from_index(0)
    hdwallet.from_index(num, hardened=is_hardened)
    return hdwallet.p2wpkh_address()


# check if online or apis will not be available
def is_connected(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False


# Creates list with addresses derived in the specifued language
def btc_list_der(lang, how_many):
    btc_list = []
    # bitcoin bip44 not hardened addresses
#    btc_list.append('---> BITCOIN BIP44 ADDRESSES <---')
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 44, 0, index, False))
        index += 1
    # bitcoin bip44 hardened addresses
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 44, 0, index, True))
        index += 1
    # bitcoin bip49 not hardened addresses
#    btc_list.append('---> BITCOIN BIP49 ADDRESSES <---')
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 49, 0, index, False))
        index += 1
    # bitcoin bip49 hardened addresses
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 49, 0, index, True))
        index += 1
    # bitcoin bip84 not hardened addresses
#    btc_list.append('---> BITCOIN BIP84 ADDRESSES <---')
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 84, 0, index, False))
        index += 1
    # bitcoin bip84 hardened addresses
    index = 0
    while index < how_many:
        btc_list.append(add_der(BTC, lang, seed_str, passphrase, 84, 0, index, True))
        index += 1
    # sam premix= 2147483645' postmix= 2147483646'
#    btc_list.append('---> BITCOIN SAMOURAI WALLET PREMIX ADDRESSES <---')
    index = 0
    while index < how_many:
        btc_list.append(sam_der(lang, seed_str, passphrase, 2147483645, index, False))
        index += 1
#    btc_list.append('---> BITCOIN SAMOURAI WALLET POSTMIX ADDRESSES <---')
    index = 0
    while index < how_many:
        btc_list.append(sam_der(lang, seed_str, passphrase, 2147483646, index, False))
        index += 1
    return btc_list
    
    
def eth_list_der(lang, how_many):    
    eth_list = []
    # ethereum bip44 not hardened addresses
    index = 0
    while index < how_many:
        eth_list.append(add_der(ETH, lang, seed_str, passphrase, 44, 0, index, False))
        index += 1
    # ethereum bip44 hardened addresses
    index = 0
    while index < how_many:
        eth_list.append(add_der(ETH, lang, seed_str, passphrase, 44, 0, index, True))
        index +=1
    return eth_list


def ltc_list_der(lang, how_many):
    ltc_list = []
    # litecoin bip44 not hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 44, 0, index, False))
        index += 1
    # litecoin bip44 hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 44, 0, index, True))
        index += 1
    # litecoin bip49 not hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 49, 0, index, False))
        index += 1
    # litecoin bip49 hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 49, 0, index, True))
        index += 1
    # litecoin bip84 not hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 84, 0, index, False))
        index += 1
    # litecoin bip84 hardened addresses
    index = 0
    while index < how_many:
        ltc_list.append(add_der(LTC, lang, seed_str, passphrase, 84, 0, index, True))
        index += 1
    return ltc_list


def dash_list_der(lang, how_many):    
    dash_list = []
    # dash bip44 not hardened addresses
    index = 0
    while index < how_many:
        dash_list.append(add_der(DASH, lang, seed_str, passphrase, 44, 0, index, False))
        index += 1
    # dash bip44 hardened addresses
    index = 0
    while index < how_many:
        dash_list.append(add_der(DASH, lang, seed_str, passphrase, 44, 0, index, True))
        index +=1
    return dash_list


def zec_list_der(lang, how_many):    
    zec_list = []
    # ethereum bip44 not hardened addresses
    index = 0
    while index < how_many:
        zec_list.append(add_der(ZEC, lang, seed_str, passphrase, 44, 0, index, False))
        index += 1
    # ethereum bip44 hardened addresses
    index = 0
    while index < how_many:
        zec_list.append(add_der(ZEC, lang, seed_str, passphrase, 44, 0, index, True))
        index +=1
    return zec_list


print('\n=====================\n===   SeedCheck   ===\n=====================\n')
print('The tool tries to identify how a mnemonic phrase has been used to generate a ')
print('crypto wallet. It checks if the seed was used with Electrum (BTC) or if it was used')
print('with a wallet using a BIP39 wordlist or if it was used with a Monero wallet.')
print('It is also able to check online if the addresses have been used to determinate which')
print('derivation path was used with the given seed. It supports BIP44, BIP49 and BIP84 derivation')
print('(also for Samourai premix and postmix wallets). It checks BTC, ETH, LTC, DASH and ZEC')
print('with Monero it tries to determinate if the seed is associated with a Monero wallet,')
print('a MyMonero wallet or a Feather wallet')
print('\nDISCLAIMER: This tool is designed to help identifying a mnemonic seed but it should not be ')
print('considered as exhaustive. Always check the seeds with many wallets to be sure about them')
print('\nPlease use only correct inputs. This tool was designed for serious persons\n')


conn = is_connected()
if conn:
    print('Internet connection is available')
    print('the tool will query apis about found addresses')
    agree = input('do you agree with that? (y/n)\n')
    if agree == 'y':
        print('Addresses will be checked\n')
        online_check = True
    elif agree == 'n':
        print('addresses will not be checked\n')
        online_check = False
    else:
        print('\nunallowed answer, closing!\n')
        quit()
else:
    print('Internet connection is not available')
    print('Found addresses will not be checked\n')
    online_check = False

leng = input('Enter seed lenght (without counting the passphrase): ')
s_lenght = int(leng)
seed = []  # stores the seed as a list
i = 0
p = 0  # stores 1 if seed has a passphrase
while(i < s_lenght):
    i += 1
    w = input(f'Insert the {i} word: ')
    seed.append(w)
ans = input('Does the seed have a passphrase?(y/n)\n')
if (ans == 'y' or ans == 'Y'):
    passphrase = input('Insert passphrase: ')
    p = 1
elif (ans == 'n' or ans == 'N'):
    passphrase = ''
    print('Proceding without passphrase')
else:
    print('No correct answer provided, proceding without passphrase')
    passphrase = ''
lan = input(
    'What is the language of the seed? (if unknown type all)\nfor spaces use _\n')
lan.lower()  # makes the string lowercase to make it easier to check only correct wordlists
seed_str = ' '.join(seed)
# Define how many addresses to derive and check online
how_many = input('how many addresses do you want to be derived?\n')
how_many = int(how_many)
if (how_many > 15 and online_check == True):
    print('You are going to check a lot of addresses. This could overload APIs.')
    over = input('do you want to continue? If no, seedcheck will derive 15 addresses for each type.\n(y/n)?: ')
    if (over == 'y' or over == 'Y'):
        print(f'SeedCheck is going to derive {how_many} addresses')
    elif (over == 'n' or over == 'N'):
        print('Seedcheck is going to derive 15 addresses for each type')
    else:
        print('No correct answer provided! Seedcheck is going to derive 15 addresses for each type')

print('STARTING THE CHECK\nProvided seed: ', seed_str)
if (p == 1):
    print(f'where {passphrase} is the passphrase')


# Declaring wordlist related variables
is_bip39cn = False
is_bip39cz = False
is_bip39en = False
is_bip39es = False
is_bip39fr = False
is_bip39it = False
is_bip39jp = False
is_bip39kr = False
is_bip39pr = False
is_bip39cn2 = False
is_bip39 = False  # used to decide if run api
is_electrumcn = False
is_electrumen = False
is_electrumes = False
is_electrumjp = False
is_electrumpr = False
is_electrum = False  # used to decide if run api
is_monerocn = False
is_moneroen = False
is_moneroes = False
is_monerofr = False
is_moneroit = False
is_monerojp = False
is_monerolo = False
is_moneropr = False
is_moneroru = False
is_moneroen2 = False
is_moneroesp = False
is_monero = False  # used to decide if run api

# Identifying wordlist
i = 0
if ((lan == 'english') or (lan == 'english_old') or (lan == 'all')):
    is_bip39en = is_mnemonic(mnemonic=seed_str, language='english')
    is_electrumen = checklist('Wordlists/elen', s_lenght, 'english', 'electrum', seed)
    is_moneroen = checklist('Wordlists/xmren', s_lenght, 'english', 'monero', seed)
    is_moneroen2 = checklist('Wordlists/xmren2', s_lenght, 'english_old', 'monero', seed)
if ((lan == 'italian') or (lan == 'all')):
    is_bip39it = is_mnemonic(mnemonic=seed_str, language='italian')
    is_moneroit = checklist('Wordlists/xmrit', s_lenght, 'italian', 'monero', seed)
if ((lan == 'french') or (lan == 'all')):
    is_bip39fr = is_mnemonic(mnemonic=seed_str, language='french')
    is_monerofr = checklist('Wordlists/xmrfr', s_lenght, 'french', 'monero', seed)
if ((lan == 'portuguese') or (lan == 'all')):
    # check only words, not checksum
    is_bip39pr = checklist('Wordlists/b39pr', s_lenght, 'portuguese', 'bip39', seed)
#    is_bip39pr = is_mnemonic(mnemonic=seed_str, language='portuguese')    #function not available for portuguese
    is_electrumpr = checklist('Wordlists/elpr', s_lenght, 'portuguese', 'electrum', seed)
    is_moneropr = checklist('Wordlists/xmrpr', s_lenght, 'portuguese', 'monero', seed)
if ((lan == 'spanish') or (lan == 'all')):
    is_bip39es = is_mnemonic(mnemonic=seed_str, language='spanish')
    is_electrumes = checklist('Wordlists/eles', s_lenght, 'spanish', 'electrum', seed)
    is_moneroes = checklist('Wordlists/xmres', s_lenght, 'spanish', 'monero', seed)
if ((lan == 'japanese') or (lan == 'all')):
    is_bip39jp = is_mnemonic(mnemonic=seed_str, language='japanese')
    is_electrumjp = checklist('Wordlists/eljp', s_lenght, 'japanese', 'electrum', seed)
    is_monerojp = checklist('Wordlists/xmrjp', s_lenght, 'japanese', 'monero', seed)
if ((lan == 'chinese') or (lan == 'all')):
    #    is_bip39cn = checklist('Wordlists/b39cn', len,'chinese_simplified', 'bip39', seed)
    #    is_bip39cn2 = checklist('Wordlists/b39cn2', len,'chinese_traditional', 'bip39', seed)
    is_bip39cn = is_mnemonic(mnemonic=seed_str, language='chinese_simplified')
    is_bip39cn2 = is_mnemonic(mnemonic=seed_str, language='chinese_traditional')
    is_electrumcn = checklist('Wordlists/elcn', s_lenght, 'chinese_simplified', 'electrum', seed)
    is_monerocn = checklist('Wordlists/xmrcn', s_lenght, 'chinese_simplified', 'monero', seed)
if ((lan == 'czech') or (lan == 'all')):
    # checks only list, not checksum
    is_bip39cz = checklist('Wordlists/b39cz', s_lenght, 'czech', 'bip39', seed)
#    is_bip39cz = is_mnemonic(mnemonic=seed_str, language='czech')  # funcion not available for czech language
if ((lan == 'korean') or (lan == 'all')):
    is_bip39kr = is_mnemonic(mnemonic=seed_str, language='korean')
if ((lan == 'russian') or (lan == 'all')):
    is_moneroru = checklist('Wordlists/xmrru', s_lenght,
                            'russian', 'monero', seed)
if ((lan == 'esperanto') or (lan == 'all')):
    is_moneroesp = checklist('Wordlists/xmresp', s_lenght, 'esperanto', 'monero', seed)
if ((lan == 'lojban') or (lan == 'all')):
    is_monerolo = checklist('Wordlists/xmrlo', s_lenght, 'lojban', 'monero', seed)


# Checking if seed works with electrum
if (is_electrumen or is_electrumcn or is_electrumes or is_electrumjp or is_electrumpr):
    is_electrum = True
    seedtype = mnemonic.seed_type(seed_str)  # old, standard, segwit
    if seedtype == 'segwit':
        index = 0
        elec_addr = []
        while (index < how_many):
            elec_addr.append(electrum_derive(
                seed_str, passphrase, index, 'p2wpkh'))
            index += 1
        print('Found Electrum addresses:')
        index = 0
        while (index < how_many):
            print(elec_addr[index])
            index += 1
    elif seedtype == 'standard':
        index = 0
        elec_addr = []
        while (index < how_many):
            elec_addr.append(electrum_derive(
                seed_str, passphrase, index, 'p2pkh'))
            index += 1
        print('Found Electrum addresses (first 10):')
        index = 0
        while (index < how_many):
            print(elec_addr[index])
            index += 1
    else:
        print('\nThis seed is not supported with Electrum')
        print('Words could be derived from an Electrum wordlist')
        print('To be sure, try it in an Electrum client\n')
        is_electrum = False

    # verify electrum slip39 wordlist
# checking if address derived with Electrum have been used
online_found_el = False
if (is_electrum and online_check):
    print('\nchecking electrum addresses online')
    index = 0
    check_used = 1
    # consider using variable to decide number of address to generate
    while (check_used and index < 10):
        link = 'https://blockchain.info/q/addressfirstseen/' + elec_addr[index]
        used = requests.get(link)
        data = used.text    # gives a string
        if data == '0':
            index += 1
        else:
            check_used = 0
            print('\n---> The entered seed has activity with Electrum <---\n')
            online_found_el = True
    if (data == '0' and index == 9):
        print('seed is compatible with electrum but seems to be unused (with btc)')

if (is_electrum == True and online_check == False):
    print('\n ---> Use block explorers to verifiy if the addresses were used <---\n')

# declaring empty lists
btc_list = []
eth_list = []
ltc_list = []
dash_list = []
zec_list = []


# deriving bip39 addresses
if (is_bip39cn):
    btc_list = btc_list_der('chinese_simplified', how_many)
    eth_list = eth_list_der('chinese_simplified', how_many)
    ltc_list = ltc_list_der('chinese_simplified', how_many)
    dash_list = dash_list_der('chinese_simplified', how_many)
    zec_list = zec_list_der('chinese_simplified', how_many)
    is_bip39 = True
if (is_bip39cn2):
    btc_list = btc_list_der('chinese_traditional', how_many)
    eth_list = eth_list_der('chinese_traditional', how_many)
    ltc_list = ltc_list_der('chinese_traditional', how_many)
    dash_list = dash_list_der('chinese_traditional', how_many)
    zec_list = zec_list_der('chinese_traditional', how_many)
    is_bip39 = True
if (is_bip39cz):
    btc_list = btc_list_der('czech', how_many)
    eth_list = eth_list_der('czech', how_many)
    ltc_list = ltc_list_der('czech', how_many)
    dash_list = dash_list_der('czech', how_many)
    zec_list = zec_list_der('czech', how_many)
    is_bip39 = True
if (is_bip39en):
    btc_list = btc_list_der('english', how_many)
    eth_list = eth_list_der('english', how_many)
    ltc_list = ltc_list_der('english', how_many)
    dash_list = dash_list_der('english', how_many)
    zec_list = zec_list_der('english', how_many)
    is_bip39 = True
if (is_bip39es):
    btc_list = btc_list_der('spanish', how_many)
    eth_list = eth_list_der('spanish', how_many)
    ltc_list = ltc_list_der('spanish', how_many)
    dash_list = dash_list_der('spanish', how_many)
    zec_list = zec_list_der('spanish', how_many)
    is_bip39 = True
if (is_bip39fr):
    btc_list = btc_list_der('french', how_many)
    eth_list = eth_list_der('french', how_many)
    ltc_list = ltc_list_der('french', how_many)
    dash_list = dash_list_der('french', how_many)
    zec_list = zec_list_der('french', how_many)
    is_bip39 = True
if (is_bip39it):
    btc_list = btc_list_der('italian', how_many)
    eth_list = eth_list_der('italian', how_many)
    ltc_list = ltc_list_der('italian', how_many)
    dash_list = dash_list_der('italian', how_many)
    zec_list = zec_list_der('italian', how_many)
    is_bip39 = True
if (is_bip39jp):
    btc_list = btc_list_der('japanese', how_many)
    eth_list = eth_list_der('japanese', how_many)
    ltc_list = ltc_list_der('japanese', how_many)
    dash_list = dash_list_der('japanese', how_many)
    zec_list = zec_list_der('japanese', how_many)
    is_bip39 = True
if (is_bip39kr):
    btc_list = btc_list_der('korean', how_many)
    eth_list = eth_list_der('korean', how_many)
    ltc_list = ltc_list_der('korean', how_many)
    dash_list = dash_list_der('korean', how_many)
    zec_list = zec_list_der('korean', how_many)
    is_bip39 = True
if (is_bip39pr):
    btc_list = btc_list_der('portuguese', how_many)
    eth_list = eth_list_der('portuguese', how_many)
    ltc_list = ltc_list_der('portuguese', how_many)
    dash_list = dash_list_der('portuguese', how_many)
    zec_list = zec_list_der('portuguese', how_many)
    is_bip39 = True

# Printing Bip39 derived addresses
if is_bip39:
    print('---> All BIP39 derived address <---')
    print('- Bitcoin addresses -')
    print('BIP44')
    i = 0
    while i < len(btc_list):
        print(btc_list[i])
        i += 1
        if (i == (how_many *2)):
            print('BIP49')
        elif (i == (how_many * 4)):
            print('BIP84')
        elif (i == (how_many * 6)):
            print('SAMOURAI PREMIX ADDRESSES')
        elif (i == (how_many * 7)):
            print('SAMOURAI POSTMIX ADDRESSES')
    print('\n- Ethereum addresses -')
    i = 0
    while i < len(eth_list):
        print(eth_list[i])
        i += 1
    print('\n- Litecoin addresses -')
    print('BIP44')
    i = 0
    while i < len(ltc_list):
        print(ltc_list[i])
        i += 1
        if (i == (how_many * 2)):
            print('BIP49')
        elif (i == (how_many * 4)):
            print('BIP84')
    print('\n- Dash addresses -')
    i = 0
    while i < len(dash_list):
        print(dash_list[i])
        i += 1
    print('\n- ZCash addresses -')
    i = 0
    while i < len(zec_list):
        print(zec_list[i])
        i += 1

if (is_bip39 == True and online_check == False):
    print('\n ---> Use block explorers to verifiy if the addresses were used <---\n')

# Checking Bip39 addresses online
online_found = False  # if True address was found used and a message will be shown
if (is_bip39 and online_check):
    print('\nchecking bip39 derived addresses online')
    #check BTC
    i = 0
    while i < len(btc_list):
        link = 'https://blockchain.info/q/addressfirstseen/' + btc_list[i]
        used = requests.get(link)
        data = used.text    # gives a string
        if data != '0':
            if i < how_many:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0 ---')
#                i = ((int(i/how_many)) * how_many) + how_many
                i = how_many
            elif i < (how_many * 2):
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0\' ---')
 #               print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0 ---')
                i = how_many * 2
            elif i < (how_many * 3):
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0 ---')
               # print('--- The given seed was used to derive Bitcoin addresses with derivation path m/84\'/0\'/0\'/0 ---')
                i = how_many * 3
            elif i < (how_many * 4):
              #  print('--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0\' ---')
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0\' ---')
                i = how_many * 4
            elif i < (how_many * 5):
             #   print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0\' ---')
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/84\'/0\'/0\'/0 ---')
                i = how_many * 5
            elif i < (how_many * 6):
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/84\'/0\'/0\'/0\' ---')
                i = how_many * 6
            elif i < (how_many * 7):
                print('--- The given seed was used to derive Bitcoin addresses with Samourai PreMix derivation path m/84\'/0\'/2147483645\'/0\' ---')
                i = how_many * 7
            elif i < (how_many * 8):
                print('--- The given seed was used to derive Bitcoin addresses with Samourai PostMix derivation path m/84\'/0\'2147483646\'/0\' ---')
                i = how_many * 8
            online_found = True
#            i = 18
        else:
            i += 1
    # check ETH
    i = 0
    while i < len(eth_list):
        link = 'https://api.blockcypher.com/v1/eth/main/addrs/' + eth_list[i]
        eth_resp = requests.get(link)
        eth_resp = eth_resp.text
        eth_resp_dict = json.loads(eth_resp)
        if eth_resp_dict['n_tx'] != 0:
            online_found = True
            if i < how_many:
                i = how_many
                print('--- The given seed was used to derive Electrum addresses with derivation path m/44\'/60\'/0\'/0 ---')
            elif i > how_many * 2:
                print('--- The given seed was used to derive Electrum addresses with derivation path m/44\'/60\'/0\'/0\' ---')
                break
        else:
            i += 1
    # check LTC
    i = 0
    while i < len(ltc_list):
        ltc_tx = blockcypher.get_total_num_transactions(ltc_list[i], coin_symbol='ltc')
        if ltc_tx != 0:
            if i < how_many:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/44\'/2\'/0\'/0 ---')
                i = how_many
            elif i < (how_many * 2):
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/49\'/2\'/0\'/0 ---')
                i = (how_many * 2)
            elif i < (how_many * 3):
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/84\'/2\'/0\'/0 ---')
                i = how_many * 3
            elif i < (how_many * 4):
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/44\'/2\'/0\'/0\' ---')
                i = how_many * 4
            elif i < (how_many * 5):
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/49\'/2\'/0\'/0\' ---')
                i = how_many * 5
            elif i < (how_many * 6):
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/84\'/2\'/0\'/0\' ---')
                i = how_many * 6
            online_found = True
#            i = 18
        else:
            i += 1
    # Check DASH
    i = 0
    while i < len(dash_list):
        dash_tx = blockcypher.get_total_num_transactions(
            dash_list[i], coin_symbol='dash')
        if dash_tx != 0:
            if i < how_many:
                print('--- The given seed was used to derive Dash addresses with derivation path m/44\'/5\'/0\'/0 ---')
                i = how_many
            elif i < (how_many * 2):
                print('--- The given seed was used to derive Dash addresses with derivation path m/44\'/5\'/0\'/0 ---')
                i = how_many * 2
            online_found = True
#            i = 6
        else:
            i += 1
    # Check ZEC
    i = 0
    while i < len(zec_list):
        link = 'https://api.zcha.in/v2/mainnet/accounts/' + zec_list[i]
        zec_resp = requests.get(link)
        zec_resp = zec_resp.text
        zec_resp_dict = json.loads(zec_resp)
        if zec_resp_dict['firstSeen'] != 0:
            online_found = True
            if i < how_many:
                i = how_many
                print('--- The given seed was used to derive ZCash addresses with derivation path m/44\'/133\'/0\'/0 ---')
            elif i < (how_many * 2):
                i = how_many * 2
                print('--- The given seed was used to derive ZCash addresses with derivation path m/44\'/133\'/0\'/0\' ---')
        else:
            i += 1

if (online_found == False and is_bip39 == True):
    print('Bip39 derivation path not found\n')

# Printing if no derivation path gave addresses used online
if (online_found == False and online_found_el == False and online_check == True and (is_bip39 == True or is_electrum == True)):
    print('It was not possible to determinate the derivation path used with the given seed or maybe it was never used')

# Checkink Monero
if (is_monerocn or is_moneroen or is_moneroen2 or is_moneroes or is_moneroesp or is_monerofr or is_moneroit or is_monerojp or is_monerolo or is_moneropr or is_moneroru):
    if s_lenght == 25 or s_lenght == 13:
        is_monero = True
        s_xmr = Seed(seed_str)
        print('---> The given seed could restore a Monero wallet <---')
        is_mym = s_xmr.is_mymonero()
        if is_mym == True:
            print('---> It could be used with MyMonero wallet <---')
        priv_v_k = s_xmr.secret_view_key()
        xmr_addr = s_xmr.public_address()
        print(f'- Secret View Key: {priv_v_k}')
        print(f'- Public address: {xmr_addr}')
    if (s_lenght == 14 and seed[1] == 'poet'):
        print('---> The given seed could restore a Feather (Monero) wallet <---')
