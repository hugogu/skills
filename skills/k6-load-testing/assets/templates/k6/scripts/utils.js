/**
 * k6 Test Utilities
 * 
 * Shared utility functions for k6 load testing scripts.
 * Includes authentication helpers, response validation, and common patterns.
 */

import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

/**
 * Creates authentication headers for Bearer token authentication
 * @param {string} token - The Bearer token
 * @returns {Object} Headers object with Authorization header
 * @example
 * const headers = bearerAuth('my-api-token');
 * http.get(url, { headers });
 */
export function bearerAuth(token) {
  return {
    'Authorization': `Bearer ${token}`
  };
}

/**
 * Creates authentication headers for Basic authentication
 * @param {string} username - The username
 * @param {string} password - The password
 * @returns {Object} Headers object with Authorization header
 * @example
 * const headers = basicAuth('user', 'pass');
 * http.get(url, { headers });
 */
export function basicAuth(username, password) {
  const credentials = `${username}:${password}`;
  const encoded = encoding.b64encode(credentials);
  return {
    'Authorization': `Basic ${encoded}`
  };
}

/**
 * Creates headers for API key authentication
 * @param {string} apiKey - The API key
 * @param {string} [headerName='X-API-Key'] - The header name (default: X-API-Key)
 * @returns {Object} Headers object with API key header
 * @example
 * const headers = apiKeyAuth('my-api-key');
 * http.get(url, { headers });
 * 
 * // Custom header name
 * const headers = apiKeyAuth('my-key', 'Authorization');
 */
export function apiKeyAuth(apiKey, headerName = 'X-API-Key') {
  return {
    [headerName]: apiKey
  };
}

/**
 * Validates HTTP response status code
 * @param {Object} response - k6 HTTP response object
 * @param {number|number[]} expectedStatus - Expected status code(s)
 * @param {string} [tag] - Optional tag for the check
 * @returns {boolean} True if status matches
 * @example
 * checkStatus(response, 200);
 * checkStatus(response, [200, 201]);
 * checkStatus(response, 200, 'login_status');
 */
export function checkStatus(response, expectedStatus, tag = 'status') {
  return check(response, {
    [`${tag} is ${expectedStatus}`]: (r) => {
      if (Array.isArray(expectedStatus)) {
        return expectedStatus.includes(r.status);
      }
      return r.status === expectedStatus;
    }
  });
}

/**
 * Validates response body contains expected content
 * @param {Object} response - k6 HTTP response object
 * @param {string} expectedContent - String to search for in response body
 * @param {string} [tag] - Optional tag for the check
 * @returns {boolean} True if content found
 * @example
 * checkBody(response, 'Welcome');
 * checkBody(response, 'user_id', 'response_has_user_id');
 */
export function checkBody(response, expectedContent, tag = 'body_contains') {
  return check(response, {
    [`${tag}`]: (r) => r.body.includes(expectedContent)
  });
}

/**
 * Validates response body as JSON and checks for property
 * @param {Object} response - k6 HTTP response object
 * @param {string} propertyPath - Dot-notation path to property (e.g., 'data.user.id')
 * @param {*} [expectedValue] - Optional expected value
 * @param {string} [tag] - Optional tag for the check
 * @returns {boolean} True if JSON is valid and property exists (and matches if expectedValue provided)
 * @example
 * checkJsonProperty(response, 'success');
 * checkJsonProperty(response, 'data.id', 123);
 * checkJsonProperty(response, 'status', 'active', 'user_status');
 */
export function checkJsonProperty(response, propertyPath, expectedValue, tag = 'json_property') {
  return check(response, {
    [`${tag}_${propertyPath}`]: (r) => {
      try {
        const json = JSON.parse(r.body);
        const value = propertyPath.split('.').reduce((obj, key) => obj && obj[key], json);
        
        if (expectedValue === undefined) {
          return value !== undefined;
        }
        return value === expectedValue;
      } catch (e) {
        return false;
      }
    }
  });
}

/**
 * Validates response time is within acceptable threshold
 * @param {Object} response - k6 HTTP response object
 * @param {number} maxDuration - Maximum acceptable duration in milliseconds
 * @param {string} [tag] - Optional tag for the check
 * @returns {boolean} True if response time is within threshold
 * @example
 * checkResponseTime(response, 500);
 * checkResponseTime(response, 200, 'api_response_time');
 */
export function checkResponseTime(response, maxDuration, tag = 'response_time') {
  return check(response, {
    [`${tag} under ${maxDuration}ms`]: (r) => r.timings.duration <= maxDuration
  });
}

/**
 * Combines multiple checks into a single validation
 * @param {Object} response - k6 HTTP response object
 * @param {Object} checks - Object containing check configurations
 * @returns {boolean} True if all checks pass
 * @example
 * validateResponse(response, {
 *   status: 200,
 *   bodyContains: 'success',
 *   maxDuration: 500,
 *   jsonProperty: { path: 'data.id', value: 123 }
 * });
 */
export function validateResponse(response, checks) {
  const results = {};
  
  if (checks.status !== undefined) {
    results.status_check = checkStatus(response, checks.status);
  }
  
  if (checks.bodyContains !== undefined) {
    results.body_check = checkBody(response, checks.bodyContains);
  }
  
  if (checks.maxDuration !== undefined) {
    results.duration_check = checkResponseTime(response, checks.maxDuration);
  }
  
  if (checks.jsonProperty !== undefined) {
    const { path, value } = checks.jsonProperty;
    results.json_check = checkJsonProperty(response, path, value);
  }
  
  return Object.values(results).every(r => r === true);
}

/**
 * Creates common headers for JSON API requests
 * @param {Object} [additionalHeaders] - Additional headers to merge
 * @returns {Object} Headers object with Content-Type and Accept
 * @example
 * const headers = jsonHeaders();
 * const headersWithAuth = jsonHeaders(bearerAuth(token));
 */
export function jsonHeaders(additionalHeaders = {}) {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...additionalHeaders
  };
}

/**
 * Parses URL query parameters into an object
 * @param {string} url - URL string
 * @returns {Object} Object containing query parameters
 * @example
 * const params = parseQueryParams('http://api.com?user=123&active=true');
 * // Returns: { user: '123', active: 'true' }
 */
export function parseQueryParams(url) {
  const queryString = url.split('?')[1];
  if (!queryString) return {};
  
  return queryString
    .split('&')
    .reduce((params, param) => {
      const [key, value] = param.split('=');
      params[decodeURIComponent(key)] = decodeURIComponent(value || '');
      return params;
    }, {});
}

/**
 * Generates a random string of specified length
 * @param {number} length - Length of the string
 * @returns {string} Random alphanumeric string
 * @example
 * const randomId = randomString(10);
 */
export function randomString(length) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * Formats bytes to human-readable format
 * @param {number} bytes - Number of bytes
 * @param {number} [decimals=2] - Number of decimal places
 * @returns {string} Human-readable string (e.g., "1.5 MB")
 * @example
 * formatBytes(1536); // Returns: "1.5 KB"
 * formatBytes(1048576, 0); // Returns: "1 MB"
 */
export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Sleep for a random duration within a range
 * @param {number} min - Minimum duration in seconds
 * @param {number} max - Maximum duration in seconds
 * @example
 * randomSleep(1, 3); // Sleep between 1-3 seconds
 */
export function randomSleep(min, max) {
  const duration = Math.random() * (max - min) + min;
  sleep(duration);
}

// Import sleep at the end to avoid circular dependencies in some k6 versions
import { sleep } from 'k6';
import encoding from 'k6/encoding';
