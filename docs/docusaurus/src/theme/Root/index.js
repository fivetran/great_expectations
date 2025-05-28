import React from 'react'
import BrowserOnly from '@docusaurus/BrowserOnly'
import NavigationTracker from '../../components/NavigationTracker'

export default function Root ({ children }) {
  return (
    <>
      {children}
      <BrowserOnly>
        {() => <NavigationTracker />}
      </BrowserOnly>
    </>
  )
}
