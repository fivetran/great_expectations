import React from 'react';
// Pass-through components that users can swizzle and customize
export default function CodeBlockLineToken({line, token, ...props}) {
  return <span {...props} />;
}
