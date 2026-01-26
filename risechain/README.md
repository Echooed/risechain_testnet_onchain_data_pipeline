# Risechain Labs Testnet Explorer API Client

A Python client for extracting data from the Risechain Labs testnet BlockScout API.

## Features

- ✅ **Comprehensive API Coverage**: Supports all major API modules (Account, Block, Contract, Transaction, Logs, Token, Stats)
- ✅ **Production-Ready**: Includes retry logic, error handling, and logging
- ✅ **Type Hints**: Full type annotations for better IDE support
- ✅ **Context Manager Support**: Proper resource management
- ✅ **Configurable**: Easy configuration for timeout, retries, and base URL
- ✅ **Well-Documented**: Detailed docstrings for all methods

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from rise_explorer_scraper import RiseExplorerClient

# Initialize client
with RiseExplorerClient() as client:
    # Get balance for an address
    balance = client.get_balance("0x95426f2bc716022fcf1def006dbc4bb81f5b5164")
    print(balance)
    
    # Get transactions
    txs = client.get_transactions(
        address="0x95426f2bc716022fcf1def006dbc4bb81f5b5164",
        page=1,
        offset=10
    )
    print(txs)
```

## API Modules

### 1. Account Module

Get account-related data including balances, transactions, and token information.

```python
# Get single balance
balance = client.get_balance("0x...")

# Get multiple balances (max 20 addresses)
balances = client.get_balance_multi([
    "0xaddress1...",
    "0xaddress2..."
])

# Get transactions
txs = client.get_transactions(
    address="0x...",
    startblock=1000,
    endblock=2000,
    page=1,
    offset=20,
    sort='desc'
)

# Get internal transactions
internal_txs = client.get_internal_transactions(
    address="0x...",
    page=1,
    offset=10
)

# Get token transfers
token_txs = client.get_token_transfers(
    address="0x...",
    contractaddress="0x...",  # optional
    page=1,
    offset=10
)

# Get token balance
token_balance = client.get_token_balance(
    contractaddress="0x...",
    address="0x..."
)

# Get all tokens owned by address
tokens = client.get_token_list("0x...")
```

### 2. Block Module

Get block-related information.

```python
# Get block reward
reward = client.get_block_reward(blockno=34092)

# Get block number by timestamp
block_num = client.get_block_number_by_timestamp(
    timestamp=1480072029,
    closest='before'  # or 'after'
)
```

### 3. Contract Module

Get contract information for verified contracts.

```python
# Get contract ABI
abi = client.get_contract_abi("0x...")

# Get contract source code
source = client.get_contract_source_code("0x...")
```

### 4. Transaction Module

Get detailed transaction information.

```python
# Get transaction info
tx_info = client.get_transaction_info("0xtxhash...")

# Get transaction receipt status
receipt = client.get_transaction_receipt_status("0xtxhash...")

# Get transaction error status
status = client.get_transaction_status("0xtxhash...")
```

### 5. Logs Module

Get event logs from the blockchain.

```python
# Get logs with filtering
logs = client.get_logs(
    fromBlock=1000,
    toBlock=2000,
    address="0x...",  # optional
    topic0="0x...",   # optional
    topic1="0x..."    # optional
)
```

### 6. Token Module

Get token-specific information.

```python
# Get token info (ERC-20 or ERC-721)
token_info = client.get_token_info("0xcontract...")

# Get token holders
holders = client.get_token_holders(
    contractaddress="0x...",
    page=1,
    offset=10
)
```

### 7. Stats Module

Get network statistics.

```python
# Get token supply
supply = client.get_token_supply("0xcontract...")

# Get total ETH supply
eth_supply = client.get_eth_supply()

# Get current coin price
price = client.get_coin_price()
```

## Configuration

Customize the client configuration:

```python
from rise_explorer_scraper import RiseExplorerClient, RiseExplorerConfig

config = RiseExplorerConfig(
    base_url="https://explorer.testnet.riselabs.xyz/api",
    timeout=30,
    max_retries=3,
    retry_delay=1
)

client = RiseExplorerClient(config)
```

## Error Handling

The client includes automatic retry logic and comprehensive error handling:

```python
from rise_explorer_scraper import RiseExplorerClient
import requests

try:
    with RiseExplorerClient() as client:
        balance = client.get_balance("0x...")
        
        # Check if API returned error
        if balance.get('status') == '0':
            print(f"API Error: {balance.get('message')}")
        else:
            print(f"Balance: {balance.get('result')}")
            
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Validation error: {e}")
```

## Logging

The client uses Python's built-in logging module:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

# Now all API calls will be logged
client = RiseExplorerClient()
```

## Advanced Usage

### Pagination

Handle large datasets with pagination:

```python
def get_all_transactions(address, max_pages=10):
    """Fetch multiple pages of transactions."""
    all_txs = []
    
    with RiseExplorerClient() as client:
        for page in range(1, max_pages + 1):
            result = client.get_transactions(
                address=address,
                page=page,
                offset=100
            )
            
            if result.get('status') == '1':
                txs = result.get('result', [])
                if not txs:
                    break
                all_txs.extend(txs)
            else:
                break
    
    return all_txs
```

### Batch Processing

Process multiple addresses:

```python
def get_balances_for_addresses(addresses):
    """Get balances for multiple addresses efficiently."""
    balances = {}
    
    with RiseExplorerClient() as client:
        # Process in chunks of 20 (API limit)
        for i in range(0, len(addresses), 20):
            chunk = addresses[i:i+20]
            result = client.get_balance_multi(chunk)
            
            if result.get('status') == '1':
                for item in result.get('result', []):
                    balances[item['address']] = item['balance']
    
    return balances
```

## API Rate Limits

The BlockScout API may have rate limits. The client includes retry logic to handle temporary failures, but for large-scale scraping, consider:

- Adding delays between requests
- Implementing exponential backoff
- Respecting the API's rate limits

## Response Format

All methods return a dictionary with the following structure:

```python
{
    "status": "1",  # "1" for success, "0" for error
    "message": "OK",
    "result": ...   # The actual data (varies by endpoint)
}
```

## Data Extraction

The package includes powerful data extraction tools that save data to files:

### Using the Data Extractor

```python
from data_extractor import DataExtractor

with DataExtractor(output_dir="my_data") as extractor:
    # Extract account data (saves to JSON and CSV)
    files = extractor.extract_account_data(
        address="0x123...",
        include_transactions=True,
        include_tokens=True,
        max_transactions=100
    )
    
    # Extract contract source code and ABI
    files = extractor.extract_contract_data("0x456...")
    
    # Extract token holders
    files = extractor.extract_token_holders("0x789...", max_holders=50)
    
    # Extract network statistics
    files = extractor.extract_network_stats()
```

### Using the CLI Tool

For quick extractions, use the command-line interface:

```bash
# Extract account data with transactions and tokens
python extract.py account 0x123... --transactions --tokens --max-tx 100 -o my_data

# Extract transactions only
python extract.py transactions 0x123... --limit 100

# Extract contract source code
python extract.py contract 0x456...

# Extract block range
python extract.py blocks --start 1000 --end 2000

# Extract token holders
python extract.py token-holders 0x789... --limit 50

# Extract network statistics
python extract.py stats
```

### Output Formats

Data is saved in multiple formats:

- **JSON**: Full data with nested structures
- **CSV**: Flat data suitable for spreadsheet analysis
- **Solidity files**: Contract source code (.sol)
- **ABI files**: Contract ABIs (.json)

### Output Directory Structure

```
extracted_data/
├── json/
│   ├── account_0x95426f.../
│   │   ├── 20250126_120000_balance.json
│   │   ├── 20250126_120000_transactions.json
│   │   └── 20250126_120000_tokens.json
│   ├── contract_0x95426f.../
│   │   ├── 20250126_120000_contract_full.json
│   │   └── 20250126_120000_abi.json
│   └── stats/
│       └── 20250126_120000_network_stats.json
├── csv/
│   ├── account_0x95426f.../
│   │   ├── 20250126_120000_transactions.csv
│   │   └── 20250126_120000_tokens.csv
│   └── blocks/
│       └── 20250126_120000_blocks_1000_to_2000.csv
└── contract_0x95426f.../
    └── 20250126_120000_source.sol
```

## Testing

Run the example usage:

```bash
# Test the basic API client
python rise_explorer_scraper.py

# Test the data extractor
python data_extractor.py

# View all examples
python examples.py
```

## License

This is a utility script for interacting with the Rise Labs testnet explorer API.

## Contributing

Feel free to submit issues and enhancement requests!

## Support

For API documentation, visit: https://explorer.testnet.riselabs.xyz/api-docs

## Disclaimer

This is an unofficial client. Always refer to the official API documentation for the most up-to-date information.