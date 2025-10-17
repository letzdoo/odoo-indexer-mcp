"""FastMCP server for Odoo index."""

import logging
from typing import Optional

from fastmcp import FastMCP

from . import tools

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
    limit: int = 20,
    offset: int = 0
) -> dict:
    """Search for indexed Odoo elements by name.

    Args:
        query: Search term (supports SQL LIKE patterns with %)
        item_type: Filter by type (model/field/function/view/menu/action/controller_route/access_right/record_rule/scheduled_action/report_template/module/xml_id)
        module: Filter by module name
        parent_name: Filter by parent (e.g., model name for fields/methods)
        limit: Maximum results per page (default: 20, max: 100)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        Search results with file locations, line numbers, and pagination info
    """
    limit = min(limit, 100)  # Cap at 100
    return tools.search_odoo_index(query, item_type, module, parent_name, limit, offset)


@mcp.tool()
def get_item_details(
    item_type: str,
    name: str,
    parent_name: Optional[str] = None,
    module: Optional[str] = None
) -> dict:
    """Get complete details for a specific Odoo element.

    Args:
        item_type: Type of item (model/field/function/view/menu/action/etc)
        name: Item name (e.g., 'sale.order' for model, 'partner_id' for field)
        parent_name: Parent name (required for fields/methods - the model name)
        module: Module name (optional, helps disambiguate)

    Returns:
        Item details with all references and related items
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


def main():
    """Run the MCP server."""
    logger.info("Starting Odoo Index MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
