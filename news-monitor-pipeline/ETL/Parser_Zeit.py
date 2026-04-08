import os
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

class ZeitHtmlParser:
    def __init__(self, html_dir):
        self.html_dir = html_dir
        
    def parse_file(self, file_path):
        """Parse a single HTML file and extract important information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract data
                data = {
                    'filename': os.path.basename(file_path),
                    'date': self._extract_date_from_filename(file_path),
                    'articles': []
                }
                
                # Find all article sections
                articles = soup.find_all('article')
                
                for article in articles:
                    article_data = {
                        'title': self._get_text(article.find(class_='headline')),
                        'summary': self._get_text(article.find(class_='summary')),
                        'content': self._get_text(article.find(class_='article-body')),
                        'author': self._get_text(article.find(class_='author')),
                        'publication_date': self._get_text(article.find(class_='date')),
                        'url': self._get_url(article)
                    }
                    data['articles'].append(article_data)
                
                return data
            
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            return None
    
    def _get_text(self, element):
        """Safely extract text from an element"""
        return element.get_text(strip=True) if element else ''
    
    def _get_url(self, article):
        """Extract article URL"""
        link = article.find('a', href=True)
        return link['href'] if link else ''
    
    def _extract_date_from_filename(self, file_path):
        """Extract date from filename (zeit_YYYY-MM-DD_HH-MM-SS.html)"""
        filename = os.path.basename(file_path)
        match = re.search(r'zeit_(\d{4}-\d{2}-\d{2})_', filename)
        return match.group(1) if match else ''
    
    def process_directory(self, output_file='extracted_data.json'):
        """Process all HTML files in the directory and save results"""
        all_data = []
        
        # Walk through all files in directory
        for root, _, files in os.walk(self.html_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    print(f"Processing {file_path}...")
                    
                    data = self.parse_file(file_path)
                    if data:
                        all_data.append(data)
        
        # Save extracted data to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nExtracted data saved to {output_file}")
        print(f"Processed {len(all_data)} files successfully")

if __name__ == '__main__':
    # Example usage
    html_dir = '../archived_html/zeit'  # Adjust path as needed
    parser = ZeitHtmlParser(html_dir)
    parser.process_directory()
