
import json
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import argparse

def normalize_text(s: str) -> str:
    """Text cleaning and normalization"""

    if not s:
        return ""
    return " ".join(s.split()).strip()

def extract_meta(soup):
    """Extract meta tags"""
    meta = {}
    
    def get_meta(property_name, name=None):
        tag = soup.find("meta", {"property": property_name})
        if not tag and name:
            tag = soup.find("meta", {"name": name})
        return tag.get("content", "").strip() if tag and tag.has_attr("content") else None
    
    meta['title'] = get_meta("og:title", "title") or (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta['description'] = get_meta("og:description", "description") or ""
    meta['author'] = get_meta("article:author", "author") or ""
    meta['published_time'] = get_meta("article:published_time", "publish_date") or get_meta("og:published_time") or ""
    meta['url'] = get_meta("og:url") or ""
    meta['image'] = get_meta("og:image") or ""
    
    return meta

def extract_articles_from_html(soup):
    """
    Extract a list of articles from HTML.
    ZDFheute typically keeps articles in <article> tags with classes like 'news-teaser' or 'content-teaser'.
    """
    articles = []
    
    # Find <article> elements
    article_elements = soup.find_all("article", class_=lambda x: x and ("news-teaser" in x or "content-teaser" in x))
    
    for article_elem in article_elements:
        try:
            # Title: usually in <h2> or <h3> inside the article
            title = ""
            h2 = article_elem.find("h2")
            h3 = article_elem.find("h3")
            if h2:
                title = h2.get_text(strip=True)
            elif h3:
                title = h3.get_text(strip=True)
            
            if not title:
                # Fallback: take article text if no <h2>/<h3> found
                title = article_elem.get_text(separator=" ", strip=True)[:100]
            
            # Summary: usually in the first <p> or as a data attribute
            summary = ""
            p_tags = article_elem.find_all("p")
            if p_tags:
                summary = p_tags[0].get_text(strip=True)
            
            # URL: inside an <a> tag
            url = ""
            a_tag = article_elem.find("a", href=True)
            if a_tag:
                url = a_tag.get("href", "")
                if url.startswith("/"):
                    url = "https://www.zdf.de" + url
            
            # Image
            image = ""
            img_tag = article_elem.find("img")
            if img_tag:
                image = img_tag.get("src") or img_tag.get("data-src") or ""
            
            # If title not empty, append
            if normalize_text(title):
                articles.append({
                    "title": normalize_text(title),
                    "summary": normalize_text(summary),
                    "url": url,
                    "image": image,
                })
        except Exception as e:
            print(f"Error extracting article: {e}")
            continue
    
    return articles

def parse_file(filepath: Path):
    """Parse a single HTML file and extract information"""
    try:
        with filepath.open("rb") as f:
            raw = f.read()
        
        # Try to decode as UTF-8, fall back to latin1
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            html = raw.decode("latin1", errors="replace")
        
        soup = BeautifulSoup(html, "lxml")
        
        # Extract page-level metadata
        meta = extract_meta(soup)
        
        # Extract list of articles
        articles = extract_articles_from_html(soup)
        
        # Output structure
        result = {
            "source_file": str(filepath),
            "source_file_name": filepath.name,
            "page_title": meta.get("title", ""),
            "page_description": meta.get("description", ""),
            "page_url": meta.get("url", ""),
            "page_published_time": meta.get("published_time", ""),
            "articles_count": len(articles),
            "articles": articles
        }
        
        return result
    
    except Exception as e:
        print(f"Error parsing file {filepath}: {e}")
        return None

def parse_directory(dirpath: Path, output_file: Path):
    """Parse all HTML files in a directory"""
    # Find all HTML files
    html_files = list(dirpath.rglob("*.html"))
    
    if not html_files:
        print(f"No HTML files found in {dirpath}.")
        return
    
    print(f"Found: {len(html_files)} HTML files")
    
    all_results = []
    all_articles = []
    
    # Process each file
    for filepath in tqdm(html_files, desc="Parsing files"):
        result = parse_file(filepath)
        if result:
            all_results.append(result)
            all_articles.extend(result["articles"])
    
    # Final output structure
    final_output = {
        "metadata": {
            "total_files_parsed": len(all_results),
            "total_articles_extracted": len(all_articles),
            "output_file": str(output_file),
        },
        "files": all_results,
        "all_articles_summary": all_articles[:50]  # sample of first 50
    }
    
    # Save to JSON
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print(f"  - Files processed: {len(all_results)}")
    print(f"  - Articles extracted: {len(all_articles)}")

def main():
    parser = argparse.ArgumentParser(
        description="Parse ZDFheute HTML articles into JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_heute_articles.py /path/to/heute --out extracted_heute.json
  python parse_heute_articles.py ~/newsdata/heute --out result.json
        """
    )
    
    parser.add_argument("directory", help="Path to the directory containing HTML files")
    parser.add_argument("--out", default="extracted_heute.json", help="Output JSON file name (default: extracted_heute.json)")
    
    args = parser.parse_args()
    
    dirpath = Path(args.directory)
    if not dirpath.exists() or not dirpath.is_dir():
        print(f"Error: {dirpath} is not a valid directory.")
        sys.exit(1)
    
    output_file = Path(args.out)
    parse_directory(dirpath, output_file)

if __name__ == "__main__":
    main()
