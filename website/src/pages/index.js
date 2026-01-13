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
    title: 'Latent Pattern Recognition',
    description: (
      <>
        Identify hidden correlations between your lifestyle, environment, and migraine
        attacks using advanced non-linear analysis.
      </>
    ),
  },
  {
    title: 'Meteorological Analysis',
    description: (
      <>
        Correlate local weather data—pressure changes, temperature, and humidity—
        with your health metrics for multidimensional risk forecasting.
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

const ScreenshotGallery = [
  { src: 'img/dashboard.png', label: 'Real-time Predictive Dashboard' },
  { src: 'img/log.png', label: 'Streamlined Data Entry' },
  { src: 'img/history.png', label: 'Detailed History Management' },
  { src: 'img/medications.png', label: 'Medication Registry & Tracking' },
  { src: 'img/triggers.png', label: 'Trigger Management' },
  { src: 'img/settings.png', label: 'Customizable Settings' },
];

function Gallery() {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const timeoutRef = React.useRef(null);

  const resetTimeout = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  React.useEffect(() => {
    resetTimeout();
    timeoutRef.current = setTimeout(
      () =>
        setCurrentIndex((prevIndex) =>
          prevIndex === ScreenshotGallery.length - 1 ? 0 : prevIndex + 1
        ),
      4000
    );

    return () => {
      resetTimeout();
    };
  }, [currentIndex]);

  return (
    <div className={styles.galleryContainer}>
      <div className={styles.gallerySlide}>
        <img
          src={useBaseUrl(ScreenshotGallery[currentIndex].src)}
          alt={ScreenshotGallery[currentIndex].label}
          className={styles.dashboardImage}
        />
        <div className={styles.galleryCaption}>
          {ScreenshotGallery[currentIndex].label}
        </div>
      </div>

      <div className={styles.galleryControls}>
        <div className={styles.galleryDots}>
          {ScreenshotGallery.map((_, idx) => (
            <div
              key={idx}
              className={clsx(
                styles.galleryDot,
                currentIndex === idx && styles.galleryDotActive
              )}
              onClick={() => setCurrentIndex(idx)}
            />
          ))}
        </div>
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
      description="Personalized Migraine Analysis">
      <HomepageHeader />
      <main>
        {/* Dashboard Section */}
        <div className={styles.dashboardSection}>
          <div className="container">
            <div className={styles.dashboardContainer}>
              <Gallery />
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