#!/usr/bin/env python
"""
Load testing script for Progage website
Tests: concurrent users, response times, throughput
"""
import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
import json
import sys

class LoadTester:
    def __init__(self, base_url="http://localhost:8000", concurrent_users=100, total_requests=1000):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.total_requests = total_requests
        self.results = []
        self.errors = []
        
    async def fetch_page(self, session, url, request_id):
        """Fetch single page and measure response time"""
        start_time = time.time()
        try:
            async with session.get(url) as response:
                content = await response.text()
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'url': url,
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'content_length': len(content),
                    'success': response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                'request_id': request_id,
                'url': url,
                'status_code': 0,
                'response_time': end_time - start_time,
                'content_length': 0,
                'success': False,
                'error': str(e)
            }
    
    async def run_concurrent_tests(self, urls):
        """Run concurrent tests"""
        print(f"🚀 Starting load test: {self.concurrent_users} concurrent users, {self.total_requests} total requests")
        print(f"🌐 Target URL: {self.base_url}")
        print("=" * 60)
        
        connector = aiohttp.TCPConnector(limit=self.concurrent_users)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            request_id = 0
            
            # Create tasks for all requests
            for _ in range(self.total_requests):
                url = urls[request_id % len(urls)]
                task = asyncio.create_task(self.fetch_page(session, url, request_id))
                tasks.append(task)
                request_id += 1
                
                # Start concurrent tasks
                if len(tasks) >= self.concurrent_users:
                    completed, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    completed_tasks = [t for t in completed if not t.cancelled()]
                    
                    for task in completed_tasks:
                        result = await task
                        self.results.append(result)
                        if not result['success']:
                            self.errors.append(result)
                    
                    tasks = [t for t in pending if not t.cancelled()]
            
            # Wait for remaining tasks
            if tasks:
                remaining_results = await asyncio.gather(*tasks)
                self.results.extend(remaining_results)
                
                for result in remaining_results:
                    if not result['success']:
                        self.errors.append(result)
    
    def analyze_results(self):
        """Analyze test results"""
        if not self.results:
            print("❌ No results to analyze")
            return
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        success_rate = (len(successful_requests) / len(self.results)) * 100
        error_rate = (len(failed_requests) / len(self.results)) * 100
        
        print("\n" + "=" * 60)
        print("📊 LOAD TEST RESULTS")
        print("=" * 60)
        
        print(f"📈 Total Requests: {len(self.results)}")
        print(f"✅ Successful: {len(successful_requests)} ({success_rate:.1f}%)")
        print(f"❌ Failed: {len(failed_requests)} ({error_rate:.1f}%)")
        
        if response_times:
            print(f"\n⏱️  Response Times:")
            print(f"   Average: {statistics.mean(response_times):.3f}s")
            print(f"   Median: {statistics.median(response_times):.3f}s")
            print(f"   Min: {min(response_times):.3f}s")
            print(f"   Max: {max(response_times):.3f}s")
            print(f"   95th percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
        
        if successful_requests:
            avg_content_length = statistics.mean([r['content_length'] for r in successful_requests])
            print(f"\n📦 Content:")
            print(f"   Average size: {avg_content_length:.0f} bytes")
        
        if self.errors:
            print(f"\n🚨 Errors ({len(self.errors)}):")
            error_types = {}
            for error in self.errors[:10]:  # Show first 10 errors
                error_key = f"{error.get('status_code', 'Network')}"
                error_types[error_key] = error_types.get(error_key, 0) + 1
                print(f"   {error_key}: {error.get('error', 'Unknown error')[:50]}")
            
            print(f"\n📊 Error Summary:")
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count} occurrences")
    
    def save_results(self, filename=None):
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'base_url': self.base_url,
                    'concurrent_users': self.concurrent_users,
                    'total_requests': self.total_requests
                },
                'results': self.results,
                'summary': {
                    'total_requests': len(self.results),
                    'successful_requests': len([r for r in self.results if r['success']]),
                    'failed_requests': len([r for r in self.results if not r['success']]),
                    'success_rate': (len([r for r in self.results if r['success']]) / len(self.results)) * 100
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
    
    async def run_test(self, urls):
        """Run complete test"""
        start_time = time.time()
        
        await self.run_concurrent_tests(urls)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n⏱️  Total test time: {total_time:.2f}s")
        print(f"🚀 Requests per second: {len(self.results) / total_time:.2f}")
        
        self.analyze_results()
        self.save_results()

def main():
    """Main function"""
    print("🔥 Progage Load Testing Tool")
    print("=" * 40)
    
    # Configuration
    base_url = input("https://9b4bccd6be5656.lhr.life").strip()
    if not base_url:
        base_url = "https://9b4bccd6be5656.lhr.life"
    
    try:
        concurrent_users = int(input("👥 Concurrent users (default: 50): ") or "50")
        total_requests = int(input("📊 Total requests (default: 500): ") or "500")
    except ValueError:
        print("❌ Invalid input. Using defaults.")
        concurrent_users = 50
        total_requests = 500
    
    # Test URLs
    test_urls = [
        f"{base_url}/",
        f"{base_url}/courses/",
        f"{base_url}/accounts/login/",
        f"{base_url}/accounts/profile/",
    ]
    
    # Run test
    tester = LoadTester(base_url, concurrent_users, total_requests)
    
    try:
        asyncio.run(tester.run_test(test_urls))
    except KeyboardInterrupt:
        print("\n⏹ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
