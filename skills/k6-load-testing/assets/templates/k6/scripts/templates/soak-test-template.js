/**
 * Soak Test Template
 * 
 * ⚠️  WARNING: This test runs for an extended period (2+ hours by default).
 * Only run when you need to test for long-term stability issues.
 * 
 * Purpose: Test system stability and performance over an extended period.
 * Unlike load tests which run for minutes, soak tests run for hours to detect:
 * - Memory leaks
 * - Resource exhaustion (file handles, connections, etc.)
 * - Performance degradation over time
 * - Database connection pool exhaustion
 * - Log file growth issues
 * 
 * Use Cases:
 * - Pre-production validation for long-running services
 * - Validating stability before major releases
 * - Detecting gradual memory leaks
 * - Testing database connection pool management
 * 
 * How to run:
 *   docker-compose run k6 run /scripts/templates/soak-test-template.js
 * 
 * Configuration:
 * - SOAK_DURATION: Total test duration (default: 2h)
 * - SOAK_VUS: Sustained load level (default: 50)
 * 
 * Expected Behavior:
 * - System maintains stable performance throughout
 * - Response times remain consistent
 * - Memory usage stays stable (no leaks)
 * - No errors or failures
 * 
 * Resource Requirements:
 * - Test runs for hours - ensure stable environment
 * - Monitor disk space (logs, metrics storage)
 * - Ensure network connectivity is stable
 * - Consider running during off-peak hours
 */

import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { checkStatus, checkResponseTime } from '../utils.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const TARGET_URL = __ENV.TARGET_URL || 'https://test.k6.io';
const SOAK_DURATION = __ENV.SOAK_DURATION || '2h';
const SOAK_VUS = parseInt(__ENV.SOAK_VUS || '50');

// =============================================================================
// CUSTOM METRICS - Track degradation over time
// =============================================================================

const hourlyErrorRate = new Trend('hourly_error_rate');
const responseTimeDrift = new Trend('response_time_drift');
const performanceDegradation = new Rate('performance_degradation_detected');
const hourlyRequestCount = new Counter('hourly_requests');

// Track baseline for comparison
let baselineMetrics = null;
let hourlySnapshot = {};

// =============================================================================
// OPTIONS - Extended duration configuration
// =============================================================================

export const options = {
  // Sustained moderate load for extended period
  vus: SOAK_VUS,
  duration: SOAK_DURATION,
  
  // Strict thresholds - any degradation is a concern in soak tests
  thresholds: {
    // Response time should stay consistent
    http_req_duration: ['p(95)<1000'],
    
    // Error rate must stay very low
    http_req_failed: ['rate<0.005'],
    
    // Custom degradation tracking
    performance_degradation_detected: ['rate<0.01'],
    
    // Trend metrics should not drift significantly
    response_time_drift: ['avg<200'],
  },
  
  // Graceful stop to allow ongoing requests to complete
  gracefulStop: '30s',
};

// =============================================================================
// SETUP
// =============================================================================

export function setup() {
  console.log('=== SOAK TEST STARTING ===');
  console.log(`⚠️  WARNING: This test will run for ${SOAK_DURATION}`);
  console.log(`Target: ${TARGET_URL}`);
  console.log(`Virtual Users: ${SOAK_VUS}`);
  console.log('');
  console.log('Purpose: Detect memory leaks, resource exhaustion, and');
  console.log('         performance degradation over extended time.');
  console.log('');
  console.log('Monitor these metrics in Grafana:');
  console.log('  1. Response time trends (should be stable)');
  console.log('  2. Error rates (should stay near zero)');
  console.log('  3. Memory usage on target system');
  console.log('  4. Database connection pools');
  console.log('');
  console.log(`Start time: ${new Date().toISOString()}`);
  console.log('');
  
  // Establish baseline with initial requests
  console.log('Establishing baseline metrics...');
  let baselineTotal = 0;
  let baselineCount = 0;
  
  for (let i = 0; i < 10; i++) {
    const response = http.get(TARGET_URL);
    baselineTotal += response.timings.duration;
    baselineCount++;
    sleep(0.5);
  }
  
  baselineMetrics = {
    avgResponseTime: baselineTotal / baselineCount,
    startTime: Date.now(),
    requestsPerHour: new Map(),
    errorsPerHour: new Map(),
  };
  
  console.log(`Baseline response time: ${baselineMetrics.avgResponseTime.toFixed(2)}ms`);
  console.log('Starting sustained load test...');
  console.log('');
  
  return {
    baseUrl: TARGET_URL,
    baselineResponseTime: baselineMetrics.avgResponseTime,
    startTime: Date.now(),
  };
}

// =============================================================================
// MAIN TEST FUNCTION
// =============================================================================

export default function(data) {
  const elapsed = (Date.now() - data.startTime) / 1000;
  const currentHour = Math.floor(elapsed / 3600);
  
  // Track hourly metrics
  if (!hourlySnapshot[currentHour]) {
    hourlySnapshot[currentHour] = {
      requests: 0,
      errors: 0,
      totalResponseTime: 0,
    };
    
    // Log hourly progress
    if (currentHour > 0) {
      const prevHour = currentHour - 1;
      const prevStats = hourlySnapshot[prevHour];
      if (prevStats) {
        const avgTime = prevStats.totalResponseTime / prevStats.requests;
        const errorRate = prevStats.errors / prevStats.requests;
        console.log(`Hour ${prevHour} complete - Avg: ${avgTime.toFixed(2)}ms, Errors: ${(errorRate * 100).toFixed(2)}%`);
      }
    }
  }
  
  // Make API request
  const response = http.get(data.baseUrl, {
    tags: {
      name: 'soak_test_endpoint',
      hour: currentHour,
    }
  });
  
  // Update hourly stats
  hourlySnapshot[currentHour].requests++;
  hourlySnapshot[currentHour].totalResponseTime += response.timings.duration;
  
  // Check response
  const isSuccess = checkStatus(response, 200, 'status_ok');
  if (!isSuccess) {
    hourlySnapshot[currentHour].errors++;
  }
  
  // Check for performance degradation
  const responseTime = response.timings.duration;
  const degradationThreshold = data.baselineResponseTime * 2; // 2x baseline
  
  if (responseTime > degradationThreshold) {
    performanceDegradation.add(1);
    responseTimeDrift.add(responseTime - data.baselineResponseTime);
    
    // Log only occasional warnings to avoid log spam
    if (Math.random() < 0.01) {
      console.log(`⚠️  Performance degradation detected at ${formatDuration(elapsed)}`);
      console.log(`   Response time: ${responseTime}ms (baseline: ${data.baselineResponseTime.toFixed(2)}ms)`);
    }
  }
  
  // Standard response time check
  checkResponseTime(response, 1000, 'response_time_check');
  
  // Variable sleep to simulate realistic usage
  // Use slightly longer sleep for soak test to prevent excessive resource usage
  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 seconds
}

// =============================================================================
// TEARDOWN
// =============================================================================

export function teardown(data) {
  const totalDuration = (Date.now() - data.startTime) / 1000;
  
  console.log('');
  console.log('=== SOAK TEST COMPLETED ===');
  console.log(`Total duration: ${formatDuration(totalDuration)}`);
  console.log(`End time: ${new Date().toISOString()}`);
  console.log('');
  
  // Print hourly summary
  console.log('Hourly Summary:');
  for (const [hour, stats] of Object.entries(hourlySnapshot)) {
    const avgTime = stats.totalResponseTime / stats.requests;
    const errorRate = (stats.errors / stats.requests) * 100;
    const drift = avgTime - data.baselineResponseTime;
    console.log(`  Hour ${hour}: Avg=${avgTime.toFixed(2)}ms (${drift >= 0 ? '+' : ''}${drift.toFixed(2)}ms), Errors=${errorRate.toFixed(2)}%, Requests=${stats.requests}`);
  }
  
  console.log('');
  console.log('Interpretation:');
  console.log('  ✓ PASS: Stable performance, minimal errors');
  console.log('  ⚠️  WARNING: Gradual performance decline or intermittent errors');
  console.log('  ✗ FAIL: Significant degradation or increasing error rates');
  console.log('');
  console.log('Check Grafana for detailed metrics and trends.');
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Formats seconds into human-readable duration
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration
 */
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}
