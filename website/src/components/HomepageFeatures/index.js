import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
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
      title={`Home`}
      description="N=1 Migraine Prediction Engine">
      <HomepageHeader />
      <main>
        <div className="container" style={{ padding: '4rem 0', textAlign: 'center' }}>
          <Heading as="h2">Project Dashboard</Heading>
          <p>A local-first predictive analytics engine using biological and meteorological data.</p>
          {/* This pulls the image we already put in your static folder */}
          <img
            src="img/dashboard.png"
            alt="Migraine Navigator Dashboard"
            style={{
              maxWidth: '100%',
              height: 'auto',
              borderRadius: '10px',
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              marginTop: '20px'
            }}
          />
        </div>
      </main>
    </Layout>
  );
}