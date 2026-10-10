// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';
import {createRequire} from 'node:module';
import {readdirSync} from 'node:fs';

// site.json is the single place that holds the site address.
// tools/convert.py reads the same file to build posts.json and llms.txt.
const site = createRequire(import.meta.url)('./site.json');

// The tag and archive pages only exist once there is at least one post.
const hasPosts = readdirSync('./blog').some((f) => f.endsWith('.md'));

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: site.title,
  tagline: site.tagline,
  url: site.url,
  baseUrl: site.baseUrl,
  trailingSlash: true,
  onBrokenLinks: 'throw',
  future: {v4: true},
  i18n: {defaultLocale: 'en', locales: ['en']},

  // Posts are plain Markdown exported from Claude Docs, so parse .md as
  // CommonMark instead of MDX. Braces and angle brackets then need no escaping.
  markdown: {format: 'detect'},

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: false,
        blog: {
          routeBasePath: '/',
          blogTitle: site.title,
          blogDescription: site.tagline,
          blogSidebarTitle: 'Posts',
          blogSidebarCount: 'ALL',
          // The home page is a one-line-per-post index, so it lists every post on one page.
          postsPerPage: 'ALL',
          showReadingTime: true,
          feedOptions: {type: ['rss', 'atom'], xslt: true},
          onInlineTags: 'ignore',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {customCss: './src/css/custom.css'},
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {respectPrefersColorScheme: true},
      navbar: {
        title: site.title,
        items: [
          ...(hasPosts
            ? [
                {to: '/tags', label: 'Tags', position: 'left'},
                {to: '/archive', label: 'Archive', position: 'left'},
              ]
            : []),
          {href: `${site.url}${site.baseUrl}rss.xml`, label: 'RSS', position: 'right'},
          {href: site.repo, label: 'GitHub', position: 'right'},
        ],
      },
      footer: {
        style: 'light',
        copyright: `© ${new Date().getFullYear()} Sam Dengler. Written in Claude Docs, built with Docusaurus.`,
      },
      prism: {theme: prismThemes.github, darkTheme: prismThemes.dracula},
    }),
};

export default config;
