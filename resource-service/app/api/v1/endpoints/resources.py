from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.resource import resource_crud
from ....schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceAllocationCreate, ResourceAllocationUpdate, ResourceAllocationResponse)


router = APIRouter()

@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
        resource_in: ResourceCreate,
        db: Session = Depends(get_db),
        user_id: int= Depends(get_current_user_id)
):
    return resource_crud.create_resource(db=db, obj_in=resource_in, owner_id=user_id)

@router.get("/", response_model=List[ResourceResponse])
def read_resources(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        user_id: int= Depends(get_current_user_id)
):
    return resource_crud.get_multi(db, skip=skip, limit=limit, owner_id=user_id)

@router.get("/{resource_id}", response_model=ResourceResponse)
def read_resource(
        resource_id: int,
        db: Session = Depends(get_db),
        user_id: int= Depends(get_current_user_id)
):
    resource = resource_crud.get_with_allocations(db, resource_id, user_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
        resource_id: int,
        resource_in: ResourceUpdate,
        db: Session = Depends(get_db),
        user_id: int= Depends(get_current_user_id)
):
    resource=resource_crud.update_resource(db, resource_id, resource_in, user_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found or access denied")
    return resource



@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
        resource_id: int,
        db: Session = Depends(get_db),
        user_id: int= Depends(get_current_user_id)):
    success = resource_crud.delete(db, resource_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found or access denied")


"""Allocations"""

@router.get("/allocations", status_code=status.HTTP_201_CREATED)
def create_resource_allocation(
        resource_allocation_in: ResourceAllocationCreate,
        db: Session=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    return resource_crud.create_allocation(db=db, obj_in=resource_allocation_in)



