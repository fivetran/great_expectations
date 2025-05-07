import { useEffect } from 'react'
import { useLocation } from '@docusaurus/router'

const logDebug = (...args) => {
  if (process.env.NODE_ENV === 'development') {
    console.debug('[NavTracker Debug]', ...args)
  }
}

export default function NavigationTracker () {
  const location = useLocation()

  useEffect(() => {
    if (typeof window === 'undefined') return

    if (window.posthog) {
      try {
        window.posthog.capture('$pageview')
        logDebug('PostHog $pageview captured (via window.posthog)')
      } catch (error) {
        console.error('[NavigationTracker] Failed to capture pageview via window.posthog:', error)
      }
    } else {
      logDebug('window.posthog not found on location change. Pageview not captured.')
    }

    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.capture('$pageview')
    }
  }, [location])

  return null
}
