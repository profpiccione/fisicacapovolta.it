#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte le sezioni XHTML dell'epub "Fisica capovolta" in file Markdown/MDX,
riconoscendo i box colorati (Per iniziare, Modello di riferimento, Esempio,
F.A.Q., Esercizi, Per riassumere) e trasformando le formule (immagini WIRIS
con MathML nascosto in data-mathml) in LaTeX vero.
"""
import re
import os
import shutil
import subprocess
import html
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, NavigableString, Tag

SRC = "/home/claude/epub_extract/OEBPS"
OUT = "/home/claude/site_content"

# ---------------------------------------------------------------------------
# 1. MathML decoding + conversion to LaTeX
# ---------------------------------------------------------------------------

def decode_wiris_mathml(raw):
    """I file WIRIS salvano l'XML MathML sostituendo < > " & con « » ¨ §."""
    txt = html.unescape(raw)
    txt = (txt.replace('\u00ab', '<')   # «
              .replace('\u00bb', '>')   # »
              .replace('\u00a8', '"')   # ¨
              .replace('\u00a7', '&'))  # §
    return txt


MATHML_NS = "{http://www.w3.org/1998/Math/MathML}"


def strip_ns(tag):
    return tag.split('}', 1)[-1] if '}' in tag else tag


LATEX_SPECIAL_RE = re.compile(r'([%&#_$])')


def esc_latex(s):
    return LATEX_SPECIAL_RE.sub(r'\\\1', s)


def mathml_to_latex(node):
    tag = strip_ns(node.tag)
    children = list(node)

    def rec(n):
        return mathml_to_latex(n)

    if tag == 'math':
        return ''.join(rec(c) for c in children)
    if tag == 'mrow':
        return ''.join(rec(c) for c in children)
    if tag == 'mi':
        return esc_latex((node.text or '').strip())
    if tag == 'mn':
        return esc_latex((node.text or '').strip())
    if tag == 'mo':
        raw = node.text or ''
        if raw and raw.strip() == '':
            # spazio/nbsp tra due fattori = moltiplicazione implicita
            return r'\times '
        op = raw.strip()
        mapping = {
            '\u00d7': r'\times ', '\u00b7': r'\cdot ', '\u2212': '-',
            '\u2264': r'\le ', '\u2265': r'\ge ', '\u2260': r'\neq ',
            '\u2248': r'\approx ', '\u00b1': r'\pm ',
            '\u2192': r'\to ', '\u25b3': r'\Delta ',
        }
        if op in mapping:
            return mapping[op]
        return esc_latex(op)
    if tag == 'msup':
        base, exp = children
        return '{%s}^{%s}' % (rec(base), rec(exp))
    if tag == 'msub':
        base, sub = children
        return '{%s}_{%s}' % (rec(base), rec(sub))
    if tag == 'msubsup':
        base, sub, sup = children
        return '{%s}_{%s}^{%s}' % (rec(base), rec(sub), rec(sup))
    if tag == 'mfrac':
        num, den = children
        return r'\frac{%s}{%s}' % (rec(num), rec(den))
    if tag == 'msqrt':
        return r'\sqrt{%s}' % ''.join(rec(c) for c in children)
    if tag == 'mroot':
        base, idx = children
        return r'\sqrt[%s]{%s}' % (rec(idx), rec(base))
    if tag == 'mover':
        base, accent = children
        accent_txt = (accent.text or '').strip()
        if accent_txt == '\u00af':  # macron -> barra sopra (es. valore medio x̄)
            return r'\bar{%s}' % rec(base)
        return r'\overline{%s}' % rec(base)
    if tag == 'mspace':
        return ' '
    if tag == 'mtext':
        return r'\text{%s}' % esc_latex(node.text or '')
    if tag in ('mtable', 'mtr', 'mtd'):
        return ' '.join(rec(c) for c in children)
    # fallback: concatenate children / text
    out = (node.text or '')
    for c in children:
        out += rec(c)
        if c.tail:
            out += c.tail
    return out


def formula_to_latex(data_mathml_raw):
    try:
        decoded = decode_wiris_mathml(data_mathml_raw)
        root = ET.fromstring(decoded)
        latex = mathml_to_latex(root)
        latex = re.sub(r'\s+', ' ', latex).strip()
        return latex
    except Exception as e:
        return None


# ---------------------------------------------------------------------------
# 2. Box/section detection (color -> component)
# ---------------------------------------------------------------------------

COLOR_MAP = {
    '#ffcc99': 'AMBIGUOUS_ARANCIO',   # Per iniziare O Per riassumere
    '#fc9': 'AMBIGUOUS_ARANCIO',
    '#cccccc': 'Esempio',
    '#ccc': 'Esempio',
    '#ffffcc': 'FAQ',
    '#e6e6ff': 'Esercizi',
}

LABEL_COMPONENT = {
    'PER INIZIARE': 'PerIniziare',
    'PER RIASSUMERE': 'PerRiassumere',
}


def get_bg_color(tag):
    style = tag.get('style', '') or ''
    m = re.search(r'background-color:\s*(#[0-9a-fA-F]{3,6})', style)
    return m.group(1).lower() if m else None


def find_top_level_boxes(soup):
    """Trova le <table> con background-color impostato direttamente (non ereditato
    da una tabella genitore) - queste sono i box semantici del libro."""
    boxes = []
    for table in soup.find_all('table'):
        # scarta le tabelle innestate dentro un altro box già trovato
        if table.find_parent('table') is not None:
            continue
        color = get_bg_color(table)
        if color:
            boxes.append(table)
    return boxes


def flatten_image_layout_tables(soup):
    """Le tabelle usate solo per affiancare immagini (nessun testo nelle celle)
    vengono 'appiattite' in una sequenza di paragrafi con immagine, per evitare
    che una tabella-nella-tabella confonda la conversione HTML->Markdown."""
    changed = True
    while changed:
        changed = False
        for table in soup.find_all('table'):
            cells = table.find_all('td')
            if not cells:
                continue
            if all(not td.get_text(strip=True) and td.find('img') for td in cells):
                imgs = table.find_all('img')
                new_nodes = []
                for img in imgs:
                    p = Tag(name='p')
                    p.append(img.extract())
                    new_nodes.append(p)
                anchor = table
                for node in new_nodes:
                    anchor.insert_after(node)
                    anchor = node
                table.decompose()
                changed = True
                break  # ricomincia: la lista find_all non è più valida
    return soup


def norm_text(t):
    return re.sub(r'\s+', ' ', t).strip()


def detect_box_type(table, color):
    text = norm_text(table.get_text(" ", strip=True)).upper()
    if color in ('#ffcc99', '#fc9'):
        if 'RIASSUM' in text[:60]:
            return 'PerRiassumere'
        return 'PerIniziare'
    if color in ('#cccccc', '#ccc'):
        return 'Esempio'
    if color == '#ffffcc':
        return 'FAQ'
    if color == '#e6e6ff':
        return 'Esercizi'
    return None


HEADER_STRIP_RE = re.compile(
    r'^(PER\s*INIZIARE|PER\s*RIASSUMERE|IL\s*MODELLO\s*DI\s*RIFERIMENTO|'
    r'F\.\s*A\.\s*Q\.|ESEMPIO|ESEMPI|ESERCIZI)\s*:?\s*$',
    re.IGNORECASE)


def remove_redundant_header(table):
    """Rimuove il primo <p><strong>TITOLO</strong></p> che duplica il nome del box,
    dato che sarà il componente stesso a mostrare il titolo."""
    first_p = table.find('p')
    if first_p and HEADER_STRIP_RE.match(norm_text(first_p.get_text())):
        first_p.decompose()


# "Il modello di riferimento" non ha sfondo colorato ma è un <table border>
# con un <p><strong><u>IL MODELLO DI RIFERIMENTO</u></strong></p>
def find_modello_riferimento_boxes(soup):
    found = []
    for table in soup.find_all('table'):
        if table.find_parent('table') is not None:
            continue
        if get_bg_color(table):
            continue
        text = norm_text(table.get_text(" ", strip=True)).upper()
        if text.startswith('IL MODELLO DI RIFERIMENTO'):
            found.append(table)
    return found


# ---------------------------------------------------------------------------
# 3. Pre-processing: sostituisce box/formule/video con placeholder testuali
#    prima di passare il tutto a pandoc (che gestisce liste, tabelle semplici,
#    grassetto/corsivo/link molto meglio di un parser scritto a mano).
# ---------------------------------------------------------------------------

YOUTUBE_RE = re.compile(r'youtube\.com/embed/([A-Za-z0-9_-]+)')


def preprocess_body(soup, img_used):
    # 3.-1 appiattisce le tabelle usate solo come layout per affiancare immagini
    flatten_image_layout_tables(soup)

    # 3.-0.5 rimuove TUTTI i <div> preesistenti nel documento originale: sono
    # solo wrapper cosmetici dell'editor WYSIWYG (centratura immagini, margini,
    # contenitori vuoti) senza alcun valore semantico. I <div> che rappresentano
    # i box del libro (Per iniziare, Esempio, ecc.) li creiamo noi più sotto,
    # DOPO questo passaggio, quindi non vengono toccati.
    for div in soup.find_all('div'):
        div.unwrap()

    # 3.0 rimuove i wrapper <span> (cruft da editor WYSIWYG: underline,
    # Apple-style-span...) e i div contenitore senza significato semantico,
    # mantenendone solo il contenuto.
    for span in soup.find_all('span'):
        span.unwrap()
    for div in soup.find_all('div', id='asset_testo'):
        div.unwrap()
    # rimuove <em>/<strong> vuoti (spesso avvolgevano solo un <br/> residuo
    # dell'editor originale) che altrimenti generano asterischi orfani
    for tag in soup.find_all(['em', 'strong', 'u']):
        if not tag.get_text(strip=True) and not tag.find(['img', 'iframe']):
            tag.decompose()

    # 3.1 formule WIRIS -> placeholder con LaTeX
    def code_placeholder(text):
        c = Tag(name='code')
        c.append(NavigableString(text))
        return c

    for img in soup.find_all('img', class_='Wirisformula'):
        raw = img.get('data-mathml')
        latex = formula_to_latex(raw) if raw else None
        if latex:
            placeholder = code_placeholder(f"%%LATEX%%{latex}%%LATEX%%")
        else:
            # fallback: tieni l'immagine come immagine normale
            src = img.get('src', '')
            if src:
                img_used.add(src)
            placeholder = code_placeholder(f"%%LATEXIMG%%{os.path.basename(src)}%%LATEXIMG%%")
        img.replace_with(placeholder)

    # 3.2 iframe YouTube -> placeholder
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        m = YOUTUBE_RE.search(src)
        title = (iframe.get('title', 'Video') or 'Video').replace('@@', ' ')
        if m:
            placeholder = code_placeholder(f"%%VIDEO%%{m.group(1)}@@{title}%%VIDEO%%")
        else:
            placeholder = NavigableString(f"\n\n[Video: {title}]({src})\n\n")
        iframe.replace_with(placeholder)

    # 3.3 immagini normali -> registra il path e riscrive il src come
    # root-assoluto (/img/nome.png), valido da qualunque pagina del sito
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            img_used.add(src)
            img['src'] = f"/img/{os.path.basename(src)}"

    # 3.4 box colorati (Per iniziare / Per riassumere / Esempio / FAQ / Esercizi)
    for table in find_top_level_boxes(soup):
        color = get_bg_color(table)
        box_type = detect_box_type(table, color)
        if not box_type:
            continue
        remove_redundant_header(table)
        inner_html = ''.join(str(c) for c in table.find_all('td')[0].contents) \
            if table.find('td') else table.decode_contents()
        wrapper = Tag(name='div')
        wrapper['data-box'] = box_type
        wrapper.append(BeautifulSoup(inner_html, 'html.parser'))
        table.replace_with(wrapper)

    # 3.5 box "Il modello di riferimento" (nessuno sfondo, riconosciuto da testo)
    for table in find_modello_riferimento_boxes(soup):
        remove_redundant_header_modello(table)
        td = table.find('td')
        inner_html = ''.join(str(c) for c in td.contents) if td else table.decode_contents()
        wrapper = Tag(name='div')
        wrapper['data-box'] = 'ModelloRiferimento'
        wrapper.append(BeautifulSoup(inner_html, 'html.parser'))
        table.replace_with(wrapper)

    return soup


MODELLO_HEADER_RE = re.compile(r'^\s*IL\s*MODELLO\s*DI\s*RIFERIMENTO\s*$', re.IGNORECASE)


def remove_redundant_header_modello(table):
    first_p = table.find('p')
    if first_p and MODELLO_HEADER_RE.match(norm_text(first_p.get_text())):
        first_p.decompose()


# ---------------------------------------------------------------------------
# 4. Placeholder -> sintassi Markdown/MDX finale (dopo il passaggio in pandoc)
# ---------------------------------------------------------------------------

def postprocess_markdown(md):
    # pandoc racchiude ogni <code> placeholder in backtick (anche multipli quando
    # più code-span sono adiacenti, es. ``A``B``). Li rimuoviamo tutti indistintamente
    # quando sono adiacenti ai nostri marcatori %%...%%, poi lavoriamo sul testo pulito.
    md = re.sub(r'`+(?=%%(?:LATEX|LATEXIMG|VIDEO)%%)', '', md)
    md = re.sub(r'(%%(?:LATEX|LATEXIMG|VIDEO)%%)`+', r'\1', md)

    md = re.sub(r'%%LATEX%%(.*?)%%LATEX%%',
                lambda m: f"${m.group(1)}$", md, flags=re.S)
    md = re.sub(r'%%LATEXIMG%%(.*?)%%LATEXIMG%%',
                lambda m: f"![formula](/img/{m.group(1)})", md, flags=re.S)

    def video_repl(m):
        vid, title = m.group(1).split('@@', 1)
        return f'\n<Video id="{vid}" title="{title}" />\n'
    md = re.sub(r'%%VIDEO%%(.*?)%%VIDEO%%', video_repl, md, flags=re.S)

    # rimuove asterischi di enfasi rimasti "orfani" intorno ai placeholder ormai
    # sostituiti (es. testo originale in corsivo che avvolgeva solo un video/formula)
    md = re.sub(r'\*(\s*(?:<Video[^>]*/>|\$[^$]*\$)\s*)\*', r'\1', md)

    # pandoc a volte inserisce un commento HTML vuoto <!-- --> per separare due
    # liste adiacenti che altrimenti si fonderebbero: non è sintassi valida in
    # JSX/MDX, va convertito nell'equivalente commento MDX.
    md = re.sub(r'<!--(.*?)-->', r'{/*\1*/}', md, flags=re.S)
    # pandoc non è riuscito a convertire in Markdown puro (celle multi-riga) e
    # ha lasciato come HTML grezzo: lo stile lo darà il CSS del sito.
    md = re.sub(r'\s*data-border="[^"]*"', '', md)
    md = re.sub(r'\s*data-cellpadding="[^"]*"', '', md)
    md = re.sub(r'\s*data-cellspacing="[^"]*"', '', md)
    md = re.sub(r'\s*class="(?:odd|even)"', '', md)

    # JSX non accetta l'attributo style come stringa (solo come oggetto): le
    # tabelle-dati rimaste come HTML grezzo portano ancora `style="width: X%"`
    # ereditato dal libro originale. Lo rimuoviamo: la larghezza delle colonne
    # verrà gestita dal CSS del sito, non da inline style per-tabella.
    md = re.sub(r'\s*style="[^"]*"', '', md)

    # div[data-box=...] sopravvivono a pandoc come blocchi HTML grezzi, ma pandoc
    # elimina il prefisso "data-" dagli attributi custom (data-box -> box).
    def box_open(m):
        return f"\n<{m.group(1)}>\n"
    md = re.sub(r'<div box="([A-Za-z]+)">', box_open, md)
    md = md.replace('</div>', '\n</__CLOSEBOX__>\n')
    return md


def fix_closing_tags(md):
    """Sostituisce ogni </__CLOSEBOX__> con il tag di chiusura del box aperto
    corrispondente, usando uno stack (i div non sono annidati in questo libro)."""
    open_re = re.compile(r'<(PerIniziare|PerRiassumere|Esempio|FAQ|Esercizi|ModelloRiferimento)>')
    out = []
    stack = []
    i = 0
    for part in re.split(r'(<(?:PerIniziare|PerRiassumere|Esempio|FAQ|Esercizi|ModelloRiferimento)>|</__CLOSEBOX__>)', md):
        m = open_re.match(part)
        if m:
            stack.append(m.group(1))
            out.append(part)
        elif part == '</__CLOSEBOX__>':
            name = stack.pop() if stack else 'div'
            out.append(f'</{name}>')
        else:
            out.append(part)
    return ''.join(out)


# ---------------------------------------------------------------------------
# 5. Struttura del libro (dal toc.ncx) e conversione di ogni sezione
# ---------------------------------------------------------------------------

# (file, titolo, cartella-modulo, slug, numero-per-ordinamento)
STRUCTURE = [
    ("sezione_424360.xhtml", "0. Premesse matematiche", "00-premesse-matematiche", "00-premesse-matematiche", None),
    ("sezione_300593.xhtml", "0.1. Notazione scientifica", "00-premesse-matematiche", "01-notazione-scientifica", None),
    ("sezione_300677.xhtml", "0.2. Grafici", "00-premesse-matematiche", "02-grafici", None),
    ("sezione_298126.xhtml", "1. Le basi della fisica", "01-le-basi-della-fisica", "00-le-basi-della-fisica", None),
    ("sezione_298127.xhtml", "1.1. La misura e le grandezze fisiche", "01-le-basi-della-fisica", "01-la-misura-e-le-grandezze-fisiche", None),
    ("sezione_298128.xhtml", "1.2. Gli strumenti di misura", "01-le-basi-della-fisica", "02-gli-strumenti-di-misura", None),
    ("sezione_298129.xhtml", "1.3. Il Sistema Internazionale", "01-le-basi-della-fisica", "03-il-sistema-internazionale", None),
    ("sezione_298131.xhtml", "1.4. Lunghezza e volume", "01-le-basi-della-fisica", "04-lunghezza-e-volume", None),
    ("sezione_298132.xhtml", "1.5. Massa e densità", "01-le-basi-della-fisica", "05-massa-e-densita", None),
    ("sezione_298134.xhtml", "1.6. Tempo, valore medio e incertezza", "01-le-basi-della-fisica", "06-tempo-valore-medio-e-incertezza", None),
    ("sezione_300061.xhtml", "2. Equilibrio", "02-equilibrio", "00-equilibrio", None),
    ("sezione_300062.xhtml", "2.1. Vettori, forze ed equilibrio", "02-equilibrio", "01-vettori-forze-ed-equilibrio", None),
    ("sezione_300063.xhtml", "2.2. Campo gravitazionale e forza peso", "02-equilibrio", "02-campo-gravitazionale-e-forza-peso", None),
    ("sezione_300064.xhtml", "2.3. Momento ed equilibrio dei corpi rigidi", "02-equilibrio", "03-momento-ed-equilibrio-dei-corpi-rigidi", None),
    ("sezione_300065.xhtml", "2.4. Pressione ed equilibrio dei fluidi", "02-equilibrio", "04-pressione-ed-equilibrio-dei-fluidi", None),
]

FRONT_PAGES = [
    ("sezione_418991.xhtml", "Presentazione", "presentazione"),
    ("sezione_418989.xhtml", "Download", "download"),
]


def html_to_markdown(inner_html):
    """Passa un frammento HTML attraverso pandoc per ottenere GFM Markdown."""
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm", "--wrap=preserve"],
        input=inner_html, capture_output=True, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout


def convert_section(filename, title):
    path = os.path.join(SRC, filename)
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    soup = BeautifulSoup(raw, "html.parser")
    body = soup.body
    # rimuovi l'h1/h2 di titolo originale (lo rimettiamo noi nel frontmatter/H1)
    for h in body.find_all(re.compile('^h[1-4]$')):
        h.decompose()
        break

    img_used = set()
    body = preprocess_body(body, img_used)
    inner_html = body.decode_contents()
    md = html_to_markdown(inner_html)
    md = postprocess_markdown(md)
    md = fix_closing_tags(md)
    # pulizia righe vuote multiple
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + "\n"
    return md, img_used


def write_mdx(path, title, md_body, order=None):
    front = ["---", f'title: "{title}"']
    if order is not None:
        front.append(f"sidebar_position: {order}")
    front.append("---")
    content = "\n".join(front) + "\n\n" + md_body
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    all_imgs_used = set()

    # pagine introduttive
    for i, (fn, title, slug) in enumerate(FRONT_PAGES):
        md, imgs = convert_section(fn, title)
        all_imgs_used |= imgs
        write_mdx(os.path.join(OUT, "intro", f"{i:02d}-{slug}.mdx"), title, md, order=i)

    # moduli del libro
    for i, (fn, title, folder, slug, _) in enumerate(STRUCTURE):
        md, imgs = convert_section(fn, title)
        all_imgs_used |= imgs
        write_mdx(os.path.join(OUT, "moduli", folder, f"{slug}.mdx"), title, md,
                  order=i)

    # copia le immagini realmente usate
    img_out = os.path.join(OUT, "static", "img")
    os.makedirs(img_out, exist_ok=True)
    copied, missing = 0, []
    for src in sorted(all_imgs_used):
        srcfile = os.path.join(SRC, src)
        dstfile = os.path.join(img_out, os.path.basename(src))
        if os.path.exists(srcfile):
            shutil.copy(srcfile, dstfile)
            copied += 1
        else:
            missing.append(src)

    print(f"Sezioni convertite: {len(STRUCTURE) + len(FRONT_PAGES)}")
    print(f"Immagini copiate: {copied}, mancanti: {len(missing)}")
    if missing:
        print("Immagini non trovate:", missing)


if __name__ == "__main__":
    main()

