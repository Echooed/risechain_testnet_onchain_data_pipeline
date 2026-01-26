"""
Rise Labs Testnet Explorer API Client
A production-ready client for extracting data from the Rise Labs testnet BlockScout API.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RiseExplorerConfig:
    """Configuration for the Rise Explorer API client."""
    base_url: str = "https://explorer.testnet.riselabs.xyz/api"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


class RiseExplorerClient:
    """
    Client for interacting with Rise Labs testnet explorer API.

    This client provides methods to extract various blockchain data including:
    - Account information and balances
    - Transactions and internal transactions
    - Token transfers and balances
    - Contract information
    - Block data
    - Logs and events
    """

    def __init__(self, config: Optional[RiseExplorerConfig] = None):
        """Initialize the Rise Explorer client."""
        self.config = config or RiseExplorerConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RiseExplorerClient/1.0'
        })

    def _make_request(
            self,
            params: Dict[str, Any],
            method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make an API request with retry logic.

        Args:
            params: Query parameters for the API request
            method: HTTP method (GET or POST)

        Returns:
            JSON response from the API

        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        for attempt in range(self.config.max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        self.config.base_url,
                        params=params,
                        timeout=self.config.timeout
                    )
                else:
                    response = self.session.post(
                        self.config.base_url,
                        data=params,
                        timeout=self.config.timeout
                    )

                response.raise_for_status()
                data = response.json()

                # Check API status
                if data.get('status') == '0':
                    logger.warning(f"API returned error: {data.get('message', 'Unknown error')}")

                return data

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

        raise requests.exceptions.RequestException("Max retries exceeded")

    # ============ Account Module ============

    def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get balance for a single address.

        Args:
            address: Ethereum address (0x...)

        Returns:
            Balance information in Wei
        """
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address
        }
        return self._make_request(params)

    def get_balance_multi(self, addresses: List[str]) -> Dict[str, Any]:
        """
        Get balances for multiple addresses (max 20).

        Args:
            addresses: List of Ethereum addresses

        Returns:
            Balance information for all addresses
        """
        if len(addresses) > 20:
            raise ValueError("Maximum 20 addresses allowed")

        params = {
            'module': 'account',
            'action': 'balancemulti',
            'address': ','.join(addresses)
        }
        return self._make_request(params)

    def get_transactions(
            self,
            address: str,
            startblock: Optional[int] = None,
            endblock: Optional[int] = None,
            page: int = 1,
            offset: int = 10,
            sort: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Get transactions for an address (max 10,000).

        Args:
            address: Ethereum address
            startblock: Starting block number
            endblock: Ending block number
            page: Page number for pagination
            offset: Number of records per page
            sort: Sort order ('asc' or 'desc')

        Returns:
            Transaction list
        """
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': sort
        }

        if startblock is not None:
            params['startblock'] = startblock
        if endblock is not None:
            params['endblock'] = endblock

        return self._make_request(params)

    def get_internal_transactions(
            self,
            address: Optional[str] = None,
            txhash: Optional[str] = None,
            startblock: Optional[int] = None,
            endblock: Optional[int] = None,
            page: int = 1,
            offset: int = 10,
            sort: str = 'asc'
    ) -> Dict[str, Any]:
        """
        Get internal transactions by address or transaction hash.

        Args:
            address: Ethereum address (optional)
            txhash: Transaction hash (optional)
            startblock: Starting block number
            endblock: Ending block number
            page: Page number
            offset: Records per page
            sort: Sort order

        Returns:
            Internal transaction list
        """
        if not address and not txhash:
            raise ValueError("Either address or txhash must be provided")

        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'page': page,
            'offset': offset,
            'sort': sort
        }

        if address:
            params['address'] = address
        if txhash:
            params['txhash'] = txhash
        if startblock is not None:
            params['startblock'] = startblock
        if endblock is not None:
            params['endblock'] = endblock

        return self._make_request(params)

    def get_token_transfers(
            self,
            address: str,
            contractaddress: Optional[str] = None,
            startblock: Optional[int] = None,
            endblock: Optional[int] = None,
            page: int = 1,
            offset: int = 10,
            sort: str = 'asc'
    ) -> Dict[str, Any]:
        """
        Get token transfer events for an address.

        Args:
            address: Account address
            contractaddress: Token contract address (optional)
            startblock: Starting block number
            endblock: Ending block number
            page: Page number
            offset: Records per page
            sort: Sort order

        Returns:
            Token transfer events
        """
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': page,
            'offset': offset,
            'sort': sort
        }

        if contractaddress:
            params['contractaddress'] = contractaddress
        if startblock is not None:
            params['startblock'] = startblock
        if endblock is not None:
            params['endblock'] = endblock

        return self._make_request(params)

    def get_token_balance(
            self,
            contractaddress: str,
            address: str
    ) -> Dict[str, Any]:
        """
        Get token balance for a specific token contract.

        Args:
            contractaddress: Token contract address
            address: Account address

        Returns:
            Token balance
        """
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': contractaddress,
            'address': address
        }
        return self._make_request(params)

    def get_token_list(self, address: str) -> Dict[str, Any]:
        """
        Get list of tokens owned by an address.

        Args:
            address: Account address

        Returns:
            List of tokens with balances
        """
        params = {
            'module': 'account',
            'action': 'tokenlist',
            'address': address
        }
        return self._make_request(params)

    # ============ Block Module ============

    def get_block_reward(self, blockno: int) -> Dict[str, Any]:
        """
        Get block reward information.

        Args:
            blockno: Block number

        Returns:
            Block reward details
        """
        params = {
            'module': 'block',
            'action': 'getblockreward',
            'blockno': blockno
        }
        return self._make_request(params)

    def get_block_number_by_timestamp(
            self,
            timestamp: int,
            closest: str = 'before'
    ) -> Dict[str, Any]:
        """
        Get block number by timestamp.

        Args:
            timestamp: Unix timestamp
            closest: 'before' or 'after'

        Returns:
            Block number
        """
        if closest not in ['before', 'after']:
            raise ValueError("closest must be 'before' or 'after'")

        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': timestamp,
            'closest': closest
        }
        return self._make_request(params)

    # ============ Contract Module ============

    def get_contract_abi(self, address: str) -> Dict[str, Any]:
        """
        Get ABI for a verified contract.

        Args:
            address: Contract address

        Returns:
            Contract ABI
        """
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': address
        }
        return self._make_request(params)

    def get_contract_source_code(self, address: str) -> Dict[str, Any]:
        """
        Get source code for a verified contract.

        Args:
            address: Contract address

        Returns:
            Contract source code and metadata
        """
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address
        }
        return self._make_request(params)

    # ============ Transaction Module ============

    def get_transaction_info(self, txhash: str) -> Dict[str, Any]:
        """
        Get detailed transaction information.

        Args:
            txhash: Transaction hash

        Returns:
            Transaction details including logs
        """
        params = {
            'module': 'transaction',
            'action': 'gettxinfo',
            'txhash': txhash
        }
        return self._make_request(params)

    def get_transaction_receipt_status(self, txhash: str) -> Dict[str, Any]:
        """
        Get transaction receipt status.

        Args:
            txhash: Transaction hash

        Returns:
            Receipt status (pass/fail)
        """
        params = {
            'module': 'transaction',
            'action': 'gettxreceiptstatus',
            'txhash': txhash
        }
        return self._make_request(params)

    def get_transaction_status(self, txhash: str) -> Dict[str, Any]:
        """
        Get transaction error status and message.

        Args:
            txhash: Transaction hash

        Returns:
            Error status and description
        """
        params = {
            'module': 'transaction',
            'action': 'getstatus',
            'txhash': txhash
        }
        return self._make_request(params)

    # ============ Logs Module ============

    def get_logs(
            self,
            fromBlock: int,
            toBlock: int,
            address: Optional[str] = None,
            topic0: Optional[str] = None,
            topic1: Optional[str] = None,
            topic2: Optional[str] = None,
            topic3: Optional[str] = None,
            topic0_1_opr: Optional[str] = None,
            topic0_2_opr: Optional[str] = None,
            topic0_3_opr: Optional[str] = None,
            topic1_2_opr: Optional[str] = None,
            topic1_3_opr: Optional[str] = None,
            topic2_3_opr: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get event logs (max 1,000).

        Args:
            fromBlock: Starting block number
            toBlock: Ending block number
            address: Contract address (optional)
            topic0-3: Event topics (optional)
            topic operators: Logical operators for combining topics

        Returns:
            Event logs
        """
        params = {
            'module': 'logs',
            'action': 'getLogs',
            'fromBlock': fromBlock,
            'toBlock': toBlock
        }

        if address:
            params['address'] = address
        if topic0:
            params['topic0'] = topic0
        if topic1:
            params['topic1'] = topic1
        if topic2:
            params['topic2'] = topic2
        if topic3:
            params['topic3'] = topic3
        if topic0_1_opr:
            params['topic0_1_opr'] = topic0_1_opr
        if topic0_2_opr:
            params['topic0_2_opr'] = topic0_2_opr
        if topic0_3_opr:
            params['topic0_3_opr'] = topic0_3_opr
        if topic1_2_opr:
            params['topic1_2_opr'] = topic1_2_opr
        if topic1_3_opr:
            params['topic1_3_opr'] = topic1_3_opr
        if topic2_3_opr:
            params['topic2_3_opr'] = topic2_3_opr

        return self._make_request(params)

    # ============ Token Module ============

    def get_token_info(self, contractaddress: str) -> Dict[str, Any]:
        """
        Get ERC-20 or ERC-721 token information.

        Args:
            contractaddress: Token contract address

        Returns:
            Token metadata
        """
        params = {
            'module': 'token',
            'action': 'getToken',
            'contractaddress': contractaddress
        }
        return self._make_request(params)

    def get_token_holders(
            self,
            contractaddress: str,
            page: int = 1,
            offset: int = 10
    ) -> Dict[str, Any]:
        """
        Get token holders for a contract.

        Args:
            contractaddress: Token contract address
            page: Page number
            offset: Records per page

        Returns:
            List of token holders
        """
        params = {
            'module': 'token',
            'action': 'getTokenHolders',
            'contractaddress': contractaddress,
            'page': page,
            'offset': offset
        }
        return self._make_request(params)

    # ============ Stats Module ============

    def get_token_supply(self, contractaddress: str) -> Dict[str, Any]:
        """
        Get total supply for a token.

        Args:
            contractaddress: Token contract address

        Returns:
            Total supply
        """
        params = {
            'module': 'stats',
            'action': 'tokensupply',
            'contractaddress': contractaddress
        }
        return self._make_request(params)

    def get_eth_supply(self) -> Dict[str, Any]:
        """Get total ETH supply from database."""
        params = {
            'module': 'stats',
            'action': 'ethsupply'
        }
        return self._make_request(params)

    def get_coin_price(self) -> Dict[str, Any]:
        """Get latest native coin price in USD and BTC."""
        params = {
            'module': 'stats',
            'action': 'coinprice'
        }
        return self._make_request(params)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ============ Example Usage ============

def main():
    """Example usage of the Rise Explorer client."""

    # Initialize client
    with RiseExplorerClient() as client:
        # Example 1: Get balance for an address
        address = "0x95426f2bc716022fcf1def006dbc4bb81f5b5164"
        logger.info(f"Fetching balance for {address}")
        balance = client.get_balance(address)
        print(f"\nBalance: {balance}")

        # Example 2: Get transactions for an address
        logger.info(f"Fetching transactions for {address}")
        transactions = client.get_transactions(
            address=address,
            page=1,
            offset=5,
            sort='desc'
        )
        print(f"\nTransactions: {transactions}")

        # Example 3: Get token list
        logger.info(f"Fetching token list for {address}")
        tokens = client.get_token_list(address)
        print(f"\nTokens: {tokens}")

        # Example 4: Get latest block number
        logger.info("Fetching latest block number")
        eth_supply = client.get_eth_supply()
        print(f"\nETH Supply: {eth_supply}")

        # Example 5: Get coin price
        logger.info("Fetching coin price")
        price = client.get_coin_price()
        print(f"\nCoin Price: {price}")


if __name__ == "__main__":
    main()