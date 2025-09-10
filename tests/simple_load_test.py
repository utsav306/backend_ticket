import requests
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor
import json

class SimpleLoadTest:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results = []
        
    def make_request(self, endpoint, method="GET", data=None):
        """Make a single request and measure time"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(f"{self.base_url}{endpoint}", timeout=10)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "response_time": response_time,
                "endpoint": endpoint
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": None,
                "endpoint": endpoint
            }
    
    def worker_thread(self, thread_id, requests_per_thread):
        """Worker thread for load testing"""
        thread_results = []
        
        endpoints = [
            "/events",
            "/health", 
            "/admin/analytics",
            "/admin/cache/status"
        ]
        
        for i in range(requests_per_thread):
            endpoint = endpoints[i % len(endpoints)]
            result = self.make_request(endpoint)
            result["thread_id"] = thread_id
            result["request_num"] = i
            thread_results.append(result)
            
            # Small delay between requests
            time.sleep(0.1)
        
        return thread_results
    
    def run_load_test(self, num_threads=5, requests_per_thread=20):
        """Run load test with multiple threads"""
        print(f"🚀 Starting Load Test: {num_threads} threads × {requests_per_thread} requests")
        print(f"📊 Total Requests: {num_threads * requests_per_thread}")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self.worker_thread, i, requests_per_thread)
                for i in range(num_threads)
            ]
            
            all_results = []
            for future in futures:
                thread_results = future.result()
                all_results.extend(thread_results)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        return self.analyze_results(all_results, total_duration)
    
    def analyze_results(self, results, total_duration):
        """Analyze load test results"""
        successful_results = [r for r in results if r["success"] and r["response_time"]]
        failed_results = [r for r in results if not r["success"]]
        
        if not successful_results:
            return {
                "error": "No successful requests",
                "total_requests": len(results),
                "failed_requests": len(failed_results)
            }
        
        response_times = [r["response_time"] for r in successful_results]
        
        # Group by endpoint
        endpoint_stats = {}
        for result in successful_results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(result["response_time"])
        
        # Calculate stats for each endpoint
        endpoint_analysis = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_analysis[endpoint] = {
                "requests": len(times),
                "avg_response_time": round(statistics.mean(times), 2),
                "min_response_time": round(min(times), 2),
                "max_response_time": round(max(times), 2),
                "median_response_time": round(statistics.median(times), 2)
            }
        
        return {
            "summary": {
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": round((len(successful_results) / len(results)) * 100, 2),
                "total_duration": round(total_duration, 2),
                "requests_per_second": round(len(results) / total_duration, 2),
                "avg_response_time": round(statistics.mean(response_times), 2),
                "min_response_time": round(min(response_times), 2),
                "max_response_time": round(max(response_times), 2),
                "p95_response_time": round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 10 else round(max(response_times), 2)
            },
            "endpoint_analysis": endpoint_analysis,
            "errors": [r.get("error", "Unknown error") for r in failed_results]
        }
    
    def cache_performance_test(self):
        """Test cache performance specifically"""
        print("🔥 Testing Cache Performance...")
        
        # Clear cache first
        self.make_request("/admin/cache/clear", "DELETE")
        time.sleep(1)
        
        # Test cold cache (first few requests)
        print("❄️  Testing Cold Cache...")
        cold_times = []
        for i in range(5):
            result = self.make_request("/events")
            if result["success"]:
                cold_times.append(result["response_time"])
            time.sleep(0.5)
        
        # Test warm cache (many requests)
        print("🔥 Testing Warm Cache...")
        warm_times = []
        for i in range(20):
            result = self.make_request("/events")
            if result["success"]:
                warm_times.append(result["response_time"])
            time.sleep(0.1)
        
        if cold_times and warm_times:
            cold_avg = statistics.mean(cold_times)
            warm_avg = statistics.mean(warm_times)
            improvement = ((cold_avg - warm_avg) / cold_avg) * 100
            
            return {
                "cold_cache_avg": round(cold_avg, 2),
                "warm_cache_avg": round(warm_avg, 2),
                "improvement_percent": round(improvement, 2),
                "cache_effectiveness": "Excellent" if improvement > 50 else "Good" if improvement > 20 else "Moderate"
            }
        
        return {"error": "Could not complete cache test"}

def main():
    print("🔧 Simple Load Testing Tool")
    print("=" * 40)
    
    tester = SimpleLoadTest()
    
    # 1. Basic Load Test
    print("\n1️⃣  Basic Load Test (5 threads × 20 requests)")
    basic_results = tester.run_load_test(num_threads=5, requests_per_thread=20)
    
    # 2. Cache Performance Test
    print("\n2️⃣  Cache Performance Test")
    cache_results = tester.cache_performance_test()
    
    # 3. Heavy Load Test
    print("\n3️⃣  Heavy Load Test (10 threads × 30 requests)")
    heavy_results = tester.run_load_test(num_threads=10, requests_per_thread=30)
    
    # Print Results
    print("\n" + "="*50)
    print("📊 LOAD TEST RESULTS")
    print("="*50)
    
    print(f"\n🎯 Basic Load Test Results:")
    if "summary" in basic_results:
        s = basic_results["summary"]
        print(f"  Total Requests: {s['total_requests']}")
        print(f"  Success Rate: {s['success_rate']}%")
        print(f"  Avg Response Time: {s['avg_response_time']}ms")
        print(f"  Requests/Second: {s['requests_per_second']}")
        print(f"  95th Percentile: {s['p95_response_time']}ms")
    
    print(f"\n🔥 Cache Performance:")
    if "cold_cache_avg" in cache_results:
        print(f"  Cold Cache: {cache_results['cold_cache_avg']}ms")
        print(f"  Warm Cache: {cache_results['warm_cache_avg']}ms")
        print(f"  Improvement: {cache_results['improvement_percent']}%")
        print(f"  Effectiveness: {cache_results['cache_effectiveness']}")
    
    print(f"\n⚡ Heavy Load Test Results:")
    if "summary" in heavy_results:
        s = heavy_results["summary"]
        print(f"  Total Requests: {s['total_requests']}")
        print(f"  Success Rate: {s['success_rate']}%")
        print(f"  Avg Response Time: {s['avg_response_time']}ms")
        print(f"  Requests/Second: {s['requests_per_second']}")
        print(f"  95th Percentile: {s['p95_response_time']}ms")
    
    # Save results
    with open("load_test_results.json", "w") as f:
        json.dump({
            "basic_test": basic_results,
            "cache_test": cache_results,
            "heavy_test": heavy_results,
            "timestamp": time.time()
        }, f, indent=2)
    
    print(f"\n💾 Results saved to load_test_results.json")

if __name__ == "__main__":
    main()
