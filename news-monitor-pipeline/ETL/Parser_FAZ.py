#--------------------------------------------------------------
#Parser für html-Dateien der Zeitung FAZ

#Parser geht ausgehend von basepath alle Unterordner durch und parsed jede Datei, die eine html-Datei ist
#Output ist eine Liste an dictionaries
#--------------------------------------------------------------

import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Iterator
from urllib.parse import urljoin

basepath = os.path.expanduser("~/newsdata/faz") #Basispfad festlegen von dem dann ausgegangen wird


def make_soup(basepath: str) -> Iterator[BeautifulSoup]:
    for root, _, files in os.walk(basepath): #geht alle Unterordner und Dateien ab, die in basepath sind
        for filename in tqdm(files, desc=f"Verarbeite Dateien in {root}"):
            if filename.endswith(".html"): # nur html Datein berücksichtigen
                snapshotPfad = os.path.join(root, filename) #fügt Dateinamen und Pfad zusammen
                with open(snapshotPfad, encoding= "utf-8") as file:
                    snapshot = file.read()
                yield BeautifulSoup(snapshot, "html.parser")



def parse_faz(soup: BeautifulSoup) -> list[dict]:
    BASE = "https://www.faz.net"
    #Leere Listen zu speichern
    articles = [] #für Artikel-Tabelle
    seen_urls = set() #für doppelte URL

    #FAZ ist jeder Artikel in einen Hauptartikel und zwei Unterartikel unterteilt
    for article_tag in soup.find_all("article"):
        #-----------------
        #Hauptartikel
        #-----------------
        a_tag = article_tag.select_one("a.js-tsr-Base_ContentLink")
        if not a_tag:
            continue
        href = a_tag.get("href")
        if not href:
            continue
        url = urljoin(BASE, href)
        titel = a_tag.get("title") or None

        div_tag = article_tag.find("div", class_="tsr-Base_Content")
        if not div_tag:
            continue
        teasertext = div_tag.get_text(strip=True)

        footer_tag =article_tag.find("footer", class_="tsr-Base_ContentMeta")
        author_li = footer_tag.select_one('li[rel="author"], li.tsr-Base_ContentMetaItem-author') if footer_tag else None
        author = author_li.get_text(strip=True) if author_li else None
        #time_tag = footer_tag.find("time") if footer_tag else None
        #datum = time_tag.get("datetime") if time_tag and time_tag.has_attr("datetime") else None

        #Speichern der einzigartigen Artikel
        if url not in seen_urls:
            article = {"url": url, "titel": titel, "autor": author, "teasertext": teasertext} #dictionary füllen mit geparsten Daten
            articles.append(article) #dictionaries in Liste speichern
            seen_urls.add(url)
                
        #-----------------
        #Nebenartikel
        #-----------------
        ul_tag = article_tag.find("ul", class_="js-tsr-Base_ListShortLinks")
        if ul_tag:
            for link in ul_tag.find_all("a"):
                href = link.get("href")
                if not href:
                    continue
                url = urljoin(BASE, href)
                titel = link.get("title") or link.get_text(strip=True)

                #Speichern der einzigartigen Artikel
                if url not in seen_urls:
                    article = {"url": url, "titel": titel, "autor": None, "teasertext": None} #dictionary füllen mit geparsten Daten
                    articles.append(article) #dictionaries in Liste speichern
                    seen_urls.add(url)
    
    return articles


if __name__ == "__main__":
    all_articles = []
    global_seen = set()

    for soup in make_soup(basepath):
        for art in parse_faz(soup):
            if art["url"] not in global_seen:
                all_articles.append(art)
                global_seen.add(art["url"])
    
    print(all_articles[:3])
    print(len(all_articles))
