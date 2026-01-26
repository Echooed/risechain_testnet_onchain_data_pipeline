#!/usr/bin/env python3
"""
Command-line interface for extracting data from Rise Labs testnet explorer.
"""

import argparse
import sys
from data_extractor import DataExtractor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_account(args):
    """Extract account data."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_account_data(
            address=args.address,
            include_transactions=args.transactions,
            include_tokens=args.tokens,
            max_transactions=args.max_tx
        )
        print(f"\n✓ Extracted account data. Saved {len(files)} files.")


def extract_transactions(args):
    """Extract transactions for an address."""
    with DataExtractor(output_dir=args.output) as extractor:
        # This uses extract_account_data with only transactions
        files = extractor.extract_account_data(
            address=args.address,
            include_transactions=True,
            include_tokens=False,
            max_transactions=args.limit
        )
        print(f"\n✓ Extracted transactions. Saved {len(files)} files.")


def extract_token_transfers(args):
    """Extract token transfers."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_token_transfers(
            address=args.address,
            contract_address=args.contract,
            max_transfers=args.limit
        )
        print(f"\n✓ Extracted token transfers. Saved {len(files)} files.")


def extract_contract(args):
    """Extract contract data."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_contract_data(
            contract_address=args.address
        )
        print(f"\n✓ Extracted contract data. Saved {len(files)} files.")


def extract_blocks(args):
    """Extract block data."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_block_range(
            start_block=args.start,
            end_block=args.end
        )
        print(f"\n✓ Extracted blocks {args.start}-{args.end}. Saved {len(files)} files.")


def extract_token_holders(args):
    """Extract token holders."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_token_holders(
            contract_address=args.contract,
            max_holders=args.limit
        )
        print(f"\n✓ Extracted token holders. Saved {len(files)} files.")


def extract_stats(args):
    """Extract network statistics."""
    with DataExtractor(output_dir=args.output) as extractor:
        files = extractor.extract_network_stats()
        print(f"\n✓ Extracted network stats. Saved {len(files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description='Extract data from Rise Labs testnet explorer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract account data
  python extract.py account 0x123... --transactions --tokens

  # Extract transactions only
  python extract.py transactions 0x123... --limit 100

  # Extract contract source code
  python extract.py contract 0x456...

  # Extract block range
  python extract.py blocks --start 1000 --end 2000

  # Extract token holders
  python extract.py token-holders 0x789... --limit 50

  # Extract network stats
  python extract.py stats
        """
    )

    parser.add_argument(
        '-o', '--output',
        default='extracted_data',
        help='Output directory (default: extracted_data)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Account command
    account_parser = subparsers.add_parser('account', help='Extract account data')
    account_parser.add_argument('address', help='Account address')
    account_parser.add_argument('--transactions', action='store_true', help='Include transactions')
    account_parser.add_argument('--tokens', action='store_true', help='Include tokens')
    account_parser.add_argument('--max-tx', type=int, default=100, help='Max transactions (default: 100)')
    account_parser.set_defaults(func=extract_account)

    # Transactions command
    tx_parser = subparsers.add_parser('transactions', help='Extract transactions')
    tx_parser.add_argument('address', help='Account address')
    tx_parser.add_argument('--limit', type=int, default=100, help='Max transactions (default: 100)')
    tx_parser.set_defaults(func=extract_transactions)

    # Token transfers command
    token_tx_parser = subparsers.add_parser('token-transfers', help='Extract token transfers')
    token_tx_parser.add_argument('address', help='Account address')
    token_tx_parser.add_argument('--contract', help='Filter by token contract address')
    token_tx_parser.add_argument('--limit', type=int, default=1000, help='Max transfers (default: 1000)')
    token_tx_parser.set_defaults(func=extract_token_transfers)

    # Contract command
    contract_parser = subparsers.add_parser('contract', help='Extract contract data')
    contract_parser.add_argument('address', help='Contract address')
    contract_parser.set_defaults(func=extract_contract)

    # Blocks command
    blocks_parser = subparsers.add_parser('blocks', help='Extract block data')
    blocks_parser.add_argument('--start', type=int, required=True, help='Start block number')
    blocks_parser.add_argument('--end', type=int, required=True, help='End block number')
    blocks_parser.set_defaults(func=extract_blocks)

    # Token holders command
    holders_parser = subparsers.add_parser('token-holders', help='Extract token holders')
    holders_parser.add_argument('contract', help='Token contract address')
    holders_parser.add_argument('--limit', type=int, default=100, help='Max holders (default: 100)')
    holders_parser.set_defaults(func=extract_token_holders)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Extract network statistics')
    stats_parser.set_defaults(func=extract_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n✗ Extraction cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()