"""Category Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.category import Category
from api.v1.models.product import Product


class CategoryService:

    def get_all(self, db: Session, search: Optional[str] = None) -> List[Category]:
        query = db.query(Category)
        if search:
            query = query.filter(Category.name.ilike(f"%{search}%"))
        return query.order_by(Category.created_at.desc()).all()

    def get_by_id(self, db: Session, category_id: str) -> Category:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    def get_product_count(self, db: Session, category_id: str) -> int:
        return db.query(Product).filter(Product.category_id == category_id).count()

    def create(self, db: Session, name: str, description: Optional[str] = None) -> Category:
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
        
        category = Category(name=name, description=description)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update(self, db: Session, category_id: str, **kwargs) -> Category:
        category = self.get_by_id(db, category_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        db.commit()
        db.refresh(category)
        return category

    def delete(self, db: Session, category_id: str):
        category = self.get_by_id(db, category_id)
        db.delete(category)
        db.commit()
        return True


category_service = CategoryService()
