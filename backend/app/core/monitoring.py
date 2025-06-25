import time
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import statistics
import threading
from collections import deque
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, max_entries=1000, slow_threshold_seconds=3.0, critical_threshold_seconds=10.0, metrics_path=None):
        """
        Initialize the performance monitoring system
        
        Args:
            max_entries: Maximum number of historical entries to keep in memory
            slow_threshold_seconds: Threshold in seconds for slow responses (warning level)
            critical_threshold_seconds: Threshold in seconds for critical responses (error level)
            metrics_path: Path to save metrics data (if None, uses ./metrics)
        """
        self.max_entries = max_entries
        self.slow_threshold = slow_threshold_seconds
        self.critical_threshold = critical_threshold_seconds
        
        # Initialize metrics store with thread safety
        self._lock = threading.Lock()
        self._requests = deque(maxlen=max_entries)
        self._endpoint_metrics = {}
        self._status_metrics = {}
        
        # Runtime statistics
        self._total_requests = 0
        self._slow_requests = 0
        self._error_requests = 0
        
        # Time periods for aggregation
        self._start_time = datetime.now()
        self._last_minute = deque(maxlen=60)
        self._last_hour = deque(maxlen=60*60)
        
        # Set up metrics path
        if metrics_path is None:
            metrics_path = Path("./metrics")
        self.metrics_path = Path(metrics_path)
        self.metrics_path.mkdir(exist_ok=True, parents=True)
        
        # Load existing metrics if available
        self._load_metrics()
        
        logger.info(f"Performance monitor initialized with slow threshold={slow_threshold_seconds}s, "
                   f"critical threshold={critical_threshold_seconds}s")
    
    def record_request(self, 
                       method: str, 
                       endpoint: str, 
                       status_code: int, 
                       duration: float,
                       metadata: Optional[Dict] = None) -> None:
        """
        Record metrics for a single request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
            duration: Request duration in seconds
            metadata: Optional additional data to store with the request
        """
        timestamp = datetime.now()
        
        # Create request record
        request_data = {
            "timestamp": timestamp.isoformat(),
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": duration,
            "metadata": metadata or {}
        }
        
        # Log slow requests
        if duration >= self.critical_threshold:
            logger.error(f"CRITICAL PERFORMANCE: {method} {endpoint} took {duration:.2f}s to complete with status {status_code}")
        elif duration >= self.slow_threshold:
            logger.warning(f"SLOW PERFORMANCE: {method} {endpoint} took {duration:.2f}s to complete with status {status_code}")
        
        # Update metrics under lock to ensure thread safety
        with self._lock:
            self._requests.append(request_data)
            self._total_requests += 1
            
            # Add to time-based collections
            self._last_minute.append((timestamp, duration))
            self._last_hour.append((timestamp, duration))
            
            # Update endpoint metrics
            if endpoint not in self._endpoint_metrics:
                self._endpoint_metrics[endpoint] = {
                    "count": 0,
                    "total_duration": 0,
                    "min_duration": float('inf'),
                    "max_duration": 0,
                    "durations": deque(maxlen=100),  # Keep last 100 durations for this endpoint
                    "status_codes": {}
                }
            
            endpoint_metrics = self._endpoint_metrics[endpoint]
            endpoint_metrics["count"] += 1
            endpoint_metrics["total_duration"] += duration
            endpoint_metrics["min_duration"] = min(endpoint_metrics["min_duration"], duration)
            endpoint_metrics["max_duration"] = max(endpoint_metrics["max_duration"], duration)
            endpoint_metrics["durations"].append(duration)
            
            # Track status codes for this endpoint
            status_str = str(status_code)
            if status_str not in endpoint_metrics["status_codes"]:
                endpoint_metrics["status_codes"][status_str] = 0
            endpoint_metrics["status_codes"][status_str] += 1
            
            # Update status code metrics
            if status_str not in self._status_metrics:
                self._status_metrics[status_str] = 0
            self._status_metrics[status_str] += 1
            
            # Update slow and error counts
            if duration >= self.slow_threshold:
                self._slow_requests += 1
            
            if status_code >= 400:
                self._error_requests += 1
        
        # Periodically save metrics (every 100 requests)
        if self._total_requests % 100 == 0:
            self._save_metrics()
    
    def get_metrics(self) -> Dict:
        """Get a comprehensive metrics report"""
        with self._lock:
            now = datetime.now()
            uptime = (now - self._start_time).total_seconds()
            
            # Calculate average response times for different time periods
            last_minute_avg = self._calculate_average(
                [duration for ts, duration in self._last_minute if (now - ts).total_seconds() <= 60]
            )
            
            last_hour_avg = self._calculate_average(
                [duration for ts, duration in self._last_hour if (now - ts).total_seconds() <= 3600]
            )
            
            # Calculate endpoint statistics
            endpoints = []
            for endpoint, data in self._endpoint_metrics.items():
                if data["count"] > 0:
                    avg_duration = data["total_duration"] / data["count"]
                    durations_list = list(data["durations"])
                    
                    # Calculate percentiles if we have enough data
                    p95 = p99 = None
                    if durations_list:
                        durations_list.sort()
                        if len(durations_list) >= 20:  # Only calculate if we have enough samples
                            p95_idx = int(len(durations_list) * 0.95)
                            p99_idx = int(len(durations_list) * 0.99)
                            p95 = durations_list[p95_idx - 1]
                            p99 = durations_list[p99_idx - 1] if p99_idx > 0 else durations_list[-1]
                    
                    endpoints.append({
                        "endpoint": endpoint,
                        "count": data["count"],
                        "avg_duration": avg_duration,
                        "min_duration": data["min_duration"],
                        "max_duration": data["max_duration"],
                        "p95": p95,
                        "p99": p99,
                        "status_codes": data["status_codes"]
                    })
            
            # Sort endpoints by average duration (slowest first)
            endpoints.sort(key=lambda x: x["avg_duration"], reverse=True)
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self._total_requests,
                "requests_per_second": self._total_requests / uptime if uptime > 0 else 0,
                "slow_requests": self._slow_requests,
                "error_requests": self._error_requests,
                "status_codes": self._status_metrics,
                "response_times": {
                    "last_minute_avg": last_minute_avg,
                    "last_hour_avg": last_hour_avg,
                    "overall_avg": self._calculate_average([r["duration"] for r in self._requests])
                },
                "endpoints": endpoints[:10],  # Top 10 slowest endpoints
                "slow_threshold": self.slow_threshold,
                "critical_threshold": self.critical_threshold
            }
    
    def get_recent_slow_requests(self, limit=10) -> List[Dict]:
        """Get the most recent slow requests"""
        with self._lock:
            slow_requests = [r for r in self._requests if r["duration"] >= self.slow_threshold]
            # Sort by timestamp (newest first) and return limited number
            slow_requests.sort(key=lambda x: x["timestamp"], reverse=True)
            return slow_requests[:limit]
    
    def _calculate_average(self, values):
        """Calculate the average of a list of values"""
        if not values:
            return None
        return sum(values) / len(values)
    
    def _save_metrics(self):
        """Save metrics to disk for persistence"""
        try:
            metrics_file = self.metrics_path / "performance_metrics.json"
            
            # Prepare data for serialization
            serializable_data = {
                "timestamp": datetime.now().isoformat(),
                "total_requests": self._total_requests,
                "slow_requests": self._slow_requests,
                "error_requests": self._error_requests,
                "start_time": self._start_time.isoformat(),
                "endpoint_summaries": {}
            }
            
            # Create endpoint summaries (exclude large data like durations lists)
            for endpoint, data in self._endpoint_metrics.items():
                if data["count"] > 0:
                    serializable_data["endpoint_summaries"][endpoint] = {
                        "count": data["count"],
                        "avg_duration": data["total_duration"] / data["count"],
                        "min_duration": data["min_duration"],
                        "max_duration": data["max_duration"],
                        "status_codes": data["status_codes"]
                    }
            
            with open(metrics_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            logger.debug(f"Performance metrics saved to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save performance metrics: {str(e)}")
    
    def _load_metrics(self):
        """Load metrics from disk if available, but only recent data to avoid stale errors"""
        try:
            metrics_file = self.metrics_path / "performance_metrics.json"
            if not metrics_file.exists():
                return
            
            with open(metrics_file, 'r') as f:
                data = json.load(f)
            
            # Check if metrics are too old (more than 24 hours)
            try:
                saved_time = datetime.fromisoformat(data.get("timestamp", ""))
                if (datetime.now() - saved_time).total_seconds() > 86400:  # 24 hours
                    logger.info("Metrics file is older than 24 hours, starting fresh")
                    return
            except:
                logger.info("Invalid timestamp in metrics file, starting fresh")
                return
            
            # Only load if the error rate isn't unrealistic (>50% indicates stale data)
            total_requests = data.get("total_requests", 0)
            error_requests = data.get("error_requests", 0)
            if total_requests > 0 and (error_requests / total_requests) > 0.5:
                logger.info("Metrics show high error rate (>50%), likely stale data. Starting fresh.")
                return
            
            # Restore basic counters only if they seem reasonable
            self._total_requests = data.get("total_requests", 0)
            self._slow_requests = data.get("slow_requests", 0)
            self._error_requests = data.get("error_requests", 0)
            
            # Restore start time if possible
            try:
                self._start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))
            except:
                self._start_time = datetime.now()
            
            logger.info(f"Loaded performance metrics from {metrics_file}: {self._total_requests} requests recorded")
        except Exception as e:
            logger.error(f"Failed to load performance metrics: {str(e)}")
            # Continue with empty metrics

    def reset_metrics(self):
        """Reset all metrics to start fresh"""
        with self._lock:
            self._requests.clear()
            self._endpoint_metrics.clear()
            self._status_metrics.clear()
            self._total_requests = 0
            self._slow_requests = 0
            self._error_requests = 0
            self._start_time = datetime.now()
            self._last_minute.clear()
            self._last_hour.clear()
            
            # Remove the metrics file
            try:
                metrics_file = self.metrics_path / "performance_metrics.json"
                if metrics_file.exists():
                    metrics_file.unlink()
                logger.info("Metrics reset successfully")
            except Exception as e:
                logger.error(f"Failed to remove metrics file: {str(e)}")

    def get_reset_endpoint(self):
        """Endpoint to reset metrics (for administrative use)"""
        self.reset_metrics()
        return {"message": "Metrics reset successfully", "timestamp": datetime.now().isoformat()}


# Create a global instance
performance_monitor = PerformanceMonitor(
    max_entries=10000,
    slow_threshold_seconds=3.0,
    critical_threshold_seconds=10.0,
    metrics_path="./metrics"
) 