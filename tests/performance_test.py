import asyncio
import httpx
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class PerformanceMonitor:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results = []
    
    async def measure_endpoint(self, endpoint, method="GET", data=None, iterations=50):
        """Measure endpoint performance"""
        async with httpx.AsyncClient() as client:
            times = []
            errors = 0
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    if method == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}")
                    elif method == "POST":
                        response = await client.post(f"{self.base_url}{endpoint}", json=data)
                    elif method == "DELETE":
                        response = await client.delete(f"{self.base_url}{endpoint}")
                    
                    end_time = time.time()
                    
                    if response.status_code in [200, 201]:
                        times.append((end_time - start_time) * 1000)  # Convert to ms
                    else:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    print(f"Error in {endpoint}: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.01)
            
            if times:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "iterations": iterations,
                    "errors": errors,
                    "avg_response_time": round(statistics.mean(times), 2),
                    "min_response_time": round(min(times), 2),
                    "max_response_time": round(max(times), 2),
                    "median_response_time": round(statistics.median(times), 2),
                    "p95_response_time": round(statistics.quantiles(times, n=20)[18], 2) if len(times) > 10 else round(max(times), 2),
                    "success_rate": round(((iterations - errors) / iterations) * 100, 2)
                }
            else:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "errors": errors,
                    "success_rate": 0
                }
    
    async def run_cache_test(self):
        """Test cache effectiveness"""
        print("🔥 Testing Cache Effectiveness...")
        
        # Clear cache first
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.base_url}/admin/cache/clear")
        
        # Test cold cache (first request)
        cold_result = await self.measure_endpoint("/events", iterations=10)
        print(f"❄️  Cold Cache - Events: {cold_result['avg_response_time']}ms avg")
        
        # Test warm cache (subsequent requests)
        warm_result = await self.measure_endpoint("/events", iterations=40)
        print(f"🔥 Warm Cache - Events: {warm_result['avg_response_time']}ms avg")
        
        improvement = ((cold_result['avg_response_time'] - warm_result['avg_response_time']) / cold_result['avg_response_time']) * 100
        print(f"📈 Cache Performance Improvement: {improvement:.1f}%")
        
        return {"cold_cache": cold_result, "warm_cache": warm_result, "improvement_percent": round(improvement, 1)}
    
    async def run_comprehensive_test(self):
        """Run comprehensive performance tests"""
        print("🚀 Starting Comprehensive Performance Tests...")
        
        endpoints_to_test = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/events", "GET"),
            ("/admin/analytics", "GET"),
            ("/admin/cache/status", "GET"),
            ("/users", "POST", {"name": "Perf Test", "email": f"perf_{int(time.time())}@test.com", "password": "test123", "role": "user"})
        ]
        
        results = []
        
        for endpoint_info in endpoints_to_test:
            endpoint = endpoint_info[0]
            method = endpoint_info[1]
            data = endpoint_info[2] if len(endpoint_info) > 2 else None
            
            print(f"Testing {method} {endpoint}...")
            result = await self.measure_endpoint(endpoint, method, data, iterations=30)
            results.append(result)
            print(f"  ✅ Avg: {result.get('avg_response_time', 'N/A')}ms, Success: {result.get('success_rate', 'N/A')}%")
        
        return results
    
    async def stress_test_concurrent(self, concurrent_users=10, requests_per_user=20):
        """Test with concurrent users"""
        print(f"⚡ Stress Testing with {concurrent_users} concurrent users...")
        
        async def user_simulation():
            async with httpx.AsyncClient() as client:
                times = []
                errors = 0
                
                for _ in range(requests_per_user):
                    start_time = time.time()
                    try:
                        # Mix of endpoints
                        endpoint = ["/events", "/health", "/admin/analytics"][time.time_ns() % 3]
                        response = await client.get(f"{self.base_url}{endpoint}")
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            times.append((end_time - start_time) * 1000)
                        else:
                            errors += 1
                    except:
                        errors += 1
                    
                    await asyncio.sleep(0.1)  # Brief pause
                
                return {"times": times, "errors": errors}
        
        # Run concurrent users
        tasks = [user_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        all_times = []
        total_errors = 0
        for result in results:
            all_times.extend(result["times"])
            total_errors += result["errors"]
        
        if all_times:
            return {
                "concurrent_users": concurrent_users,
                "total_requests": concurrent_users * requests_per_user,
                "total_errors": total_errors,
                "avg_response_time": round(statistics.mean(all_times), 2),
                "p95_response_time": round(statistics.quantiles(all_times, n=20)[18], 2) if len(all_times) > 10 else round(max(all_times), 2),
                "success_rate": round(((len(all_times)) / (concurrent_users * requests_per_user)) * 100, 2)
            }
        
        return {"error": "No successful requests"}

async def main():
    monitor = PerformanceMonitor()
    
    print("🔧 Event Booking API - Performance Test Suite")
    print("=" * 50)
    
    # 1. Basic performance test
    basic_results = await monitor.run_comprehensive_test()
    
    # 2. Cache effectiveness test
    cache_results = await monitor.run_cache_test()
    
    # 3. Concurrent users test
    stress_results = await monitor.stress_test_concurrent(concurrent_users=15, requests_per_user=10)
    
    # Summary
    print("\n📊 PERFORMANCE TEST SUMMARY")
    print("=" * 50)
    
    print("\n🎯 Endpoint Performance:")
    for result in basic_results:
        if 'avg_response_time' in result:
            print(f"  {result['endpoint']:20} | {result['avg_response_time']:6}ms avg | {result['success_rate']:5}% success")
    
    print(f"\n🔥 Cache Performance:")
    print(f"  Cold Cache: {cache_results['cold_cache']['avg_response_time']}ms")
    print(f"  Warm Cache: {cache_results['warm_cache']['avg_response_time']}ms")
    print(f"  Improvement: {cache_results['improvement_percent']}%")
    
    print(f"\n⚡ Stress Test Results:")
    print(f"  Concurrent Users: {stress_results['concurrent_users']}")
    print(f"  Avg Response Time: {stress_results['avg_response_time']}ms")
    print(f"  95th Percentile: {stress_results['p95_response_time']}ms")
    print(f"  Success Rate: {stress_results['success_rate']}%")
    
    # Save results to file
    with open("performance_results.json", "w") as f:
        json.dump({
            "basic_results": basic_results,
            "cache_results": cache_results,
            "stress_results": stress_results,
            "timestamp": time.time()
        }, f, indent=2)
    
    print(f"\n💾 Results saved to performance_results.json")

if __name__ == "__main__":
    asyncio.run(main())
