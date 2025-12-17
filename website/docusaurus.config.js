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

  // THIS IS THE CRITICAL FIX:
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

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
          src: 'img/favicon.ico',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'System Overview', // Fixed label
          },
          { to: '/blog', label: 'Perfect Storm Study', position: 'left' }, // Fixed label
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