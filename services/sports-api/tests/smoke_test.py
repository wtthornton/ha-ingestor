"""
Simple smoke test for deployed Sports API service
Run this after deployment to verify basic functionality
"""

import asyncio
import aiohttp
import sys


async def smoke_test(base_url: str = "http://localhost:8015"):
    """
    Run basic smoke tests against deployed service.
    
    Args:
        base_url: Service base URL
    """
    print(f"Running smoke tests against {base_url}...")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("\n1. Testing health check...")
        async with session.get(f"{base_url}/health") as resp:
            if resp.status != 200:
                print(f"[FAIL] Health check failed: {resp.status}")
                return False
            data = await resp.json()
            if data.get('status') != 'healthy':
                print(f"[FAIL] Service not healthy: {data}")
                return False
            print(f"[PASS] Health check passed - Service: {data.get('service')}")
        
        # Test 2: NFL scores endpoint
        print("\n2. Testing NFL scores endpoint...")
        async with session.get(f"{base_url}/api/nfl/scores") as resp:
            if resp.status not in [200, 503]:  # 503 if no API key
                print(f"[FAIL] NFL scores endpoint error: {resp.status}")
                return False
            print(f"[PASS] NFL scores endpoint responsive ({resp.status})")
        
        # Test 3: NHL scores endpoint
        print("\n3. Testing NHL scores endpoint...")
        async with session.get(f"{base_url}/api/nhl/scores") as resp:
            if resp.status not in [200, 503]:
                print(f"[FAIL] NHL scores endpoint error: {resp.status}")
                return False
            print(f"[PASS] NHL scores endpoint responsive ({resp.status})")
        
        # Test 4: Stats endpoint
        print("\n4. Testing stats endpoint...")
        async with session.get(f"{base_url}/api/sports/stats") as resp:
            if resp.status != 200:
                print(f"[FAIL] Stats endpoint failed: {resp.status}")
                return False
            data = await resp.json()
            if 'stats' not in data:
                print(f"[FAIL] Stats response invalid: {data}")
                return False
            print(f"[PASS] Stats endpoint working")
            print(f"   Cache hit rate: {data['stats'].get('cache', {}).get('hit_rate_percentage', 'N/A')}")
    
    print("\n[SUCCESS] All smoke tests passed!")
    return True


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8015"
    
    try:
        result = asyncio.run(smoke_test(base_url))
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[FAIL] Smoke test failed with error: {e}")
        sys.exit(1)

