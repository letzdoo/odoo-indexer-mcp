# Odoo Index MCP

A lightweight MCP (Model Context Protocol) server for indexing Odoo code elements. Designed to help coding agents quickly look up models, fields, functions, views, and other Odoo components with their exact file locations.

## Features

- **Fast Indexing**: Uses AST parsing for Python and lxml for XML
- **Incremental Updates**: Only re-indexes changed files (MD5 hash tracking)
- **Comprehensive Coverage**: Indexes models, fields, methods, views, menus, actions, access rights, rules, scheduled actions, report templates, controller routes, and more
- **Multiple References**: Tracks all occurrences (definition, inheritance, override, etc.)
- **Lightweight**: Pure SQLite, no vector DB, no embeddings
- **MCP Compatible**: Works with Claude Desktop and other MCP clients

## What Gets Indexed

### Core Elements
- **Models**: Name, type (regular/transient/abstract), inheritance
- **Fields**: Name, type, attributes (required, readonly, compute, related, etc.)
- **Functions/Methods**: Name, decorators (@api.depends, @api.onchange, etc.)
- **Views**: Type (form/tree/kanban/search), model, inheritance
- **Menus**: Hierarchy, actions, security groups
- **Actions**: Type (act_window/server/report), models, domains
- **Access Rights**: Model permissions by security group
- **Record Rules**: Domain-based access rules
- **Controller Routes**: HTTP/JSON routes with auth types
- **Scheduled Actions**: Cron jobs with intervals
- **Report Templates**: QWeb templates
- **Module Metadata**: Dependencies, version, description

### Multiple References
Each element can have multiple file:line references:
- **definition**: Where it's originally defined
- **inheritance**: Where models are extended
- **override**: Where methods/fields are overridden
- **reference**: Where it's referenced
- **modification**: Where views are modified with xpath

## Installation

### Prerequisites
- Python 3.10+
- uv package manager

### Setup

```bash
# Clone or navigate to the project
cd odoo-index-mcp

# Create .env file
cp .env.example .env

# Edit .env and set your ODOO_PATH
nano .env

# Install dependencies with uv
uv sync
```

## Usage

### CLI Tool

```bash
# Full indexing
uv run python cli.py --index

# Incremental indexing (skip unchanged files)
uv run python cli.py --index --incremental

# Index specific modules
uv run python cli.py --index --modules sale,account,stock

# Clear database and re-index
uv run python cli.py --clear --index

# Show statistics
uv run python cli.py --stats

# Search from CLI
uv run python cli.py --search "sale.order" --type model
uv run python cli.py --search "partner_id" --type field --module sale

# Search XML IDs
uv run python cli.py --search-xml-id "action_view_%"
uv run python cli.py --search-xml-id "action_view_sale_order" --module sale
```

### MCP Server

```bash
# Start MCP server
uv run odoo-index-mcp
```

### Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "odoo-index": {
      "command": "uv",
      "args": ["run", "odoo-index-mcp"],
      "cwd": "/path/to/odoo-index-mcp",
      "env": {
        "ODOO_PATH": "/path/to/odoo"
      }
    }
  }
}
```

## MCP Tools

The server provides 7 MCP tools:

### 1. `search_odoo_index`
Search for elements by name with wildcard support.

**Parameters:**
- `query` (str): Search term (supports SQL LIKE with %)
- `item_type` (str, optional): Filter by type
- `module` (str, optional): Filter by module
- `parent_name` (str, optional): Filter by parent (for fields/methods)
- `limit` (int, default=50): Max results

**Example:**
```python
search_odoo_index(query="sale.order", item_type="model")
search_odoo_index(query="partner%", item_type="field", module="sale")
```

### 2. `get_item_details`
Get complete details for a specific element including related items.

**Parameters:**
- `item_type` (str): Type of item
- `name` (str): Item name
- `parent_name` (str, optional): Parent (for fields/methods)
- `module` (str, optional): Module to disambiguate

**Example:**
```python
get_item_details(item_type="model", name="sale.order")
get_item_details(item_type="field", name="partner_id", parent_name="sale.order")
```

### 3. `list_modules`
List all indexed modules with item counts.

**Parameters:**
- `pattern` (str, optional): Filter by name pattern

**Example:**
```python
list_modules()
list_modules(pattern="sale")
```

### 4. `get_module_stats`
Get detailed statistics for a module.

**Parameters:**
- `module` (str): Module name

**Example:**
```python
get_module_stats(module="sale")
```

### 5. `find_references`
Find all references to an element across the codebase.

**Parameters:**
- `item_type` (str): Type of item
- `name` (str): Item name
- `reference_type` (str, optional): Filter by type (definition/inheritance/etc)

**Example:**
```python
find_references(item_type="model", name="sale.order")
find_references(item_type="model", name="sale.order", reference_type="inheritance")
```

### 6. `search_by_attribute`
Advanced search by element attributes.

**Parameters:**
- `item_type` (str): Type to search
- `attribute_filters` (dict): Attribute filters
- `module` (str, optional): Filter by module
- `limit` (int, default=50): Max results

**Example:**
```python
# Find all Many2one fields
search_by_attribute(
    item_type="field",
    attribute_filters={"field_type": "Many2one"}
)

# Find all transient models (wizards)
search_by_attribute(
    item_type="model",
    attribute_filters={"model_type": "transient"}
)

# Find all form views
search_by_attribute(
    item_type="view",
    attribute_filters={"view_type": "form"}
)
```

### 7. `search_xml_id`
Search for XML IDs by name pattern.

**Parameters:**
- `query` (str): Search term (supports SQL LIKE patterns with %)
- `module` (str, optional): Filter by module
- `limit` (int, default=50): Max results

**Example:**
```python
# Find all action_view XML IDs
search_xml_id(query="action_view_%")

# Find specific action
search_xml_id(query="action_view_sale_order")

# Find form views in sale module
search_xml_id(query="%_form_view", module="sale")
```

## Performance

- **Indexing Speed**: ~500-1000 files/second with concurrent processing and async database operations
- **Database Size**: ~50-100MB for typical Odoo installation
- **Search Speed**: <50ms for exact match, <200ms for pattern search
- **Memory Usage**: <500MB during indexing, <100MB when serving
- **Database**: Async connection pooling with aiosqlite for efficient concurrent writes

## Configuration

Environment variables in `.env`:

```bash
# Required
ODOO_PATH=/path/to/odoo

# Optional (with defaults)
SQLITE_DB_PATH=./odoo_index.db
LOG_LEVEL=INFO
MAX_CONCURRENT_MODULES=4
MAX_CONCURRENT_FILES=8
```

## Project Structure

```
odoo-index-mcp/
├── pyproject.toml              # uv project config
├── .env.example                # Environment template
├── .python-version             # Python version
├── README.md                   # This file
├── cli.py                      # CLI tool
├── odoo_index_mcp/
│   ├── __init__.py
│   ├── config.py               # Configuration
│   ├── database.py             # SQLite operations
│   ├── indexer.py              # Main indexing logic
│   ├── server.py               # FastMCP server
│   ├── tools.py                # MCP tool implementations
│   └── parsers/
│       ├── __init__.py
│       ├── python_parser.py    # AST parsing for Python
│       ├── xml_parser.py       # XML parsing for views/data
│       ├── csv_parser.py       # CSV parsing for access rights
│       └── manifest_parser.py  # Manifest file parsing
```

## Database Schema

The index uses a normalized SQLite schema with 3 main tables:

1. **indexed_items**: Core item data (type, name, module, attributes JSON)
2. **item_references**: File locations (many-to-one with items)
3. **file_metadata**: File hashes for incremental indexing

All queries use proper indexes for fast lookups.

## Development

```bash
# Install development dependencies
uv sync

# Run tests (TODO: add tests)
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .
```

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation in ODOO_CODE_INDEXER.md

## Roadmap

Future enhancements (not in v1):
- [ ] Call graph analysis
- [ ] Full-text search in method bodies
- [ ] Dependency graph visualization
- [ ] Watch mode (auto-reindex on changes)
- [ ] Web UI for browsing
- [ ] Export to other formats
