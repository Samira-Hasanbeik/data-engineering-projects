#--------------------------------------------------------------
#Parser für html-Dateien der Zeitung Spiegel

#Parser geht ausgehend von basepath alle Unterordner durch und parsed jede Datei, die eine html-Datei ist
#Output ist eine Liste an dictionaries
#--------------------------------------------------------------

import os
from typing import Iterator
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

basepath = os.path.expanduser("~/newsdata/spiegel") #Basispfad festlegen von dem dann ausgegangen wird

def make_soup(basepath: str) -> Iterator[BeautifulSoup]:
    for root, _, files in os.walk(basepath): #geht alle Unterordner und Dateien ab, die in basepath sind
        for filename in tqdm(files, desc=f"Verarbeite Dateien in {root}"):
            if filename.endswith(".html"): # nur html Datein berücksichtigen
                snapshotPfad = os.path.join(root, filename) #fügt Dateinamen und Pfad zusammen
                with open(snapshotPfad, encoding= "utf-8") as file:
                    snapshot = file.read()
                yield BeautifulSoup(snapshot, "html.parser")


def extract_author_spiegel(article) -> str | None:
    """
    Autor-Extraktion für SPIEGEL ohne Scoring.
    - akzeptiert nur klare Byline-Muster
    - verhindert Rubriken / Überschriften als Autor
    - bereinigt Prefixe ("Von", "Ein Interview von", ...)
    - entfernt Orts-/Dateline-Enden
    """
    # 1) mögliche Kandidaten sammeln (font-sansUI-Spans)
    candidates = []

    for s in article.find_all("span", class_=lambda c: c and "font-sansUI" in c):
        txt = s.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            continue

        # Länge begrenzen
        if len(txt) > 140:
            continue

        # harte Ausschlüsse
        if re.search(r"\bbilder\b|\bpodcast\b|\bvideo\b|\banzeige\b", txt, flags=re.IGNORECASE):
            continue

        # Rubriken / Labels ausschließen
        if re.match(
            r"^\s*(nach|wegen|bei|mit|ohne|trotz|im|am|zum|zur|unter|gegen)\b",
            txt,
            flags=re.IGNORECASE
        ):
            continue

        candidates.append(txt)

    if not candidates:
        return None

    # 2) nur echte Byline-Muster zulassen
    byline_pattern = re.compile(
        r"^\s*(?:"
        r"von\s+.+|"                               # Von Max Mustermann
        r"(?:ein(?:e)?\s+)?(?:interview|gespräch)\s+von\s+.+|"  # Ein Interview von ...
        r"(?:eine\s+)?stilkritik\s+von\s+.+|"     # Eine Stilkritik von ...
        r"(?:ein(?:e)?\s+)?(?:analyse|einordnung|bericht|reportage|kolumne|kommentar|porträt)\s+von\s+.+"
        r")$",
        flags=re.IGNORECASE
    )

    author_raw = None
    for txt in candidates:
        if byline_pattern.match(txt):
            author_raw = txt
            break

    if not author_raw:
        # kein eindeutiger Autor → bewusst None
        return None

    # 3) Prefixe entfernen
    author = re.sub(
        r"^\s*(?:"
        r"von|"
        r"ein(?:e)?\s+(?:interview|gespräch)\s+von|"
        r"(?:interview|gespräch)\s+von|"
        r"eine\s+stilkritik\s+von|"
        r"ein(?:e)?\s+(?:analyse|einordnung|bericht|reportage|kolumne|kommentar|porträt)\s+von|"
        r"(?:analyse|einordnung|bericht|reportage|kolumne|kommentar|porträt)\s+von"
        r")\s+",
        "",
        author_raw,
        flags=re.IGNORECASE
    ).strip()

    # 4) Orts-/Dateline-Enden entfernen
    author = re.sub(
        r"\s*(?:"
        r"(?:,|–|-)\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\- ]{2,}$|"
        r"\s+(?:aus|in)\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß.\- ]{2,}$"
        r")\s*$",
        "",
        author
    ).strip()

    # 5) Whitespace normalisieren + "und" vereinheitlichen
    author = re.sub(r"\s+", " ", author).strip()
    author = re.sub(r"\s+\bund\b\s+", ", ", author, flags=re.IGNORECASE).strip()

    return author or None


BASE = "https://www.spiegel.de"

def parse_spiegel(soup: BeautifulSoup) -> list[dict]:
    by_url = {}
        
    article_elements = soup.find_all("article")
        
    for article in article_elements:
        # URL extrahieren
        url = None
        link = article.find("a")
        if not link:
            continue
        href = link.get('href') or ""
        if "/fotostrecke/" in href or "/gutscheine/" in href:
            continue

        url = urljoin(BASE, href)
        host = urlparse(url).netloc.lower()
        if not (host == "www.spiegel.de" or host.endswith(".spiegel.de")):
            continue
                
        # Überschrift extrahieren
        ueberschrift = article.get('aria-label') or link.get("title")
        if not ueberschrift:
            continue
                
        # Teaser/Text extrahieren
        textinhalt = None
        section = article.find("section")
        if section:
            teaser_container = section.select_one("span.font-serifUI")
            if teaser_container:
                textinhalt = teaser_container.get_text(" ", strip=True) or None
            else:
                a = section.find("a")
                if a:
                    textinhalt = a.get_text(" ", strip=True) or None 

        autor = extract_author_spiegel(article)

        article = {"url": url, "titel": ueberschrift, "autor": autor, "teasertext": textinhalt} #dictionary füllen mit geparsten Daten
        
        old = by_url.get(url)
        if old is None:
            by_url[url] = article
        else:
            # bessere Version ersetzt schlechtere
            if old.get("teasertext") is None and article.get("teasertext") is not None:
                by_url[url] = article
            elif old.get("autor") is None and article.get("autor") is not None:
                by_url[url] = article

    articles = list(by_url.values())
    return articles


if __name__ == "__main__":
    all_articles = []
    global_seen = set()

    for soup in make_soup(basepath):
        for art in parse_spiegel(soup):
            if art["url"] not in global_seen:
                all_articles.append(art)
                global_seen.add(art["url"])
    
    print(all_articles[:3])
    print(len(all_articles))
