import React from 'react';
import clsx from 'clsx';
export default function CodeBlockButton({className, ...props}) {
  return (
    <button type="button" {...props} className={clsx('clean-btn', className)} />
  );
}
