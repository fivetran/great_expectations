import * as React from 'react'
import { act } from 'react'
import { test, describe, jest, beforeEach, afterEach } from '@jest/globals'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import CopyButton from '../src/theme/CodeBlock/Buttons/CopyButton'

// Mock the dependencies
jest.mock('@docusaurus/theme-common/internal', () => ({
  useCodeBlockContext: jest.fn()
}))

jest.mock('@docusaurus/Translate', () => ({
  translate: jest.fn(({ message }) => message)
}))

jest.mock('@theme/CodeBlock/Buttons/Button', () => {
  return function MockButton ({ children, onClick, ...props }) {
    return (
      <button onClick={onClick} {...props}>
        {children}
      </button>
    )
  }
})

jest.mock('@theme/Icon/Copy', () => {
  return function MockIconCopy () {
    return <svg data-testid="icon-copy" />
  }
})

jest.mock('@theme/Icon/Success', () => {
  return function MockIconSuccess () {
    return <svg data-testid="icon-success" />
  }
})

// Import the mocked hook
import { useCodeBlockContext } from '@docusaurus/theme-common/internal'

describe('CodeBlock CopyButton', () => {
  let mockWriteText
  let clipboardData

  beforeEach(() => {
    clipboardData = ''
    mockWriteText = jest.fn((text) => {
      clipboardData = text
      return Promise.resolve()
    })
    global.navigator.clipboard = {
      writeText: mockWriteText
    }
  })

  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
    clipboardData = ''
    document.body.innerHTML = ''
  })

  const createCodeBlockDOM = (hasHiddenLines = false) => {
    // Create the full DOM structure
    const container = document.createElement('div')
    container.className = 'codeBlockContent'
    
    const codeElement = document.createElement('code')
    
    if (hasHiddenLines) {
      // Create visible line
      const visibleLine = document.createElement('span')
      visibleLine.className = 'token-line'
      visibleLine.textContent = 'import great_expectations as gx'
      codeElement.appendChild(visibleLine)
      codeElement.appendChild(document.createElement('br'))
      
      // Create hidden line
      const hiddenLine = document.createElement('span')
      hiddenLine.className = 'code-block-hide-line token-line'
      hiddenLine.textContent = 'set_up_context_for_example(context)'
      codeElement.appendChild(hiddenLine)
      codeElement.appendChild(document.createElement('br'))
      
      // Create another visible line
      const visibleLine2 = document.createElement('span')
      visibleLine2.className = 'token-line'
      visibleLine2.textContent = 'preset_expectation = gx.expectations.ExpectColumnMaxToBeBetween('
      codeElement.appendChild(visibleLine2)
    } else {
      // Simple code block without hidden lines
      const line1 = document.createElement('span')
      line1.className = 'token-line'
      line1.textContent = 'import great_expectations as gx'
      codeElement.appendChild(line1)
      codeElement.appendChild(document.createElement('br'))
      
      const line2 = document.createElement('span')
      line2.className = 'token-line'
      line2.textContent = 'context = gx.get_context()'
      codeElement.appendChild(line2)
    }
    
    container.appendChild(codeElement)
    
    // Create button group container
    const buttonGroup = document.createElement('div')
    buttonGroup.className = 'buttonGroup'
    container.appendChild(buttonGroup)
    
    document.body.appendChild(container)
    
    return { container, buttonGroup }
  }

  test('renders copy button', () => {
    useCodeBlockContext.mockReturnValue({
      metadata: { code: 'test code' }
    })

    render(<CopyButton />)
    
    const button = screen.getByRole('button', { name: /copy code to clipboard/i })
    expect(button).toBeInTheDocument()
  })

  test('copies code to clipboard when clicked', async () => {
    const testCode = 'import great_expectations as gx\ncontext = gx.get_context()'
    useCodeBlockContext.mockReturnValue({
      metadata: { code: testCode }
    })

    const { container, buttonGroup } = createCodeBlockDOM(false)
    
    // Render the button into the buttonGroup
    const { container: renderContainer } = render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    await userEvent.click(copyButton)
    
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalled()
    })
  })

  test('filters out hidden lines when copying', async () => {
    const originalCode = 'import great_expectations as gx\nset_up_context_for_example(context)\npreset_expectation = gx.expectations.ExpectColumnMaxToBeBetween('
    
    useCodeBlockContext.mockReturnValue({
      metadata: { code: originalCode }
    })

    const { container, buttonGroup } = createCodeBlockDOM(true)
    
    // Render the button into the buttonGroup
    render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    await userEvent.click(copyButton)
    
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalled()
      const copiedText = mockWriteText.mock.calls[0][0]
      // Should not contain the hidden line
      expect(copiedText).not.toContain('set_up_context_for_example')
      // Should contain visible lines
      expect(copiedText).toContain('import great_expectations as gx')
      expect(copiedText).toContain('preset_expectation')
    })
  })

  test('preserves line breaks when copying', async () => {
    const testCode = 'line1\nline2\nline3'
    useCodeBlockContext.mockReturnValue({
      metadata: { code: testCode }
    })

    const { container, buttonGroup } = createCodeBlockDOM(false)
    
    // Render the button into the buttonGroup
    render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    await userEvent.click(copyButton)
    
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalled()
      const copiedText = mockWriteText.mock.calls[0][0]
      // Should contain newlines
      expect(copiedText).toContain('\n')
      // Should have multiple lines
      const lines = copiedText.split('\n')
      expect(lines.length).toBeGreaterThan(1)
    })
  })

  test('falls back to original code if DOM structure is not found', async () => {
    const testCode = 'import great_expectations as gx\nset_up_context_for_example(context)'
    useCodeBlockContext.mockReturnValue({
      metadata: { code: testCode }
    })

    render(<CopyButton />)
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    // Click without setting up DOM structure - should fall back to original code
    await userEvent.click(copyButton)
    
    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalled()
      // Should fall back to original code (may include hidden lines)
      const copiedText = mockWriteText.mock.calls[0][0]
      expect(copiedText).toBe(testCode)
    })
  })

  test('shows copied state after clicking', async () => {
    useCodeBlockContext.mockReturnValue({
      metadata: { code: 'test code' }
    })

    const { container, buttonGroup } = createCodeBlockDOM(false)
    
    // Render the button into the buttonGroup
    render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    await userEvent.click(copyButton)
    
    await waitFor(() => {
      // Should show "Copied" aria-label after clicking
      expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument()
    })
  })

  test('resets copied state after timeout', async () => {
    jest.useFakeTimers()
    
    useCodeBlockContext.mockReturnValue({
      metadata: { code: 'test code' }
    })

    const { container, buttonGroup } = createCodeBlockDOM(false)
    
    // Render the button into the buttonGroup
    render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    // Click with fake timers - wrap in act
    await act(async () => {
      await userEvent.click(copyButton, { delay: null })
    })
    
    // Wait for copied state to appear - wrap in act
    await act(async () => {
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument()
      })
    })
    
    // Fast-forward time by 1000ms - wrap in act
    act(() => {
      jest.advanceTimersByTime(1000)
    })
    
    // Wait for state to reset - wrap in act
    await act(async () => {
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy code to clipboard/i })).toBeInTheDocument()
      })
    })
    
    jest.useRealTimers()
  })

  test('handles multiple hidden lines correctly', async () => {
    const originalCode = 'line1\nhidden1\nline2\nhidden2\nline3'
    
    useCodeBlockContext.mockReturnValue({
      metadata: { code: originalCode }
    })

    const container = document.createElement('div')
    container.className = 'codeBlockContent'
    const codeElement = document.createElement('code')
    
    // Create multiple lines with hidden ones
    const lines = [
      { text: 'line1', hidden: false },
      { text: 'hidden1', hidden: true },
      { text: 'line2', hidden: false },
      { text: 'hidden2', hidden: true },
      { text: 'line3', hidden: false }
    ]
    
    lines.forEach(({ text, hidden }) => {
      const span = document.createElement('span')
      span.className = hidden ? 'code-block-hide-line token-line' : 'token-line'
      span.textContent = text
      codeElement.appendChild(span)
      codeElement.appendChild(document.createElement('br'))
    })
    
    container.appendChild(codeElement)
    
    // Create button group container
    const buttonGroup = document.createElement('div')
    buttonGroup.className = 'buttonGroup'
    container.appendChild(buttonGroup)
    
    document.body.appendChild(container)
    
    // Render the button into the buttonGroup
    render(<CopyButton />, {
      container: buttonGroup
    })
    
    const copyButton = screen.getByRole('button', { name: /copy code to clipboard/i })
    
    await userEvent.click(copyButton)
    
    await waitFor(
      () => {
        expect(mockWriteText).toHaveBeenCalled()
        const copiedText = mockWriteText.mock.calls[0][0]
        // Should not contain hidden lines
        expect(copiedText).not.toContain('hidden1')
        expect(copiedText).not.toContain('hidden2')
        // Should contain visible lines
        expect(copiedText).toContain('line1')
        expect(copiedText).toContain('line2')
        expect(copiedText).toContain('line3')
      },
      { timeout: 3000 }
    )
  })
})

