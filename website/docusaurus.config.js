// @ts-check
import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Migraine Navigator',
  tagline: 'Track, Analyze, and Predict',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://aretaj.github.io',
  baseUrl: '/Migraine-Navigator/',

  // GitHub pages deployment config.
  organizationName: 'AreTaj',
  projectName: 'Migraine-Navigator',

  // FIX 1: Removed deprecated 'onBrokenMarkdownLinks' to stop the warning
  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
        },
        blog: {
          showReadingTime: true,
          // FIX 2: Tell Docusaurus it's okay to define authors inside the file
          onInlineAuthors: 'ignore',
          onUntruncatedBlogPosts: 'ignore',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/dashboard.png',
      navbar: {
        title: 'Migraine Navigator',
        logo: {
          alt: 'Migraine Navigator Logo',
          src: 'img/logo.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'System Overview',
          },
          {
            type: 'doc',
            docId: 'patients',
            position: 'left',
            label: 'For Patients',
          },
          {
            type: 'doc',
            docId: 'practitioners',
            position: 'left',
            label: 'For Practitioners',
          },
          {
            type: 'doc',
            docId: 'researchers',
            position: 'left',
            label: 'For Researchers',
          },
          { to: '/blog', label: 'Perfect Storm Study', position: 'left' },
          {
            href: 'https://github.com/AreTaj/Migraine-Navigator',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'System Overview',
                to: '/docs/architecture',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Perfect Storm Analysis',
                to: '/blog',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/AreTaj/Migraine-Navigator',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Aresh Tajvar. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;

// Force rebuild