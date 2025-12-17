import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

// NUCLEAR OPTION: Import the image directly. 
// This forces Webpack to bundle it. No more broken paths.
import DashboardImg from '@site/static/img/dashboard.png';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className={styles.heroTitle}>
          {siteConfig.title}
        </Heading>
        <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/architecture">
            View Architecture
          </Link>
          <span style={{ margin: '0 10px' }}></span>
          <Link
            className="button button--secondary button--lg"
            to="/blog">
            Read "Perfect Storm" Study
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title="Home"
      description="N=1 Migraine Prediction Engine">
      <HomepageHeader />
      <main>
        <div className={styles.dashboardSection}>
          <div className={styles.dashboardContainer}>
            {/* using the imported variable 'DashboardImg' ensures it loads */}
            <img
              src={DashboardImg}
              alt="Migraine Navigator Dashboard"
              className={styles.dashboardImage}
            />
          </div>

          <div className={styles.descSection}>
            <Heading as="h2">Biological & Meteorological Intelligence</Heading>
            <p>
              A local-first predictive engine that correlates
              weather patterns with personal biomarkers to forecast risk.
            </p>
          </div>
        </div>
      </main>
    </Layout>
  );
}