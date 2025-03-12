import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import isInternalUrl from '@docusaurus/isInternalUrl';
import {translate} from '@docusaurus/Translate';
import styles from './styles.module.css';
import useBaseUrl from '@docusaurus/useBaseUrl';

function CardContainer({href, children}) {
  return (
    <Link
      href={href}
      className={clsx('card padding--lg', styles.cardContainer)}>
      {children}
    </Link>
  );
}

function CardLayout({item, href, icon, title, description}) {
  return (
    <CardContainer href={href}>
      <h2 className={clsx('text--truncate', styles.cardTitle)} title={title}>
        {icon}&nbsp;{title}
      </h2>
      {description && (
        <p
          className={clsx('text--truncate', styles.cardDescription)}
          title={description}>
          {description}
        </p>
      )}
    </CardContainer>
  );
}

function findFirstLink(item) {
  if (item.href) {
    return item.href;
  }
  if (item.items?.length) {
    for (const subItem of item.items) {
      const link = findFirstLink(subItem);
      if (link) {
        return link;
      }
    }
  }
  return null;
}

function CardCategory({item}) {
  const href = findFirstLink(item);
  // Unexpected: categories that don't have a link have been filtered upfront
  if (!href) {
    return null;
  }
  return (
    <CardLayout
      href={href}
      icon={<img src={useBaseUrl(`img/groupicon.svg`)} alt="icon" />}
      title={item.label}
      description={translate(
        {
          message: '{count} items',
          id: 'theme.docs.DocCard.categoryDescription',
          description:
            'The default description for a category card in the generated index about how many items this category includes',
        },
        {count: item.items.length},
      )}
    />
  );
}

function CardLink({item}) {
  const icon = isInternalUrl(item.href) ? 
    <img src={useBaseUrl(`img/integrations/page_icon.svg`)} alt="icon" /> : 
    '🔗';
  return (
    <CardLayout
      href={item.href}
      icon={item?.customProps?.icon ? 
        <img src={useBaseUrl(item.customProps.icon)} alt="icon" /> : 
        icon}
      title={item.label}
    />
  );
}

export default function DocCard({item}) {
  switch (item.type) {
    case 'link':
      return <CardLink item={item} />;
    case 'category':
      return <CardCategory item={item} />;
    default:
      throw new Error(`unknown item type ${JSON.stringify(item)}`);
  }
}