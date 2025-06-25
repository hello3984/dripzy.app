from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from app.core.monitoring import performance_monitor

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/metrics", summary="Get performance metrics")
async def get_metrics():
    """
    Get comprehensive performance metrics for the API.
    
    Returns metrics including:
    - Request counts and rates
    - Response time statistics
    - Status code distribution
    - Endpoint performance data
    """
    return performance_monitor.get_metrics()

@router.get("/slow-requests", summary="Get recent slow requests")
async def get_slow_requests(limit: int = Query(10, description="Max number of requests to return")):
    """
    Get details of recent slow requests that exceeded the slow threshold.
    
    Args:
        limit: Maximum number of slow requests to return
    """
    return performance_monitor.get_recent_slow_requests(limit=limit)

@router.get("/endpoints", summary="Get endpoint performance data")
async def get_endpoints_performance():
    """
    Get detailed performance metrics for each endpoint.
    """
    metrics = performance_monitor.get_metrics()
    return {
        "endpoints": metrics.get("endpoints", []),
        "slow_threshold": metrics.get("slow_threshold"),
        "critical_threshold": metrics.get("critical_threshold")
    }

@router.get("/status", summary="Get system status")
async def get_status():
    """
    Get a summary of the system health status based on performance metrics.
    """
    metrics = performance_monitor.get_metrics()
    
    # Calculate health status
    uptime = metrics.get("uptime_seconds", 0)
    total_requests = metrics.get("total_requests", 0)
    error_rate = metrics.get("error_requests", 0) / total_requests if total_requests > 0 else 0
    slow_rate = metrics.get("slow_requests", 0) / total_requests if total_requests > 0 else 0
    
    # Determine overall status
    status = "healthy"
    if error_rate > 0.05:  # More than 5% errors
        status = "critical"
    elif slow_rate > 0.10:  # More than 10% slow responses
        status = "warning"
    elif uptime < 300:  # Less than 5 minutes uptime
        status = "starting"
    
    # Get recent response time averages
    response_times = metrics.get("response_times", {})
    
    return {
        "status": status,
        "uptime": format_duration(uptime),
        "uptime_seconds": uptime,
        "total_requests": total_requests,
        "requests_per_second": metrics.get("requests_per_second", 0),
        "error_rate": error_rate,
        "slow_rate": slow_rate,
        "recent_response_times": {
            "last_minute_avg": response_times.get("last_minute_avg"),
            "last_hour_avg": response_times.get("last_hour_avg")
        }
    }

@router.post("/reset", summary="Reset performance metrics")
async def reset_metrics():
    """
    Reset all performance metrics to start fresh.
    
    This endpoint clears all stored metrics and starts tracking from zero.
    Useful when stale data is causing incorrect error rates.
    """
    return performance_monitor.get_reset_endpoint()

def format_duration(seconds):
    """Format seconds into a human-readable duration string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days" 