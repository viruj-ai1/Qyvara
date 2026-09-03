from duckduckgo_search import DDGS

def search_duckduckgo(query):
    """Searches DuckDuckGo for optimization evidence."""
    results = []
    try:
        # Use DuckDuckGo Search
        print(f"Searching: {query}")
        with DDGS() as ddgs:
            # text search with html backend to avoid rate limits
            search_gen = ddgs.text(query, max_results=3, backend="html")
            
            for i, r in enumerate(search_gen):
                title = r.get('title', 'No Title')
                link = r.get('href', '')
                snippet = r.get('body', 'No Snippet')
                
                results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")
                
    except Exception as e:
        print(f"Search failed: {e}")
        results.append("Search failed or no results found.")
    
    return "\n\n---\n".join(results)

if __name__ == "__main__":
    query = "optimization of Diazotization reaction Fc1ccc(F)cc1C(=O)Cn2nccn2 yield"
    print(search_duckduckgo(query))
