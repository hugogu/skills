/**
 * Spike Test Template
 * 
 * Purpose: Simulate sudden, extreme increases in traffic to test how well
 * your API handles unexpected traffic spikes. This is different from stress
 * testing because the increase is sudden, not gradual.
 * 
 * Use Cases:
 * - Black Friday / flash sale traffic spikes
 * - Viral content sudden popularity
 * - DDoS attack simulation (at lower scale)
 * - Recovery from downtime when users rush back
 * 
 * How to run:
 *   docker-compose run k6 run /scripts/templates/spike-test-template.js
 * 
 * Configuration:
 * - BASELINE_VUS: Normal operating load (default: 10)
 * - SPIKE_VUS: Maximum spike load (default: 100)
 * - BASELINE_DURATION: How long to hold baseline (default: 2m)
 * - SPIKE_DURATION: How long the spike lasts (default: 2m)
 * 
 * Test Pattern:
 * 1. Baseline (0-2 min): 10 VUs - Normal operation
 * 2. Spike (2-4 min): 10 -> 100 VUs - Sudden 10x increase
 * 3. Recovery (4-6 min): 100 -> 10 VUs - Back to baseline
 * 4. Observation (6-8 min): 10 VUs - Check for lingering issues
 * 
 * Interpretation:
 * - PASS: System handles spike, may slow but doesn't fail, recovers quickly
 * - WARNING: Errors during spike but system recovers
 * - FAIL: System crashes or doesn't recover after spike ends
 */

import http from 'k6/http';
import { sleep, check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { checkStatus, checkResponseTime } from '../utils.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const TARGET_URL = __ENV.TARGET_URL || 'https://test.k6.io';
const BASELINE_VUS = parseInt(__ENV.SPIKE_BASELINE_VUS || '10');
const SPIKE_VUS = parseInt(__ENV.SPIKE_VUS || '100');

// =============================================================================
// CUSTOM METRICS - Track spike impact and recovery
// =============================================================================

const spikeImpact = new Counter('spike_impact_events');
const recoveryDetected = new Counter('recovery_events');
const errorDuringSpike = new Rate('error_during_spike');
const spikeResponseTime = new Trend('spike_response_time');

// =============================================================================
// OPTIONS - Sudden spike pattern
// =============================================================================

export const options = {
  // Spike pattern: baseline -> sudden spike -> recovery -> observation
  stages: [
    { duration: '2m', target: BASELINE_VUS },    // Baseline: Normal load
    { duration: '1m', target: SPIKE_VUS },       // Spike: Sudden jump (very fast ramp)
    { duration: '2m', target: SPIKE_VUS },       // Hold spike
    { duration: '1m', target: BASELINE_VUS },    // Recovery: Back to baseline
    { duration: '2m', target: BASELINE_VUS },    // Observation: Monitor recovery
  ],
  
  // Thresholds - more lenient during spike
  thresholds: {
    // During spike, up to 5 second response times might be acceptable
    http_req_duration: ['p(95)<5000'],
    
    // Error rate should stay under 10% (some errors expected during extreme spike)
    http_req_failed: ['rate<0.10'],
    
    // Track spike-specific metrics
    error_during_spike: ['rate<0.15'],
  },
};

// Track which phase we're in
let currentPhase = 'baseline';
let spikeStartTime = null;
let errorsDuringSpike = 0;

// =============================================================================
// SETUP
// =============================================================================

export function setup() {
  console.log('=== SPIKE TEST STARTING ===');
  console.log(`Target: ${TARGET_URL}`);
  console.log(`Baseline VUs: ${BASELINE_VUS}`);
  console.log(`Spike VUs: ${SPIKE_VUS}`);
  console.log(`Intensity: ${(SPIKE_VUS / BASELINE_VUS).toFixed(1)}x increase`);
  console.log('');
  console.log('Timeline:');
  console.log('  0-2 min:  Baseline - Normal operation');
  console.log('  2-3 min:  SPIKE - Sudden traffic surge');
  console.log('  3-5 min:  SUSTAIN - Holding peak load');
  console.log('  5-6 min:  RECOVERY - Traffic returns to normal');
  console.log('  6-8 min:  OBSERVATION - Monitoring for issues');
  console.log('');
  
  return {
    baseUrl: TARGET_URL,
    baselineVus: BASELINE_VUS,
    spikeVus: SPIKE_VUS,
    startTime: Date.now(),
  };
}

// =============================================================================
// MAIN TEST FUNCTION
// =============================================================================

export default function(data) {
  const elapsed = (Date.now() - data.startTime) / 1000;
  const phase = getCurrentPhase(elapsed);
  
  // Detect phase transitions
  if (phase !== currentPhase) {
    console.log(`→ Phase transition: ${currentPhase} -> ${phase} (${elapsed}s)`);
    currentPhase = phase;
    
    if (phase === 'spike') {
      spikeStartTime = elapsed;
      console.log(`  ⚡ SPIKE STARTED: Traffic increased to ${data.spikeVus} VUs`);
    } else if (phase === 'recovery' && spikeStartTime) {
      const spikeDuration = elapsed - spikeStartTime;
      console.log(`  ↓ SPIKE ENDED: Duration ${spikeDuration}s`);
    }
  }
  
  // Make API request
  const response = http.get(data.baseUrl, {
    tags: {
      name: 'spike_test_endpoint',
      phase: phase,
    }
  });
  
  // Track metrics based on phase
  const responseTime = response.timings.duration;
  spikeResponseTime.add(responseTime, { phase: phase });
  
  // Check for errors
  const isSuccess = checkStatus(response, 200, 'status_ok');
  
  if (!isSuccess) {
    if (phase === 'spike' || phase === 'sustain') {
      errorDuringSpike.add(1);
      errorsDuringSpike++;
      spikeImpact.add(1);
    }
  }
  
  // Response time checks based on phase expectations
  const maxAcceptableTime = getMaxResponseTime(phase);
  const isWithinThreshold = checkResponseTime(response, maxAcceptableTime, `response_time_${phase}`);
  
  // Log significant events
  if (phase === 'spike' && responseTime > 2000) {
    console.log(`  ⚠️  Slow response during spike: ${responseTime}ms`);
  }
  
  // Recovery detection
  if (phase === 'observation' && responseTime < 1000) {
    recoveryDetected.add(1);
  }
  
  // Minimal sleep to maximize load during spike
  sleep(0.1);
}

// =============================================================================
// TEARDOWN
// =============================================================================

export function teardown(data) {
  console.log('');
  console.log('=== SPIKE TEST COMPLETED ===');
  console.log('');
  console.log('Results Interpretation:');
  console.log('  ✓ PASS: System handled spike and recovered');
  console.log('  ⚠️  WARNING: Some errors during spike, but recovered');
  console.log('  ✗ FAIL: System failed to recover or crashed');
  console.log('');
  console.log('Key Metrics to Review in Grafana:');
  console.log('  - Error rate during spike phase');
  console.log('  - Response time increase during spike');
  console.log('  - Recovery time after spike ends');
  console.log('  - Any errors during observation phase');
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Determines the current test phase based on elapsed time
 * @param {number} elapsedSeconds - Time elapsed since test start
 * @returns {string} Current phase name
 */
function getCurrentPhase(elapsedSeconds) {
  if (elapsedSeconds < 120) return 'baseline';      // 0-2 min
  if (elapsedSeconds < 180) return 'spike';         // 2-3 min
  if (elapsedSeconds < 300) return 'sustain';       // 3-5 min
  if (elapsedSeconds < 360) return 'recovery';      // 5-6 min
  return 'observation';                              // 6-8 min
}

/**
 * Returns maximum acceptable response time based on phase
 * @param {string} phase - Current test phase
 * @returns {number} Maximum acceptable response time in ms
 */
function getMaxResponseTime(phase) {
  switch(phase) {
    case 'baseline':
      return 500;    // 500ms - normal expectation
    case 'spike':
    case 'sustain':
      return 3000;   // 3 seconds - lenient during spike
    case 'recovery':
      return 2000;   // 2 seconds - should be improving
    case 'observation':
      return 1000;   // 1 second - should be back to normal
    default:
      return 1000;
  }
}
