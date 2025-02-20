import React from 'react';
import Admonition from '@theme-original/Admonition';
import AlertInfo from "../../../static/img/alert-info.svg";
import AlertWarning from "../../../static/img/alert-warning.svg";
import CautionIcon from "../../../static/img/admonition-caution-icon.svg"
import AlertBell from "../../../static/img/alert-bell.svg";
import AlertPin from "../../../static/img/alert-pin.svg";
import DangerIcon from "../../../static/img/admonition-danger-icon.svg"
import CtaIcon from "../../../static/img/admonition-cta-icon.svg"

export default function AdmonitionWrapper(props) {

  switch(props.type) {
    case 'info':
      return <Admonition {...props} icon={<AlertBell/>} />;
    case 'note':
      return <Admonition {...props} icon={<AlertPin/>} />;
    case 'tip':
      return <Admonition {...props} icon={<AlertInfo/>} />;
    case 'caution':
      return <Admonition {...props} icon={<CautionIcon/>} />;
    case 'warning':
      return <Admonition {...props} icon={<AlertWarning/>} />;
    case 'danger':
      return <Admonition {...props} icon={<DangerIcon/>} />;
    case 'cta':
      if (props.icon == null) {
        // Display default CtaIcon if no other icon is supplied.
        return <Admonition {...props} icon={<CtaIcon/>} />;
      } else {
        // Enable calling admonition to specify a custom icon.
        return <Admonition {...props} icon={props.icon} />;
      }
    default:
      return <Admonition {...props} />
  }
}
