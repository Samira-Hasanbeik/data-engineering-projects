#--------------------------------------------------------------
#Parser für html-Dateien der Zeitung Handelsblatt

#Parser geht ausgehend von basepath alle Unterordner durch und parsed jede Datei, die eine html-Datei ist
#Output ist eine Liste an dictionaries
#--------------------------------------------------------------

import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Iterator
import re
import copy
from urllib.parse import urljoin

basepath = os.path.expanduser("~/newsdata/handelsblatt") #Basispfad festlegen von dem dann ausgegangen wird


def make_soup(basepath: str) -> Iterator[BeautifulSoup]:
    for root, _, files in os.walk(basepath): #geht alle Unterordner und Dateien ab, die in basepath sind
        for filename in tqdm(files, desc=f"Verarbeite Dateien in {root}"):
            if filename.endswith(".html"): # nur html Datein berücksichtigen
                snapshotPfad = os.path.join(root, filename) #fügt Dateinamen und Pfad zusammen
                with open(snapshotPfad, encoding= "utf-8") as file:
                    snapshot = file.read()
                yield BeautifulSoup(snapshot, "html.parser")



def parse_handelsblatt(soup: BeautifulSoup) -> list[dict]:
    BASE = "https://www.handelsblatt.com"
    # Leere Listen erstellen
    articles = [] #für Artikel-Tabelle
    seen_urls = set() #für doppelte URL

    article_links = soup.select("div.c-megaaufmacher a, a.u-hover-underline-child, div.vhb-teaser--wrapper a, a.vhb-teaser-link")
    for a_tag in article_links:
        href = a_tag.get("href")
        if not href:
            continue
        if href.startswith("http") and not href.endswith(".html") and "handelsblatt.com" not in href:
            continue
        url = urljoin(BASE, href)

        title = None
        title_container = a_tag.find("h1", class_="u-space-0") # Sonderaufmacher
        if not title_container:
            title_container = a_tag.find("h3") # normale Artikel
        if not title_container:
            title_container = a_tag.find("span", class_="vhb-headline") # Newsticker, Gastbeiträge, etc.
        if title_container:
            title = " ".join(title_container.stripped_strings)
        else:
            title = " ".join(a_tag.stripped_strings) or None #Meistgelesen
        if not title:
            continue

        teaser_container = a_tag.find("p")
        if not teaser_container:
            continue
                 
        author_tag = teaser_container.find("span", class_=lambda c: c and "vhb-author" in c.split())
        clean_author = None
        if author_tag:
            raw_author = author_tag.get_text(" ", strip=True)
            clean_author = re.sub(r"\s+", " ", raw_author).strip()
        else: 
            author_tag = teaser_container.find("span", class_= lambda c: c and "u-italic" in c.split())
            if author_tag:
                raw_author = author_tag.get_text(" ", strip=True)
                raw_author = re.sub(r"^\s*von\s+", "", raw_author, flags=re.IGNORECASE).strip()
                clean_author = re.sub(r"\s+", " ", raw_author).strip() if raw_author else None

        teaser_copy = copy.copy(teaser_container)
        for span in teaser_copy.find_all("span"):
            span.decompose()
        teasertext = teaser_copy.get_text(" ", strip=True) or None

        #Speichern der einzigartigen Artikel
        if url not in seen_urls:
            article = {"url": url, "titel": title, "autor": clean_author, "teasertext": teasertext} #dictionary füllen mit geparsten Daten
            articles.append(article) #dictionaries in Liste speichern
            seen_urls.add(url)
                  
    return articles


if __name__ == "__main__":
    all_articles = []
    global_seen = set()

    for soup in make_soup(basepath):
        for art in parse_handelsblatt(soup):
            if art["url"] not in global_seen:
                all_articles.append(art)
                global_seen.add(art["url"])
    
    print(all_articles[:3])
    print(len(all_articles))
