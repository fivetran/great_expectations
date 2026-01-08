jest.mock('@docusaurus/useBaseUrl', () =>
  jest.fn(() => {
    const originalModule = jest.requireActual('@docusaurus/useBaseUrl')
    return {
      ...originalModule,
      useBaseUrl: (url) => url
    }
  })
)

// Suppress ReactDOMTestUtils.act deprecation warning from @testing-library/react
// This is a known issue with React Testing Library's internal usage
// We're already using React.act correctly in our tests
const originalError = console.error
console.error = (...args) => {
  const message = args[0]
  if (
    (typeof message === 'string' &&
      (message.includes('ReactDOMTestUtils.act is deprecated') ||
       message.includes('The current testing environment is not configured to support act'))) ||
    (args.length > 0 && typeof args[args.length - 1] === 'string' &&
      args[args.length - 1].includes('react-dom/test-utils'))
  ) {
    return
  }
  originalError.call(console, ...args)
}
