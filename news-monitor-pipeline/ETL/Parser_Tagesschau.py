#--------------------------------------------------------------
#Parser für html-Dateien der Zeitung Tagesschau

#Parser geht ausgehend von basepath alle Unterordner durch und parsed jede Datei, die eine html-Datei ist
#Output ist eine Liste an dictionaries
#--------------------------------------------------------------

import os
from typing import Iterator
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from tqdm import tqdm

basepath = os.path.expanduser("~/newsdata/tagesschau") #Basispfad festlegen von dem dann ausgegangen wird

def make_soup(basepath: str) -> Iterator[BeautifulSoup]:
    for root, _, files in os.walk(basepath): #geht alle Unterordner und Dateien ab, die in basepath sind
        for filename in tqdm(files, desc=f"Verarbeite Dateien in {root}"):
            if filename.endswith(".html"): # nur html Datein berücksichtigen
                snapshotPfad = os.path.join(root, filename) #fügt Dateinamen und Pfad zusammen
                with open(snapshotPfad, encoding= "utf-8") as file:
                    snapshot = file.read()
                yield BeautifulSoup(snapshot, "html.parser")



def parse_tagesschau(soup: BeautifulSoup) -> list[dict]:
    BASE = "https://www.tagesschau.de"

    articles = []
    seen_urls = set()

    # typische Tagesschau-Teaser-Container
    teaser_containers = soup.select("div.teaser, li.teaser-xs")

    for container in teaser_containers:
        # ---------- Link / URL ----------
        link = (
            container.select_one("a.teaser__link, a.teaser-xs__link")
            or container.find("a", href=True)
        )
        if not link:
            continue

        href = (link.get("href") or "").strip()
        if not href:
            continue

        url = urljoin(BASE, href)

        if url in seen_urls:
            continue
        seen_urls.add(url)

        # ---------- Titel ----------
        title_tag = (
            container.select_one(".teaser__h3, .teaser-xs__headline-wrapper, .teaser__headline-wrapper")
            or link.select_one(".teaser__h3, .teaser-xs__headline-wrapper, .teaser__headline-wrapper")
        )

        raw_title = None
        if title_tag:
            raw_title = " ".join(title_tag.stripped_strings)
        else:
            raw_title = link.get("title")
        if not raw_title:
            continue
        titel = re.sub(r"\s+", " ", raw_title).strip()

        # ---------- Teasertext ----------
        teaser_tag = container.select_one(
            "p.teaser__shorttext, "
            "p.teaser-xs__shorttext, "
            "p.teaser__text, "
            "p.teaser-xs__text"
        )

        teasertext = None
        autor = None
        if teaser_tag:
            # Autor steht meist im <em>
            em_tag = teaser_tag.find("em")
            if em_tag:
                raw_author = " ".join(em_tag.stripped_strings)
                raw_author = re.sub(r"^\s*von\s+", "", raw_author, flags=re.IGNORECASE)
                autor = re.sub(r"\s+", " ", raw_author).strip() or None

                # <em> aus dem Teaser entfernen
                em_tag.decompose()

            # --- irrelevante <span> entfernen (z.B. "mehr") ---
            for span in teaser_tag.find_all("span"):
                span.decompose()

            # Teasertext OHNE <em>
            raw_teaser = " ".join(teaser_tag.stripped_strings)
            teasertext = re.sub(r"\s+", " ", raw_teaser).strip() or None

        # ---------- Ergebnis ----------
        articles.append(
            {
                "url": url,
                "titel": titel,
                "teasertext": teasertext,
                "autor": autor,
            }
        )

    return articles



if __name__ == "__main__":
    all_articles = []
    global_seen = set()

    for soup in make_soup(basepath):
        for art in parse_tagesschau(soup):
            if art["url"] not in global_seen:
                all_articles.append(art)
                global_seen.add(art["url"])
    
    print(all_articles)
    print(len(all_articles))
