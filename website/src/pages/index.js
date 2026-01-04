import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

const FeatureList = [
  {
    title: 'Biological Intelligence',
    description: (
      <>
        Track your personal biomarkers and patterns to understand your unique
        migraine triggers using advanced analytics.
      </>
    ),
  },
  {
    title: 'Meteorological Analysis',
    description: (
      <>
        Correlate local weather data—pressure changes, temperature, and humidity—
        with your health metrics for precise risk forecasting.
      </>
    ),
  },
  {
    title: 'Privacy First',
    description: (
      <>
        Your health data stays on your device. Migraine Navigator is a local-first
        application that respects your privacy.
      </>
    ),
  },
];

function Feature({ title, description }) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

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
            System Overview
          </Link>
          <Link
            className="button button--primary button--lg"
            to="/blog">
            "Perfect Storm" Study
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
        {/* Dashboard Section */}
        <div className={styles.dashboardSection}>
          <div className="container">
            <div className={styles.dashboardContainer}>
              <img
                src={useBaseUrl('img/dashboard.png')}
                alt="Migraine Navigator Dashboard"
                className={styles.dashboardImage}
              />
            </div>
          </div>
        </div>

        {/* Features Section */}
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}