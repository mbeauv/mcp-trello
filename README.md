# MCP Trello Extension

A Model Context Protocol (MCP) extension for Claude that provides comprehensive Trello integration. This extension allows you to manage Trello workspaces, boards, lists, cards, and checklists directly through Claude.

## Features

### Workspace Management
- **List Workspaces**: View all accessible Trello workspaces
- **Create Workspace**: Create new workspaces with optional display name, description, and website
- **Delete Workspace**: Permanently delete workspaces
- **Set Current Workspace**: Set a workspace as current for context-aware operations
- **Get Current Workspace**: View information about the currently selected workspace

### Board Management
- **List Boards**: View all boards in the current workspace
- **Create Board**: Create new boards with optional descriptions
- **Delete Board**: Permanently delete boards

### List (Column) Management
- **List Board Lists**: View all lists/columns in a specific board
- **Create Board List**: Create new lists with positioning options (top, bottom, or specific position)
- **Delete Board List**: Archive/delete lists from boards

### Card Management
- **List Board Cards**: View all cards in a specific board with detailed information
- **Create Card**: Create new cards with optional descriptions and due dates
- **Update Card**: Modify existing cards (name, description, due date, or move between lists)
- **Delete Card**: Permanently delete cards

### Checklist Management
- **Create Checklist**: Create new checklists in cards
- **Delete Checklist**: Permanently delete checklists
- **Add Checklist Item**: Add items to checklists with optional checked state
- **Delete Checklist Item**: Remove items from checklists

## Prerequisites

- Python 3.11+
- Trello API credentials (API Key and Token)
- Optional: [uv](https://github.com/astral-sh/uv) package manager (for development or uvx installation)

## Installation

### Option 1: Desktop Extension (Recommended for Claude Desktop)

Download the latest `.dxt` file from the [releases page](https://github.com/mbeauv/mcp-trello/releases) and install it directly in Claude Desktop:

1. Open Claude Desktop
2. Go to Settings > Extensions
3. Click "Install Extension" 
4. Select the downloaded `.dxt` file
5. Configure your Trello API credentials in the extension settings

### Option 2: Standard MCP Server (via PyPI)

```bash
pip install mbeauv-mcp-trello
```

### Option 3: Install from source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mbeauv/mcp-trello.git
   cd mcp-trello
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```env
   TRELLO_API_KEY=your_trello_api_key
   TRELLO_TOKEN=your_trello_token
   LOG_LEVEL=INFO
   SAFE_MODE=true
   ```

## Safe Mode

The extension includes a **Safe Mode** feature to prevent accidental destructive operations. When enabled (default), destructive tools are not available:

### Safe Mode Enabled (Default)
- ✅ **Available**: All read and create operations
- ❌ **Disabled**: All delete operations

### Safe Mode Disabled
- ✅ **Available**: All operations including destructive ones

### Destructive Tools (Disabled in Safe Mode)
- `delete_workspace` - Delete workspaces
- `delete_board` - Delete boards  
- `delete_board_list` - Delete lists
- `delete_card` - Delete cards
- `delete_checklist` - Delete checklists
- `delete_checklist_item` - Delete checklist items

### Configuration
Set `SAFE_MODE=false` in your environment variables to enable destructive operations:

```env
SAFE_MODE=false
```

**⚠️ Warning**: Only disable safe mode when you're confident about destructive operations. Deletions are permanent and cannot be undone.

## Getting Trello Credentials

1. **Get your API Key**:
   - Go to [Trello API Keys](https://trello.com/app-key)
   - Copy your API Key

2. **Generate a Token**:
   - Visit: `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=MCP%20Trello&key=YOUR_API_KEY`
   - Replace `YOUR_API_KEY` with your actual API key
   - Authorize the application
   - Copy the generated token

## Configuration

### For Claude Desktop

Create or update your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

#### Option 1: Using pip installation (Recommended)

```json
{
  "mcpServers": {
    "trello": {
      "command": "python",
      "args": ["-m", "mcp_trello.main"],
      "env": {
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "your_token",
        "LOG_LEVEL": "INFO",
        "SAFE_MODE": "true"
      }
    }
  }
}
```

#### Option 2: Using uvx (if you prefer uv)

```json
{
  "mcpServers": {
    "trello": {
      "command": "uvx",
      "args": ["--from", "mbeauv-mcp-trello", "mbeauv-mcp-trello"],
      "env": {
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "your_token",
        "LOG_LEVEL": "INFO",
        "SAFE_MODE": "true"
      }
    }
  }
}
```

#### Option 3: From source (development)

```json
{
  "mcpServers": {
    "trello": {
      "command": "/path/to/uv",
      "args": ["run", "python", "-m", "mcp_trello.main"],
      "env": {
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "your_token",
        "LOG_LEVEL": "INFO",
        "SAFE_MODE": "true"
      }
    }
  }
}
```

### For mcp-cli

Create a `server_config.json` file in the project root:

```json
{
  "mcpServers": {
    "trello": {
      "command": "/path/to/uv",
      "args": ["run", "python", "main.py"],
      "env": {
        "PYTHONPATH": ".",
        "TRELLO_API_KEY": "your_api_key",
        "TRELLO_TOKEN": "your_token",
        "LOG_LEVEL": "INFO",
        "SAFE_MODE": true
      }
    }
  }
}
```

## Usage

### Starting the Server

```bash
uv run python main.py
```

### Using with mcp-cli

```bash
# List available tools
uv run mcp-cli tools --server main.py list

# List workspaces
uv run mcp-cli tools --server main.py list_workspaces

# Set current workspace
uv run mcp-cli tools --server main.py set_workspace --workspace_id "your_workspace_id"

# List boards in current workspace
uv run mcp-cli tools --server main.py list_boards_for_selected

# Create a board
uv run mcp-cli tools --server main.py create_board --name "New Project" --description "Project description"

# List cards in a board
uv run mcp-cli tools --server main.py list_board_cards --board_id "your_board_id"

# Create a card
uv run mcp-cli tools --server main.py create_card --name "New Task" --list_id "your_list_id" --description "Task description"

# Update a card
uv run mcp-cli tools --server main.py update_card --card_id "your_card_id" --name "Updated Task" --description "Updated description"
```

### Using with Claude Desktop

Once configured, the Trello tools will be available in Claude's interface. You can interact with them naturally:

- "Show me all my Trello workspaces"
- "Create a new board called 'Project Alpha'"
- "List all cards in my current board"
- "Create a card called 'Important Task' in the 'To Do' list"

## Available Tools

### Workspace Tools
- `list_workspaces` - List all accessible workspaces
- `create_workspace` - Create a new workspace
- `delete_workspace` - Delete a workspace
- `set_workspace` - Set current workspace
- `get_current_workspace` - Get current workspace info

### Board Tools
- `list_boards_for_selected` - List boards in current workspace
- `create_board` - Create a new board
- `delete_board` - Delete a board

### List Tools
- `list_board_lists` - List all lists in a board
- `create_board_list` - Create a new list
- `delete_board_list` - Delete a list

### Card Tools
- `list_board_cards` - List all cards in a board
- `create_card` - Create a new card
- `update_card` - Update an existing card
- `delete_card` - Delete a card

### Checklist Tools
- `create_checklist` - Create a new checklist
- `delete_checklist` - Delete a checklist
- `add_checklist_item` - Add item to checklist
- `delete_checklist_item` - Delete item from checklist

## Architecture

### TrelloClient Class
The core API client that handles all Trello API interactions:

- **Refactored Design**: Uses a centralized `_make_request()` method to reduce code duplication
- **Error Handling**: Consistent error handling across all API calls
- **Authentication**: Automatic inclusion of API credentials in all requests
- **Type Safety**: Full type hints for better development experience

### MCP Server
Built using FastMCP for simplified tool definition:

- **Tool Decorators**: Uses `@mcp.tool()` decorators for clean tool definitions
- **Global State**: Maintains current workspace context
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Error Recovery**: Graceful error handling with user-friendly messages

## Building Desktop Extension

To build the `.dxt` file for Desktop Extension deployment:

```bash
# From the project root (recommended)
uv run python dxt/build_dxt.py

# Or with regular Python (if uv not available)
python dxt/build_dxt.py
```

This creates a `mbeauv-mcp-trello-{version}.dxt` file that can be installed directly in Claude Desktop.

## Development

### Project Structure
```
mcp-trello/
├── main.py              # MCP server implementation
├── trello_client.py     # Trello API client
├── pyproject.toml       # Project dependencies
├── server_config.json   # mcp-cli configuration
├── .env                 # Environment variables (create this)
└── README.md           # This file
```

### Adding New Features

1. **Add API method** to `trello_client.py`:
   ```python
   async def new_feature(self, param: str) -> dict:
       return await self._make_request(
           method="GET",
           endpoint="/api/endpoint",
           params={"param": param},
           error_message="Error message"
       )
   ```

2. **Add MCP tool** to `main.py`:
   ```python
   @mcp.tool()
   async def new_tool(param: str) -> List[TextContent]:
       # Tool implementation
       pass
   ```

### Testing

Test individual tools using mcp-cli:

```bash
# Test workspace listing
uv run mcp-cli tools --server main.py list_workspaces

# Test card creation
uv run mcp-cli tools --server main.py create_card --name "Test Card" --list_id "your_list_id"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **"Missing Trello credentials"**
   - Ensure `.env` file exists with `TRELLO_API_KEY` and `TRELLO_TOKEN`
   - Check that credentials are valid

2. **"uv not found"**
   - Update the command path in configuration files
   - Use absolute path to uv executable

3. **"Server disconnected"**
   - Check log files for detailed error messages
   - Verify API credentials are correct
   - Ensure network connectivity

### Logging

The server provides comprehensive logging:

- **File**: `mcp_trello.log` (if file logging is enabled)
- **Console**: Real-time logging to stderr
- **Levels**: DEBUG, INFO, WARNING, ERROR

Set log level via `LOG_LEVEL` environment variable.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review the Trello API documentation
- Open an issue in the repository
