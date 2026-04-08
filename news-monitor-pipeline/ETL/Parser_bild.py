
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Iterator
from urllib.parse import urljoin, urlparse
import re

basepath = os.path.expanduser("~/newsdata/bild") #Basispfad festlegen von dem dann ausgegangen wird


def make_soup(basepath: str) -> Iterator[BeautifulSoup]:
    for root, _, files in os.walk(basepath): #geht alle Unterordner und Dateien ab, die in basepath sind
        for filename in tqdm(files, desc=f"Verarbeite Dateien in {root}"):
            if filename.endswith(".html"): # nur html Datein berücksichtigen
                snapshotPfad = os.path.join(root, filename) #fügt Dateinamen und Pfad zusammen
                with open(snapshotPfad, encoding= "utf-8") as file:
                    snapshot = file.read()
                yield BeautifulSoup(snapshot, "html.parser")
    


def parse_bild(soup: BeautifulSoup) -> list[dict]:
    BASE = "https://www.bild.de"
    # Leere Listen erstellen
    articles = [] #für Artikel-Tabelle
    seen_urls = set() #für doppelte URL

    for a_tag in soup.find_all("a"):
        if ("data-tb-kicker" in a_tag.attrs
            and "data-tb-title" in a_tag.attrs
            and a_tag.has_attr("href")):
            raw_title = a_tag["data-tb-kicker"]+ " " + a_tag["data-tb-title"]
            clean_title = re.sub(r"\s+", " ", raw_title.replace("\xa0", " ")).strip()
            if not clean_title:
                continue

            if clean_title.lower().startswith("link:") or "http" in clean_title.lower():
                continue

            href = a_tag["href"]
            if not href:
                continue
            url = urljoin(BASE, href)

            parsed = urlparse(url)
            host = parsed.netloc.lower()
            if not (host == "bild.de" or host == "www.bild.de"):
                continue

            path = parsed.path.lower()
            if any(bad in path for bad in ["/gutscheine/", "/angebote/", "/shopping/"]):
                continue


            #Speichern der einzigartigen Artikel
            if url not in seen_urls:
                article = {"url": url, "titel": clean_title, "autor": None, "teasertext": None} #dictionary füllen mit geparsten Daten
                articles.append(article) #dictionaries in Liste speichern
                seen_urls.add(url)       
        else:
            pass

    for article_tag in soup.find_all("article", class_="stage-teaser"):
        a_tag = article_tag.find("a", class_="stage-teaser__anchor")
        if not a_tag:
            continue
        href = a_tag["href"]
        if not href:
            continue
        url = urljoin(BASE, href)

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        if not (host == "bild.de" or host == "www.bild.de"):
            continue

        path = parsed.path.lower()
        if any(bad in path for bad in ["/gutscheine/", "/angebote/", "/shopping/"]):
            continue

        clean_title = None
        title_container = a_tag.find("div", class_="teaser__title")
        if title_container:
            clean_title = " ".join(title_container.stripped_strings)

        if not clean_title: 
            img = a_tag.find("img")
            if img:
                clean_title = img.get("alt")

        clean_title = re.sub(r"\s+", " ", clean_title).strip() if clean_title else None
        if not clean_title:
            continue

        if clean_title.lower().startswith("link:") or "http" in clean_title.lower():
            continue
        
        #Speichern der einzigartigen Artikel
        if url not in seen_urls:
            article = {"url": url, "titel": clean_title, "autor": None, "teasertext": None} #dictionary füllen mit geparsten Daten
            articles.append(article) #dictionaries in Liste speichern
            seen_urls.add(url)

    return articles


if __name__ == "__main__":
    all_articles = []
    global_seen = set()

    for soup in make_soup(basepath):
        for art in parse_bild(soup):
            if art["url"] not in global_seen:
                all_articles.append(art)
                global_seen.add(art["url"])
    
    print(all_articles[:3])
    print(len(all_articles))
