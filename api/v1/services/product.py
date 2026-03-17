"""Product Service"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1.models.product import Product, ProductImage
from api.v1.models.category import Category
import re


def _sanitize_image_url(url: str) -> str:
    """Fix double-prefixed URLs like 'https://api.comhttps://res.cloudinary.com/...'"""
    # Find if there's a second https:// or http:// embedded in the URL
    match = re.search(r'(https?://res\.cloudinary\.com/.+)$', url)
    if match and not url.startswith('https://res.cloudinary.com'):
        return match.group(1)
    return url


class ProductService:

    def get_all(self, db: Session, gender: Optional[str] = None, category_id: Optional[str] = None, 
                status_filter: Optional[str] = None, search: Optional[str] = None,
                is_best_seller: Optional[bool] = None, is_new_collection: Optional[bool] = None) -> List[Product]:
        query = db.query(Product)
        
        if gender and gender != "all":
            if gender in ("male", "female"):
                query = query.filter(Product.gender.in_([gender, "unisex"]))
            else:
                query = query.filter(Product.gender == gender)
        if category_id and category_id != "all":
            query = query.filter(Product.category_id == category_id)
        if status_filter and status_filter != "all":
            query = query.filter(Product.status == status_filter)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        if is_best_seller is not None:
            query = query.filter(Product.is_best_seller == is_best_seller)
        if is_new_collection is not None:
            query = query.filter(Product.is_new_collection == is_new_collection)
        
        return query.order_by(Product.created_at.desc()).all()

    def get_by_id(self, db: Session, product_id: str) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def create(self, db: Session, name: str, price: float, stock: int, gender: str = "female",
               status_val: str = "active", category_id: Optional[str] = None,
               is_best_seller: bool = False, is_new_collection: bool = False,
               description: Optional[str] = None, image_urls: Optional[List[str]] = None,
               video_url: Optional[str] = None, video_position: Optional[int] = None) -> Product:
        
        # Validate category exists if provided
        if category_id:
            cat = db.query(Category).filter(Category.id == category_id).first()
            if not cat:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

        product = Product(
            name=name,
            category_id=category_id,
            price=price,
            stock=stock,
            gender=gender,
            status=status_val,
            is_best_seller=is_best_seller,
            is_new_collection=is_new_collection,
            description=description,
            video_url=video_url,
            video_position=video_position,
        )
        db.add(product)
        db.flush()  # Get the product ID

        # Add images
        if image_urls:
            for i, url in enumerate(image_urls):
                img = ProductImage(product_id=product.id, image_url=_sanitize_image_url(url), sort_order=i)
                db.add(img)

        db.commit()
        db.refresh(product)
        return product

    def update(self, db: Session, product_id: str, **kwargs) -> Product:
        product = self.get_by_id(db, product_id)

        image_urls = kwargs.pop("image_urls", None)

        for key, value in kwargs.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)

        # Update images if provided
        if image_urls is not None:
            # Delete existing images
            db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()
            # Add new images
            for i, url in enumerate(image_urls):
                img = ProductImage(product_id=product_id, image_url=_sanitize_image_url(url), sort_order=i)
                db.add(img)

        db.commit()
        db.refresh(product)
        return product

    def delete(self, db: Session, product_id: str):
        product = self.get_by_id(db, product_id)
        db.delete(product)
        db.commit()
        return True


product_service = ProductService()
