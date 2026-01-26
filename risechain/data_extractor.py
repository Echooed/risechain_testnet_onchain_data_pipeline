"""
Rise Labs Testnet Data Extractor
Extracts data from the API and saves it to various formats (JSON, CSV)
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from rise_explorer_scraper import RiseExplorerClient
import logging

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Extracts blockchain data and saves it to files.
    """

    def __init__(self, output_dir: str = "extracted_data"):
        """
        Initialize the data extractor.

        Args:
            output_dir: Directory where extracted data will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = RiseExplorerClient()

        # Create subdirectories
        self.json_dir = self.output_dir / "json"
        self.csv_dir = self.output_dir / "csv"
        self.json_dir.mkdir(exist_ok=True)
        self.csv_dir.mkdir(exist_ok=True)

        logger.info(f"Data will be saved to: {self.output_dir.absolute()}")

    def _save_json(self, data: Any, filename: str, subdir: str = ""):
        """Save data as JSON file."""
        if subdir:
            save_dir = self.json_dir / subdir
            save_dir.mkdir(exist_ok=True)
        else:
            save_dir = self.json_dir

        filepath = save_dir / f"{filename}.json"

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved JSON: {filepath}")
        return filepath

    def _save_csv(self, data: List[Dict], filename: str, subdir: str = ""):
        """Save data as CSV file."""
        if not data:
            logger.warning(f"No data to save for {filename}")
            return None

        if subdir:
            save_dir = self.csv_dir / subdir
            save_dir.mkdir(exist_ok=True)
        else:
            save_dir = self.csv_dir

        filepath = save_dir / f"{filename}.csv"

        # Get all unique keys from all records
        keys = set()
        for record in data:
            keys.update(record.keys())
        keys = sorted(keys)

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Saved CSV: {filepath}")
        return filepath

    def extract_account_data(
            self,
            address: str,
            include_transactions: bool = True,
            include_tokens: bool = True,
            max_transactions: int = 100
    ) -> Dict[str, Path]:
        """
        Extract all data for an account and save to files.

        Args:
            address: Account address
            include_transactions: Whether to fetch transactions
            include_tokens: Whether to fetch token data
            max_transactions: Maximum number of transactions to fetch

        Returns:
            Dictionary of saved file paths
        """
        logger.info(f"Extracting account data for {address}")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        account_dir = f"account_{address[:10]}"

        # 1. Get balance
        balance_result = self.client.get_balance(address)
        saved_files['balance'] = self._save_json(
            balance_result,
            f"{timestamp}_balance",
            account_dir
        )

        # 2. Get transactions
        if include_transactions:
            all_transactions = []
            page = 1
            offset = min(100, max_transactions)

            while len(all_transactions) < max_transactions:
                tx_result = self.client.get_transactions(
                    address=address,
                    page=page,
                    offset=offset,
                    sort='desc'
                )

                if tx_result.get('status') == '1':
                    txs = tx_result.get('result', [])
                    if not txs:
                        break
                    all_transactions.extend(txs)
                    page += 1
                else:
                    break

            # Limit to max_transactions
            all_transactions = all_transactions[:max_transactions]

            # Save as JSON
            saved_files['transactions_json'] = self._save_json(
                all_transactions,
                f"{timestamp}_transactions",
                account_dir
            )

            # Save as CSV
            if all_transactions:
                saved_files['transactions_csv'] = self._save_csv(
                    all_transactions,
                    f"{timestamp}_transactions",
                    account_dir
                )

        # 3. Get token list
        if include_tokens:
            token_result = self.client.get_token_list(address)

            if token_result.get('status') == '1':
                tokens = token_result.get('result', [])

                # Save as JSON
                saved_files['tokens_json'] = self._save_json(
                    tokens,
                    f"{timestamp}_tokens",
                    account_dir
                )

                # Save as CSV
                if tokens:
                    saved_files['tokens_csv'] = self._save_csv(
                        tokens,
                        f"{timestamp}_tokens",
                        account_dir
                    )

        logger.info(f"Account data extraction complete. Saved {len(saved_files)} files.")
        return saved_files

    def extract_token_transfers(
            self,
            address: str,
            contract_address: Optional[str] = None,
            max_transfers: int = 1000
    ) -> Dict[str, Path]:
        """
        Extract token transfers for an address.

        Args:
            address: Account address
            contract_address: Optional token contract filter
            max_transfers: Maximum number of transfers to fetch

        Returns:
            Dictionary of saved file paths
        """
        logger.info(f"Extracting token transfers for {address}")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        all_transfers = []
        page = 1
        offset = 100

        while len(all_transfers) < max_transfers:
            result = self.client.get_token_transfers(
                address=address,
                contractaddress=contract_address,
                page=page,
                offset=offset,
                sort='desc'
            )

            if result.get('status') == '1':
                transfers = result.get('result', [])
                if not transfers:
                    break
                all_transfers.extend(transfers)
                page += 1
            else:
                break

        # Limit to max_transfers
        all_transfers = all_transfers[:max_transfers]

        if all_transfers:
            # Save as JSON
            saved_files['json'] = self._save_json(
                all_transfers,
                f"{timestamp}_token_transfers_{address[:10]}",
                "token_transfers"
            )

            # Save as CSV
            saved_files['csv'] = self._save_csv(
                all_transfers,
                f"{timestamp}_token_transfers_{address[:10]}",
                "token_transfers"
            )

        logger.info(f"Extracted {len(all_transfers)} token transfers")
        return saved_files

    def extract_contract_data(self, contract_address: str) -> Dict[str, Path]:
        """
        Extract contract source code and ABI.

        Args:
            contract_address: Contract address

        Returns:
            Dictionary of saved file paths
        """
        logger.info(f"Extracting contract data for {contract_address}")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        contract_dir = f"contract_{contract_address[:10]}"

        # Get source code
        source_result = self.client.get_contract_source_code(contract_address)

        if source_result.get('status') == '1':
            contracts = source_result.get('result', [])

            if contracts:
                contract = contracts[0]

                # Save full data as JSON
                saved_files['full_data'] = self._save_json(
                    contract,
                    f"{timestamp}_contract_full",
                    contract_dir
                )

                # Save source code separately
                source_code = contract.get('SourceCode', '')
                source_file = self.output_dir / contract_dir / f"{timestamp}_source.sol"
                source_file.parent.mkdir(exist_ok=True)

                with open(source_file, 'w') as f:
                    f.write(source_code)
                saved_files['source_code'] = source_file
                logger.info(f"Saved source code: {source_file}")

                # Save ABI separately
                abi = contract.get('ABI', '')
                abi_file = self.output_dir / contract_dir / f"{timestamp}_abi.json"

                try:
                    abi_parsed = json.loads(abi)
                    with open(abi_file, 'w') as f:
                        json.dump(abi_parsed, f, indent=2)
                    saved_files['abi'] = abi_file
                    logger.info(f"Saved ABI: {abi_file}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse ABI as JSON")
        else:
            logger.warning(f"Contract not verified or not found: {contract_address}")

        return saved_files

    def extract_block_range(
            self,
            start_block: int,
            end_block: int
    ) -> Dict[str, Path]:
        """
        Extract block rewards for a range of blocks.

        Args:
            start_block: Starting block number
            end_block: Ending block number

        Returns:
            Dictionary of saved file paths
        """
        logger.info(f"Extracting blocks {start_block} to {end_block}")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        block_data = []

        for block_num in range(start_block, end_block + 1):
            result = self.client.get_block_reward(block_num)

            if result.get('status') == '1':
                block_data.append(result.get('result', {}))

            # Progress logging
            if (block_num - start_block + 1) % 10 == 0:
                logger.info(f"Processed {block_num - start_block + 1} blocks...")

        if block_data:
            # Save as JSON
            saved_files['json'] = self._save_json(
                block_data,
                f"{timestamp}_blocks_{start_block}_to_{end_block}",
                "blocks"
            )

            # Save as CSV
            saved_files['csv'] = self._save_csv(
                block_data,
                f"{timestamp}_blocks_{start_block}_to_{end_block}",
                "blocks"
            )

        logger.info(f"Extracted {len(block_data)} blocks")
        return saved_files

    def extract_token_holders(
            self,
            contract_address: str,
            max_holders: int = 100
    ) -> Dict[str, Path]:
        """
        Extract token holder information.

        Args:
            contract_address: Token contract address
            max_holders: Maximum number of holders to fetch

        Returns:
            Dictionary of saved file paths
        """
        logger.info(f"Extracting token holders for {contract_address}")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get token info first
        token_info_result = self.client.get_token_info(contract_address)
        token_info = {}

        if token_info_result.get('status') == '1':
            token_info = token_info_result.get('result', {})

        # Get holders
        all_holders = []
        page = 1
        offset = min(100, max_holders)

        while len(all_holders) < max_holders:
            result = self.client.get_token_holders(
                contractaddress=contract_address,
                page=page,
                offset=offset
            )

            if result.get('status') == '1':
                holders = result.get('result', [])
                if not holders:
                    break
                all_holders.extend(holders)
                page += 1
            else:
                break

        # Limit to max_holders
        all_holders = all_holders[:max_holders]

        if all_holders:
            # Combine token info with holders
            data_to_save = {
                'token_info': token_info,
                'holders': all_holders,
                'total_holders_fetched': len(all_holders)
            }

            # Save as JSON
            saved_files['json'] = self._save_json(
                data_to_save,
                f"{timestamp}_token_holders_{contract_address[:10]}",
                "token_holders"
            )

            # Save holders as CSV
            saved_files['csv'] = self._save_csv(
                all_holders,
                f"{timestamp}_token_holders_{contract_address[:10]}",
                "token_holders"
            )

        logger.info(f"Extracted {len(all_holders)} token holders")
        return saved_files

    def extract_network_stats(self) -> Dict[str, Path]:
        """
        Extract network-wide statistics.

        Returns:
            Dictionary of saved file paths
        """
        logger.info("Extracting network statistics")
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        stats = {
            'timestamp': timestamp,
            'date': datetime.now().isoformat()
        }

        # Get ETH supply
        supply_result = self.client.get_eth_supply()
        if supply_result.get('status') == '1':
            stats['eth_supply_wei'] = supply_result.get('result')
            stats['eth_supply_eth'] = int(supply_result.get('result', 0)) / 10 ** 18

        # Get coin price
        price_result = self.client.get_coin_price()
        if price_result.get('status') == '1':
            stats['price'] = price_result.get('result', {})

        # Save as JSON
        saved_files['json'] = self._save_json(
            stats,
            f"{timestamp}_network_stats",
            "stats"
        )

        logger.info("Network statistics extracted")
        return saved_files

    def close(self):
        """Close the client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """
    Example usage of the data extractor.
    """

    # Sample addresses (replace with real ones)
    sample_address = "0x95426f2bc716022fcf1def006dbc4bb81f5b5164"
    sample_contract = "0x95426f2bc716022fcf1def006dbc4bb81f5b5164"

    with DataExtractor(output_dir="rise_testnet_data") as extractor:
        print("\n" + "=" * 60)
        print("Rise Labs Testnet Data Extractor")
        print("=" * 60 + "\n")

        # 1. Extract account data
        print("1. Extracting account data...")
        account_files = extractor.extract_account_data(
            address=sample_address,
            include_transactions=True,
            include_tokens=True,
            max_transactions=50
        )
        print(f"   Saved {len(account_files)} files")

        # 2. Extract network stats
        print("\n2. Extracting network statistics...")
        stats_files = extractor.extract_network_stats()
        print(f"   Saved {len(stats_files)} files")

        # 3. Extract block range
        print("\n3. Extracting block data...")
        block_files = extractor.extract_block_range(
            start_block=34090,
            end_block=34100
        )
        print(f"   Saved {len(block_files)} files")

        print("\n" + "=" * 60)
        print(f"Data extraction complete!")
        print(f"Check the 'rise_testnet_data' directory for all extracted files")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()