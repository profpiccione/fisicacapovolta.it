# Fisica capovolta → sito Docusaurus — stato del lavoro (checkpoint 2)

Questo checkpoint contiene un **progetto Docusaurus funzionante e già
testato con una build reale** (`npm run build` completata senza errori né
warning), non solo i file Markdown grezzi del checkpoint precedente.

## Come riprendere in locale

```bash
cd fisica-capovolta-site
npm install       # ricrea node_modules (escluso da questo archivio)
npm start         # server di sviluppo su http://localhost:3000
# oppure
npm run build && npm run serve   # build di produzione + anteprima
```

## Cosa contiene / cosa è stato fatto

- **Contenuti**: `docs/intro/` (Presentazione, Download) e
  `docs/moduli/00-premesse-matematiche|01-le-basi-della-fisica|02-equilibrio/`,
  17 file `.mdx` totali, con sidebar ordinata via `_category_.json` e
  `sidebar_position` nel frontmatter.
- **Componenti React** in `src/components/BookBoxes/`: `PerIniziare`,
  `PerRiassumere`, `Esempio`, `FAQ`, `Esercizi`, `ModelloRiferimento`,
  `Video` — con i colori originali del libro (arancione/grigio/giallo/
  azzurro) e supporto dark mode. Registrati globalmente in
  `src/theme/MDXComponents.js`, quindi nei file `.mdx` si usano come tag
  diretti senza import.
- **Formule matematiche**: renderizzate con KaTeX (`remark-math` +
  `rehype-katex`), non più come immagini.
- **Homepage** (`src/pages/index.js`, `src/components/HomepageFeatures/`)
  personalizzata con titolo, tagline e 3 punti di forza del libro (metodo
  capovolto, esempi/esercizi/FAQ, progetto aperto), pulsante che porta
  direttamente a `/intro/presentazione`.
- **`docusaurus.config.js`**: titolo/lingua italiana, blog disabilitato
  (non serviva), `routeBasePath: '/'` per i docs, integrazione KaTeX CSS.

### Bug reali trovati e corretti grazie alla build di prova

La build ha fatto da controllo di qualità automatico sui 5 file "a
rischio" (quelli con tabelle-dati complesse). Ha permesso di scovare e
sistemare nello script `convert.py`:
- `<div>` cosmetici dell'editor originale (solo centratura immagini) che
  spezzavano il parsing MDX — ora rimossi in blocco a monte
- un commento HTML di Pandoc (`<!-- -->`, separatore tra due liste)
  convertito nell'equivalente commento MDX (`{/* */}`)
- attributi `style="..."` come stringa nelle tabelle HTML residue (JSX
  vuole un oggetto, non una stringa) — ora rimossi
- due formule non gestite dal convertitore MathML→LaTeX: il valore medio
  con barra sopra (x̄ → `\bar{x}`) e il simbolo Δ salvato internamente
  come triangolo Unicode invece che come lettera greca
- il carattere `%` nelle formule, che va scappato (`\%`) per non essere
  letto da KaTeX come inizio di un commento LaTeX

`convert.py` (nella cartella superiore di questo checkpoint, vedi sotto)
è quindi più robusto adesso e ha superato la build reale su tutti i 17 file.

## Cosa NON è ancora stato fatto (prossimi passi)

1. **Revisione visiva vera**: finora è stato verificato solo che il sito
   *compili* senza errori — non è stata ancora fatta un'ispezione pagina
   per pagina del risultato renderizzato (impaginazione, immagini,
   formule, video).
2. **Rifinitura estetica**: logo/favicon ancora quelli di default di
   Docusaurus, navbar/footer da personalizzare ulteriormente.
3. **Repository Git**: la cartella è pronta per `git init`, ma non è
   ancora stata collegata a un repository GitHub reale né pubblicata
   (GitHub Pages / Vercel / Netlify).
4. **App interattive e Google Gem**, come discusso nella prima parte
   della conversazione.

## File inclusi in questo archivio

- `fisica-capovolta-site/` — il progetto Docusaurus completo (senza
  `node_modules`, `build`, `.docusaurus`: si rigenerano con `npm install`
  e `npm run build`)
- `convert.py` — lo script di conversione EPUB → MDX aggiornato con tutte
  le correzioni di questo step
- `site_content/` — l'output grezzo dello script (stesso contenuto già
  presente in `fisica-capovolta-site/docs`, tenuto anche qui separato
  come riferimento/backup indipendente dal progetto Docusaurus)
