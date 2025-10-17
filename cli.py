"""Command-line tool for Odoo indexer."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from odoo_index_mcp import config
from odoo_index_mcp.database import Database
from odoo_index_mcp.indexer import index_odoo_codebase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Odoo Index CLI - Index and search Odoo codebase'
    )

    parser.add_argument(
        '--index',
        action='store_true',
        help='Run indexing process'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        default=True,
        help='Use incremental indexing (skip unchanged files) - default: True'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Force full re-indexing (ignore file hashes)'
    )

    parser.add_argument(
        '--modules',
        type=str,
        help='Comma-separated list of modules to index (e.g., sale,account,stock)'
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear database before indexing'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show indexing statistics'
    )

    parser.add_argument(
        '--search',
        type=str,
        help='Search for an item by name'
    )

    parser.add_argument(
        '--type',
        type=str,
        help='Filter search by item type (model/field/function/view/etc)'
    )

    parser.add_argument(
        '--module',
        type=str,
        help='Filter search by module name'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum search results (default: 20)'
    )

    parser.add_argument(
        '--search-xml-id',
        type=str,
        help='Search for XML IDs by name pattern (supports %% wildcards, e.g., action_view_%%)'
    )

    args = parser.parse_args()

    # Handle indexing
    if args.index:
        try:
            incremental = not args.full
            module_filter = None
            if args.modules:
                module_filter = [m.strip() for m in args.modules.split(',')]

            logger.info("Starting indexing...")
            asyncio.run(
                index_odoo_codebase(
                    incremental=incremental,
                    module_filter=module_filter,
                    clear_db=args.clear
                )
            )
            logger.info("Indexing completed successfully")

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            sys.exit(1)

    # Handle stats
    elif args.stats:
        try:
            db = Database(config.SQLITE_DB_PATH)
            stats = db.get_module_stats()

            print("\n=== Odoo Index Statistics ===\n")
            print(f"Total modules: {stats['total_modules']}")
            print(f"\nModules:")

            for module_info in stats['modules'][:20]:  # Show top 20
                print(f"  - {module_info['module']}: {module_info['total_items']} items")

            if len(stats['modules']) > 20:
                print(f"  ... and {len(stats['modules']) - 20} more modules")

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            sys.exit(1)

    # Handle search
    elif args.search:
        try:
            db = Database(config.SQLITE_DB_PATH)
            items = db.search_items(
                args.search,
                args.type,
                args.module,
                limit=args.limit
            )

            print(f"\n=== Search Results for '{args.search}' ===\n")
            print(f"Found {len(items)} items\n")

            for item in items:
                print(f"[{item['item_type']}] {item['name']}")
                if item['parent_name']:
                    print(f"  Parent: {item['parent_name']}")
                print(f"  Module: {item['module']}")

                # Show attributes
                if item['attributes']:
                    print(f"  Attributes:")
                    for key, value in item['attributes'].items():
                        if key in ('description', 'display_name', 'field_type', 'view_type', 'action_type'):
                            print(f"    {key}: {value}")

                # Show references
                print(f"  References ({len(item['references'])}):")
                for ref in item['references'][:3]:  # Show first 3
                    print(f"    {ref['file']}:{ref['line']} ({ref['type']})")

                if len(item['references']) > 3:
                    print(f"    ... and {len(item['references']) - 3} more")

                print()

        except Exception as e:
            logger.error(f"Search failed: {e}")
            sys.exit(1)

    # Handle XML ID search
    elif args.search_xml_id:
        try:
            from odoo_index_mcp import tools
            result = tools.search_xml_id(
                args.search_xml_id,
                args.module,
                limit=args.limit
            )

            print(f"\n=== XML ID Search Results for '{args.search_xml_id}' ===\n")
            print(f"Found {result['total']} items\n")

            for item in result['results']:
                print(f"[{item['item_type']}] {item['name']}")
                print(f"  Module: {item['module']}")

                # Show attributes
                if item['attributes']:
                    print(f"  Attributes:")
                    for key, value in item['attributes'].items():
                        if key in ('model', 'display_name', 'view_type', 'action_type', 'res_model'):
                            print(f"    {key}: {value}")

                # Show references
                print(f"  References ({len(item['references'])}):")
                for ref in item['references'][:3]:  # Show first 3
                    print(f"    {ref['file']}:{ref['line']} ({ref['type']})")

                if len(item['references']) > 3:
                    print(f"    ... and {len(item['references']) - 3} more")

                print()

        except Exception as e:
            logger.error(f"XML ID search failed: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
