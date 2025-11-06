/**
 * Common Room Signals.js Integration with SPA Navigation Tracking
 *
 * How it works:
 * 1. Initial state (queue): We create window.signals as an array with methods (page, identify, form)
 *    that push calls into the queue. This allows tracking calls to be made immediately,
 *    even before signals.js loads.
 *
 * 2. After signals.js loads: Common Room's script automatically processes all queued calls
 *    and sends data to Common Room's servers.
 *
 * 3. SPA tracking code: The trackPageview() queues up SPA page events in the signals queue
 *
 * SPA Navigation: Set up listeners for browser history changes (popstate, pushState,
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

  // Debug logging for preview/production environments
  const DEBUG = window.location.hostname.includes('preview') || window.location.hostname.includes('localhost')

  if (DEBUG) {
    console.log('[Common Room] Initializing signals queue')
    console.log('[Common Room] Script URL:', script.src)
  }

  // Track SPA navigation for Common Room
  let currentPath = window.location.pathname
  let spaTrackingSetup = false

  function trackPageview() {
    const newPath = window.location.pathname
    if (newPath === currentPath) return // Skip if path hasn't changed

    currentPath = newPath

    if (window.signals && window.signals.page) {
      window.signals.page(window.location.href)
      if (DEBUG) {
        const queueLength = Array.isArray(window.signals) ? window.signals.length : 'N/A (real implementation)'
        console.log('[Common Room] Pageview queued:', newPath, '| Queue length:', queueLength)
      }
    }
  }

  // Set up SPA tracking immediately (don't wait for script to load)
  // This ensures tracking works even before signals.js has loaded.
  function setupSPATracking() {
    if (spaTrackingSetup) return
    spaTrackingSetup = true

    // Listen for browser back/forward
    window.addEventListener('popstate', function() {
      setTimeout(trackPageview, 50) // Delay to ensure URL has updated
    })

    // Override pushState and replaceState to catch navigation events
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

  // Track initial pageview
  if (window.signals && window.signals.page) {
    window.signals.page(window.location.href)
    if (DEBUG) {
      console.log('[Common Room] Initial pageview queued:', window.location.pathname)
    }
  }

  // Monitor script loading and queue processing
  script.onload = function() {
    if (DEBUG) {
      console.log('[Common Room] signals.js script loaded successfully')
      // Check if queue was processed after a short delay
      setTimeout(function() {
        const isQueue = Array.isArray(window.signals)
        const queueLength = isQueue ? window.signals.length : 'N/A'
        const hasRealImpl = !isQueue && typeof window.signals.page === 'function'
        console.log('[Common Room] After script load:', {
          isQueue: isQueue,
          queueLength: queueLength,
          hasRealImplementation: hasRealImpl,
          signalsType: typeof window.signals
        })
      }, 500)
    }
  }

  script.onerror = function(event) {
    if (DEBUG) {
      console.error('[Common Room] Failed to load signals.js script', {
        src: script.src,
        error: event,
        readyState: script.readyState
      })
      // Check network accessibility
      fetch(script.src, { method: 'HEAD', mode: 'no-cors' })
        .then(() => console.log('[Common Room] Script URL is accessible (HEAD request succeeded)'))
        .catch(err => console.error('[Common Room] Script URL check failed:', err))
    }
  }

  // Periodic monitoring of queue state (for debugging)
  if (DEBUG) {
    let checkCount = 0
    const queueMonitor = setInterval(function() {
      checkCount++
      const isQueue = Array.isArray(window.signals)
      const queueLength = isQueue ? window.signals.length : 'N/A'
      const hasRealImpl = !isQueue && typeof window.signals.page === 'function'

      if (checkCount <= 10) { // Log first 10 checks (10 seconds)
        console.log('[Common Room] Queue monitor (check #' + checkCount + '):', {
          isQueue: isQueue,
          queueLength: queueLength,
          hasRealImplementation: hasRealImpl
        })
      }

      // Stop monitoring if queue was processed or after 30 seconds
      if (!isQueue || checkCount >= 30) {
        clearInterval(queueMonitor)
        if (!isQueue) {
          console.log('[Common Room] Queue processed! Monitoring stopped.')
        } else {
          console.warn('[Common Room] Queue still not processed after 30 seconds. Monitoring stopped.')
        }
      }
    }, 1000)
  }

  document.head.appendChild(script)
  if (DEBUG) {
    console.log('[Common Room] Script element added to document.head')
  }
})()
