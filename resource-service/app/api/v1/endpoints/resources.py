from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List

from ....core.database import get_db
from ....core.security import get_current_user_id
from ....core.permissions import check_resource_permissions, ALLOWED_ROLES
from ....crud.resource import resource_crud
from ....models.resource import AllocationStatus
from ....schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceAllocationCreate, ResourceAllocationUpdate, ResourceAllocationResponse)
from ....core.auth_client import is_admin
from ....core.event_client import get_user_events_with_roles


router = APIRouter()


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
        resource_in: ResourceCreate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    resource=await resource_crud.create_resource(db=db, obj_in=resource_in, owner_id=user_id)
    return resource


@router.get("/", response_model=List[ResourceResponse])
async def read_resources(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    if await is_admin(user_id):
        return await resource_crud.get_multi_resources(db, skip, limit)

    events=await get_user_events_with_roles(user_id)
    allowed_event_ids = [
        e["event_id"]
        for e in events
        if e["role"] in ALLOWED_ROLES
    ]
    if not allowed_event_ids:
        return []

    return await resource_crud.ge


@router.get("/{resource_id}", response_model=ResourceResponse)
async def read_resource(
        resource_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    resource = await resource_crud.get_with_allocations(db, resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
        resource_id: int,
        resource_in: ResourceUpdate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    resource=await resource_crud.update_resource(db, resource_id, resource_in)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
        resource_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    success = await resource_crud.delete_resource(db, resource_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found or access denied")


"""Allocations"""

@router.post("/allocations/", response_model=ResourceAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
        allocation_in: ResourceAllocationCreate,
        db: AsyncSession=Depends(get_db),
        user_id: int =Depends(get_current_user_id)
):
    await check_resource_permissions(allocation_in.event_id, user_id)
    try:
        allocation=await resource_crud.create_allocation(db=db, obj_in=allocation_in, owner_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return allocation


@router.get("/allocations/", response_model=List[ResourceAllocationResponse])
async def read_allocations(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    if await is_admin(user_id):
        return await resource_crud.get_multi_allocations(db, skip, limit)

    events=await get_user_events_with_roles(user_id)
    allowed_event_ids = [
        e["event_id"]
        for e in events
        if e["role"] in ALLOWED_ROLES
    ]
    if not allowed_event_ids:
        return []
    return await resource_crud.get_allocations_by_event_ids(db, allowed_event_ids, skip, limit)



@router.get("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def read_allocation(
        allocation_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    allocation=await resource_crud.get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    await check_resource_permissions(allocation.event_id, user_id)
    return allocation


@router.put("/allocations/{allocation_id}", response_model=ResourceAllocationResponse)
async def update_allocation(
        allocation_id: int,
        allocation_in: ResourceAllocationUpdate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    allocation=await resource_crud.get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource allocation not found"
        )

    await check_resource_permissions(allocation.event_id, user_id)

    try:
        updated=await resource_crud.update_allocation(db, allocation_id, allocation_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return updated


@router.delete("/allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation(
        allocation_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    allocation=await resource_crud.get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource allocation not found"
        )

    await check_resource_permissions(allocation.event_id, user_id)

    success = await resource_crud.delete_allocation(db, allocation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource allocation not found or access denied")


@router.patch("/allocations/{allocation_id}/cancel")
async def cancel_allocation(
        allocation_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    allocation=await resource_crud.get_allocation(db, allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource allocation not found")

    await check_resource_permissions(allocation.event_id, user_id)

    if allocation.status in [AllocationStatus.COMPLETED, AllocationStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel completed and cancelled allocation")

    allocation.status=AllocationStatus.CANCELLED
    await db.commit()
    await db.refresh(allocation)
    return {"status": "cancelled"}
