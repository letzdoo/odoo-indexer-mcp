"""FastMCP server for Odoo index."""

import asyncio
import logging
from typing import Optional

from fastmcp import FastMCP

from . import config, tools
from .database import Database
from .indexer import index_odoo_codebase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("Odoo Index MCP")


@mcp.tool()
def search_odoo_index(
    query: str,
    item_type: Optional[str] = None,
    module: Optional[str] = None,
    parent_name: Optional[str] = None,
    limit: int = 5,
    offset: int = 0
) -> dict:
    """Search for indexed Odoo elements by name (returns CONCISE results).

    This tool returns minimal, essential information only:
    - name, type, module, file, line number
    - Key attributes (description, field_type, etc.)

    Results are sorted by relevance (exact matches first, then by dependency depth).
    The most relevant results are typically in the first 5 items.

    Use get_item_details() if you need full details about a specific item.

    PAGINATION: Results include 'has_more' and 'next_offset' fields. If has_more=true,
    call again with offset=next_offset to get more results.

    Args:
        query: Search term (supports SQL LIKE patterns with %)
        item_type: Filter by type (model/field/function/view/menu/action/etc)
        module: Filter by module name
        parent_name: Filter by parent (e.g., model name for fields/methods)
        limit: Maximum results per page (default: 5, max: 50)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        {
            total: Total matching items,
            returned: Number of items in this page,
            has_more: Whether more results are available,
            next_offset: Offset to use for next page (null if no more),
            results: Array of concise item data
        }
    """
    limit = min(limit, 50)  # Cap at 50
    return tools.search_odoo_index(query, item_type, module, parent_name, limit, offset)


@mcp.tool()
def get_item_details(
    item_type: str,
    name: str,
    parent_name: Optional[str] = None,
    module: Optional[str] = None
) -> dict:
    """Get FULL details for a specific Odoo element.

    WARNING: This returns ALL information including ALL references, ALL fields, ALL methods,
    ALL views, etc. for models. Use search_odoo_index() for quick lookups.

    Use this ONLY when you specifically need:
    - All references (inheritance, overrides, usages)
    - All fields/methods of a model
    - All views/actions related to a model
    - Full attribute details

    Args:
        item_type: Type of item (model/field/function/view/menu/action/etc)
        name: Item name (e.g., 'sale.order' for model, 'partner_id' for field)
        parent_name: Parent name (required for fields/methods - the model name)
        module: Module name (optional, helps disambiguate)

    Returns:
        Complete item details with all references and related items
    """
    return tools.get_item_details(item_type, name, parent_name, module)


@mcp.tool()
def list_modules(pattern: Optional[str] = None) -> dict:
    """List all indexed Odoo modules.

    Args:
        pattern: Filter by module name pattern (optional)

    Returns:
        List of modules with item counts
    """
    return tools.list_modules(pattern)


@mcp.tool()
def get_module_stats(module: str) -> dict:
    """Get detailed statistics for a specific Odoo module.

    Args:
        module: Module name (e.g., 'sale', 'account', 'stock')

    Returns:
        Module statistics including counts by item type
    """
    return tools.get_module_stats(module)


@mcp.tool()
def find_references(
    item_type: str,
    name: str,
    reference_type: Optional[str] = None
) -> dict:
    """Find all references to a specific Odoo element across the codebase.

    Args:
        item_type: Type of item (model/field/function/view/etc)
        name: Item name
        reference_type: Filter by reference type (definition/inheritance/override/reference/modification)

    Returns:
        All file locations where this item is referenced
    """
    return tools.find_references(item_type, name, reference_type)


@mcp.tool()
def search_by_attribute(
    item_type: str,
    attribute_filters: dict,
    module: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """Search Odoo elements by their attributes (advanced filtering).

    Args:
        item_type: Type of item to search (model/field/view/action/etc)
        attribute_filters: Dict of attribute filters (e.g., {"field_type": "Many2one", "required": true})
        module: Filter by module (optional)
        limit: Maximum results per page (default: 20, max: 100)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        Matching items with their details and pagination info

    Examples:
        - Find all Many2one fields: item_type="field", attribute_filters={"field_type": "Many2one"}
        - Find all transient models: item_type="model", attribute_filters={"model_type": "transient"}
        - Find all form views: item_type="view", attribute_filters={"view_type": "form"}
    """
    limit = min(limit, 100)  # Cap at 100
    return tools.search_by_attribute(item_type, attribute_filters, module, limit, offset)


@mcp.tool()
def search_xml_id(
    query: str,
    module: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """Search for XML IDs by name pattern.

    This tool searches across all Odoo elements that have XML IDs (views, actions, menus,
    rules, scheduled actions, report templates, and other data records).

    Args:
        query: Search term (supports SQL LIKE patterns with %, e.g., 'action_view_%')
        module: Filter by module name (optional)
        limit: Maximum results per page (default: 20, max: 100)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        XML IDs with their details including item type, model, file location, line numbers, and pagination info

    Examples:
        - Find all action views: query="action_view_%"
        - Find specific action: query="action_view_sale_order"
        - Find form views: query="%_form_view"
    """
    limit = min(limit, 100)  # Cap at 100
    return tools.search_xml_id(query, module, limit, offset)


# Global variable to track indexing status
_indexing_status = {
    "is_running": False,
    "start_time": None,
    "incremental": None,
    "modules": None
}


async def _run_indexing_task(incremental: bool, module_filter: Optional[list[str]], clear_db: bool):
    """Background task to run indexing."""
    global _indexing_status
    try:
        import time
        _indexing_status["is_running"] = True
        _indexing_status["start_time"] = time.time()
        _indexing_status["incremental"] = incremental
        _indexing_status["modules"] = module_filter

        logger.info(f"Background indexing started (incremental={incremental}, modules={module_filter}, clear_db={clear_db})")
        await index_odoo_codebase(
            incremental=incremental,
            module_filter=module_filter,
            clear_db=clear_db
        )
        logger.info("Background indexing completed successfully")
    except Exception as e:
        logger.error(f"Background indexing failed: {e}", exc_info=True)
    finally:
        _indexing_status["is_running"] = False
        _indexing_status["start_time"] = None


@mcp.tool()
async def update_index(
    incremental: bool = True,
    modules: Optional[str] = None,
    clear_db: bool = False
) -> dict:
    """Update the Odoo index by scanning and parsing the codebase.

    This tool triggers a re-indexing of the Odoo codebase in the background. By default,
    it performs incremental indexing (only re-parsing changed files). The function returns
    immediately while indexing continues in the background.

    Args:
        incremental: If True, skip unchanged files (default: True). Set to False for full re-index.
        modules: Comma-separated list of module names to index (e.g., "sale,account,stock").
                If not provided, all modules will be indexed.
        clear_db: If True, clear the entire database before indexing (default: False).
                WARNING: This will delete all existing index data!

    Returns:
        Status message confirming indexing has started

    Examples:
        - Incremental update: update_index()
        - Full re-index: update_index(incremental=False)
        - Index specific modules: update_index(modules="sale,account")
        - Clear and re-index: update_index(clear_db=True, incremental=False)
    """
    try:
        module_filter = None
        if modules:
            module_filter = [m.strip() for m in modules.split(',')]

        # Start indexing as a background task
        asyncio.create_task(_run_indexing_task(incremental, module_filter, clear_db))

        message = "Index update started in background"
        if module_filter:
            message += f" for modules: {', '.join(module_filter)}"
        message += ". Check server logs for progress."

        logger.info(message)
        return {
            "success": True,
            "status": "started",
            "message": message
        }
    except Exception as e:
        error_msg = f"Failed to start index update: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg
        }


@mcp.tool()
def get_index_status() -> dict:
    """Get the current status of the index and any ongoing indexing operations.

    Returns information about:
    - Database location
    - Whether indexing is currently running
    - Total number of indexed items
    - Number of modules indexed
    - Breakdown by item type
    - Indexing progress (if running)

    Returns:
        Status information including database path, item counts and indexing state
    """
    try:
        import time
        db = Database(config.SQLITE_DB_PATH)

        # Get total items and modules count
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Total items
            cursor.execute("SELECT COUNT(*) as count FROM indexed_items")
            row = cursor.fetchone()
            total_items = row['count'] if row else 0

            # Total modules
            cursor.execute("SELECT COUNT(DISTINCT module) as count FROM indexed_items")
            row = cursor.fetchone()
            total_modules = row['count'] if row else 0

            # Counts by type
            cursor.execute("""
                SELECT item_type, COUNT(*) as count
                FROM indexed_items
                GROUP BY item_type
                ORDER BY count DESC
            """)
            counts_by_type = {row['item_type']: row['count'] for row in cursor.fetchall()}

        # Build response
        response = {
            "database_path": str(config.SQLITE_DB_PATH.resolve()),
            "total_items": total_items,
            "total_modules": total_modules,
            "counts_by_type": counts_by_type,
            "indexing": {
                "is_running": _indexing_status["is_running"],
            }
        }

        # Add indexing details if running
        if _indexing_status["is_running"]:
            elapsed = int(time.time() - _indexing_status["start_time"])
            response["indexing"]["elapsed_seconds"] = elapsed
            response["indexing"]["incremental"] = _indexing_status["incremental"]
            if _indexing_status["modules"]:
                response["indexing"]["modules"] = _indexing_status["modules"]

        return response

    except Exception as e:
        logger.error(f"Failed to get index status: {e}", exc_info=True)
        return {
            "error": f"Failed to get index status: {str(e)}"
        }


def _check_index_exists() -> bool:
    """Check if the database has any indexed items.

    Returns:
        True if index exists and has data, False otherwise
    """
    try:
        db = Database(config.SQLITE_DB_PATH)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM indexed_items")
            row = cursor.fetchone()
            count = row['count'] if row else 0
            return count > 0
    except Exception as e:
        logger.warning(f"Could not check index status: {e}")
        return False


def _start_background_indexing():
    """Start background indexing process in a separate thread."""
    import threading
    import time

    def run_indexing():
        global _indexing_status
        try:
            _indexing_status["is_running"] = True
            _indexing_status["start_time"] = time.time()
            _indexing_status["incremental"] = False
            _indexing_status["modules"] = None

            logger.info("Starting background indexing (no index found)...")
            asyncio.run(index_odoo_codebase(incremental=False, clear_db=False))
            logger.info("Background indexing completed successfully")
        except Exception as e:
            logger.error(f"Background indexing failed: {e}", exc_info=True)
        finally:
            _indexing_status["is_running"] = False
            _indexing_status["start_time"] = None

    thread = threading.Thread(target=run_indexing, daemon=True, name="IndexerThread")
    thread.start()
    logger.info("Background indexing thread started")


def main():
    """Run the MCP server."""
    logger.info("Starting Odoo Index MCP server")

    # Check if index exists
    if not _check_index_exists():
        logger.warning("No index found in database. Starting background indexing...")
        _start_background_indexing()
        logger.info("Server will continue to start while indexing runs in background")
    else:
        logger.info("Index found in database")

    mcp.run()


if __name__ == "__main__":
    main()
