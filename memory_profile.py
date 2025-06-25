#!/usr/bin/env python3
"""
Memory and Performance Profiler for Fashion AI

This script helps identify memory leaks and performance bottlenecks in the Fashion AI application
by monitoring memory usage over time and during specific API calls. It can create visual graphs
showing memory consumption patterns and identify components that might cause memory issues.

Usage:
    python memory_profile.py [command]

Commands:
    monitor     - Monitor memory usage over time
    api-test    - Test memory usage during specific API calls
    leak-detect - Run garbage collection analysis to find potential memory leaks
    report      - Generate a comprehensive memory and performance report
"""

import os
import sys
import time
import psutil
import requests
import gc
import tracemalloc
import json
import platform
import logging
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='memory_profile.log',
    filemode='a'
)

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "outfits": "/outfits/generate",
    "health": "/health",
    "products": "/products/search",
    "match": "/outfits/match"
}
MONITOR_INTERVAL = 1  # seconds
MONITOR_DURATION = 300  # seconds (5 minutes)
OUTPUT_DIR = Path("./profiling_reports")

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        logging.info(f"Created output directory: {OUTPUT_DIR}")


def get_memory_usage():
    """Get current memory usage of the process"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / (1024 * 1024),  # RSS in MB
        'vms': memory_info.vms / (1024 * 1024),  # VMS in MB
        'percent': process.memory_percent(),
        'system_percent': psutil.virtual_memory().percent
    }


def monitor_memory(duration=MONITOR_DURATION, interval=MONITOR_INTERVAL):
    """
    Monitor memory usage over time and generate graph
    
    Args:
        duration: Duration to monitor in seconds
        interval: Interval between measurements in seconds
    """
    ensure_output_dir()
    logging.info(f"Starting memory monitoring for {duration} seconds...")
    
    timestamps = []
    rss_values = []
    vms_values = []
    system_percent = []
    
    start_time = time.time()
    end_time = start_time + duration
    
    try:
        while time.time() < end_time:
            current_time = time.time() - start_time
            memory = get_memory_usage()
            
            timestamps.append(current_time)
            rss_values.append(memory['rss'])
            vms_values.append(memory['vms'])
            system_percent.append(memory['system_percent'])
            
            logging.info(f"Time: {current_time:.1f}s, RSS: {memory['rss']:.2f} MB, "
                        f"VMS: {memory['vms']:.2f} MB, System: {memory['system_percent']:.1f}%")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    
    # Generate graph
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, rss_values, 'b-', label='RSS Memory (MB)')
    plt.plot(timestamps, vms_values, 'r-', label='VMS Memory (MB)')
    plt.title('Memory Usage Over Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Memory (MB)')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, system_percent, 'g-', label='System Memory Usage (%)')
    plt.title('System Memory Usage')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Memory Usage (%)')
    plt.legend()
    plt.grid(True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = OUTPUT_DIR / f"memory_profile_{timestamp}.png"
    plt.tight_layout()
    plt.savefig(filename)
    logging.info(f"Memory profile saved to {filename}")
    
    # Save raw data
    data_file = OUTPUT_DIR / f"memory_data_{timestamp}.json"
    with open(data_file, 'w') as f:
        json.dump({
            'timestamps': timestamps,
            'rss_values': rss_values,
            'vms_values': vms_values,
            'system_percent': system_percent
        }, f)
    logging.info(f"Raw data saved to {data_file}")


def test_api_memory_usage():
    """Test memory usage during specific API calls"""
    ensure_output_dir()
    logging.info("Starting API memory usage testing...")
    
    tracemalloc.start()
    results = {}
    
    for name, endpoint in ENDPOINTS.items():
        logging.info(f"Testing endpoint: {endpoint}")
        
        # Clear cache before each test
        gc.collect()
        
        # First snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Make API call
        try:
            if name == "outfits":
                response = requests.post(f"{BASE_URL}{endpoint}", json={
                    "prompt": "Casual summer outfit for a man",
                    "gender": "male",
                    "budget": 200
                }, timeout=30)
            elif name == "products":
                response = requests.get(f"{BASE_URL}{endpoint}?query=blue%20jeans", timeout=10)
            elif name == "match":
                response = requests.post(f"{BASE_URL}{endpoint}", json={
                    "items": [
                        {"name": "blue jeans", "category": "pants"},
                        {"name": "white t-shirt", "category": "tops"}
                    ]
                }, timeout=20)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                
            status = response.status_code
        except Exception as e:
            logging.error(f"Error calling {endpoint}: {str(e)}")
            status = "Error"
        
        # Second snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Record results
        memory_diff = sum(stat.size_diff for stat in top_stats)
        memory_diff_mb = memory_diff / (1024 * 1024)
        
        results[name] = {
            'endpoint': endpoint,
            'status': status,
            'memory_diff_mb': memory_diff_mb,
            'top_allocations': [
                {
                    'file': stat.traceback[0].filename,
                    'line': stat.traceback[0].lineno,
                    'size': stat.size_diff / 1024,
                    'count': stat.count_diff
                }
                for stat in top_stats[:10]
            ]
        }
        
        logging.info(f"Endpoint {endpoint} used {memory_diff_mb:.2f} MB additional memory")
    
    tracemalloc.stop()
    
    # Generate report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = OUTPUT_DIR / f"api_memory_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"API memory report saved to {report_file}")
    
    # Generate graph
    plt.figure(figsize=(10, 6))
    endpoints = list(results.keys())
    memory_usage = [results[ep]['memory_diff_mb'] for ep in endpoints]
    
    plt.bar(endpoints, memory_usage)
    plt.title('Memory Usage by API Endpoint')
    plt.xlabel('Endpoint')
    plt.ylabel('Memory Usage (MB)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    graph_file = OUTPUT_DIR / f"api_memory_graph_{timestamp}.png"
    plt.savefig(graph_file)
    logging.info(f"API memory graph saved to {graph_file}")


def detect_memory_leaks():
    """Detect potential memory leaks using garbage collection analysis"""
    ensure_output_dir()
    logging.info("Starting memory leak detection...")
    
    # Run garbage collection
    gc.collect()
    
    # Get objects currently in memory
    objects = gc.get_objects()
    logging.info(f"Total objects in memory: {len(objects)}")
    
    # Count object types
    type_counts = Counter(type(obj).__name__ for obj in objects)
    top_types = type_counts.most_common(20)
    
    logging.info("Top object types in memory:")
    for type_name, count in top_types:
        logging.info(f"{type_name}: {count}")
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = OUTPUT_DIR / f"memory_leak_report_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'total_objects': len(objects),
            'top_types': dict(top_types)
        }, f, indent=2)
    logging.info(f"Memory leak report saved to {report_file}")
    
    # Generate graph
    plt.figure(figsize=(12, 8))
    
    types = [t[0] for t in top_types]
    counts = [t[1] for t in top_types]
    
    plt.barh(types, counts)
    plt.title('Object Count by Type')
    plt.xlabel('Count')
    plt.ylabel('Object Type')
    plt.tight_layout()
    
    graph_file = OUTPUT_DIR / f"memory_leak_graph_{timestamp}.png"
    plt.savefig(graph_file)
    logging.info(f"Memory leak graph saved to {graph_file}")


def generate_comprehensive_report():
    """Generate a comprehensive memory and performance report"""
    ensure_output_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = OUTPUT_DIR / f"comprehensive_report_{timestamp}.md"
    
    logging.info("Generating comprehensive report...")
    
    process = psutil.Process(os.getpid())
    
    with open(report_file, 'w') as f:
        f.write("# Fashion AI Memory and Performance Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # System information
        f.write("## System Information\n\n")
        f.write(f"- OS: {platform.system()} {platform.release()}\n")
        f.write(f"- Python: {platform.python_version()}\n")
        f.write(f"- CPU: {psutil.cpu_count(logical=False)} cores ({psutil.cpu_count()} logical)\n")
        f.write(f"- Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB total\n")
        f.write(f"- Memory Available: {psutil.virtual_memory().available / (1024**3):.2f} GB\n")
        f.write(f"- Memory Used: {psutil.virtual_memory().percent}%\n\n")
        
        # Current process info
        f.write("## Current Process Information\n\n")
        f.write(f"- PID: {os.getpid()}\n")
        f.write(f"- Memory Usage (RSS): {process.memory_info().rss / (1024**2):.2f} MB\n")
        f.write(f"- Memory Usage (VMS): {process.memory_info().vms / (1024**2):.2f} MB\n")
        f.write(f"- CPU Usage: {process.cpu_percent()}%\n")
        f.write(f"- Threads: {process.num_threads()}\n\n")
        
        # Server health check
        f.write("## Server Health Check\n\n")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                f.write("- Status: Online\n")
                f.write(f"- Version: {health_data.get('version', 'Unknown')}\n")
                
                # API keys
                api_keys = health_data.get('api_keys', {})
                f.write("- API Keys:\n")
                for key, value in api_keys.items():
                    f.write(f"  - {key}: {'Available' if value else 'Missing'}\n")
            else:
                f.write(f"- Status: Error (HTTP {response.status_code})\n")
        except Exception as e:
            f.write(f"- Status: Offline ({str(e)})\n")
        
        f.write("\n## Recommendations\n\n")
        
        # Memory recommendations
        if psutil.virtual_memory().percent > 80:
            f.write("- **WARNING**: System memory usage is high. Consider closing other applications.\n")
        
        if process.memory_info().rss / (1024**2) > 500:
            f.write("- **WARNING**: Application memory usage is high. Check for memory leaks.\n")
        
        f.write("- Run the memory monitoring tool regularly to track memory usage patterns.\n")
        f.write("- Check for any processes that hold onto memory after completing tasks.\n")
        f.write("- Consider implementing connection pooling for HTTP clients if not already done.\n")
        f.write("- Review caching strategies to optimize memory usage.\n")
    
    logging.info(f"Comprehensive report saved to {report_file}")


def print_usage():
    """Print usage information"""
    print(f"Usage: python {sys.argv[0]} [command]")
    print("\nCommands:")
    print("  monitor     - Monitor memory usage over time")
    print("  api-test    - Test memory usage during specific API calls")
    print("  leak-detect - Run garbage collection analysis to find potential memory leaks")
    print("  report      - Generate a comprehensive memory and performance report")
    print("  help        - Show this help message")


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2 or sys.argv[1] == 'help':
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'monitor':
        monitor_memory()
    elif command == 'api-test':
        test_api_memory_usage()
    elif command == 'leak-detect':
        detect_memory_leaks()
    elif command == 'report':
        generate_comprehensive_report()
    else:
        print(f"Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main() 