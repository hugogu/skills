/**
 * Load Test Template
 * 
 * Purpose: Simulate normal expected load on your API to validate performance
 * under typical traffic conditions. Use this to establish baseline performance
 * metrics and ensure your API can handle expected concurrent users.
 * 
 * How to run:
 *   docker-compose run k6 run /scripts/templates/load-test-template.js
 * 
 * Or with custom duration/VUs:
 *   docker-compose run -e K6_DURATION=5m -e K6_VUS=50 k6 run /scripts/templates/load-test-template.js
 * 
 * Customization Points:
 * - TARGET_URL: Set via environment variable or modify default below
 * - VUs: Number of virtual users (concurrent requests)
 * - duration: How long to run the test
 * - thresholds: Performance criteria for pass/fail
 */

import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { 
  bearerAuth, 
  checkStatus, 
  checkResponseTime, 
  jsonHeaders 
} from '../utils.js';

// =============================================================================
// CONFIGURATION - Customize these values for your specific test
// =============================================================================

const TARGET_URL = __ENV.TARGET_URL || 'https://test.k6.io';
const VUS = parseInt(__ENV.K6_VUS || '10');
const DURATION = __ENV.K6_DURATION || '30s';

// =============================================================================
// CUSTOM METRICS - Track additional performance indicators
// =============================================================================

const successfulRequests = new Counter('successful_requests');
const errorRate = new Rate('errors');
const apiResponseTime = new Trend('api_response_time');

// =============================================================================
// OPTIONS - Test execution configuration
// =============================================================================

export const options = {
  // Number of virtual users
  vus: VUS,
  
  // Test duration
  duration: DURATION,
  
  // Performance thresholds - test fails if these are exceeded
  thresholds: {
    // 95% of requests must complete within 500ms
    http_req_duration: ['p(95)<500'],
    
    // Error rate must be less than 1%
    http_req_failed: ['rate<0.01'],
    
    // Average response time should be under 200ms
    api_response_time: ['avg<200'],
    
    // At least 95% of custom checks should pass
    successful_requests: ['count>0'],
  },
  
  // Output configuration for InfluxDB
  ext: {
    loadimpact: {
      projectID: __ENV.K6_PROJECT_ID,
      name: 'Load Test Template',
    },
  },
};

// =============================================================================
// SETUP - Runs once before all VUs start
// =============================================================================

export function setup() {
  console.log(`Starting load test against: ${TARGET_URL}`);
  console.log(`Configuration: ${VUS} VUs for ${DURATION}`);
  
  // Perform any initialization here (e.g., authenticate, create test data)
  // Return data that will be passed to the default function
  return {
    baseUrl: TARGET_URL,
    // authToken: authenticate(), // Uncomment if you need authentication
  };
}

// =============================================================================
// MAIN TEST FUNCTION - Executed by each VU
// =============================================================================

export default function(data) {
  const baseUrl = data.baseUrl;
  
  // Example 1: Simple GET request
  // Customize the endpoint to match your API
  const getResponse = http.get(`${baseUrl}/`, {
    tags: { 
      name: 'homepage',
      method: 'GET' 
    }
  });
  
  // Validate the response
  const getCheck = check(getResponse, {
    'GET status is 200': (r) => r.status === 200,
    'GET response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  if (getCheck) {
    successfulRequests.add(1);
  } else {
    errorRate.add(1);
  }
  
  apiResponseTime.add(getResponse.timings.duration);
  
  sleep(1); // Think time between requests
  
  // Example 2: POST request with JSON payload
  // Uncomment and customize for your API
  /*
  const payload = JSON.stringify({
    username: `user_${__VU}`,  // Use VU number for unique data
    email: `user_${__VU}@example.com`,
    action: 'test'
  });
  
  const headers = jsonHeaders();
  // Add authentication if needed:
  // const headers = jsonHeaders(bearerAuth(data.authToken));
  
  const postResponse = http.post(`${baseUrl}/api/endpoint`, payload, {
    headers: headers,
    tags: {
      name: 'api_create',
      method: 'POST'
    }
  });
  
  const postCheck = check(postResponse, {
    'POST status is 201': (r) => r.status === 201,
    'POST response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  if (postCheck) {
    successfulRequests.add(1);
  } else {
    errorRate.add(1);
  }
  
  apiResponseTime.add(postResponse.timings.duration);
  
  sleep(2);
  */
  
  // Example 3: PUT request (update operation)
  /*
  const updatePayload = JSON.stringify({
    id: __VU,
    status: 'updated'
  });
  
  const putResponse = http.put(`${baseUrl}/api/resource/${__VU}`, updatePayload, {
    headers: headers,
    tags: {
      name: 'api_update',
      method: 'PUT'
    }
  });
  
  check(putResponse, {
    'PUT status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
  */
  
  // Example 4: DELETE request
  /*
  const deleteResponse = http.del(`${baseUrl}/api/resource/${__VU}`, null, {
    headers: headers,
    tags: {
      name: 'api_delete',
      method: 'DELETE'
    }
  });
  
  check(deleteResponse, {
    'DELETE status is 204': (r) => r.status === 204,
  });
  
  sleep(1);
  */
}

// =============================================================================
// TEARDOWN - Runs once after all VUs complete
// =============================================================================

export function teardown(data) {
  console.log('Load test completed');
  console.log(`Target URL: ${data.baseUrl}`);
  
  // Perform cleanup here (e.g., delete test data, logout)
}
