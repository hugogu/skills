/**
 * Stress Test Template
 * 
 * Purpose: Gradually increase load on your API to find its breaking point.
 * Unlike load tests which validate normal operation, stress tests push the
 * system beyond expected limits to identify:
 * - Maximum capacity before degradation
 * - How the system fails (gracefully or catastrophically)
 * - Recovery behavior after overload
 * 
 * How to run:
 *   docker-compose run k6 run /scripts/templates/stress-test-template.js
 * 
 * Expected Behavior at Each Stage:
 * - Ramp-up (0-5 min): System should handle increasing load smoothly
 * - Plateau (5-10 min): System at high but sustainable load
 * - Peak (10-15 min): System under maximum stress, may show degradation
 * - Ramp-down (15-20 min): System should recover as load decreases
 * 
 * Interpretation:
 * - Good: System maintains acceptable response times throughout
 * - Warning: Response times increase but system remains stable
 * - Critical: Errors occur or system becomes unresponsive
 */

import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { checkStatus, checkResponseTime } from '../utils.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const TARGET_URL = __ENV.TARGET_URL || 'https://test.k6.io';

// =============================================================================
// CUSTOM METRICS - Track system behavior under stress
// =============================================================================

const breakingPoint = new Counter('breaking_point_detected');
const degradationRate = new Rate('performance_degradation');
const recoveryTime = new Trend('recovery_time');
const errorRate = new Rate('error_rate');

// =============================================================================
// OPTIONS - Ramping stages configuration
// =============================================================================

export const options = {
  // Stages define the ramp pattern:
  // 1. Ramp-up: Gradually increase from 0 to 100 VUs over 5 minutes
  // 2. Plateau: Hold at 100 VUs for 5 minutes (sustained load)
  // 3. Peak: Spike to 200 VUs over 5 minutes (maximum stress)
  // 4. Ramp-down: Gradually decrease to 0 VUs over 5 minutes
  stages: [
    { duration: '5m', target: 100 },   // Ramp-up: 0 -> 100 VUs
    { duration: '5m', target: 100 },   // Plateau: Hold at 100 VUs
    { duration: '5m', target: 200 },   // Peak: 100 -> 200 VUs
    { duration: '5m', target: 0 },     // Ramp-down: 200 -> 0 VUs
  ],
  
  // Thresholds for acceptable degradation
  // These are more relaxed than load tests since we're pushing limits
  thresholds: {
    // p95 should stay under 2 seconds (more lenient than load test)
    http_req_duration: ['p(95)<2000'],
    
    // Error rate should stay under 5% (some errors expected under extreme load)
    http_req_failed: ['rate<0.05'],
    
    // Track degradation
    performance_degradation: ['rate<0.10'],
  },
};

// Track baseline performance for degradation detection
let baselineResponseTime = null;
let isDegraded = false;

// =============================================================================
// SETUP
// =============================================================================

export function setup() {
  console.log('=== STRESS TEST STARTING ===');
  console.log(`Target: ${TARGET_URL}`);
  console.log('');
  console.log('Stage Overview:');
  console.log('  1. Ramp-up (0-5 min): 0 -> 100 VUs - System warming up');
  console.log('  2. Plateau (5-10 min): 100 VUs - Sustained high load');
  console.log('  3. Peak (10-15 min): 100 -> 200 VUs - Maximum stress');
  console.log('  4. Ramp-down (15-20 min): 200 -> 0 VUs - Recovery phase');
  console.log('');
  
  // Establish baseline with a few warmup requests
  const warmupResponse = http.get(TARGET_URL);
  baselineResponseTime = warmupResponse.timings.duration;
  console.log(`Baseline response time: ${baselineResponseTime}ms`);
  
  return {
    baseUrl: TARGET_URL,
    baselineResponseTime: baselineResponseTime,
    startTime: Date.now(),
  };
}

// =============================================================================
// MAIN TEST FUNCTION
// =============================================================================

export default function(data) {
  const elapsed = (Date.now() - data.startTime) / 1000;
  const currentStage = getCurrentStage(elapsed);
  
  // Make a representative API call
  const response = http.get(data.baseUrl, {
    tags: {
      name: 'stress_test_endpoint',
      stage: currentStage,
    }
  });
  
  // Check response status
  const statusOk = checkStatus(response, 200, 'status_ok');
  
  if (!statusOk) {
    errorRate.add(1);
    console.log(`ERROR at ${elapsed}s: Status ${response.status}`);
  }
  
  // Track response time and detect degradation
  const responseTime = response.timings.duration;
  
  // Degradation detection: response time > 3x baseline
  if (responseTime > data.baselineResponseTime * 3) {
    degradationRate.add(1);
    if (!isDegraded) {
      isDegraded = true;
      breakingPoint.add(1);
      console.log(`⚠️  PERFORMANCE DEGRADATION DETECTED at ${elapsed}s`);
      console.log(`   Response time: ${responseTime}ms (baseline: ${data.baselineResponseTime}ms)`);
      console.log(`   Current stage: ${currentStage}`);
    }
  } else if (isDegraded && responseTime < data.baselineResponseTime * 2) {
    // Recovery detected
    isDegraded = false;
    const recoveryDuration = elapsed; // Simplified recovery tracking
    recoveryTime.add(recoveryDuration);
    console.log(`✓ RECOVERY DETECTED at ${elapsed}s`);
  }
  
  // Validate response time based on stage expectations
  // Stage 1-2: Should handle normally
  // Stage 3: May show some degradation
  // Stage 4: Should improve
  let maxAcceptableTime;
  switch(currentStage) {
    case 'ramp-up':
    case 'plateau':
      maxAcceptableTime = 1000; // 1 second
      break;
    case 'peak':
      maxAcceptableTime = 3000; // 3 seconds (more lenient)
      break;
    case 'ramp-down':
      maxAcceptableTime = 1500; // Should improve
      break;
    default:
      maxAcceptableTime = 2000;
  }
  
  checkResponseTime(response, maxAcceptableTime, `response_time_${currentStage}`);
  
  // Variable sleep to simulate realistic user behavior
  // Sleep less during stress to generate more load
  const sleepTime = Math.random() * 0.5 + 0.1; // 0.1-0.6 seconds
  sleep(sleepTime);
}

// =============================================================================
// TEARDOWN
// =============================================================================

export function teardown(data) {
  const totalDuration = (Date.now() - data.startTime) / 1000;
  
  console.log('');
  console.log('=== STRESS TEST COMPLETED ===');
  console.log(`Total duration: ${totalDuration}s`);
  console.log(`Baseline response time: ${data.baselineResponseTime}ms`);
  console.log('');
  console.log('Interpretation Guide:');
  console.log('  ✓ No degradation: System handled all stages well');
  console.log('  ⚠️  Some degradation: System slowed but remained stable');
  console.log('  ✗ Critical failure: Errors or unresponsive during peak');
  console.log('');
  console.log('Check the Grafana dashboard to see detailed metrics.');
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Determines the current test stage based on elapsed time
 * @param {number} elapsedSeconds - Time elapsed since test start
 * @returns {string} Current stage name
 */
function getCurrentStage(elapsedSeconds) {
  if (elapsedSeconds < 300) return 'ramp-up';      // 0-5 min
  if (elapsedSeconds < 600) return 'plateau';      // 5-10 min
  if (elapsedSeconds < 900) return 'peak';         // 10-15 min
  return 'ramp-down';                              // 15-20 min
}
