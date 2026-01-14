import React from 'react';
import clsx from 'clsx';
import {translate} from '@docusaurus/Translate';
import {useCodeBlockContext} from '@docusaurus/theme-common/internal';
import Button from '@theme/CodeBlock/Buttons/Button';
import IconWordWrap from '@theme/Icon/WordWrap';
import styles from './styles.module.css';
export default function WordWrapButton({className}) {
  const {wordWrap} = useCodeBlockContext();
  const canShowButton = wordWrap.isEnabled || wordWrap.isCodeScrollable;
  if (!canShowButton) {
    return false;
  }
  const title = translate({
    id: 'theme.CodeBlock.wordWrapToggle',
    message: 'Toggle word wrap',
    description:
      'The title attribute for toggle word wrapping button of code block lines',
  });
  return (
    <Button
      onClick={() => wordWrap.toggle()}
      className={clsx(
        className,
        wordWrap.isEnabled && styles.wordWrapButtonEnabled,
      )}
      aria-label={title}
      title={title}>
      <IconWordWrap className={styles.wordWrapButtonIcon} aria-hidden="true" />
    </Button>
  );
}
