"""
Routes Registration
File: api/v1/routes/__init__.py
"""
from fastapi import APIRouter

from api.v1.routes.auth_route import auth
from api.v1.routes.product_route import products
from api.v1.routes.category_route import categories
from api.v1.routes.order_route import orders
from api.v1.routes.discount_route import discounts
from api.v1.routes.review_route import reviews
from api.v1.routes.custom_request_route import custom_requests
from api.v1.routes.upload_route import upload
from api.v1.routes.dashboard_route import dashboard
from api.v1.routes.subscriber_route import subscribers
from api.v1.routes.favorite_route import favorites
from api.v1.routes.setting_route import setting_router
from api.v1.routes.shipping_route import shipping


api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(products)
api_version_one.include_router(categories)
api_version_one.include_router(orders)
api_version_one.include_router(discounts)
api_version_one.include_router(reviews)
api_version_one.include_router(custom_requests)
api_version_one.include_router(upload)
api_version_one.include_router(dashboard)
api_version_one.include_router(subscribers)
api_version_one.include_router(favorites)
api_version_one.include_router(setting_router)
api_version_one.include_router(shipping)

