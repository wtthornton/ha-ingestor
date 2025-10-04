#!/usr/bin/env python3
"""
Home Assistant Ingestor - Comprehensive Smoke Tests

This script provides comprehensive smoke testing for the complete system:
- Service health validation
- API endpoint testing
- Data pipeline validation
- Database connectivity
- External service integration
- Performance baseline checks

Usage:
    python tests/smoke_tests.py
    python tests/smoke_tests.py --admin-url http://localhost:8003
    python tests/smoke_tests.py --verbose
    python tests/smoke_tests.py --output json
"""

import asyncio
import sys
import argparse
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Third-party imports
try:
    import aiohttp
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install required packages:")
    print("pip install aiohttp requests python-dotenv")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmokeTestResult:
    """Container for smoke test results"""
    
    def __init__(self, name: str, category: str = "general"):
        self.name = name
        self.category = category
        self.success = False
        self.error = None
        self.details = {}
        self.duration_ms = 0
        self.timestamp = datetime.now().isoformat()
        self.severity = "info"  # info, warning, critical
    
    def set_success(self, details: Dict[str, Any] = None, duration_ms: float = 0):
        """Mark test as successful"""
        self.success = True
        self.duration_ms = duration_ms
        if details:
            self.details.update(details)
    
    def set_error(self, error: str, details: Dict[str, Any] = None, duration_ms: float = 0, severity: str = "warning"):
        """Mark test as failed"""
        self.success = False
        self.error = error
        self.duration_ms = duration_ms
        self.severity = severity
        if details:
            self.details.update(details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'category': self.category,
            'success': self.success,
            'error': self.error,
            'details': self.details,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp,
            'severity': self.severity
        }


class ServiceHealthTester:
    """Test service health and connectivity"""
    
    def __init__(self, admin_url: str = "http://localhost:8003"):
        self.admin_url = admin_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def test_admin_api_health(self) -> SmokeTestResult:
        """Test admin API health endpoint"""
        result = SmokeTestResult("Admin API Health Check", "service_health")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.admin_url}/api/v1/health") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        result.set_success({
                            'status_code': response.status,
                            'overall_status': data.get('status'),
                            'uptime_seconds': data.get('uptime_seconds'),
                            'version': data.get('version'),
                            'services_count': len(data.get('services', {})),
                            'dependencies_count': len(data.get('dependencies', {}))
                        }, duration_ms)
                    else:
                        result.set_error(f"HTTP {response.status}: {await response.text()}", 
                                       {'status_code': response.status}, duration_ms, "critical")
        
        except asyncio.TimeoutError:
            result.set_error("Request timeout - admin API not responding", 
                           {'timeout_seconds': self.timeout.total}, 
                           (time.time() - start_time) * 1000, "critical")
        except Exception as e:
            result.set_error(f"Connection error: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "critical")
        
        return result
    
    async def test_services_health(self) -> SmokeTestResult:
        """Test individual services health"""
        result = SmokeTestResult("Services Health Check", "service_health")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.admin_url}/api/v1/health/services") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        healthy_services = sum(1 for s in data.values() if s.get('status') == 'healthy')
                        total_services = len(data)
                        
                        result.set_success({
                            'total_services': total_services,
                            'healthy_services': healthy_services,
                            'unhealthy_services': total_services - healthy_services,
                            'services': data
                        }, duration_ms)
                    else:
                        result.set_error(f"HTTP {response.status}: {await response.text()}", 
                                       {'status_code': response.status}, duration_ms, "critical")
        
        except Exception as e:
            result.set_error(f"Services health check failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "critical")
        
        return result
    
    async def test_dependencies_health(self) -> SmokeTestResult:
        """Test external dependencies health"""
        result = SmokeTestResult("Dependencies Health Check", "service_health")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.admin_url}/api/v1/health/dependencies") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        healthy_deps = sum(1 for d in data.values() if d.get('status') == 'healthy')
                        total_deps = len(data)
                        
                        result.set_success({
                            'total_dependencies': total_deps,
                            'healthy_dependencies': healthy_deps,
                            'unhealthy_dependencies': total_deps - healthy_deps,
                            'dependencies': data
                        }, duration_ms)
                    else:
                        result.set_error(f"HTTP {response.status}: {await response.text()}", 
                                       {'status_code': response.status}, duration_ms, "warning")
        
        except Exception as e:
            result.set_error(f"Dependencies health check failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "warning")
        
        return result


class APIEndpointTester:
    """Test API endpoints functionality"""
    
    def __init__(self, admin_url: str = "http://localhost:8003"):
        self.admin_url = admin_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def test_api_endpoints(self) -> List[SmokeTestResult]:
        """Test critical API endpoints"""
        results = []
        
        # Test endpoints
        endpoints = [
            ("/api/v1/health", "Health Check"),
            ("/api/v1/stats", "System Statistics"),
            ("/api/v1/config", "Configuration"),
            ("/api/v1/events/recent", "Recent Events"),
            ("/docs", "API Documentation")
        ]
        
        for endpoint, name in endpoints:
            result = SmokeTestResult(f"API Endpoint: {name}", "api_testing")
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(f"{self.admin_url}{endpoint}") as response:
                        duration_ms = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            result.set_success({
                                'endpoint': endpoint,
                                'status_code': response.status,
                                'content_type': response.headers.get('content-type', 'unknown'),
                                'content_length': response.headers.get('content-length', 'unknown')
                            }, duration_ms)
                        else:
                            result.set_error(f"HTTP {response.status}", 
                                           {'endpoint': endpoint, 'status_code': response.status}, 
                                           duration_ms, "warning")
            
            except Exception as e:
                result.set_error(f"Endpoint test failed: {str(e)}", 
                               {'endpoint': endpoint}, 
                               (time.time() - start_time) * 1000, "warning")
            
            results.append(result)
        
        return results


class DataPipelineTester:
    """Test data pipeline functionality"""
    
    def __init__(self, admin_url: str = "http://localhost:8003"):
        self.admin_url = admin_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def test_data_pipeline(self) -> List[SmokeTestResult]:
        """Test data pipeline components"""
        results = []
        
        # Test data retention service
        result = SmokeTestResult("Data Retention Service", "data_pipeline")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get("http://localhost:8080/api/v1/health") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        result.set_success({
                            'service': 'data-retention',
                            'status': data.get('status'),
                            'uptime': data.get('uptime_seconds')
                        }, duration_ms)
                    else:
                        result.set_error(f"Data retention service unhealthy: HTTP {response.status}", 
                                       {'status_code': response.status}, duration_ms, "critical")
        
        except Exception as e:
            result.set_error(f"Data retention service test failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "critical")
        
        results.append(result)
        
        # Test enrichment pipeline
        result = SmokeTestResult("Enrichment Pipeline Service", "data_pipeline")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get("http://localhost:8002/api/v1/health") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        result.set_success({
                            'service': 'enrichment-pipeline',
                            'status': data.get('status'),
                            'uptime': data.get('uptime_seconds')
                        }, duration_ms)
                    else:
                        result.set_error(f"Enrichment pipeline unhealthy: HTTP {response.status}", 
                                       {'status_code': response.status}, duration_ms, "critical")
        
        except Exception as e:
            result.set_error(f"Enrichment pipeline test failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "critical")
        
        results.append(result)
        
        # Test InfluxDB connectivity
        result = SmokeTestResult("InfluxDB Connectivity", "data_pipeline")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get("http://localhost:8086/health") as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        result.set_success({
                            'service': 'influxdb',
                            'status': 'healthy',
                            'response_time_ms': duration_ms
                        }, duration_ms)
                    else:
                        result.set_error(f"InfluxDB unhealthy: HTTP {response.status}", 
                                       {'status_code': response.status}, duration_ms, "critical")
        
        except Exception as e:
            result.set_error(f"InfluxDB connectivity test failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "critical")
        
        results.append(result)
        
        return results


class PerformanceTester:
    """Test system performance baselines"""
    
    def __init__(self, admin_url: str = "http://localhost:8003"):
        self.admin_url = admin_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=5)
    
    async def test_performance_baselines(self) -> List[SmokeTestResult]:
        """Test performance baselines"""
        results = []
        
        # Test API response times
        result = SmokeTestResult("API Response Time Baseline", "performance")
        start_time = time.time()
        
        try:
            response_times = []
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Test multiple requests to get average response time
                for i in range(5):
                    req_start = time.time()
                    async with session.get(f"{self.admin_url}/api/v1/health") as response:
                        req_duration = (time.time() - req_start) * 1000
                        if response.status == 200:
                            response_times.append(req_duration)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                # Performance thresholds
                if avg_response_time < 1000:  # 1 second
                    result.set_success({
                        'average_response_time_ms': round(avg_response_time, 2),
                        'max_response_time_ms': round(max_response_time, 2),
                        'min_response_time_ms': round(min_response_time, 2),
                        'requests_tested': len(response_times),
                        'performance_grade': 'excellent'
                    }, (time.time() - start_time) * 1000)
                elif avg_response_time < 2000:  # 2 seconds
                    result.set_success({
                        'average_response_time_ms': round(avg_response_time, 2),
                        'max_response_time_ms': round(max_response_time, 2),
                        'min_response_time_ms': round(min_response_time, 2),
                        'requests_tested': len(response_times),
                        'performance_grade': 'good'
                    }, (time.time() - start_time) * 1000)
                else:
                    result.set_error(f"Slow API response time: {avg_response_time:.2f}ms average", 
                                   {
                                       'average_response_time_ms': round(avg_response_time, 2),
                                       'max_response_time_ms': round(max_response_time, 2),
                                       'min_response_time_ms': round(min_response_time, 2),
                                       'requests_tested': len(response_times)
                                   }, (time.time() - start_time) * 1000, "warning")
            else:
                result.set_error("No successful API requests", {}, (time.time() - start_time) * 1000, "critical")
        
        except Exception as e:
            result.set_error(f"Performance test failed: {str(e)}", 
                           {}, (time.time() - start_time) * 1000, "warning")
        
        results.append(result)
        
        return results


class SmokeTestSuite:
    """Main smoke test suite"""
    
    def __init__(self, admin_url: str = "http://localhost:8003"):
        self.admin_url = admin_url
        self.service_tester = ServiceHealthTester(admin_url)
        self.api_tester = APIEndpointTester(admin_url)
        self.pipeline_tester = DataPipelineTester(admin_url)
        self.performance_tester = PerformanceTester(admin_url)
        self.results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        logger.info("Starting comprehensive smoke tests...")
        
        # Test 1: Service Health
        logger.info("Testing service health...")
        health_tests = [
            await self.service_tester.test_admin_api_health(),
            await self.service_tester.test_services_health(),
            await self.service_tester.test_dependencies_health()
        ]
        self.results.extend(health_tests)
        
        # Test 2: API Endpoints
        logger.info("Testing API endpoints...")
        api_tests = await self.api_tester.test_api_endpoints()
        self.results.extend(api_tests)
        
        # Test 3: Data Pipeline
        logger.info("Testing data pipeline...")
        pipeline_tests = await self.pipeline_tester.test_data_pipeline()
        self.results.extend(pipeline_tests)
        
        # Test 4: Performance
        logger.info("Testing performance baselines...")
        performance_tests = await self.performance_tester.test_performance_baselines()
        self.results.extend(performance_tests)
        
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - successful_tests
        
        # Categorize failures by severity
        critical_failures = sum(1 for result in self.results if not result.success and result.severity == "critical")
        warning_failures = sum(1 for result in self.results if not result.success and result.severity == "warning")
        
        # Overall system health
        system_health = "healthy"
        if critical_failures > 0:
            system_health = "critical"
        elif warning_failures > 0:
            system_health = "degraded"
        elif failed_tests > 0:
            system_health = "warning"
        
        summary = {
            'summary': {
                'total_tests': total_tests,
                'successful': successful_tests,
                'failed': failed_tests,
                'critical_failures': critical_failures,
                'warning_failures': warning_failures,
                'success_rate': f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                'system_health': system_health,
                'deployment_ready': critical_failures == 0
            },
            'results': [result.to_dict() for result in self.results],
            'timestamp': datetime.now().isoformat(),
            'test_duration_ms': sum(result.duration_ms for result in self.results)
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted test summary"""
        print("\n" + "="*80)
        print("HOME ASSISTANT INGESTOR - SMOKE TEST RESULTS")
        print("="*80)
        
        # Summary
        s = summary['summary']
        print(f"\nSUMMARY:")
        print(f"  Total Tests: {s['total_tests']}")
        print(f"  Successful:  {s['successful']} [PASS]")
        print(f"  Failed:      {s['failed']} [FAIL]")
        print(f"  Critical:    {s['critical_failures']} [CRITICAL]")
        print(f"  Warnings:    {s['warning_failures']} [WARNING]")
        print(f"  Success Rate: {s['success_rate']}")
        print(f"  System Health: {s['system_health'].upper()}")
        print(f"  Deployment Ready: {'YES' if s['deployment_ready'] else 'NO'}")
        
        # Detailed results by category
        categories = {}
        for result in summary['results']:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            print("-" * 60)
            
            for result in results:
                status = "[PASS]" if result['success'] else "[FAIL]"
                severity = f"[{result['severity'].upper()}]" if not result['success'] else ""
                duration = f"({result['duration_ms']:.1f}ms)"
                
                print(f"  {status} {severity} {result['name']} {duration}")
                
                if result['success'] and result['details']:
                    for key, value in result['details'].items():
                        print(f"    {key}: {value}")
                elif not result['success']:
                    print(f"    Error: {result['error']}")
                    if result['details']:
                        for key, value in result['details'].items():
                            print(f"    {key}: {value}")
        
        print("\n" + "="*80)
        
        # Deployment recommendation
        if s['deployment_ready']:
            print("🎉 DEPLOYMENT READY - All critical tests passed!")
        else:
            print("⚠️  DEPLOYMENT NOT READY - Critical failures detected!")
            print("   Please fix critical issues before deployment.")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Home Assistant Ingestor Smoke Tests')
    parser.add_argument('--admin-url', default='http://localhost:8003', help='Admin API URL')
    parser.add_argument('--output', choices=['console', 'json'], default='console', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--timeout', type=int, default=30, help='Test timeout in seconds')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run tests
    test_suite = SmokeTestSuite(args.admin_url)
    summary = await test_suite.run_all_tests()
    
    # Output results
    if args.output == 'json':
        print(json.dumps(summary, indent=2))
    else:
        test_suite.print_summary(summary)
    
    # Exit with appropriate code
    if summary['summary']['deployment_ready']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
