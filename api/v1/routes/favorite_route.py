"""Favorite Routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.favorite import Favorite
from api.v1.models.product import Product
from api.v1.models.user import User

favorites = APIRouter(prefix="/favorites", tags=["Favorites"])


@favorites.get("", status_code=status.HTTP_200_OK)
def get_user_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all favorites for the authenticated user, with product details."""
    favs = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    result = []
    for f in favs:
        product = db.query(Product).filter(Product.id == f.product_id).first()
        if product:
            result.append({
                "id": f.id,
                "product_id": f.product_id,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "image": product.images[0].image_url if product.images else None,
                    "video_url": product.video_url,
                    "category_name": product.category.name if product.category else None,
                },
                "created_at": str(f.created_at) if f.created_at else None,
            })
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Favorites retrieved successfully",
        data=result,
    )


@favorites.get("/ids", status_code=status.HTTP_200_OK)
def get_favorite_ids(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get just the product IDs of favorites (for quick lookups)."""
    favs = db.query(Favorite.product_id).filter(Favorite.user_id == current_user.id).all()
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Favorite IDs retrieved",
        data=[f.product_id for f in favs],
    )


@favorites.post("/{product_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a product to favorites."""
    # Check if already favorited
    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.product_id == product_id)
        .first()
    )
    if existing:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Already in favorites",
            data={"product_id": product_id},
        )

    fav = Favorite(user_id=current_user.id, product_id=product_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return success_response(
        status_code=status.HTTP_201_CREATED,
        message="Added to favorites",
        data={"id": fav.id, "product_id": fav.product_id},
    )


@favorites.delete("/{product_id}", status_code=status.HTTP_200_OK)
def remove_favorite(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a product from favorites."""
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.product_id == product_id)
        .first()
    )
    if not fav:
        return success_response(
            status_code=status.HTTP_200_OK,
            message="Not in favorites",
            data={"product_id": product_id},
        )
    db.delete(fav)
    db.commit()
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Removed from favorites",
        data={"product_id": product_id},
    )
