"""Trello API client using httpx for JSON passthrough."""

import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("mcp_trello.trello_client")


class TrelloClient:
    """Client for interacting with the Trello API."""
    
    def __init__(self, api_key: str, token: str):
        """Initialize the Trello client.
        
        Args:
            api_key: Trello API key
            token: Trello API token
        """
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"
        logger.info("TrelloClient initialized")
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for API requests."""
        return {
            "key": self.api_key,
            "token": self.token
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        error_message: str = "API request failed"
    ) -> Any:
        """Make an HTTP request to the Trello API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            error_message: Custom error message
            
        Returns:
            Response data (dict or list)
        """
        try:
            async with httpx.AsyncClient() as client:
                # Add auth params to query params
                if params is None:
                    params = {}
                params.update(self._get_auth_params())
                
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data
                )
                response.raise_for_status()
                
                # For DELETE requests, return True on success
                if method == "DELETE":
                    return True
                
                return response.json()
                
        except Exception as e:
            raise Exception(f"{error_message}: {e}")
    
    async def get_workspaces(self) -> List[dict]:
        """Get all workspaces accessible to the authenticated user.
        
        Returns:
            List of workspace dictionaries
        """
        return await self._make_request(
            method="GET",
            endpoint="/members/me/organizations",
            params={"fields": "id,name,displayName,desc,url,website,logoHash,logoUrl,premiumFeatures,enterprise,public,available,dateCreated,dateLastActivity"},
            error_message="Error fetching workspaces"
        )

    async def create_workspace(self, name: str, display_name: str = None, description: str = None, website: str = None) -> dict:
        """Create a new Trello workspace.
        
        Args:
            name: The name of the workspace
            display_name: The display name (optional)
            description: The workspace description (optional)
            website: The workspace website URL (optional)
            
        Returns:
            Dictionary containing the created workspace data
        """
        data = {"name": name}
        
        if display_name:
            data["displayName"] = display_name
        if description:
            data["desc"] = description
        if website:
            data["website"] = website
        
        return await self._make_request(
            method="POST",
            endpoint="/organizations",
            data=data,
            error_message="Error creating workspace"
        )

    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a Trello workspace.
        
        Args:
            workspace_id: The ID of the workspace to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/organizations/{workspace_id}",
            error_message="Error deleting workspace"
        )

    async def get_workspace_boards(self, workspace_id: str) -> List[dict]:
        """Get all boards in a specific workspace.
        
        Args:
            workspace_id: The ID of the workspace
            
        Returns:
            List of board dictionaries
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/organizations/{workspace_id}/boards",
            params={"fields": "id,name,desc,url,closed,dateLastActivity,prefs"},
            error_message="Error fetching workspace boards"
        )

    async def create_board(self, name: str, workspace_id: str, description: str = None) -> dict:
        """Create a new board in a specific workspace.
        
        Args:
            name: The name of the board
            workspace_id: The ID of the workspace to create the board in
            description: The board description (optional)
            
        Returns:
            Dictionary containing the created board data
        """
        data = {
            "name": name,
            "idOrganization": workspace_id
        }
        
        if description:
            data["desc"] = description
        
        return await self._make_request(
            method="POST",
            endpoint="/boards",
            data=data,
            error_message="Error creating board"
        )

    async def delete_board(self, board_id: str) -> bool:
        """Delete a Trello board.
        
        Args:
            board_id: The ID of the board to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/boards/{board_id}",
            error_message="Error deleting board"
        )

    async def get_board_lists(self, board_id: str) -> List[dict]:
        """Get all lists (columns) in a specific board.
        
        Args:
            board_id: The ID of the board
            
        Returns:
            List of list dictionaries
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/boards/{board_id}/lists",
            params={"fields": "id,name,pos,closed,subscribed"},
            error_message="Error fetching board lists"
        )

    async def delete_board_list(self, list_id: str) -> bool:
        """Delete a list (column) from a board.
        
        Args:
            list_id: The ID of the list to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="PUT",
            endpoint=f"/lists/{list_id}/closed",
            params={"value": "true"},
            error_message="Error deleting board list"
        )

    async def create_board_list(self, name: str, board_id: str, position: str = "bottom") -> dict:
        """Create a new list (column) in a specific board.
        
        Args:
            name: The name of the list
            board_id: The ID of the board to create the list in
            position: The position of the list ("top", "bottom", or a number)
            
        Returns:
            Dictionary containing the created list data
        """
        data = {
            "name": name,
            "idBoard": board_id
        }
        
        if position and position != "bottom":
            data["pos"] = position
        
        return await self._make_request(
            method="POST",
            endpoint="/lists",
            data=data,
            error_message="Error creating board list"
        )

    async def get_board_cards(self, board_id: str) -> List[dict]:
        """Get all cards in a specific board.
        
        Args:
            board_id: The ID of the board
            
        Returns:
            List of card dictionaries
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/boards/{board_id}/cards",
            params={"fields": "id,name,desc,idList,pos,closed,due,dueComplete,labels,members,attachments,checklists"},
            error_message="Error fetching board cards"
        )

    async def create_card(self, name: str, list_id: str, description: str = None, due_date: str = None) -> dict:
        """Create a new card in a specific list.
        
        Args:
            name: The name of the card
            list_id: The ID of the list to create the card in
            description: The card description (optional)
            due_date: The due date in ISO format (optional)
            
        Returns:
            Dictionary containing the created card data
        """
        data = {
            "name": name,
            "idList": list_id
        }
        
        if description:
            data["desc"] = description
        if due_date:
            data["due"] = due_date
        
        return await self._make_request(
            method="POST",
            endpoint="/cards",
            data=data,
            error_message="Error creating card"
        )

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card.
        
        Args:
            card_id: The ID of the card to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/cards/{card_id}",
            error_message="Error deleting card"
        )

    async def create_checklist(self, name: str, card_id: str) -> dict:
        """Create a new checklist in a specific card.
        
        Args:
            name: The name of the checklist
            card_id: The ID of the card to create the checklist in
            
        Returns:
            Dictionary containing the created checklist data
        """
        data = {
            "name": name,
            "idCard": card_id
        }
        
        return await self._make_request(
            method="POST",
            endpoint="/checklists",
            data=data,
            error_message="Error creating checklist"
        )

    async def delete_checklist(self, checklist_id: str) -> bool:
        """Delete a checklist from a card.
        
        Args:
            checklist_id: The ID of the checklist to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/checklists/{checklist_id}",
            error_message="Error deleting checklist"
        )

    async def add_checklist_item(self, name: str, checklist_id: str, checked: bool = False) -> dict:
        """Add a new item to a checklist.
        
        Args:
            name: The name of the checklist item
            checklist_id: The ID of the checklist to add the item to
            checked: Whether the item is checked (optional, defaults to False)
            
        Returns:
            Dictionary containing the created checklist item data
        """
        data = {
            "name": name,
            "checked": str(checked).lower()
        }
        
        return await self._make_request(
            method="POST",
            endpoint=f"/checklists/{checklist_id}/checkItems",
            data=data,
            error_message="Error adding checklist item"
        )

    async def delete_checklist_item(self, checklist_id: str, check_item_id: str) -> bool:
        """Delete an item from a checklist.
        
        Args:
            checklist_id: The ID of the checklist
            check_item_id: The ID of the checklist item to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/checklists/{checklist_id}/checkItems/{check_item_id}",
            error_message="Error deleting checklist item"
        )

    async def update_card(self, card_id: str, name: str = None, description: str = None, due_date: str = None, list_id: str = None) -> dict:
        """Update an existing card.
        
        Args:
            card_id: The ID of the card to update
            name: The new name of the card (optional)
            description: The new description of the card (optional)
            due_date: The new due date in ISO format (optional)
            list_id: The new list ID to move the card to (optional)
            
        Returns:
            Dictionary containing the updated card data
        """
        data = {}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["desc"] = description
        if due_date is not None:
            data["due"] = due_date
        if list_id is not None:
            data["idList"] = list_id
        
        return await self._make_request(
            method="PUT",
            endpoint=f"/cards/{card_id}",
            data=data,
            error_message="Error updating card"
        )
                