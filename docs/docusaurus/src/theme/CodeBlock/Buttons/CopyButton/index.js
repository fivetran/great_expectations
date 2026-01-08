import React, {useCallback, useState, useRef, useEffect} from 'react';
import clsx from 'clsx';
import {translate} from '@docusaurus/Translate';
import {useCodeBlockContext} from '@docusaurus/theme-common/internal';
import Button from '@theme/CodeBlock/Buttons/Button';
import IconCopy from '@theme/Icon/Copy';
import IconSuccess from '@theme/Icon/Success';
import styles from './styles.module.css';
function title() {
  return translate({
    id: 'theme.CodeBlock.copy',
    message: 'Copy',
    description: 'The copy button label on code blocks',
  });
}
function ariaLabel(isCopied) {
  return isCopied
    ? translate({
        id: 'theme.CodeBlock.copied',
        message: 'Copied',
        description: 'The copied button label on code blocks',
      })
    : translate({
        id: 'theme.CodeBlock.copyButtonAriaLabel',
        message: 'Copy code to clipboard',
        description: 'The ARIA label for copy code blocks button',
      });
}
/**
 * Filters out lines with the 'code-block-hide-line' class from the code block.
 * This respects Prism magic comments that hide lines from display.
 * @param {string} originalCode - Fallback code string if DOM access fails
 * @param {HTMLElement} buttonElement - The button element that triggered the copy
 * @returns {string} - The filtered code with hidden lines removed, or originalCode if filtering fails
 */
function filterHiddenLines(originalCode, buttonElement) {
  // We need DOM access to filter hidden lines. If we can't access the DOM,
  // we fall back to the original code (which may include hidden lines).
  if (!buttonElement) {
    return originalCode;
  }

  // Find the code block container by traversing up the DOM
  // Structure: button -> buttonGroup -> codeBlockContent -> Container -> code block
  const codeBlockContent = buttonElement.closest('[class*="codeBlockContent"]');
  if (!codeBlockContent) {
    return originalCode;
  }

  // Find the <code> element within the code block
  const codeElement = codeBlockContent.querySelector('code');
  if (!codeElement) {
    return originalCode;
  }

  // Clone the code element to avoid modifying the original
  const clonedCode = codeElement.cloneNode(true);

  // Remove all spans with the 'code-block-hide-line' class
  const hiddenLines = clonedCode.querySelectorAll('.code-block-hide-line');
  hiddenLines.forEach((line) => {
    // Remove the line span and its trailing <br> if present
    // Lines are structured as: <span class="...">content</span><br />
    const nextSibling = line.nextSibling;
    if (nextSibling && nextSibling.nodeName === 'BR') {
      nextSibling.remove();
    }
    line.remove();
  });

  // Replace all <br> tags with newlines before extracting text
  // textContent doesn't convert <br> to newlines, so we need to do it manually
  const brElements = clonedCode.querySelectorAll('br');
  brElements.forEach((br) => {
    br.replaceWith('\n');
  });

  // Extract text content from the cleaned clone
  const filteredCode = clonedCode.textContent || clonedCode.innerText;
  return filteredCode || originalCode;
}

function useCopyButton() {
  const {
    metadata: {code},
  } = useCodeBlockContext();
  const [isCopied, setIsCopied] = useState(false);
  const copyTimeout = useRef(undefined);
  const copyCode = useCallback((event) => {
    // Get the button element from the event
    const buttonElement = event?.currentTarget;
    
    // Filter out hidden lines before copying
    const filteredCode = filterHiddenLines(code, buttonElement);
    navigator.clipboard.writeText(filteredCode).then(() => {
      setIsCopied(true);
      copyTimeout.current = window.setTimeout(() => {
        setIsCopied(false);
      }, 1000);
    });
  }, [code]);
  useEffect(() => () => window.clearTimeout(copyTimeout.current), []);
  return {copyCode, isCopied};
}
export default function CopyButton({className}) {
  const {copyCode, isCopied} = useCopyButton();
  return (
    <Button
      aria-label={ariaLabel(isCopied)}
      title={title()}
      className={clsx(
        className,
        styles.copyButton,
        isCopied && styles.copyButtonCopied,
      )}
      onClick={copyCode}>
      <span className={styles.copyButtonIcons} aria-hidden="true">
        <IconCopy className={styles.copyButtonIcon} />
        <IconSuccess className={styles.copyButtonSuccessIcon} />
      </span>
    </Button>
  );
}
