"""Dashboard Analytics Routes"""

from datetime import datetime, timedelta
from calendar import month_abbr

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.order import Order
from api.v1.models.product import Product
from api.v1.models.review import Review
from api.v1.models.custom_request import CustomRequest
from api.v1.models.category import Category

dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard.get("/stats", status_code=status.HTTP_200_OK)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overview statistics for the dashboard."""
    
    # Revenue from completed orders
    total_revenue = db.query(func.sum(Order.total)).filter(Order.status == "completed").scalar() or 0
    
    # Order counts
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(
        (Order.status == "pending") | (Order.status == "awaiting_payment")
    ).count()
    
    # Product counts
    total_products = db.query(Product).count()
    active_products = db.query(Product).filter(Product.status == "active").count()
    
    # Review counts
    pending_reviews = db.query(Review).filter(Review.status == "pending").count()
    
    # Custom request counts
    pending_requests = db.query(CustomRequest).filter(CustomRequest.status == "pending").count()
    
    # Average order value
    completed_orders_count = db.query(Order).filter(Order.status == "completed").count()
    avg_order_value = total_revenue / completed_orders_count if completed_orders_count > 0 else 0
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Dashboard stats retrieved successfully",
        data={
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_products": total_products,
            "active_products": active_products,
            "pending_reviews": pending_reviews,
            "pending_requests": pending_requests,
            "avg_order_value": round(avg_order_value, 2),
        },
    )


@dashboard.get("/chart-data", status_code=status.HTTP_200_OK)
def get_dashboard_chart_data(db: Session = Depends(get_db)):
    """Get monthly sales/order trends and category breakdown for dashboard charts."""

    # --- Monthly sales & order trends (last 6 months) ---
    now = datetime.utcnow()
    six_months_ago = now - timedelta(days=180)

    # Query: group completed orders by year+month
    monthly_rows = (
        db.query(
            extract("year", Order.created_at).label("year"),
            extract("month", Order.created_at).label("month"),
            func.coalesce(func.sum(Order.total), 0).label("sales"),
            func.count(Order.id).label("orders"),
        )
        .filter(Order.created_at >= six_months_ago)
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    # Build a dict keyed by (year, month) for easy lookup
    monthly_map = {}
    for row in monthly_rows:
        monthly_map[(int(row.year), int(row.month))] = {
            "sales": round(float(row.sales), 2),
            "orders": int(row.orders),
        }

    # Build the last 6 calendar months (including current) so we always show 6 data points
    sales_trend = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=30 * i)
        key = (dt.year, dt.month)
        data = monthly_map.get(key, {"sales": 0, "orders": 0})
        sales_trend.append({
            "month": month_abbr[dt.month],
            "sales": data["sales"],
            "orders": data["orders"],
        })

    # --- Category breakdown (product count per category) ---
    category_rows = (
        db.query(
            Category.name,
            func.count(Product.id).label("value"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .group_by(Category.name)
        .all()
    )

    category_breakdown = [
        {"name": row.name, "value": int(row.value)}
        for row in category_rows
    ]

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Chart data retrieved successfully",
        data={
            "sales_trend": sales_trend,
            "category_breakdown": category_breakdown,
        },
    )


RANGE_DAYS = {"1month": 30, "3months": 90, "6months": 180, "1year": 365}


@dashboard.get("/financial-report-data", status_code=status.HTTP_200_OK)
def get_financial_report_data(
    date_range: str = Query("6months", alias="range"),
    db: Session = Depends(get_db),
):
    """Return financial report data for the admin reports page."""

    days = RANGE_DAYS.get(date_range, 180)
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # ---- Revenue trend by month (completed orders) ----
    monthly_rows = (
        db.query(
            extract("year", Order.created_at).label("year"),
            extract("month", Order.created_at).label("month"),
            func.coalesce(func.sum(Order.total), 0).label("sales"),
        )
        .filter(Order.created_at >= start_date, Order.status == "completed")
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    monthly_map = {}
    for row in monthly_rows:
        monthly_map[(int(row.year), int(row.month))] = round(float(row.sales), 2)

    # Build ordered month list
    months_count = max(days // 30, 1)
    revenue_trend = []
    for i in range(months_count - 1, -1, -1):
        dt = now - timedelta(days=30 * i)
        key = (dt.year, dt.month)
        revenue_trend.append({
            "month": month_abbr[dt.month],
            "sales": monthly_map.get(key, 0),
        })

    # ---- Payment method breakdown ----
    payment_rows = (
        db.query(
            Order.payment_method,
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .filter(Order.created_at >= start_date, Order.status == "completed")
        .group_by(Order.payment_method)
        .all()
    )

    payment_breakdown = {
        "BTC": {"count": 0, "revenue": 0},
        "USDT": {"count": 0, "revenue": 0},
        "Paystack": {"count": 0, "revenue": 0},
    }
    for row in payment_rows:
        method = row.payment_method or "Paystack"
        payment_breakdown[method] = {
            "count": int(row.count),
            "revenue": round(float(row.revenue), 2),
        }

    # ---- Aggregate metrics ----
    total_revenue = sum(v["revenue"] for v in payment_breakdown.values())
    total_completed = sum(v["count"] for v in payment_breakdown.values())
    all_orders_count = db.query(Order).filter(Order.created_at >= start_date).count()
    avg_order_value = round(total_revenue / total_completed, 2) if total_completed > 0 else 0

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Financial report data retrieved successfully",
        data={
            "revenue_trend": revenue_trend,
            "payment_breakdown": payment_breakdown,
            "total_revenue": total_revenue,
            "total_orders": all_orders_count,
            "completed_orders": total_completed,
            "avg_order_value": avg_order_value,
        },
    )
