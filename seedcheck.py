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
    hdwallet.from_index(mix, hardened=True)  #sam premix= 2147483645' postmix= 2147483646'
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


def bip39_derive(s_seed, psph, lang):
    addr_dict = {
        'btc_bip44_0': '',
        'btc_bip44_1': '',
        'btc_bip44_2': '',
        'btc_bip44_0h': '',
        'btc_bip44_1h': '',
        'btc_bip44_2h': '',
        'btc_bip49_0': '',
        'btc_bip49_1': '',
        'btc_bip49_2': '',
        'btc_bip49_0h': '',
        'btc_bip49_1h': '',
        'btc_bip49_2h': '',
        'btc_bip84_0': '',
        'btc_bip84_1': '',
        'btc_bip84_2': '',
        'btc_bip84_0h': '',
        'btc_bip84_1h': '',
        'btc_bip84_2h': '',
        'btc_sam_pre0': '',
        'btc_sam_pre1': '',
        'btc_sam_pre2': '',
        'btc_sam_post0': '',
        'btc_sam_post1': '',
        'btc_sam_post2': '',
        'eth_bip44_0': '',
        'eth_bip44_1': '',
        'eth_bip44_2': '',
        'eth_bip44_0h': '',
        'eth_bip44_1h': '',
        'eth_bip44_2h': '',
        'ltc_bip44_0': '',
        'ltc_bip44_1': '',
        'ltc_bip44_2': '',
        'ltc_bip44_0h': '',
        'ltc_bip44_1h': '',
        'ltc_bip44_2h': '',
        'ltc_bip49_0': '',
        'ltc_bip49_1': '',
        'ltc_bip49_2': '',
        'ltc_bip49_0h': '',
        'ltc_bip49_1h': '',
        'ltc_bip49_2h': '',
        'ltc_bip84_0': '',
        'ltc_bip84_1': '',
        'ltc_bip84_2': '',
        'ltc_bip84_0h': '',
        'ltc_bip84_1h': '',
        'ltc_bip84_2h': '',
        'zec_bip44_0': '',
        'zec_bip44_1': '',
        'zec_bip44_2': '',
        'zec_bip44_0h': '',
        'zec_bip44_1h': '',
        'zec_bip44_2h': '',
        'dash_bip44_0': '',
        'dash_bip44_1': '',
        'dash_bip44_2': '',
        'dash_bip44_0h': '',
        'dash_bip44_1h': '',
        'dash_bip44_2h': ''
    }
    # Bip44 standard Bitcoin addresses dervation
    addr_dict.update({'btc_bip44_0': add_der(BTC, lang, s_seed, psph, 44, 0, 0, False)})
    addr_dict.update({'btc_bip44_1': add_der(BTC, lang, s_seed, psph, 44, 0, 1, False)})
    addr_dict.update({'btc_bip44_2': add_der(BTC, lang, s_seed, psph, 44, 0, 2, False)})
    # Bip44 hardened Bitcoin addresses derivation
    addr_dict.update({'btc_bip44_0h': add_der(BTC, lang, s_seed, psph, 44, 0, 0, True)})
    addr_dict.update({'btc_bip44_1h': add_der(BTC, lang, s_seed, psph, 44, 0, 1, True)})
    addr_dict.update({'btc_bip44_2h': add_der(BTC, lang, s_seed, psph, 44, 0, 2, True)})
    # Bip49 standard Bitcoin addresses derivation
    addr_dict.update({'btc_bip49_0': add_der(BTC, lang, s_seed, psph, 49, 0, 0, False)})
    addr_dict.update({'btc_bip49_1': add_der(BTC, lang, s_seed, psph, 49, 0, 1, False)})
    addr_dict.update({'btc_bip49_2': add_der(BTC, lang, s_seed, psph, 49, 0, 2, False)})
    # Bip49 hardened Bitcoin addresses derivation
    addr_dict.update({'btc_bip49_0h': add_der(BTC, lang, s_seed, psph, 49, 0, 0, True)})
    addr_dict.update({'btc_bip49_1h': add_der(BTC, lang, s_seed, psph, 49, 0, 1, True)})
    addr_dict.update({'btc_bip49_2h': add_der(BTC, lang, s_seed, psph, 49, 0, 2, True)})
    # Bip84 standard Bitcoin addresses derivation
    addr_dict.update({'btc_bip84_0': add_der(BTC, lang, s_seed, psph, 84, 0, 0, False)})
    addr_dict.update({'btc_bip84_1': add_der(BTC, lang, s_seed, psph, 84, 0, 1, False)})
    addr_dict.update({'btc_bip84_2': add_der(BTC, lang, s_seed, psph, 84, 0, 2, False)})
    # Bip84 hardened Bitcoin addresses derivation
    addr_dict.update({'btc_bip84_0h': add_der(BTC, lang, s_seed, psph, 84, 0, 0, True)})
    addr_dict.update({'btc_bip84_1h': add_der(BTC, lang, s_seed, psph, 84, 0, 1, True)})
    addr_dict.update({'btc_bip84_2h': add_der(BTC, lang, s_seed, psph, 84, 0, 2, True)})   
    # Samourai PreMix addresses
    addr_dict.update({'btc_sam_pre0': sam_der(lang, s_seed, psph, 2147483645, 0, False)})   #sam premix= 2147483645' postmix= 2147483646'
    addr_dict.update({'btc_sam_pre1': sam_der(lang, s_seed, psph, 2147483645, 1, False)})
    addr_dict.update({'btc_sam_pre2': sam_der(lang, s_seed, psph, 2147483645, 2, False)})
    # Samourai PostMix addresses
    addr_dict.update({'btc_sam_post0': sam_der(lang, s_seed, psph, 2147483646, 0, False)})   #sam premix= 2147483645' postmix= 2147483646'
    addr_dict.update({'btc_sam_post1': sam_der(lang, s_seed, psph, 2147483646, 1, False)})
    addr_dict.update({'btc_sam_post2': sam_der(lang, s_seed, psph, 2147483646, 2, False)})
    # Bip 44 standard Ethereum address dervation
    addr_dict.update({'eth_bip44_0': add_der(ETH, lang, s_seed, psph, 44, 60, 0, False)})
    addr_dict.update({'eth_bip44_1': add_der(ETH, lang, s_seed, psph, 44, 60, 1, False)})
    addr_dict.update({'eth_bip44_2': add_der(ETH, lang, s_seed, psph, 44, 60, 2, False)})
    # Bip44 hardened Ethereum addresses derivation
    addr_dict.update({'eth_bip44_0h': add_der(ETH, lang, s_seed, psph, 44, 60, 0, True)})
    addr_dict.update({'eth_bip44_1h': add_der(ETH, lang, s_seed, psph, 44, 60, 1, True)})
    addr_dict.update({'eth_bip44_2h': add_der(ETH, lang, s_seed, psph, 44, 60, 2, True)})    
    # Bip44 standard Litecoin addresses dervation
    addr_dict.update({'ltc_bip44_0': add_der(LTC, lang, s_seed, psph, 44, 2, 0, False)})
    addr_dict.update({'ltc_bip44_1': add_der(LTC, lang, s_seed, psph, 44, 2, 1, False)})
    addr_dict.update({'ltc_bip44_2': add_der(LTC, lang, s_seed, psph, 44, 2, 2, False)})
    # Bip44 hardened Litecoin addresses derivation
    addr_dict.update({'ltc_bip44_0h': add_der(LTC, lang, s_seed, psph, 44, 2, 0, True)})
    addr_dict.update({'ltc_bip44_1h': add_der(LTC, lang, s_seed, psph, 44, 2, 1, True)})
    addr_dict.update({'ltc_bip44_2h': add_der(LTC, lang, s_seed, psph, 44, 2, 2, True)})
    # Bip49 standard Litecoin addresses derivation
    addr_dict.update({'ltc_bip49_0': add_der(LTC, lang, s_seed, psph, 49, 2, 0, False)})
    addr_dict.update({'ltc_bip49_1': add_der(LTC, lang, s_seed, psph, 49, 2, 1, False)})
    addr_dict.update({'ltc_bip49_2': add_der(LTC, lang, s_seed, psph, 49, 2, 2, False)})
    # Bip49 hardened Litecoin addresses derivation
    addr_dict.update({'ltc_bip49_0h': add_der(LTC, lang, s_seed, psph, 49, 2, 0, True)})
    addr_dict.update({'ltc_bip49_1h': add_der(LTC, lang, s_seed, psph, 49, 2, 1, True)})
    addr_dict.update({'ltc_bip49_2h': add_der(LTC, lang, s_seed, psph, 49, 2, 2, True)})
    # Bip84 standard Litecoin addresses derivation
    addr_dict.update({'ltc_bip84_0': add_der(LTC, lang, s_seed, psph, 84, 2, 0, False)})
    addr_dict.update({'ltc_bip84_1': add_der(LTC, lang, s_seed, psph, 84, 2, 1, False)})
    addr_dict.update({'ltc_bip84_2': add_der(LTC, lang, s_seed, psph, 84, 2, 2, False)})
    # Bip84 hardened Litecoin addresses derivation
    addr_dict.update({'ltc_bip84_0h': add_der(LTC, lang, s_seed, psph, 84, 2, 0, True)})
    addr_dict.update({'ltc_bip84_1h': add_der(LTC, lang, s_seed, psph, 84, 2, 1, True)})
    addr_dict.update({'ltc_bip84_2h': add_der(LTC, lang, s_seed, psph, 84, 2, 2, True)})
    # Bip44 standard ZCash addresses derivation
    addr_dict.update({'zec_bip44_0': add_der(ZEC, lang, s_seed, psph, 44, 133, 0, False)})
    addr_dict.update({'zec_bip44_1': add_der(ZEC, lang, s_seed, psph, 44, 133, 1, False)})
    addr_dict.update({'zec_bip44_2': add_der(ZEC, lang, s_seed, psph, 44, 133, 2, False)})
    # Bip44 hardened ZCash addresses derivation
    addr_dict.update({'zec_bip44_0h': add_der(ZEC, lang, s_seed, psph, 44, 133, 0, True)})
    addr_dict.update({'zec_bip44_1h': add_der(ZEC, lang, s_seed, psph, 44, 133, 1, True)})
    addr_dict.update({'zec_bip44_2h': add_der(ZEC, lang, s_seed, psph, 44, 133, 2, True)})
    # Bip44 standard Dash addresses derivation
    addr_dict.update({'dash_bip44_0': add_der(DASH, lang, s_seed, psph, 44, 5, 0, False)})
    addr_dict.update({'dash_bip44_1': add_der(DASH, lang, s_seed, psph, 44, 5, 1, False)})
    addr_dict.update({'dash_bip44_2': add_der(DASH, lang, s_seed, psph, 44, 5, 2, False)})
    # Bip44 hardened Dash addresses derivation
    addr_dict.update({'dash_bip44_0h': add_der(DASH, lang, s_seed, psph, 44, 5, 0, True)})
    addr_dict.update({'dash_bip44_1h': add_der(DASH, lang, s_seed, psph, 44, 5, 1, True)})
    addr_dict.update({'dash_bip44_2h': add_der(DASH, lang, s_seed, psph, 44, 5, 2, True)})
    return addr_dict


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
is_bip39 = False # used to decide if run api
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
is_monero = False #used to decide if run api

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
    is_bip39pr = checklist('Wordlists/b39pr', s_lenght, 'portuguese', 'bip39', seed)  #check only words, not checksum
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
    is_bip39cz = checklist('Wordlists/b39cz', s_lenght, 'czech', 'bip39', seed)  # checks only list, not checksum
#    is_bip39cz = is_mnemonic(mnemonic=seed_str, language='czech')  # funcion not available for czech language
if ((lan == 'korean') or (lan == 'all')):
    is_bip39kr = is_mnemonic(mnemonic=seed_str, language='korean')
if ((lan == 'russian') or (lan == 'all')):
    is_moneroru = checklist('Wordlists/xmrru', s_lenght, 'russian', 'monero', seed)
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
        while (index < 10):
            elec_addr.append(electrum_derive(seed_str, passphrase, index, 'p2wpkh'))
            index += 1
        print('Found Electrum addresses:')
        index = 0
        while (index < 10):
            print(elec_addr[index])
            index += 1
    elif seedtype == 'standard':
        index = 0
        elec_addr = []
        while (index < 10):
            elec_addr.append(electrum_derive(seed_str, passphrase, index, 'p2pkh'))
            index += 1
        print('Found Electrum addresses (first 10):')
        index = 0
        while (index < 10):
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

# deriving bip39 addresses
if (is_bip39cn):
    address_dict = bip39_derive(seed_str, passphrase, 'chinese_simplified')
    is_bip39 = True
if (is_bip39cn2):
    address_dict = bip39_derive(seed_str, passphrase, 'chinese_traditional')
    is_bip39 = True
if (is_bip39cz):
    address_dict = bip39_derive(seed_str, passphrase, 'czech')
    is_bip39 = True
if (is_bip39en):
    address_dict = bip39_derive(seed_str, passphrase, 'english')
    is_bip39 = True
if (is_bip39es):
    address_dict = bip39_derive(seed_str, passphrase, 'spanish')
    is_bip39 = True
if (is_bip39fr):
    address_dict = bip39_derive(seed_str, passphrase, 'french')
    is_bip39 = True
if (is_bip39it):
    address_dict = bip39_derive(seed_str, passphrase, 'italian')
    is_bip39 = True
if (is_bip39jp):
    address_dict = bip39_derive(seed_str, passphrase, 'japanese')
    is_bip39 = True
if (is_bip39kr):
    address_dict = bip39_derive(seed_str, passphrase, 'korean')
    is_bip39 = True
if (is_bip39pr):
    address_dict = bip39_derive(seed_str, passphrase, 'portuguese')
    is_bip39 = True

# Printing Bip39 derived addresses
if is_bip39:
    print('---> All BIP39 derived address <---')
    print('- Bitcoin addresses -')
    i = 0
    btc_list = []
    btc_list.append(address_dict['btc_bip44_0'])
    btc_list.append(address_dict['btc_bip44_1'])
    btc_list.append(address_dict['btc_bip44_2'])
    btc_list.append(address_dict['btc_bip49_0'])
    btc_list.append(address_dict['btc_bip49_1'])
    btc_list.append(address_dict['btc_bip49_2'])
    btc_list.append(address_dict['btc_bip84_0'])
    btc_list.append(address_dict['btc_bip84_1'])
    btc_list.append(address_dict['btc_bip84_2'])
    btc_list.append(address_dict['btc_bip44_0h'])
    btc_list.append(address_dict['btc_bip44_1h'])
    btc_list.append(address_dict['btc_bip44_2h'])
    btc_list.append(address_dict['btc_bip49_0h'])
    btc_list.append(address_dict['btc_bip49_1h'])
    btc_list.append(address_dict['btc_bip49_2h'])
    btc_list.append(address_dict['btc_bip84_0h'])
    btc_list.append(address_dict['btc_bip84_1h'])
    btc_list.append(address_dict['btc_bip84_2h'])
    btc_list.append(address_dict['btc_sam_pre0'])
    btc_list.append(address_dict['btc_sam_pre1'])
    btc_list.append(address_dict['btc_sam_pre2'])
    btc_list.append(address_dict['btc_sam_post0'])
    btc_list.append(address_dict['btc_sam_post1'])
    btc_list.append(address_dict['btc_sam_post2'])
    while i < len(btc_list):
        print(btc_list[i])
        i += 1  
    print('- Ethereum addresses -')
    i = 0
    eth_list = []
    eth_list.append(address_dict['eth_bip44_0'])
    eth_list.append(address_dict['eth_bip44_1'])
    eth_list.append(address_dict['eth_bip44_2'])
    eth_list.append(address_dict['eth_bip44_0h'])
    eth_list.append(address_dict['eth_bip44_1h'])
    eth_list.append(address_dict['eth_bip44_2h'])
    while i < len(eth_list):
        print(eth_list[i])
        i += 1
    print('- Litecoin addresses -')
    i = 0
    ltc_list = []
    ltc_list.append(address_dict['ltc_bip44_0'])
    ltc_list.append(address_dict['ltc_bip44_1'])
    ltc_list.append(address_dict['ltc_bip44_2'])
    ltc_list.append(address_dict['ltc_bip49_0'])
    ltc_list.append(address_dict['ltc_bip49_1'])
    ltc_list.append(address_dict['ltc_bip49_2'])
    ltc_list.append(address_dict['ltc_bip84_0'])
    ltc_list.append(address_dict['ltc_bip84_1'])
    ltc_list.append(address_dict['ltc_bip84_2'])
    ltc_list.append(address_dict['ltc_bip44_0h'])
    ltc_list.append(address_dict['ltc_bip44_1h'])
    ltc_list.append(address_dict['ltc_bip44_2h'])
    ltc_list.append(address_dict['ltc_bip49_0h'])
    ltc_list.append(address_dict['ltc_bip44_1h'])
    ltc_list.append(address_dict['ltc_bip44_2h'])
    ltc_list.append(address_dict['ltc_bip49_0h'])
    ltc_list.append(address_dict['ltc_bip49_1h'])
    ltc_list.append(address_dict['ltc_bip49_2h'])
    ltc_list.append(address_dict['ltc_bip84_0h'])
    ltc_list.append(address_dict['ltc_bip84_1h'])
    ltc_list.append(address_dict['ltc_bip84_2h'])
    while i < len(ltc_list):
        print(ltc_list[i])
        i += 1
    print('- Dash addresses -')
    i = 0
    dash_list = []
    dash_list.append(address_dict['dash_bip44_0'])
    dash_list.append(address_dict['dash_bip44_1'])
    dash_list.append(address_dict['dash_bip44_2'])
    dash_list.append(address_dict['dash_bip44_0h'])
    dash_list.append(address_dict['dash_bip44_1h'])
    dash_list.append(address_dict['dash_bip44_2h'])
    while i < len(dash_list):
        print(dash_list[i])
        i += 1
    print('- ZCash addresses -')
    i = 0
    zec_list = []
    zec_list.append(address_dict['zec_bip44_0'])
    zec_list.append(address_dict['zec_bip44_1'])
    zec_list.append(address_dict['zec_bip44_2'])
    zec_list.append(address_dict['zec_bip44_0h'])
    zec_list.append(address_dict['zec_bip44_1h'])
    zec_list.append(address_dict['zec_bip44_2h'])
    while i < len(zec_list):
        print(zec_list[i])
        i += 1

if (is_bip39 == True and online_check == False):
    print('\n ---> Use block explorers to verifiy if the addresses were used <---\n')

# Checking Bip39 addresses online
online_found = False   #if True address was found used and a message will be shown
if (is_bip39 and online_check):
    print('\nchecking bip39 derived addresses online')
    #check BTC
    i = 0
    while i < 24:
        link = 'https://blockchain.info/q/addressfirstseen/' + btc_list[i]
        used = requests.get(link)
        data = used.text    # gives a string
        if data != '0':
            if i < 3:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 6:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 9:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/84\'/0\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 12:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/44\'/0\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 15:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/49\'/0\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 18:
                print('--- The given seed was used to derive Bitcoin addresses with derivation path m/84\'/0\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 21:
                print('--- The given seed was used to derive Bitcoin addresses with Samourai PreMix derivation path m/84\'/0\'/2147483645\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 24:
                print('--- The given seed was used to derive Bitcoin addresses with Samourai PostMix derivation path m/84\'/0\'2147483646\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            online_found = True
#            i = 18
        else:
            i += 1
    # check ETH
    i = 0
    while i < 6:
        link = 'https://api.blockcypher.com/v1/eth/main/addrs/' + eth_list[i]
        eth_resp = requests.get(link)
        eth_resp = eth_resp.text
        eth_resp_dict = json.loads(eth_resp)
        if eth_resp_dict['n_tx'] != 0:
            online_found = True
            if i < 3:
                i = ((int(i/3)) * 3) + 3
                print('--- The given seed was used to derive Electrum addresses with derivation path m/44\'/60\'/0\'/0 ---')
            elif i > 2:
                i = ((int(i/3)) * 3) + 3
                print('--- The given seed was used to derive Electrum addresses with derivation path m/44\'/60\'/0\'/0\' ---')
        else:
            i += 1
    # check LTC
    i = 0
    while i < 18:
        ltc_tx = blockcypher.get_total_num_transactions(ltc_list[i], coin_symbol='ltc')
        if ltc_tx != 0:
            if i < 3:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/44\'/2\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 6:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/49\'/2\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 9:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/84\'/2\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 12:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/44\'/2\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 15:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/49\'/2\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 18:
                print('--- The given seed was used to derive Litecoin addresses with derivation path m/84\'/2\'/0\'/0\' ---')
                i = ((int(i/3)) * 3) + 3
            online_found = True
#            i = 18
        else:
            i += 1
    # Check DASH
    i = 0
    while i < 6:
        dash_tx = blockcypher.get_total_num_transactions(dash_list[i], coin_symbol='dash')
        if dash_tx != 0:
            if i < 3:
                print('--- The given seed was used to derive Dash addresses with derivation path m/44\'/5\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            elif i < 6:
                print('--- The given seed was used to derive Dash addresses with derivation path m/44\'/5\'/0\'/0 ---')
                i = ((int(i/3)) * 3) + 3
            online_found = True
#            i = 6  
        else:
            i += 1
    # Check ZEC
    i = 0
    while i < 6:
        link = 'https://api.zcha.in/v2/mainnet/accounts/' + zec_list[i]
        zec_resp = requests.get(link)
        zec_resp = zec_resp.text
        zec_resp_dict = json.loads(zec_resp)
        if zec_resp_dict['firstSeen'] != 0:
            online_found = True
            if i < 3:
                i = ((int(i/3)) * 3) + 3
                print('--- The given seed was used to derive ZCash addresses with derivation path m/44\'/133\'/0\'/0 ---')
            elif i > 2:
                i = 6
                print('--- The given seed was used to derive ZCash addresses with derivation path m/44\'/133\'/0\'/0\' ---')
        else:
            i += 1

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
        
