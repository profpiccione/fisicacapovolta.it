import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Metodo capovolto',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Ogni argomento parte da un&apos;attività da fare prima della lezione
        (<strong>Per iniziare</strong>), per arrivare in classe già con le idee
        chiare e usare il tempo insieme per fare, non solo ascoltare.
      </>
    ),
  },
  {
    title: 'Esempi, esercizi, F.A.Q.',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Ogni modulo alterna spiegazione, esempi svolti, domande frequenti ed
        esercizi, con formule, video e simulazioni interattive integrate.
      </>
    ),
  },
  {
    title: 'Progetto aperto',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        I contenuti sono su GitHub: chiunque (docenti, studenti) può proporre
        correzioni e miglioramenti tramite pull request.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
