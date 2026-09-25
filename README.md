# SeedCheck (bip-utils Refactor)

Cryptocurrency mnemonic phrase identifier and address derivation analysis tool.

## Key Upgrades & Changes

1. **Unified Derivation Engine (`bip-utils`):**
   - Replaced custom Electrum submodule, `hdwallet`, and `blockcypher` with `bip-utils`.
   - The bundled `electrum/` repository is completely removed.
2. **Account-Level Derivations (EVM, Solana, Tron):**
   - **Ethereum / EVM:** Derives the first accounts (`m/44'/60'/account'/0/0`) rather than address indexes on account 0.
   - **Solana:** Derives the first accounts (`m/44'/501'/account'/0'`).
   - **Tron:** Derives the first accounts (`m/44'/195'/account'/0/0`).
3. **Privacy Disclaimer & Confirmation:**
   - Warns before querying public Electrum servers and RPC endpoints.
   - User must confirm (`[y/N]`) before online requests are sent; declining falls back to offline derivation automatically.
   - Use `-y` / `--yes` to auto-accept in non-interactive scripts.
4. **Online Checks via Public Stratum & RPCs:**
   - **BTC / LTC / DASH:** Direct connection to public Electrum Stratum servers over SSL (port 50002) via scripthash queries (`blockchain.scripthash.get_balance`, `blockchain.scripthash.get_history`).
   - **EVM (Ethereum):** Direct queries to public EVM JSON-RPC endpoints (`eth_getBalance`, `eth_getTransactionCount`).
   - **Solana:** Direct queries to public Solana JSON-RPC endpoints (`getBalance`, `getSignaturesForAddress`).
   - **Tron:** Direct queries to public TronGrid API (`/v1/accounts/{address}`).
   - **No API keys or third-party rate limits required.**
5. **Offline Mode:**
   - Run `--offline` to perform purely local derivation and seed identification without contacting any network servers.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode:
```bash
python seedcheck.py
```

### Command-line Arguments:
```bash
# Check a seed phrase (prompts for online confirmation)
python seedcheck.py -s "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

# Auto-confirm online checks
python seedcheck.py -s "your mnemonic here" -y

# Derive 5 accounts/addresses instead of the default 3
python seedcheck.py -s "your mnemonic here" -c 5 -y

# Offline derivation only (no disclaimer, no network requests)
python seedcheck.py -s "your mnemonic here" --offline

# With a passphrase
python seedcheck.py -s "your mnemonic here" -p "mySecretPassphrase"
```
