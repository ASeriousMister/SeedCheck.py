#!/usr/bin/env python3
"""
SeedCheck - Cryptocurrency Mnemonic Identifier and Wallet Derivation Tool
Refactored to use bip-utils and direct public RPC / Electrum Stratum servers.
"""

import sys
import argparse
import socket
import ssl
import json
import hashlib
import requests
from typing import Optional, Tuple, Dict, Any, List

from bip_utils import (
    Bip39MnemonicValidator, Bip39SeedGenerator, Bip39Languages,
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    ElectrumV1MnemonicValidator, ElectrumV1,
    ElectrumV2MnemonicValidator, ElectrumV2Standard, ElectrumV2Segwit, ElectrumV2MnemonicTypes,
    MoneroMnemonicValidator, MoneroSeedGenerator, Monero,
    Base58Decoder, SegwitBech32Decoder
)

class Colors:
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

# ==========================================
# PUBLIC SERVERS & RPCs
# ==========================================

ELECTRUM_SERVERS = {
    'BTC': [
        ('electrum.blockstream.info', 50002, True),
        ('btc.curalle.ovh', 50002, True),
        ('electrum.emzy.de', 50002, True)
    ],
    'LTC': [
        ('electrum-ltc.bysh.me', 50002, True),
        ('ltc.curalle.ovh', 50002, True)
    ],
    'DASH': [
        ('electrum.dash.siampm.com', 50002, True),
        ('dash.curalle.ovh', 50002, True)
    ]
}

EVM_RPCS = [
    'https://cloudflare-eth.com',
    'https://rpc.ankr.com/eth',
    'https://ethereum.publicnode.com'
]

SOLANA_RPCS = [
    'https://api.mainnet-beta.solana.com',
    'https://solana-mainnet.rpc.extrnode.com'
]

TRON_API = 'https://api.trongrid.io/v1/accounts'

# ==========================================
# ONLINE CHECKERS
# ==========================================

def address_to_scripthash(address: str) -> Optional[str]:
    """Computes Electrum 2.0 scripthash (SHA256(scriptPubKey) reversed)."""
    try:
        if address.startswith('bc1q') or address.startswith('ltc1q'):
            hrp = address[:address.find('1')]
            _, prog = SegwitBech32Decoder.Decode(hrp, address)
            script = bytes([0x00, len(prog)]) + bytes(prog)
        elif address.startswith('3') or address.startswith('M'):
            raw = Base58Decoder.CheckDecode(address)[1:]
            script = bytes([0xa9, 0x14]) + raw + bytes([0x87])
        else:
            raw = Base58Decoder.CheckDecode(address)[1:]
            script = bytes([0x76, 0xa9, 0x14]) + raw + bytes([0x88, 0xac])
        h = hashlib.sha256(script).digest()
        return h[::-1].hex()
    except Exception:
        return None

def check_electrum_stratum(coin: str, address: str) -> Tuple[int, int]:
    """Queries Electrum server for (balance_sats, tx_count)."""
    scripthash = address_to_scripthash(address)
    if not scripthash:
        return 0, 0

    servers = ELECTRUM_SERVERS.get(coin, [])
    for host, port, use_ssl in servers:
        try:
            sock = socket.create_connection((host, port), timeout=3)
            if use_ssl:
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=host)

            req_bal = json.dumps({"id": 1, "method": "blockchain.scripthash.get_balance", "params": [scripthash]}) + "\n"
            sock.sendall(req_bal.encode())
            res_bal = json.loads(sock.recv(4096).decode())
            confirmed = res_bal.get("result", {}).get("confirmed", 0)

            req_hist = json.dumps({"id": 2, "method": "blockchain.scripthash.get_history", "params": [scripthash]}) + "\n"
            sock.sendall(req_hist.encode())
            res_hist = json.loads(sock.recv(8192).decode())
            tx_count = len(res_hist.get("result", []))

            sock.close()
            return confirmed, tx_count
        except Exception:
            continue
    return 0, 0

def check_evm(address: str) -> Tuple[int, int]:
    """Queries public EVM RPC for (balance_wei, tx_count)."""
    for rpc in EVM_RPCS:
        try:
            payload = [
                {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1},
                {"jsonrpc": "2.0", "method": "eth_getTransactionCount", "params": [address, "latest"], "id": 2}
            ]
            r = requests.post(rpc, json=payload, timeout=4).json()
            bal = int(r[0]['result'], 16) if 'result' in r[0] else 0
            txs = int(r[1]['result'], 16) if 'result' in r[1] else 0
            return bal, txs
        except Exception:
            continue
    return 0, 0

def check_solana(address: str) -> Tuple[int, int]:
    """Queries Solana public RPC for (balance_lamports, tx_count)."""
    for rpc in SOLANA_RPCS:
        try:
            bal_payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]}
            bal_res = requests.post(rpc, json=bal_payload, timeout=4).json()
            bal = bal_res.get("result", {}).get("value", 0)

            tx_payload = {"jsonrpc": "2.0", "id": 2, "method": "getSignaturesForAddress", "params": [address, {"limit": 5}]}
            tx_res = requests.post(rpc, json=tx_payload, timeout=4).json()
            txs = len(tx_res.get("result", []))
            return bal, txs
        except Exception:
            continue
    return 0, 0

def check_tron(address: str) -> Tuple[int, int]:
    """Queries TronGrid API for (balance_sun, is_active)."""
    try:
        url = f"{TRON_API}/{address}"
        res = requests.get(url, timeout=4).json()
        data = res.get("data", [])
        if not data:
            return 0, 0
        bal = data[0].get("balance", 0)
        trc20_tokens = len(data[0].get("trc20", []))
        is_active = 1 if bal > 0 or trc20_tokens > 0 else 0
        return bal, is_active
    except Exception:
        return 0, 0

# ==========================================
# SEED IDENTIFICATION & ANALYSIS
# ==========================================

def identify_and_check(seed_str: str, passphrase: str = "", count: int = 3, offline: bool = False, auto_yes: bool = False):
    words = seed_str.strip().split()
    word_count = len(words)
    clean_seed = " ".join(words)

    print(Colors.YELLOW + "\n=====================\n===   SeedCheck   ===\n=====================\n" + Colors.END)

    if not offline and not auto_yes:
        print(f"{Colors.YELLOW}{Colors.BOLD}[!] PRIVACY & NETWORK NOTICE:{Colors.END}")
        print("This tool will perform online queries against public Electrum servers and")
        print("public RPC endpoints to check balances and transaction history for derived addresses.")
        try:
            confirm = input(f"Do you want to proceed with online checks? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)
        if confirm != 'y':
            print(f"{Colors.YELLOW}[*] Proceeding in OFFLINE mode (address derivation only).{Colors.END}\n")
            offline = True
        else:
            print(f"{Colors.GREEN}[*] Proceeding with online checks.{Colors.END}\n")

    print(f"Input seed length: {word_count} words")

    found_activity = False

    # 1. Monero check
    if word_count in (13, 25):
        try:
            val_xmr = MoneroMnemonicValidator()
            if val_xmr.IsValid(clean_seed):
                print(f"{Colors.GREEN}[+] Identified: Monero ({word_count} words){Colors.END}")
                seed_bytes = MoneroSeedGenerator(clean_seed).Generate()
                xmr = Monero.FromSeed(seed_bytes)
                primary_addr = xmr.PrimaryAddress()
                print(f"  Primary Address: {primary_addr}")
                return
        except Exception:
            pass

    # 2. Electrum V2 check
    try:
        val_elec2 = ElectrumV2MnemonicValidator()
        if val_elec2.IsValid(clean_seed):
            m_type = val_elec2.GetMnemonicType(clean_seed)
            print(f"{Colors.GREEN}[+] Identified: Electrum V2 ({m_type.name}){Colors.END}")
            if m_type == ElectrumV2MnemonicTypes.SEGWIT:
                master = ElectrumV2Segwit.FromMnemonic(clean_seed, passphrase)
                addr_type = "p2wpkh (Segwit)"
            else:
                master = ElectrumV2Standard.FromMnemonic(clean_seed, passphrase)
                addr_type = "p2pkh (Legacy)"

            print(f"Deriving Electrum BTC addresses ({addr_type}):")
            for i in range(count):
                addr = master.GetAddress(Bip44Changes.CHAIN_EXT, i)
                status = ""
                if not offline:
                    bal, txs = check_electrum_stratum('BTC', addr)
                    if txs > 0 or bal > 0:
                        status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                        found_activity = True
                    else:
                        status = " -> No history"
                print(f"  m/0/{i}: {addr}{status}")

            change_addr = master.GetAddress(Bip44Changes.CHAIN_INT, 0)
            status = ""
            if not offline:
                bal, txs = check_electrum_stratum('BTC', change_addr)
                if txs > 0 or bal > 0:
                    status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                    found_activity = True
                else:
                    status = " -> No history"
            print(f"  Change m/1/0: {change_addr}{status}")
            return
    except Exception:
        pass

    # 3. Electrum V1 check
    try:
        val_elec1 = ElectrumV1MnemonicValidator()
        if val_elec1.IsValid(clean_seed):
            print(f"{Colors.GREEN}[+] Identified: Electrum V1 (Old standard){Colors.END}")
            # Derive standard Electrum V1
            master = ElectrumV1.FromMnemonic(clean_seed)
            for i in range(count):
                addr = master.GetAddress(Bip44Changes.CHAIN_EXT, i)
                status = ""
                if not offline:
                    bal, txs = check_electrum_stratum('BTC', addr)
                    if txs > 0 or bal > 0:
                        status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                        found_activity = True
                    else:
                        status = " -> No history"
                print(f"  m/0/{i}: {addr}{status}")
            return
    except Exception:
        pass

    # 4. BIP39 check
    bip39_val = Bip39MnemonicValidator()
    if not bip39_val.IsValid(clean_seed):
        print(f"{Colors.RED}[-] Not a valid BIP39, Electrum, or Monero seed phrase.{Colors.END}")
        return

    # Identify BIP39 Language
    lang_found = "unknown"
    for lang in Bip39Languages:
        if Bip39MnemonicValidator(lang).IsValid(clean_seed):
            lang_found = lang.name.lower()
            break

    print(f"{Colors.GREEN}[+] Identified: BIP39 Mnemonic (Language: {lang_found}){Colors.END}")
    seed_bytes = Bip39SeedGenerator(clean_seed).Generate(passphrase)

    # --- BITCOIN (BIP44, BIP49, BIP84, Samourai) ---
    print(f"\n{Colors.BLUE}=== Bitcoin (BTC) ==={Colors.END}")
    schemes = [
        ("BIP44 (Legacy p2pkh)", Bip44, Bip44Coins.BITCOIN),
        ("BIP49 (Nested Segwit p2sh-p2wpkh)", Bip49, Bip49Coins.BITCOIN),
        ("BIP84 (Native Segwit p2wpkh)", Bip84, Bip84Coins.BITCOIN)
    ]
    for name, bip_cls, coin_type in schemes:
        print(f"--- {name} ---")
        acc = bip_cls.FromSeed(seed_bytes, coin_type).Purpose().Coin().Account(0)
        ext = acc.Change(Bip44Changes.CHAIN_EXT)
        for i in range(count):
            addr = ext.AddressIndex(i).PublicKey().ToAddress()
            status = ""
            if not offline:
                bal, txs = check_electrum_stratum('BTC', addr)
                if txs > 0 or bal > 0:
                    status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                    found_activity = True
                else:
                    status = " -> No history"
            print(f"  Receiving #{i}: {addr}{status}")

        change_addr = acc.Change(Bip44Changes.CHAIN_INT).AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, txs = check_electrum_stratum('BTC', change_addr)
            if txs > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  Change #0:    {change_addr}{status}")

    # Samourai Accounts (Postmix & Badbank)
    print("--- Samourai Postmix & Badbank Accounts (BIP84) ---")
    for acc_idx, acc_label in [(2147483646, "Postmix (acc 2147483646)"), (2147483647, "Badbank (acc 2147483647)")]:
        acc = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN).Purpose().Coin().Account(acc_idx)
        addr = acc.Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, txs = check_electrum_stratum('BTC', addr)
            if txs > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} sats){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  {acc_label} #0: {addr}{status}")

    # --- ETHEREUM / EVM ---
    print(f"\n{Colors.BLUE}=== Ethereum / EVM (First {count} Accounts) ==={Colors.END}")
    for acc_idx in range(count):
        bip_eth = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).Purpose().Coin().Account(acc_idx).Change(Bip44Changes.CHAIN_EXT)
        addr = bip_eth.AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, txs = check_evm(addr)
            if txs > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Nonce/Txs: {txs}, Bal: {bal} wei){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  Account #{acc_idx} (m/44'/60'/{acc_idx}'/0/0): {addr}{status}")

    # --- SOLANA ---
    print(f"\n{Colors.BLUE}=== Solana (First {count} Accounts) ==={Colors.END}")
    for acc_idx in range(count):
        # Solana derivation: m/44'/501'/account'/0'
        bip_sol = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA).Purpose().Coin().Account(acc_idx).Change(Bip44Changes.CHAIN_EXT)
        addr = bip_sol.AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, txs = check_solana(addr)
            if txs > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Lamports: {bal}){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  Account #{acc_idx} (m/44'/501'/{acc_idx}'/0'): {addr}{status}")

    # --- TRON ---
    print(f"\n{Colors.BLUE}=== Tron (First {count} Accounts) ==={Colors.END}")
    for acc_idx in range(count):
        bip_trx = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON).Purpose().Coin().Account(acc_idx).Change(Bip44Changes.CHAIN_EXT)
        addr = bip_trx.AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, active = check_tron(addr)
            if active > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Bal: {bal} SUN){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  Account #{acc_idx} (m/44'/195'/{acc_idx}'/0/0): {addr}{status}")

    # --- LITECOIN ---
    print(f"\n{Colors.BLUE}=== Litecoin (LTC) ==={Colors.END}")
    for name, bip_cls, coin_type in [
        ("BIP44 (Legacy)", Bip44, Bip44Coins.LITECOIN),
        ("BIP49 (Nested Segwit)", Bip49, Bip49Coins.LITECOIN),
        ("BIP84 (Native Segwit)", Bip84, Bip84Coins.LITECOIN)
    ]:
        acc = bip_cls.FromSeed(seed_bytes, coin_type).Purpose().Coin().Account(0)
        addr = acc.Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
        status = ""
        if not offline:
            bal, txs = check_electrum_stratum('LTC', addr)
            if txs > 0 or bal > 0:
                status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} litoshis){Colors.END}"
                found_activity = True
            else:
                status = " -> No history"
        print(f"  {name} #0: {addr}{status}")

    # --- DASH ---
    print(f"\n{Colors.BLUE}=== Dash ==={Colors.END}")
    dash_addr = Bip44.FromSeed(seed_bytes, Bip44Coins.DASH).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
    status = ""
    if not offline:
        bal, txs = check_electrum_stratum('DASH', dash_addr)
        if txs > 0 or bal > 0:
            status = f" -> {Colors.GREEN}ACTIVE (Txs: {txs}, Bal: {bal} duffs){Colors.END}"
            found_activity = True
        else:
            status = " -> No history"
    print(f"  BIP44 #0: {dash_addr}{status}")

    # --- ZCASH ---
    print(f"\n{Colors.BLUE}=== Zcash (Transparent) ==={Colors.END}")
    zec_addr = Bip44.FromSeed(seed_bytes, Bip44Coins.ZCASH).Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
    print(f"  BIP44 #0: {zec_addr} (Offline derivation)")

    print("\n" + "="*30)
    if not offline:
        if found_activity:
            print(f"{Colors.GREEN}[✓] Active addresses found with on-chain history.{Colors.END}")
        else:
            print(f"{Colors.YELLOW}[!] No on-chain activity detected on the checked addresses.{Colors.END}")
    print("Done.\n")

# ==========================================
# ENTRY POINT
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="SeedCheck - Cryptocurrency Mnemonic Identifier & Checker")
    parser.add_argument("-s", "--seed", help="Mnemonic seed phrase (wrap in quotes)")
    parser.add_argument("-p", "--passphrase", default="", help="Optional BIP39 / Electrum passphrase")
    parser.add_argument("-c", "--count", type=int, default=3, help="Number of receiving addresses / accounts to derive per scheme (default: 3)")
    parser.add_argument("--offline", action="store_true", help="Perform address derivation only (skip online checks)")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically accept online checks disclaimer")

    args = parser.parse_args()

    if args.seed:
        seed_phrase = args.seed
    else:
        seed_phrase = input("Enter seed phrase: ").strip()

    passphrase = args.passphrase
    if not args.seed and not args.passphrase:
        pass_in = input("Enter passphrase (press Enter to skip): ").strip()
        if pass_in:
            passphrase = pass_in

    identify_and_check(seed_phrase, passphrase, count=args.count, offline=args.offline, auto_yes=args.yes)

if __name__ == "__main__":
    main()
