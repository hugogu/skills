/**
 * Basic Load Test Example
 * 
 * This is a simple, ready-to-run example that demonstrates basic load testing.
 * It uses the k6 test site (https://test.k6.io) as a safe target for testing.
 * 
 * How to run:
 *   docker-compose run k6 run /scripts/examples/basic-load-test.js
 * 
 * What this test does:
 * - Simulates 10 virtual users
 * - Runs for 30 seconds
 * - Makes GET requests to the test site
 * - Validates response status and timing
 * - Reports results to InfluxDB for Grafana visualization
 * 
 * Expected Results:
 * - All requests should return HTTP 200
 * - 95th percentile response time should be under 500ms
 * - Error rate should be 0%
 * 
 * After running, check Grafana at http://localhost:3000 to see the results.
 */

import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter } from 'k6/metrics';

// Test configuration
export const options = {
  vus: 10,          // 10 virtual users
  duration: '30s',  // Run for 30 seconds
  
  thresholds: {
    // 95% of requests must complete within 500ms
    http_req_duration: ['p(95)<500'],
    // Error rate must be 0%
    http_req_failed: ['rate<0.01'],
  },
};

// Custom counter for successful requests
const successfulRequests = new Counter('successful_requests');

export default function() {
  // Make a GET request to the test site
  const response = http.get('https://test.k6.io', {
    tags: {
      name: 'basic_load_test',
      type: 'example'
    }
  });
  
  // Validate the response
  const checkResult = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  if (checkResult) {
    successfulRequests.add(1);
  }
  
  // Wait 1 second between requests
  sleep(1);
}

export function handleSummary(data) {
  console.log('');
  console.log('=== Basic Load Test Complete ===');
  console.log(`Total requests: ${data.metrics.http_reqs.count}`);
  console.log(`Failed requests: ${data.metrics.http_req_failed.passes}`);
  console.log(`Avg response time: ${data.metrics.http_req_duration.avg.toFixed(2)}ms`);
  console.log(`95th percentile: ${data.metrics.http_req_duration['p(95)'].toFixed(2)}ms`);
  console.log('');
  console.log('View detailed results in Grafana: http://localhost:3000');
}
