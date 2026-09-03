from playwright.sync_api import sync_playwright
import re

def scrape_urls(urls):
    """Scrapes clean text content from a list of URLs using Playwright."""
    scraped_data = []
    
    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for url in urls:
                try:
                    print(f"Visiting {url}...")
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    
                    # Extract meaningful text (headings + paragraphs)
                    content = page.eval_on_selector("body", """body => {
                        const formatting_tags = ['h1', 'h2', 'h3', 'p', 'li', 'article'];
                        let text = "";
                        formatting_tags.forEach(tag => {
                             const elements = body.querySelectorAll(tag);
                             elements.forEach(el => text += el.innerText + "\\n");
                        });
                        return text;
                    }""")
                    
                    # simple cleanup
                    clean_text = re.sub(r'\s+', ' ', content).strip()
                    if clean_text:
                        scraped_data.append(f"Source: {url}\nContent: {clean_text[:200]}...")
                        print(f"Successfully scraped {len(clean_text)} chars from {url}")
                        
                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")
            
            browser.close()
            
    except Exception as e:
        print(f"Playwright Error: {e}")
        
    return scraped_data

if __name__ == "__main__":
    results = scrape_urls(["https://example.com"])
    print("\nResults:")
    for r in results:
        print(r)
