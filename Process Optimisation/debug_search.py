from playwright.sync_api import sync_playwright
import time

def inspect_page(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            url = f"https://patents.google.com/?q={query}&num=3"
            print(f"Navigating to {url}")
            page.goto(url)
            
            # Wait for search-results container
            try:
                page.wait_for_selector("#results", timeout=10000)
                print("Found #results container")
            except:
                print("Could not find #results container")
            
            # Wait a bit more for children to populate
            time.sleep(5)
            
            # Get inner HTML of results
            results_el = page.query_selector("search-results")
            if results_el:
                print("Dumping search-results match...")
                # checking if we can find items inside
                items = results_el.query_selector_all("search-result-item")
                print(f"Items found inside search-results: {len(items)}")
                
                print("Inner HTML of search-results (first 1000 chars):")
                print(results_el.inner_html()[:1000])
            else:
                 print("search-results element not found via query_selector")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    inspect_page("test")
