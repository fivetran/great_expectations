import { useEffect } from 'react';
import { useLocation } from '@docusaurus/router';

export default function NavigationTracker() {
  const location = useLocation();

  useEffect(() => {
    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.capture('$pageview');
    }
  }, [location]);

  return null;
} 