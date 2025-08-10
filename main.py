import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from trello_client import TrelloClient
from typing import List
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
# Configure logging to output to stderr
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp_trello")


# Get credentials from environment variables
def get_credentials():
    """Get Trello credentials from environment variables."""
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    
    if not api_key or not token:
        logger.error("Missing Trello credentials. Please set TRELLO_API_KEY and TRELLO_TOKEN environment variables.")
        raise ValueError("Missing Trello credentials")
    
    return api_key, token


# Initialize the Trello client
logger.info("Initializing Trello client...")
try:
    api_key, token = get_credentials()
    trello_client = TrelloClient(api_key=api_key, token=token)
    logger.info("Trello client initialized successfully")
except ValueError as e:
    logger.error(f"Failed to initialize Trello client: {e}")
    raise

# Create FastMCP server
logger.info("Creating FastMCP server...")
mcp = FastMCP("trello")

# Global state for current workspace
current_workspace_id = None
current_workspace_name = None

# Check if safe mode is enabled
SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() == "true"
if SAFE_MODE:
    logger.info("SAFE MODE ENABLED - Destructive tools will not be available")
else:
    logger.info("SAFE MODE DISABLED - All tools including destructive ones are available")

def get_current_workspace_info():
    """Get current workspace info or return None if not set."""
    global current_workspace_id, current_workspace_name
    if current_workspace_id:
        return {
            "id": current_workspace_id,
            "name": current_workspace_name
        }
    return None


@mcp.tool()
async def list_workspaces() -> List[TextContent]:
    """List all Trello workspaces accessible to the user."""
    logger.info("Tool called: list_workspaces")
    
    try:
        workspaces_json = await trello_client.get_workspaces()
        
        if not workspaces_json:
            return [TextContent(type="text", text="No workspaces found.")]

        result = f"🏢 **Available Workspaces:**\n\n"
        for i, workspace in enumerate(workspaces_json, 1):
            result += f"{i}. **{workspace.get('displayName', workspace.get('name', 'Unknown'))}**\n"
            result += f"   ID: `{workspace.get('id')}`\n"
            if workspace.get('desc'):
                result += f"   Description: {workspace.get('desc')}\n"
            result += f"   URL: {workspace.get('url')}\n"
            result += f"   Enterprise: {workspace.get('enterprise', False)}\n"
            result += f"   Public: {workspace.get('public', False)}\n"
            result += f"   Available: {workspace.get('available', True)}\n"
            if workspace.get('website'):
                result += f"   Website: {workspace.get('website')}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching workspaces: {str(e)}")]


@mcp.tool()
async def create_workspace(name: str, display_name: str = None, description: str = None, website: str = None) -> List[TextContent]:
    """Create a new Trello workspace.
    
    Args:
        name: The name of the workspace (required)
        display_name: The display name (optional, defaults to name)
        description: The workspace description (optional)
        website: The workspace website URL (optional)
    """
    logger.info("Tool called: create_workspace")
    logger.debug(f"Creating workspace with name: {name}, display_name: {display_name}")
    
    try:
        display_name = display_name or name
        
        logger.debug("Calling Trello API to create workspace...")
        workspace_data = await trello_client.create_workspace(
            name=name,
            display_name=display_name,
            description=description,
            website=website
        )
        
        logger.info(f"Successfully created workspace: {workspace_data.get('name')}")
        
        result = f"✅ **Workspace Created Successfully!**\n\n"
        result += f"**Name:** {workspace_data.get('name')}\n"
        result += f"**Display Name:** {workspace_data.get('displayName')}\n"
        result += f"**ID:** `{workspace_data.get('id')}`\n"
        if workspace_data.get('desc'):
            result += f"**Description:** {workspace_data.get('desc')}\n"
        if workspace_data.get('website'):
            result += f"**Website:** {workspace_data.get('website')}\n"
        result += f"**URL:** {workspace_data.get('url')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in create_workspace tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error creating workspace: {str(e)}")]


# Only register delete_workspace if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_workspace(workspace_id: str) -> List[TextContent]:
        """Delete a Trello workspace.
        
        Args:
            workspace_id: The ID of the workspace to delete (required)
        """
        logger.info("Tool called: delete_workspace")
        logger.debug(f"Deleting workspace with ID: {workspace_id}")
        
        try:
            logger.debug("Calling Trello API to delete workspace...")
            success = await trello_client.delete_workspace(workspace_id)
            
            if success:
                logger.info(f"Successfully deleted workspace: {workspace_id}")
                result = f"✅ **Workspace Deleted Successfully!**\n\n"
                result += f"**Workspace ID:** `{workspace_id}`\n"
                result += f"The workspace has been permanently deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete workspace: {workspace_id}")
                return [TextContent(type="text", text="Failed to delete workspace.")]
            
        except Exception as e:
            logger.error(f"Error in delete_workspace tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting workspace: {str(e)}")]


@mcp.tool()
async def set_workspace(workspace_id: str) -> List[TextContent]:
    """Set the current workspace for subsequent operations.
    
    Args:
        workspace_id: The ID of the workspace to set as current (required)
    """
    global current_workspace_id, current_workspace_name
    
    try:
        # Verify the workspace exists by trying to get its details
        workspaces = await trello_client.get_workspaces()
        workspace = None
        
        for ws in workspaces:
            if ws.get('id') == workspace_id:
                workspace = ws
                break
        
        if not workspace:
            logger.warning(f"Workspace not found: {workspace_id}")
            return [TextContent(type="text", text=f"❌ **Workspace not found!**\n\nWorkspace ID `{workspace_id}` was not found in your accessible workspaces.")]
        
        # Set the current workspace
        current_workspace_id = workspace_id
        current_workspace_name = workspace.get('displayName', workspace.get('name', 'Unknown'))
        
        logger.info(f"Successfully set current workspace: {current_workspace_name} ({current_workspace_id})")
        
        result = f"✅ **Current Workspace Set!**\n\n"
        result += f"**Workspace:** {current_workspace_name}\n"
        result += f"**ID:** `{current_workspace_id}`\n"
        result += f"**URL:** {workspace.get('url')}\n"
        if workspace.get('desc'):
            result += f"**Description:** {workspace.get('desc')}\n"
        result += f"\nYou can now use workspace-specific tools without specifying the workspace ID."
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error setting workspace: {str(e)}")]


@mcp.tool()
async def get_current_workspace() -> List[TextContent]:
    """Get information about the currently set workspace."""
    global current_workspace_id, current_workspace_name
    
    if not current_workspace_id:
        return [TextContent(type="text", text="❌ **No workspace set!**\n\nUse `set_workspace` to select a workspace first.")]
    
    try:
        # Get updated workspace info
        workspaces = await trello_client.get_workspaces()
        workspace = None
        
        for ws in workspaces:
            if ws.get('id') == current_workspace_id:
                workspace = ws
                break
        
        if not workspace:
            logger.warning(f"Current workspace no longer accessible: {current_workspace_id}")
            return [TextContent(type="text", text="❌ **Workspace no longer accessible!**\n\nPlease use `set_workspace` to select a different workspace.")]
        
        result = f"🏢 **Current Workspace:**\n\n"
        result += f"**Name:** {workspace.get('displayName', workspace.get('name', 'Unknown'))}\n"
        result += f"**ID:** `{current_workspace_id}`\n"
        result += f"**URL:** {workspace.get('url')}\n"
        if workspace.get('desc'):
            result += f"**Description:** {workspace.get('desc')}\n"
        result += f"**Enterprise:** {workspace.get('enterprise', False)}\n"
        result += f"**Public:** {workspace.get('public', False)}\n"
        if workspace.get('website'):
            result += f"**Website:** {workspace.get('website')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting current workspace: {str(e)}")]


@mcp.tool()
async def list_boards_for_selected() -> List[TextContent]:
    """List all boards in the currently selected workspace."""
    global current_workspace_id, current_workspace_name
    
    if not current_workspace_id:
        return [TextContent(type="text", text="❌ **No workspace selected!**\n\nUse `set_workspace` to select a workspace first.")]
    
    try:
        boards = await trello_client.get_workspace_boards(current_workspace_id)
        
        if not boards:
            result = f"📋 **No Boards Found**\n\n"
            result += f"Workspace: **{current_workspace_name}**\n"
            result += f"ID: `{current_workspace_id}`\n\n"
            result += f"This workspace has no boards yet."
            
            return [TextContent(type="text", text=result)]

        result = f"📋 **Boards in {current_workspace_name}:**\n\n"
        for i, board in enumerate(boards, 1):
            status = "🟢 Active" if not board.get('closed', False) else "🔴 Archived"
            result += f"{i}. **{board.get('name', 'Unknown')}** {status}\n"
            result += f"   ID: `{board.get('id')}`\n"
            if board.get('desc'):
                result += f"   Description: {board.get('desc')}\n"
            result += f"   URL: {board.get('url')}\n"
            if board.get('dateLastActivity'):
                result += f"   Last Activity: {board.get('dateLastActivity')}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching boards: {str(e)}")]


@mcp.tool()
async def create_board(name: str, description: str = None) -> List[TextContent]:
    """Create a new board in the currently selected workspace.
    
    Args:
        name: The name of the board (required)
        description: The board description (optional)
    """
    global current_workspace_id, current_workspace_name
    
    if not current_workspace_id:
        return [TextContent(type="text", text="❌ **No workspace selected!**\n\nUse `set_workspace` to select a workspace first.")]
    
    try:
        board_data = await trello_client.create_board(
            name=name,
            workspace_id=current_workspace_id,
            description=description
        )
        
        result = f"✅ **Board Created Successfully!**\n\n"
        result += f"**Name:** {board_data.get('name')}\n"
        result += f"**ID:** `{board_data.get('id')}`\n"
        if board_data.get('desc'):
            result += f"**Description:** {board_data.get('desc')}\n"
        result += f"**URL:** {board_data.get('url')}\n"
        result += f"**Workspace:** {current_workspace_name}\n"
        result += f"**Workspace ID:** `{current_workspace_id}`\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating board: {str(e)}")]


# Only register delete_board if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_board(board_id: str) -> List[TextContent]:
        """Delete a Trello board.
        
        Args:
            board_id: The ID of the board to delete (required)
        """
        logger.info("Tool called: delete_board")
        logger.debug(f"Deleting board with ID: {board_id}")
        
        try:
            success = await trello_client.delete_board(board_id)
            
            if success:
                result = f"✅ **Board Deleted Successfully!**\n\n"
                result += f"**Board ID:** `{board_id}`\n"
                result += f"The board has been permanently deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete board: {board_id}")
                return [TextContent(type="text", text="Failed to delete board.")]
            
        except Exception as e:
            logger.error(f"Error in delete_board tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting board: {str(e)}")]


@mcp.tool()
async def list_board_lists(board_id: str) -> List[TextContent]:
    """List all lists (columns) in a specific board.
    
    Args:
        board_id: The ID of the board to list lists for (required)
    """
    logger.info("Tool called: list_board_lists")
    logger.debug(f"Listing lists for board ID: {board_id}")
    
    try:
        lists_data = await trello_client.get_board_lists(board_id)
        
        if not lists_data:
            result = f"📝 **No Lists Found**\n\n"
            result += f"Board ID: `{board_id}`\n\n"
            result += f"This board has no lists yet."
            
            return [TextContent(type="text", text=result)]

        result = f"📝 **Lists in Board:**\n\n"
        for i, list_item in enumerate(lists_data, 1):
            status = "🟢 Active" if not list_item.get('closed', False) else "🔴 Archived"
            result += f"{i}. **{list_item.get('name', 'Unknown')}** {status}\n"
            result += f"   ID: `{list_item.get('id')}`\n"
            result += f"   Position: {list_item.get('pos', 'Unknown')}\n"
            result += f"   Subscribed: {list_item.get('subscribed', False)}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in list_board_lists tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error fetching board lists: {str(e)}")]


# Only register delete_board_list if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_board_list(list_id: str) -> List[TextContent]:
        """Delete a list (column) from a board.
        
        Args:
            list_id: The ID of the list to delete (required)
        """
        logger.info("Tool called: delete_board_list")
        logger.debug(f"Deleting list with ID: {list_id}")
        
        try:
            success = await trello_client.delete_board_list(list_id)
            
            if success:
                result = f"✅ **List Deleted Successfully!**\n\n"
                result += f"**List ID:** `{list_id}`\n"
                result += f"The list has been archived/deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete list: {list_id}")
                return [TextContent(type="text", text="Failed to delete list.")]
            
        except Exception as e:
            logger.error(f"Error in delete_board_list tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting list: {str(e)}")]


@mcp.tool()
async def create_board_list(name: str, board_id: str, position: str = "bottom") -> List[TextContent]:
    """Create a new list (column) in a specific board.
    
    Args:
        name: The name of the list (required)
        board_id: The ID of the board to create the list in (required)
        position: The position of the list - "top", "bottom", or a number (optional, defaults to "bottom")
    """
    logger.info("Tool called: create_board_list")
    logger.debug(f"Creating list '{name}' in board ID: {board_id}, position: {position}")
    
    try:
        list_data = await trello_client.create_board_list(
            name=name,
            board_id=board_id,
            position=position
        )
        
        result = f"✅ **List Created Successfully!**\n\n"
        result += f"**Name:** {list_data.get('name')}\n"
        result += f"**ID:** `{list_data.get('id')}`\n"
        result += f"**Board ID:** `{list_data.get('idBoard')}`\n"
        result += f"**Position:** {list_data.get('pos', 'bottom')}\n"
        result += f"**Closed:** {list_data.get('closed', False)}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in create_board_list tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error creating list: {str(e)}")]


@mcp.tool()
async def list_board_cards(board_id: str) -> List[TextContent]:
    """List all cards in a specific board.
    
    Args:
        board_id: The ID of the board to list cards for (required)
    """
    logger.info("Tool called: list_board_cards")
    logger.debug(f"Listing cards for board ID: {board_id}")
    
    try:
        cards_data = await trello_client.get_board_cards(board_id)
        
        if not cards_data:
            result = f"🃏 **No Cards Found**\n\n"
            result += f"Board ID: `{board_id}`\n\n"
            result += f"This board has no cards yet."
            
            return [TextContent(type="text", text=result)]

        result = f"🃏 **Cards in Board:**\n\n"
        for i, card in enumerate(cards_data, 1):
            status = "🟢 Active" if not card.get('closed', False) else "🔴 Archived"
            result += f"{i}. **{card.get('name', 'Unknown')}** {status}\n"
            result += f"   ID: `{card.get('id')}`\n"
            result += f"   List ID: `{card.get('idList')}`\n"
            result += f"   Position: {card.get('pos', 'Unknown')}\n"
            
            if card.get('desc'):
                # Truncate description if too long
                desc = card.get('desc')
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                result += f"   Description: {desc}\n"
            
            if card.get('due'):
                due_status = "✅ Complete" if card.get('dueComplete', False) else "⏰ Due"
                result += f"   Due Date: {card.get('due')} ({due_status})\n"
            
            if card.get('labels'):
                result += f"   Labels: {len(card.get('labels', []))} label(s)\n"
            
            if card.get('members'):
                result += f"   Members: {len(card.get('members', []))} member(s)\n"
            
            if card.get('attachments'):
                result += f"   Attachments: {len(card.get('attachments', []))} file(s)\n"
            
            if card.get('checklists'):
                result += f"   Checklists: {len(card.get('checklists', []))} checklist(s)\n"
            
            result += "\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in list_board_cards tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error fetching board cards: {str(e)}")]


@mcp.tool()
async def create_card(name: str, list_id: str, description: str = None, due_date: str = None) -> List[TextContent]:
    """Create a new card in a specific list.
    
    Args:
        name: The name of the card (required)
        list_id: The ID of the list to create the card in (required)
        description: The card description (optional)
        due_date: The due date in ISO format YYYY-MM-DD (optional)
    """
    logger.info("Tool called: create_card")
    logger.debug(f"Creating card '{name}' in list ID: {list_id}")
    
    try:
        card_data = await trello_client.create_card(
            name=name,
            list_id=list_id,
            description=description,
            due_date=due_date
        )
        
        result = f"✅ **Card Created Successfully!**\n\n"
        result += f"**Name:** {card_data.get('name')}\n"
        result += f"**ID:** `{card_data.get('id')}`\n"
        result += f"**List ID:** `{card_data.get('idList')}`\n"
        result += f"**Position:** {card_data.get('pos', 'Unknown')}\n"
        
        if card_data.get('desc'):
            result += f"**Description:** {card_data.get('desc')}\n"
        
        if card_data.get('due'):
            result += f"**Due Date:** {card_data.get('due')}\n"
        
        result += f"**URL:** {card_data.get('url')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in create_card tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error creating card: {str(e)}")]


# Only register delete_card if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_card(card_id: str) -> List[TextContent]:
        """Delete a card.
        
        Args:
            card_id: The ID of the card to delete (required)
        """
        logger.info("Tool called: delete_card")
        logger.debug(f"Deleting card with ID: {card_id}")
        
        try:
            success = await trello_client.delete_card(card_id)
            
            if success:
                result = f"✅ **Card Deleted Successfully!**\n\n"
                result += f"**Card ID:** `{card_id}`\n"
                result += f"The card has been permanently deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete card: {card_id}")
                return [TextContent(type="text", text="Failed to delete card.")]
            
        except Exception as e:
            logger.error(f"Error in delete_card tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting card: {str(e)}")]


@mcp.tool()
async def create_checklist(name: str, card_id: str) -> List[TextContent]:
    """Create a new checklist in a specific card.
    
    Args:
        name: The name of the checklist (required)
        card_id: The ID of the card to create the checklist in (required)
    """
    logger.info("Tool called: create_checklist")
    logger.debug(f"Creating checklist '{name}' in card ID: {card_id}")
    
    try:
        checklist_data = await trello_client.create_checklist(
            name=name,
            card_id=card_id
        )
        
        result = f"✅ **Checklist Created Successfully!**\n\n"
        result += f"**Name:** {checklist_data.get('name')}\n"
        result += f"**ID:** `{checklist_data.get('id')}`\n"
        result += f"**Card ID:** `{checklist_data.get('idCard')}`\n"
        result += f"**Position:** {checklist_data.get('pos', 'Unknown')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in create_checklist tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error creating checklist: {str(e)}")]


# Only register delete_checklist if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_checklist(checklist_id: str) -> List[TextContent]:
        """Delete a checklist from a card.
        
        Args:
            checklist_id: The ID of the checklist to delete (required)
        """
        logger.info("Tool called: delete_checklist")
        logger.debug(f"Deleting checklist with ID: {checklist_id}")
        
        try:
            success = await trello_client.delete_checklist(checklist_id)
            
            if success:
                result = f"✅ **Checklist Deleted Successfully!**\n\n"
                result += f"**Checklist ID:** `{checklist_id}`\n"
                result += f"The checklist has been permanently deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete checklist: {checklist_id}")
                return [TextContent(type="text", text="Failed to delete checklist.")]
            
        except Exception as e:
            logger.error(f"Error in delete_checklist tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting checklist: {str(e)}")]


@mcp.tool()
async def add_checklist_item(name: str, checklist_id: str, checked: bool = False) -> List[TextContent]:
    """Add a new item to a checklist.
    
    Args:
        name: The name of the checklist item (required)
        checklist_id: The ID of the checklist to add the item to (required)
        checked: Whether the item is checked (optional, defaults to False)
    """
    logger.info("Tool called: add_checklist_item")
    logger.debug(f"Adding checklist item '{name}' to checklist ID: {checklist_id}, checked: {checked}")
    
    try:
        item_data = await trello_client.add_checklist_item(
            name=name,
            checklist_id=checklist_id,
            checked=checked
        )
        
        result = f"✅ **Checklist Item Added Successfully!**\n\n"
        result += f"**Name:** {item_data.get('name')}\n"
        result += f"**ID:** `{item_data.get('id')}`\n"
        result += f"**Checklist ID:** `{checklist_id}`\n"
        result += f"**Checked:** {item_data.get('state', 'incomplete')}\n"
        result += f"**Position:** {item_data.get('pos', 'Unknown')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in add_checklist_item tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error adding checklist item: {str(e)}")]


# Only register delete_checklist_item if safe mode is disabled
if not SAFE_MODE:
    @mcp.tool()
    async def delete_checklist_item(checklist_id: str, check_item_id: str) -> List[TextContent]:
        """Delete an item from a checklist.
        
        Args:
            checklist_id: The ID of the checklist (required)
            check_item_id: The ID of the checklist item to delete (required)
        """
        logger.info("Tool called: delete_checklist_item")
        logger.debug(f"Deleting checklist item {check_item_id} from checklist {checklist_id}")
        
        try:
            success = await trello_client.delete_checklist_item(checklist_id, check_item_id)
            
            if success:
                result = f"✅ **Checklist Item Deleted Successfully!**\n\n"
                result += f"**Checklist ID:** `{checklist_id}`\n"
                result += f"**Item ID:** `{check_item_id}`\n"
                result += f"The checklist item has been permanently deleted."
                
                return [TextContent(type="text", text=result)]
            else:
                logger.warning(f"Failed to delete checklist item: {check_item_id}")
                return [TextContent(type="text", text="Failed to delete checklist item.")]
            
        except Exception as e:
            logger.error(f"Error in delete_checklist_item tool: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error deleting checklist item: {str(e)}")]


@mcp.tool()
async def update_card(card_id: str, name: str = None, description: str = None, due_date: str = None, list_id: str = None) -> List[TextContent]:
    """Update an existing card.
    
    Args:
        card_id: The ID of the card to update (required)
        name: The new name of the card (optional)
        description: The new description of the card (optional)
        due_date: The new due date in ISO format YYYY-MM-DD (optional)
        list_id: The new list ID to move the card to (optional)
    """
    logger.info("Tool called: update_card")
    logger.debug(f"Updating card ID: {card_id}")
    
    # Build update info for logging
    updates = []
    if name is not None:
        updates.append(f"name: {name}")
    if description is not None:
        updates.append(f"description: {description[:50]}..." if len(description) > 50 else f"description: {description}")
    if due_date is not None:
        updates.append(f"due_date: {due_date}")
    if list_id is not None:
        updates.append(f"list_id: {list_id}")
    
    if updates:
        logger.debug(f"Updates: {', '.join(updates)}")
    else:
        logger.warning("No updates provided for card")
        return [TextContent(type="text", text="❌ **No Updates Provided!**\n\nPlease provide at least one field to update (name, description, due_date, or list_id).")]
    
    try:
        card_data = await trello_client.update_card(
            card_id=card_id,
            name=name,
            description=description,
            due_date=due_date,
            list_id=list_id
        )
        
        result = f"✅ **Card Updated Successfully!**\n\n"
        result += f"**Card ID:** `{card_id}`\n"
        result += f"**Name:** {card_data.get('name', 'Unchanged')}\n"
        result += f"**List ID:** `{card_data.get('idList', 'Unchanged')}`\n"
        result += f"**Position:** {card_data.get('pos', 'Unknown')}\n"
        
        if card_data.get('desc'):
            result += f"**Description:** {card_data.get('desc')}\n"
        
        if card_data.get('due'):
            result += f"**Due Date:** {card_data.get('due')}\n"
        
        result += f"**URL:** {card_data.get('url')}\n"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error in update_card tool: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error updating card: {str(e)}")]


if __name__ == "__main__":
    logger.info("Starting MCP Trello server...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)