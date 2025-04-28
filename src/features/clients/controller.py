"""
Client controller for handling client-related business logic.
"""
from typing import List, Optional, Tuple, Union

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.core.database.connection import get_db
from src.core.exceptions.exceptions import NotFoundException
from src.features.clients.model import Client, ClientContact, ClientGroup, ClientGroupMember
from src.features.clients.schemas import (
    ClientContactCreate,
    ClientContactResponse,
    ClientContactUpdate,
    ClientCreate,
    ClientGroupCreate,
    ClientGroupResponse,
    ClientGroupUpdate,
    ClientResponse,
    ClientUpdate,
)


class ClientController:
    """Client controller for handling client-related business logic."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        """Initialize client controller with database session."""
        self.db = db

    async def get_clients(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> Tuple[List[Client], int]:
        """
        Get all clients for an organization.

        Args:
            skip: Number of clients to skip
            limit: Maximum number of clients to return
            search: Optional search term

        Returns:
            Tuple[List[Client], int]: List of clients and total count
        """
        # Create base query
        query = select(Client)

        # Add search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Client.name.ilike(search_term))
                | (Client.email.ilike(search_term))
                | (Client.phone.ilike(search_term))
                | (Client.code.ilike(search_term))
            )

        # Get total count
        total_query = select(Client.id)
        if search:
            search_term = f"%{search}%"
            total_query = total_query.filter(
                (Client.name.ilike(search_term))
                | (Client.email.ilike(search_term))
                | (Client.phone.ilike(search_term))
                | (Client.code.ilike(search_term))
            )

        total_result = await self.db.execute(total_query)
        total = len(total_result.all())

        # Get clients with pagination
        query = query.options(selectinload(Client.contacts)).order_by(Client.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        clients = result.scalars().all()

        return clients, total

    async def get_client(self, client_id: str) -> Optional[Client]:
        """
        Get client by ID.

        Args:
            client_id: Client ID

        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        query = select(Client).filter(Client.id == client_id).options(selectinload(Client.contacts))
        result = await self.db.execute(query)
        client = result.scalar_one_or_none()
        return client

    async def create_client(self, client_data: ClientCreate) -> Client:
        """
        Create new client.

        Args:
            client_data: Client data for creation

        Returns:
            Client: Created client
        """
        # Extract contacts data
        contacts_data = client_data.contacts or []
        client_dict = client_data.model_dump(exclude={"contacts"})

        # Create client instance
        client = Client(**client_dict)

        # Add client to database
        self.db.add(client)
        await self.db.flush()

        # Create contacts if provided
        for contact_data in contacts_data:
            contact = ClientContact(**contact_data.model_dump(), client_id=str(client.id))
            self.db.add(contact)

        # Commit changes
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def update_client(self, client_id: str, client_data: ClientUpdate) -> Optional[Client]:
        """
        Update client.

        Args:
            client_id: Client ID
            client_data: Client data for update

        Returns:
            Optional[Client]: Updated client if found, None otherwise
        """
        # Get client
        client = await self.get_client(client_id)
        if not client:
            return None

        # Update client fields
        update_data = client_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)

        # Save changes
        await self.db.commit()
        await self.db.refresh(client)

        return client

    async def delete_client(self, client_id: str) -> bool:
        """
        Delete client.

        Args:
            client_id: Client ID

        Returns:
            bool: True if client was deleted, False otherwise
        """
        # Get client
        client = await self.get_client(client_id)
        if not client:
            return False

        # Delete client
        await self.db.delete(client)
        await self.db.commit()

        return True

    async def get_client_contact(self, contact_id: str) -> Optional[ClientContact]:
        """
        Get client contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            Optional[ClientContact]: Contact if found, None otherwise
        """
        query = select(ClientContact).filter(ClientContact.id == contact_id)
        result = await self.db.execute(query)
        contact = result.scalar_one_or_none()
        return contact

    async def create_client_contact(
        self, client_id: str, contact_data: ClientContactCreate
    ) -> ClientContact:
        """
        Create new client contact.

        Args:
            client_id: Client ID
            contact_data: Contact data for creation

        Returns:
            ClientContact: Created contact

        Raises:
            NotFoundException: If client not found
        """
        # Check if client exists
        client = await self.get_client(client_id)
        if not client:
            raise NotFoundException("Client not found")

        # Create contact instance
        contact = ClientContact(**contact_data.model_dump(), client_id=client_id)

        # Add contact to database
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def update_client_contact(
        self, contact_id: str, contact_data: ClientContactUpdate
    ) -> Optional[ClientContact]:
        """
        Update client contact.

        Args:
            contact_id: Contact ID
            contact_data: Contact data for update

        Returns:
            Optional[ClientContact]: Updated contact if found, None otherwise
        """
        # Get contact
        contact = await self.get_client_contact(contact_id)
        if not contact:
            return None

        # Update contact fields
        update_data = contact_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        # Save changes
        await self.db.commit()
        await self.db.refresh(contact)

        return contact

    async def delete_client_contact(self, contact_id: str) -> bool:
        """
        Delete client contact.

        Args:
            contact_id: Contact ID

        Returns:
            bool: True if contact was deleted, False otherwise
        """
        # Get contact
        contact = await self.get_client_contact(contact_id)
        if not contact:
            return False

        # Delete contact
        await self.db.delete(contact)
        await self.db.commit()

        return True

    async def get_client_groups(
        self,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> Tuple[List[ClientGroup], int]:
        """
        Get all client groups for an organization.

        Args:
            organization_id: Organization ID
            skip: Number of groups to skip
            limit: Maximum number of groups to return
            search: Optional search term

        Returns:
            Tuple[List[ClientGroup], int]: List of client groups and total count
        """
        # Create base query
        query = select(ClientGroup).filter(ClientGroup.organization_id == organization_id)

        # Add search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (ClientGroup.name.ilike(search_term))
                | (ClientGroup.description.ilike(search_term))
            )

        # Get total count
        total_query = select(ClientGroup.id).filter(ClientGroup.organization_id == organization_id)
        if search:
            search_term = f"%{search}%"
            total_query = total_query.filter(
                (ClientGroup.name.ilike(search_term))
                | (ClientGroup.description.ilike(search_term))
            )

        total_result = await self.db.execute(total_query)
        total = len(total_result.all())

        # Get client groups with pagination
        query = query.options(selectinload(ClientGroup.clients)).order_by(ClientGroup.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        groups = result.scalars().all()

        return groups, total

    async def get_client_group(self, group_id: str) -> Optional[ClientGroup]:
        """
        Get client group by ID.

        Args:
            group_id: Group ID

        Returns:
            Optional[ClientGroup]: Group if found, None otherwise
        """
        query = select(ClientGroup).filter(ClientGroup.id == group_id).options(selectinload(ClientGroup.clients))
        result = await self.db.execute(query)
        group = result.scalar_one_or_none()
        return group

    async def create_client_group(self, group_data: ClientGroupCreate) -> ClientGroup:
        """
        Create new client group.

        Args:
            group_data: Group data for creation

        Returns:
            ClientGroup: Created group
        """
        # Extract client IDs
        client_ids = group_data.client_ids or []
        group_dict = group_data.model_dump(exclude={"client_ids"})

        # Create group instance
        group = ClientGroup(**group_dict)

        # Add group to database
        self.db.add(group)
        await self.db.flush()

        # Add clients to group if provided
        for client_id in client_ids:
            member = ClientGroupMember(group_id=str(group.id), client_id=client_id)
            self.db.add(member)

        # Commit changes
        await self.db.commit()
        await self.db.refresh(group)

        return group

    async def update_client_group(
        self, group_id: str, group_data: ClientGroupUpdate
    ) -> Optional[ClientGroup]:
        """
        Update client group.

        Args:
            group_id: Group ID
            group_data: Group data for update

        Returns:
            Optional[ClientGroup]: Updated group if found, None otherwise
        """
        # Get group
        group = await self.get_client_group(group_id)
        if not group:
            return None

        # Update client IDs if provided
        if group_data.client_ids is not None:
            # Delete existing group members
            await self.db.execute("DELETE FROM client_group_members WHERE group_id = :group_id", {"group_id": group_id})

            # Add new group members
            for client_id in group_data.client_ids:
                member = ClientGroupMember(group_id=group_id, client_id=client_id)
                self.db.add(member)

        # Update group fields
        update_data = group_data.model_dump(exclude={"client_ids"}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        # Save changes
        await self.db.commit()
        await self.db.refresh(group)

        return group

    async def delete_client_group(self, group_id: str) -> bool:
        """
        Delete client group.

        Args:
            group_id: Group ID

        Returns:
            bool: True if group was deleted, False otherwise
        """
        # Get group
        group = await self.get_client_group(group_id)
        if not group:
            return False

        # Delete group
        await self.db.delete(group)
        await self.db.commit()

        return True
