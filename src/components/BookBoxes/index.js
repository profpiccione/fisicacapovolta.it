import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

function Box({className, titleClassName, title, icon, children}) {
  return (
    <div className={clsx(styles.box, className)}>
      {title && (
        <div className={clsx(styles.boxTitle, titleClassName)}>
          {icon && <span aria-hidden="true">{icon}</span>}
          <span>{title}</span>
        </div>
      )}
      <div>{children}</div>
    </div>
  );
}

export function PerIniziare({children}) {
  return (
    <Box className={styles.perIniziare} icon="🚀" title="Per iniziare">
      {children}
    </Box>
  );
}

export function PerRiassumere({children}) {
  return (
    <Box className={styles.perRiassumere} icon="📌" title="Per riassumere">
      {children}
    </Box>
  );
}

export function Esempio({children}) {
  return (
    <Box className={styles.esempio} icon="✏️" title="Esempio">
      {children}
    </Box>
  );
}

export function FAQ({children}) {
  return (
    <Box className={styles.faq} icon="❓" title="F.A.Q.">
      {children}
    </Box>
  );
}

export function Esercizi({children}) {
  return (
    <Box className={styles.esercizi} icon="📝" title="Esercizi">
      {children}
    </Box>
  );
}

export function ModelloRiferimento({children}) {
  return (
    <Box className={styles.modelloRiferimento} title="Il modello di riferimento">
      {children}
    </Box>
  );
}

export function Video({id, title}) {
  if (!id) return null;
  return (
    <div className={styles.videoWrapper}>
      <iframe
        src={`https://www.youtube.com/embed/${id}`}
        title={title || 'Video'}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
}
