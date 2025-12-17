import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

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
            className={styles.goldButton}
            to="/docs/architecture">
            View Architecture
          </Link>
          <Link
            className={styles.goldButton}
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
            {/* Using Raw GitHub URL to guarantee image loads */}
            <img
              src="https://raw.githubusercontent.com/AreTaj/Migraine-Navigator/main/screenshots/dashboard.png"
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