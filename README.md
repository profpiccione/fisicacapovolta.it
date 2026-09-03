# Fisica capovolta

Sito del libro di fisica **"Fisica capovolta"** di Andrea Piccione — un
testo pensato per il primo biennio degli istituti professionali secondo il
metodo della classe capovolta (*flipped classroom*), open e collaborativo.

Il sito è generato con [Docusaurus](https://docusaurus.io/): i contenuti
sono file Markdown/MDX versionati in questo repository, e chiunque può
proporre correzioni o miglioramenti tramite pull request.

## Struttura dei contenuti

```
docs/
├── intro/                        # Presentazione, download
└── moduli/
    ├── 00-premesse-matematiche/  # Notazione scientifica, grafici
    ├── 01-le-basi-della-fisica/  # Misura, grandezze, SI...
    └── 02-equilibrio/            # Vettori, forze, momento, pressione
```

Ogni sezione è un file `.mdx` con frontmatter (`title`, `sidebar_position`)
che ne determina titolo e posizione nel menu laterale.

### Componenti del libro

I box colorati tipici del libro sono componenti React, disponibili in ogni
file `.mdx` senza bisogno di import (vedi `src/components/BookBoxes/` e
`src/theme/MDXComponents.js`):

| Componente | Uso |
|---|---|
| `<PerIniziare>` | attività da fare prima della lezione |
| `<IlModelloDiRiferimento>` (`ModelloRiferimento`) | definizioni e regole |
| `<Esempio>` | esempi svolti |
| `<FAQ>` | domande frequenti |
| `<Esercizi>` | esercizi |
| `<PerRiassumere>` | riepilogo del modulo |
| `<Video id="..." title="..." />` | video YouTube incorporato |

Le formule matematiche si scrivono in LaTeX tra `$...$` (o `$$...$$` per le
formule su riga separata) e vengono renderizzate con
[KaTeX](https://katex.org/).

## Sviluppo locale

```bash
npm install
npm start        # server di sviluppo su http://localhost:3000
```

```bash
npm run build     # build di produzione in build/
npm run serve     # anteprima della build di produzione
```

## Contribuire

Le correzioni ai contenuti (refusi, esempi da migliorare, nuovi esercizi)
si possono proporre modificando i file `.mdx` in `docs/` e aprendo una
pull request.

## Stato del progetto / roadmap

Vedi [`CHECKPOINT.md`](./CHECKPOINT.md) per lo stato di avanzamento
dettagliato, cosa è stato automatizzato nella migrazione dall'EPUB
originale e i prossimi passi pianificati (app interattive, assistente
Google Gem, ecc.).

## Licenza

Da definire (consigliata una licenza Creative Commons per contenuti
didattici, es. CC BY-SA, coerente con lo spirito di progetto aperto).
