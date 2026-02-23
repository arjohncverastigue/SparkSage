from fastapi import APIRouter, Depends, Query
from api.deps import get_current_user
import db as database
import datetime
import config

router = APIRouter()

@router.get("/summary")
async def get_analytics_summary(user: dict = Depends(get_current_user)):
    db_connection = await database.get_db()
    # This is a placeholder. Real implementation would involve complex DB queries.
    # For now, return some dummy data or a basic count.
    # Count total events
    total_events_cursor = await db_connection.execute("SELECT COUNT(*) FROM analytics")
    total_events = (await total_events_cursor.fetchone())[0]

    # Events per type
    events_by_type_cursor = await db_connection.execute("SELECT event_type, COUNT(*) FROM analytics GROUP BY event_type")
    events_by_type = {row[0]: row[1] for row in await events_by_type_cursor.fetchall()}

    # Provider usage (simple count for now)
    provider_usage_cursor = await db_connection.execute("SELECT provider, COUNT(*) FROM analytics WHERE provider IS NOT NULL GROUP BY provider")
    provider_usage = {row[0]: row[1] for row in await provider_usage_cursor.fetchall()}

    return {
        "total_events": total_events,
        "events_by_type": events_by_type,
        "provider_usage": provider_usage,
        # Add more summary data as needed
    }

@router.get("/history")
async def get_analytics_history(
    user: dict = Depends(get_current_user),
    event_type: str | None = None,
    guild_id: str | None = None,
    channel_id: str | None = None,
    start_date: str | None = None, # YYYY-MM-DD
    end_date: str | None = None,   # YYYY-MM-DD
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    query = "SELECT * FROM analytics WHERE 1=1"
    params = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    if guild_id:
        query += " AND guild_id = ?"
        params.append(guild_id)
    if channel_id:
        query += " AND channel_id = ?"
        params.append(channel_id)
    if start_date:
        query += " AND created_at >= ?"
        params.append(start_date + " 00:00:00")
    if end_date:
        query += " AND created_at <= ?"
        params.append(end_date + " 23:59:59")
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    db_connection = await database.get_db()
    cursor = await db_connection.execute(query, params)
    history_data = await cursor.fetchall()

    return {"history": [dict(row) for row in history_data]}

@router.get("/rate_limits")
async def get_rate_limits(user: dict = Depends(get_current_user)):
    return {
        "rate_limit_enabled": config.RATE_LIMIT_ENABLED,
        "rate_limit_user": config.RATE_LIMIT_USER,
        "rate_limit_guild": config.RATE_LIMIT_GUILD,
    }

@router.get("/costs/summary")
async def get_costs_summary(user: dict = Depends(get_current_user)):
    db_connection = await database.get_db()

    total_cost_cursor = await db_connection.execute("SELECT SUM(estimated_cost) FROM analytics WHERE estimated_cost IS NOT NULL")
    total_cost = (await total_cost_cursor.fetchone())[0] or 0.0

    cost_by_provider_cursor = await db_connection.execute("SELECT provider, SUM(estimated_cost) FROM analytics WHERE estimated_cost IS NOT NULL GROUP BY provider")
    cost_by_provider = {row[0]: row[1] for row in await cost_by_provider_cursor.fetchall()}

    # Calculate projected monthly cost (very rough estimate based on last 30 days)
    # This would need more sophisticated logic for accurate projection
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    cost_last_30_days_cursor = await db_connection.execute(
        "SELECT SUM(estimated_cost) FROM analytics WHERE estimated_cost IS NOT NULL AND created_at >= ?",
        (thirty_days_ago.isoformat(),)
    )
    cost_last_30_days = (await cost_last_30_days_cursor.fetchone())[0] or 0.0
    projected_monthly_cost = (cost_last_30_days / 30) * 30 if cost_last_30_days > 0 else 0.0 # Simple projection

    return {
        "total_cost": total_cost,
        "cost_by_provider": cost_by_provider,
        "projected_monthly_cost": projected_monthly_cost,
    }

@router.get("/costs/history")
async def get_costs_history(
    user: dict = Depends(get_current_user),
    start_date: str | None = None, # YYYY-MM-DD
    end_date: str | None = None,   # YYYY-MM-DD
    limit: int = Query(30, ge=1, le=365), # Default to last 30 days
    offset: int = Query(0, ge=0)
):
    db_connection = await database.get_db()
    query = """
        SELECT
            STRFTIME('%Y-%m-%d', created_at) as date,
            SUM(estimated_cost) as daily_cost
        FROM analytics
        WHERE estimated_cost IS NOT NULL
    """
    params = []

    if start_date:
        query += " AND created_at >= ?"
        params.append(start_date + " 00:00:00")
    if end_date:
        query += " AND created_at <= ?"
        params.append(end_date + " 23:59:59")
    
    query += " GROUP BY date ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db_connection.execute(query, params)
    cost_history_data = await cursor.fetchall()

    return {"cost_history": [dict(row) for row in cost_history_data]}