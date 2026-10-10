// The home page: a dated index of every post, newest first, grouped by year.
// Replaces the classic theme's list of full post previews. Post pages are unchanged.
import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {PageMetadata, HtmlClassNameProvider, ThemeClassNames} from '@docusaurus/theme-common';
import Layout from '@theme/Layout';
import SearchMetadata from '@theme/SearchMetadata';
import BlogListPaginator from '@theme/BlogListPaginator';
import BlogListPageStructuredData from '@theme/BlogListPage/StructuredData';
import styles from './styles.module.css';

const dayFormat = new Intl.DateTimeFormat('en-US', {month: 'short', day: 'numeric', timeZone: 'UTC'});

function byYear(items) {
  const posts = items
    .map(({content}) => content.metadata)
    .sort((a, b) => new Date(b.date) - new Date(a.date));
  const years = [];
  for (const post of posts) {
    const year = new Date(post.date).getUTCFullYear();
    if (years.at(-1)?.year !== year) years.push({year, posts: []});
    years.at(-1).posts.push(post);
  }
  return years;
}

export default function BlogListPage(props) {
  const {metadata, items} = props;
  const {siteConfig} = useDocusaurusContext();
  const title = metadata.permalink === '/' ? siteConfig.title : metadata.blogTitle;
  return (
    <HtmlClassNameProvider
      className={clsx(ThemeClassNames.wrapper.blogPages, ThemeClassNames.page.blogListPage)}>
      <PageMetadata title={title} description={metadata.blogDescription} />
      <SearchMetadata tag="blog_posts_list" />
      <BlogListPageStructuredData {...props} />
      <Layout>
        <main className={styles.index}>
          {byYear(items).map(({year, posts}) => (
            <section key={year} className={styles.year}>
              <h2 className={styles.yearLabel}>{year}</h2>
              <ul className={styles.rows}>
                {posts.map((post) => (
                  <li key={post.permalink} className={styles.row}>
                    <time className={styles.date} dateTime={post.date}>
                      {dayFormat.format(new Date(post.date))}
                    </time>
                    <Link to={post.permalink} className={styles.title}>
                      {post.title}
                    </Link>
                    {post.tags.length > 0 && (
                      <span className={styles.tags}>
                        {post.tags.map((tag, i) => (
                          <React.Fragment key={tag.permalink}>
                            {i > 0 && ' · '}
                            <Link to={tag.permalink} className={styles.tag}>
                              {tag.label}
                            </Link>
                          </React.Fragment>
                        ))}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
          <BlogListPaginator metadata={metadata} />
        </main>
      </Layout>
    </HtmlClassNameProvider>
  );
}
