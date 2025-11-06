/**
 * Common Room Signals.js Integration with SPA Navigation Tracking
 *
 * This script implements a queue-based tracking system that works even if Common Room's
 * signals.js script hasn't loaded yet (e.g., due to CSP or network issues).
 *
 * How it works:
 * 1. Initial state (queue): We create window.signals as an array with methods (page, identify, form)
 *    that push calls into the queue. This allows tracking calls to be made immediately,
 *    even before signals.js loads.
 *
 * 2. After signals.js loads: Common Room's script automatically processes all queued calls
 *    and replaces window.signals with the actual functions that sends data to Common Room's servers.
 *
 * 3. Our tracking code: The trackPageview() function checks if signals.page is a function
 *    (CommonRoom implementation) or uses the queue (array). This ensures tracking works both
 *    before and after signals.js loads.
 *
 * SPA Navigation: We also set up listeners for browser history changes (popstate, pushState,
 * replaceState) to track single-page app navigation, which doesn't trigger full page reloads.
 */
(function () {
  if (typeof window === 'undefined') return
  if (typeof window.signals !== 'undefined') return

  // Initialize signals queue before script loads
  window.signals = Object.assign(
    [],
    ['page', 'identify', 'form'].reduce(function (acc, method) {
      acc[method] = function () {
        signals.push([method, arguments])
        return signals
      }
      return acc
    }, {})
  )

  // Load Common Room signals.js
  const script = document.createElement('script')
  script.src = 'https://cdn.cr-relay.com/v1/site/fa55f78e-0306-4363-88ae-e92ab04d95c6/signals.js'
  script.async = true

  // Track SPA navigation for Common Room
  let currentPath = window.location.pathname
  let spaTrackingSetup = false

  // Function to track pageview
  // According to Common Room docs: signals.page() or signals.page('https://example.com/page')
  function trackPageview() {
    const newPath = window.location.pathname
    if (newPath === currentPath) return // Skip if path hasn't changed

    currentPath = newPath

    // Check if signals.js has loaded and replaced the queue
    if (window.signals && typeof window.signals.page === 'function') {
      try {
        // Call with URL string as per Common Room documentation
        window.signals.page(window.location.href)
      } catch (error) {
        // Silently fail - tracking errors shouldn't break the site
      }
    } else {
      // Queue-based tracking (will be processed when signals.js loads)
      if (window.signals && Array.isArray(window.signals)) {
        try {
          window.signals.page(window.location.href)
        } catch (error) {
          // Silently fail - tracking errors shouldn't break the site
        }
      }
    }
  }

  // Set up SPA tracking immediately (don't wait for script to load)
  // This ensures tracking works even if signals.js fails to load due to CSP
  function setupSPATracking() {
    if (spaTrackingSetup) return
    spaTrackingSetup = true

    // Listen for browser back/forward
    window.addEventListener('popstate', function() {
      setTimeout(trackPageview, 50) // Delay to ensure URL has updated
    })

    // Override pushState and replaceState to catch programmatic navigation
    const originalPushState = history.pushState
    const originalReplaceState = history.replaceState

    history.pushState = function(...args) {
      originalPushState.apply(this, args)
      setTimeout(trackPageview, 50) // Delay to ensure URL has updated
    }

    history.replaceState = function(...args) {
      originalReplaceState.apply(this, args)
      setTimeout(trackPageview, 50) // Delay to ensure URL has updated
    }
  }

  setupSPATracking()

  document.head.appendChild(script)
})()
