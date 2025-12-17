import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl'; // <--- The Fix for broken images
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className={styles.hero__title}>
          {siteConfig.title}
        </Heading>
        <p className={styles.hero__subtitle}>{siteConfig.tagline}</p>
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
        <div className="container" style={{ padding: '0 1rem 4rem', textAlign: 'center' }}>

          {/* The Image Container with the new CSS class */}
          <div className="dashboard-container">
            <img
              src={useBaseUrl('/img/dashboard.png')} // <--- Forces correct path
              alt="Migraine Navigator Dashboard"
              style={{ width: '100%', borderRadius: '8px', display: 'block' }}
            />
          </div>

          <div style={{ marginTop: '3rem', maxWidth: '800px', margin: '3rem auto' }}>
            <Heading as="h2">Biological & Meteorological Intelligence</Heading>
            <p style={{ fontSize: '1.2rem', opacity: 0.8 }}>
              A local-first predictive engine that correlates
              weather patterns with personal biomarkers to forecast risk.
            </p>
          </div>
        </div>
      </main>
    </Layout>
  );
}