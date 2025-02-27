import React from 'react';
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from './styles.module.css';

export default  function BetaBadge(){
    const betaIcon = useBaseUrl(`img/beta.svg`);

    return <img src={betaIcon} alt="Beta badge" className={styles.betaIcon} />
}