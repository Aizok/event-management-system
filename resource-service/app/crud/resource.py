from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ..models.resource import Resource, ResourceAllocation
from ..schemas.resource import ResourceCreate, ResourceUpdate, ResourceAllocationCreate, ResourceAllocationUpdate

class ResourceCRUD:
    def create_resource(self, db: Session, obj_in: ResourceCreate, owner_id: int) -> Resource:
        db_obj=Resource(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def get_resource(self, db: Session, resource_id: int) -> Optional[Resource]:
        return db.query(Resource).filter(Resource.id==resource_id).first()


    def get_with_allocations(self, db: Session, resource_id: int, owner_id: int) -> Optional[Resource]:
        query=db.query(Resource).options(joinedload(Resource.allocations))
        res=query.filter(Resource.id==resource_id).first()
        if res is None:
            return None
        if owner_id is not None and res.owner_id != owner_id:
            return None
        return res


    def get_multi(self, db: Session, skip: int=0, limit: int=100, owner_id: int = None) -> List[Resource]:
        query=db.query(Resource)
        if owner_id:
            query=query.filter(Resource.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()


    def update_resource(self, db: Session, resource_id: int, obj_in: ResourceUpdate, owner_id: int) -> Optional[Resource]:
        db_obj=self.get_resource(db, resource_id)
        if not db_obj or db_obj.owner_id != owner_id:
            raise ValueError("Resource not found or access denied")

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj


    def delete_resource(self, db: Session, resource_id: int, owner_id: int) -> bool:
        obj=self.get_resource(db, resource_id)
        if obj and obj.owner_id==owner_id:
            db.delete(obj)
            db.commit()
            return True
        return False


    def create_allocation(self, db: Session, obj_in: ResourceAllocationCreate) -> ResourceAllocation:
        db_obj=ResourceAllocation(
            **obj_in.model_dump()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    

    def get_allocation(self, db: Session, allocation_id: int) -> Optional[ResourceAllocation]:
        return db.query(ResourceAllocation).filter(ResourceAllocation.id==allocation_id).first()


    def update_allocation(self, db: Session, allocation_id: int, obj_in: ResourceAllocationUpdate)->Optional[ResourceAllocation]:
        db_obj=self.get_allocation(db, allocation_id)
        if not db_obj:
            raise ValueError("Resource allocation not found")
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj


    def delete_allocation(self, db: Session, allocation_id: int) -> bool:
        obj=self.get_allocation(db, allocation_id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False


resource_crud=ResourceCRUD()