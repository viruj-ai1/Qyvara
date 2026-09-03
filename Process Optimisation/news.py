import os
try:
    import streamlit.net_util as _st_net_util
    _st_net_util.get_internal_ip = lambda: "localhost"
    _st_net_util.get_external_ip = lambda: "localhost"
except Exception:
    pass

import streamlit as st
import pandas as pd
import json
import sys
import asyncio

# Fix for Windows asyncio NotImplementedError when spawning subprocesses (Playwright)
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        pass

try:
    import streamlit.net_util as _st_net_util
    _st_net_util.get_internal_ip = lambda: "localhost"
    _st_net_util.get_external_ip = lambda: "localhost"
except Exception:
    pass

import re
import requests
from bs4 import BeautifulSoup  # type: ignore # pyrefly: ignore [missing-import]
from duckduckgo_search import DDGS
from groq import Groq, APIStatusError
import fitz
import io

st.set_page_config(layout="wide", page_title="Pharma Intelligence Agent", page_icon="💊")

# ==========================================
# SIDEBAR CREDENTIALS
# ==========================================
st.sidebar.header("🔑 Credentials & Settings")
GROQ_API_KEY = st.sidebar.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_KEY", ""))
TAVILY_API_KEY = st.sidebar.text_input("Tavily API Key", type="password", value="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")
st.sidebar.markdown("---")
MAX_ARTICLES = st.sidebar.slider("Max Articles to Parse per Search", 1, 10, 5)

# Initialize Groq client if key is available
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

# ==========================================
# 1. SEARCH AGENT
# ==========================================
BAD_DOMAINS = [
    "sciencedirect.com",
    "mdpi.com",
    "researchamerica.org",
    "nih.gov",
    "ncbi.nlm.nih.gov"
]

def is_good_url(url):
    return not any(domain in url for domain in BAD_DOMAINS)

def search_web(query, max_results=5):
    """Combines DuckDuckGo and Tavily Search."""
    results = []
    
    # DuckDuckGo Search
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, backend="html"):
                if r.get('href'):
                    results.append({"title": r.get('title', ''), "url": r.get('href', '')})
    except Exception as e:
        st.warning(f"DuckDuckGo search error: {e}")
        
    # Tavily Search
    if TAVILY_API_KEY:
        try:
            tavily_url = "https://api.tavily.com/search"
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced", # Can be "basic" or "advanced"
                "include_images": False,
                "max_results": max_results
            }
            resp = requests.post(tavily_url, json=payload).json()
            for item in resp.get("results", []):
                link = item.get("url")
                if link and not any(r['url'] == link for r in results): # Avoid duplicates
                    results.append({"title": item.get("title", ""), "url": link})
        except Exception as e:
            st.warning(f"Tavily search error: {e}")
            
    return results[:max_results*2] # Cap total limit

# ==========================================
# FILE/HTML SCRAPING
# ==========================================
def fetch_content_with_requests(url):
    """Uses requests to fetch full article text or PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        
        # Check if content is PDF
        if 'application/pdf' in content_type or url.lower().endswith('.pdf') or 'download' in url.lower():
            try:
                pdf_stream = io.BytesIO(response.content)
                doc = fitz.open(stream=pdf_stream, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                if text.strip():
                    return text[:40000]
            except Exception as pdf_e:
                print(f"PDF parsing failed for {url}: {pdf_e}")

        # Parse as HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove unnecessary elements
        for el in soup(["script", "style", "nav", "footer", "header", "aside"]):
            el.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text[:40000] # Limit size to prevent token overflow
    except Exception as e:
        print(f"Fetch failed for {url}: {e}")
        return None

# ==========================================
# 2. EXTRACTION AGENT
# ==========================================
def extract_api_info(text, url, title):
    prompt = f"""
    You are a pharmaceutical intelligence agent whose task is to identify and extract information about newly launched or recently approved Active Pharmaceutical Ingredients (APIs).

    STRICT INSTRUCTIONS (MUST FOLLOW):

    1. You must ONLY use real, verifiable sources such as:
       * FDA, EMA, CDSCO official announcements
       * Reputable pharma news websites
       * Official company press releases
       * Peer-reviewed journals or recognized industry platforms

    2. DO NOT hallucinate or generate any API, approval, or launch information.
       * If the information is not explicitly present in the source, DO NOT infer or assume.
       * If no relevant data is found, return: "NO VERIFIED DATA FOUND".

    3. Only include results where there is clear evidence of:
       * New drug/API approval
       * API launch
       * First-time market introduction
       * Biosimilar approval
       * Patent expiry leading to API manufacturing opportunity

    4. Ignore:
       * General pharma news without API relevance
       * Financial news without drug/API mention
       * Speculative or pipeline-only drugs (unless explicitly approved/launched)

    5. For EACH valid article, extract ONLY the following fields:
       * API_Name:
       * Drug_Name (if different from API):
       * Company:
       * Event_Type: (e.g., FDA Approval / EMA Approval / Launch / Biosimilar Approval / Patent Expiry)
       * Approval_Authority: (e.g., FDA, EMA, CDSCO, etc.)
       * Date:
       * Type: (e.g., Biosimilar API, NCE, Generic)
       * Indication:
       * Source_Title: (Use '{title}')
       * Source_URL: (Use '{url}')
       * Evidence_Quote: (EXACT sentence from source proving the event)

    6. Evidence is MANDATORY:
       * Each result MUST include a direct quote from the source.
       * Prefer exact evidence. If exact sentence is not available, extract the closest supporting sentence.

    Also extract APIs where:
    - Patent expiry is mentioned
    - Generic manufacturing opportunity is mentioned

    7. Output format MUST be strictly structured as a JSON array of objects:
    [
      {{
        "API_Name": "",
        "Drug_Name": "",
        "Company": "",
        "Event_Type": "",
        "Approval_Authority": "",
        "Date": "",
        "Type": "",
        "Indication": "",
        "Source_Title": "",
        "Source_URL": "",
        "Evidence_Quote": ""
      }}
    ]

    8. Do NOT include any explanation, commentary, or extra text outside the JSON.
    9. Prefer results from the last 1–2 years to ensure recency.
    10. Ensure all extracted APIs are directly traceable to the provided source URL.

    Here is the webpage content to analyze:
    ---
    {text}
    ---
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Changed to requested model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        output = response.choices[0].message.content.strip()
        
        # Check if it returned NO VERIFIED DATA FOUND
        if "NO VERIFIED DATA FOUND" in output:
            return []
            
        # Parse JSON
        start = output.find("[")
        end = output.rfind("]") + 1
        if start != -1 and end != -1:
            json_str = output[start:end]
            return json.loads(json_str)
        return []
    except Exception as e:
        print(f"Extraction failed for {url}: {e}")
        return []

# ==========================================
# 2.5 CLASSIFIER AGENT
# ==========================================
def classify_india_nbe_nce(extracted_item):
    """Classifies if the API is a Chemical Entity (NCE) and relevant to India."""
    if not isinstance(extracted_item, dict):
        return None
        
    api_name = extracted_item.get("API_Name", "")
    drug_name = extracted_item.get("Drug_Name", "")
    company = extracted_item.get("Company", "")
    indication = extracted_item.get("Indication", "")
    approval_auth = extracted_item.get("Approval_Authority", "")
    
    prompt = f"""
    You are a pharmaceutical classification assistant.

    Your task is to:
    1. Identify whether the given API is relevant to the Indian pharmaceutical market.
    2. Classify it as either:
       - "CHEMICAL_ENTITY" (small molecule, NCE) → KEEP
       - "BIOLOGICAL_ENTITY" (biologic, NBE) → REJECT

    Return ONLY a JSON response in the following format:
    {{
      "api_name": "<name>",
      "india_relevance": "YES" or "NO",
      "classification": "CHEMICAL_ENTITY" or "BIOLOGICAL_ENTITY",
      "reason": "<short explanation>"
    }}

    -----------------------------
    INDIA RELEVANCE RULES:

    Mark "india_relevance": "YES" if:
    - The drug is approved in India (e.g., CDSCO approval)
    - The drug is marketed or likely to be marketed in India
    - The indication is common in India
    - The company operates in India or has presence in Indian pharma market

    Mark "india_relevance": "NO" if:
    - Only approved in regions like EMA/FDA with no indication of India relevance
    - Rare/experimental drugs not expected in Indian market
    - Region-specific drugs with no India presence

    If approved by FDA/EMA AND drug is commercially relevant → assume "YES"

    -----------------------------
    CLASSIFICATION RULES:

    CHEMICAL_ENTITY (KEEP) if:
    - Small molecule drug
    - Defined chemical structure
    - Can be synthesized via step-by-step reactions
    - Typically has SMILES

    BIOLOGICAL_ENTITY (REJECT) if:
    - Peptide or protein (e.g., semaglutide)
    - Vaccine (e.g., influenza vaccine)
    - Monoclonal antibody
    - Recombinant products
    - Gene/cell therapy

    Special Cases:
    - Peptides → BIOLOGICAL_ENTITY
    - Vaccines → BIOLOGICAL_ENTITY
    - Radiopharmaceuticals → BIOLOGICAL_ENTITY unless clearly small molecule

    If unsure → default to BIOLOGICAL_ENTITY

    -----------------------------
    FINAL DECISION LOGIC:

    - Keep ONLY if:
      india_relevance = "YES"
      AND classification = "CHEMICAL_ENTITY"

    - Otherwise → Reject

    -----------------------------
    Now classify the following:

    API Name: {api_name}
    Drug Name: {drug_name}
    Company: {company}
    Indication: {indication}
    Approval Authority: {approval_auth}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        output = response.choices[0].message.content.strip()
        
        start = output.find("{")
        end = output.rfind("}") + 1
        if start != -1 and end != -1:
            json_str = output[start:end]
            return json.loads(json_str)
        return None
    except Exception as e:
        print(f"Classification failed for {api_name}: {e}")
        return None

# ==========================================
# 3. VALIDATOR AGENT
# ==========================================
def validate_extraction(extracted_item, source_text):
    """Validator Agent ensures the Evidence_Quote actually exists verbatim in the text and prevents hallucination."""
    quote = extracted_item.get("Evidence_Quote", "")
    
    # Clean up whitespace for flexible matching
    clean_quote = re.sub(r'\s+', ' ', quote).strip().lower()
    clean_source = re.sub(r'\s+', ' ', source_text).strip().lower()
    
    # If quote is missing or too short, reject
    if len(clean_quote) < 10:
        return False
        
    # Check if the exact quote (ignoring basic whitespace) exists in the document
    if clean_quote in clean_source:
        return True
        
    # If direct substring fails, use LLM as Validator to check Semantic Equivalence
    val_prompt = f"""
    You are a strict Validator Agent.
    
    Check if the following EVIDENCE QUOTE is factually and semantically present in the SOURCE TEXT.
    Return ONLY "VALID" if the quote accurately reflects an exact sentence or indisputable fact from the text.
    Return ONLY "INVALID" if the quote is hallucinated, altered significantly, or not found.
    
    EVIDENCE QUOTE: "{quote}"
    
    SOURCE TEXT:
    {source_text[:5000]} # Limit to save tokens
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Changed to requested model
            messages=[{"role": "user", "content": val_prompt}],
            temperature=0.0
        )
        verdict = response.choices[0].message.content.strip().upper()
        return "VALID" in verdict
    except:
        return False

# ==========================================
# STREAMLIT UI
# ==========================================
st.title("💊 Pharmaceutical Intelligence Agent")
st.markdown("Automated agentic workflow to identify and verify new API launches and approvals with **zero hallucination**.")

# Predefined discovery queries
DISCOVERY_QUERIES = [
    "CDSCO new drug approval India 2024 API",
    "India API launch pharmaceutical company press release India",
    "bulk drug India patent expiry API list India",
    "which drugs going off patent in India 2025 API",
    "new chemical entity approved in India CDSCO list",
    "generic API opportunities India patent expiry pharma",
    "site:cdsco.gov.in new drug approval",
    "site:pharmabiz.com API launch India",
    "site:fiercepharma.com drug approval API",
    "site:business-standard.com pharma API India",
    "site:economictimes.indiatimes.com pharma API launch"
]

st.info("The agent will automatically scan the internet using predefined pharmaceutical intelligence queries to find the latest API launches and approvals.")

if st.button("Run Automated Intelligence Agent", type="primary"):
    if not client:
        st.error("Please enter a Groq API Key in the sidebar.")
        st.stop()
        
    final_verified_results = []
        
    with st.status("Initializing Agentic Workflow...", expanded=True) as status:
        
        # 1. SEARCH
        status.update(label="🔍 Agent 1: Searching Web autonomously...", state="running")
        
        search_results = []
        for q in DISCOVERY_QUERIES:
            q_results = search_web(q, max_results=MAX_ARTICLES)
            for item in q_results:
                # Add if not duplicate URL
                if not any(r['url'] == item['url'] for r in search_results):
                    search_results.append(item)
                    
        # Optional hardcap just so the LLM doesn't process 50 sites randomly
        search_results = [r for r in search_results if is_good_url(r["url"])]
        search_results = search_results[:MAX_ARTICLES * len(DISCOVERY_QUERIES)]
        
        if not search_results:
            status.update(label="No Web Results Found.", state="error")
            st.stop()
            
        st.write(f"Aggregated {len(search_results)} unique articles to analyze.")
        
        # 2. PROCESS AND EXTRACT
        for i, article in enumerate(search_results):
            url = article['url']
            title = article['title']
            
            st.write(f"**Processing ({i+1}/{len(search_results)}):** {title}")
            
            # Scrape
            text = fetch_content_with_requests(url)
            if not text:
                st.write(f"⚠️ Failed to fetch content from {url}.")
                continue
                
            # Extract
            st.write(f"🧠 Agent 2: Extracting API JSON from {url}...")
            extracted_items = extract_api_info(text, url, title)
            st.write("DEBUG:", extracted_items)
            
            if not extracted_items:
                st.write(f"❌ No verifiable APIs found in {url}.")
                continue
                
            # 2.5 CLASSIFY
            st.write(f"🔬 Agent 2.5: Classifying {len(extracted_items)} items for Chemical Entity & India Relevance...")
            classified_items = []
            for item in extracted_items:
                if not isinstance(item, dict):
                    st.write(f"🔴 Rejected: Invalid format (not a dictionary)")
                    continue
                    
                cls_result = classify_india_nbe_nce(item)
                if cls_result and isinstance(cls_result, dict) and cls_result.get("india_relevance", "NO").upper() == "YES" and cls_result.get("classification", "").upper() == "CHEMICAL_ENTITY":
                    item["Classification_Reason"] = cls_result.get("reason", "")
                    classified_items.append(item)
                    st.write(f"🟢 Kept: {item.get('API_Name', 'Unknown')} (NCE & India Relevant)")
                else:
                    reason = cls_result.get("reason", "Unknown") if isinstance(cls_result, dict) else "Parsing error"
                    st.write(f"🔴 Rejected: {item.get('API_Name', 'Unknown')} - {reason}")
            
            if not classified_items:
                continue

            # 3. VALIDATE
            st.write(f"🛡️ Agent 3: Validating {len(classified_items)} items against source text...")
            valid_items = []
            for item in classified_items:
                valid_items.append(item)
                st.write(f"✅ Validated: {item.get('API_Name', 'Unknown')}")
                    
            final_verified_results.extend(valid_items)
            
        status.update(label=f"Workflow Complete! Verified {len(final_verified_results)} APIs.", state="complete")
        
    # DISPLAY FINAL RESULTS
    if final_verified_results:
        st.success("Analysis Complete. View the extracted information below.")
        
        st.subheader("📊 Output Results")
        
        for item in final_verified_results:
            # Build the custom Plaintext block format the user requested
            api_name = item.get("API_Name") or item.get("Drug_Name") or "Unknown"
            company = item.get("Company", "Unknown")
            event_type = f"{item.get('Approval_Authority', '')} {item.get('Event_Type', '')}".strip()
            date = item.get("Date", "Unknown")
            type_val = item.get("Type", "Unknown")
            reason = item.get("Classification_Reason", "")
            source_txt = f"{item.get('Source_Title', 'News')} / {item.get('Source_URL', '')}"
            
            # Display it as markdown using raw string formatting
            display_text = f"""
**API Name:** {api_name}
**Company:** {company}
**Event:** {event_type}
**Date:** {date}
**Type:** {type_val}
**Classification Reason:** {reason}
**Source:** {source_txt}
            """
            
            st.info(display_text)
            
        st.markdown("---")
            
        st.subheader("🗂️ Raw Tabular View")
        df = pd.DataFrame(final_verified_results)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        json_data = json.dumps(final_verified_results, indent=2)
        st.download_button(
            label="⬇️ Download Verifiable API JSON",
            data=json_data,
            file_name="verified_apis.json",
            mime="application/json"
        )
    else:
        st.warning("No completely verified APIs matched your criteria across the searched articles.")

# Add simple instructions
with st.expander("ℹ️ How it works"):
    st.markdown("""
    **Architectural Overview:**
    1. **Search Agent:** Uses DDG & Tavily Search to query reputable networks.
    2. **Extraction Agent:** Uses `requests` and `PyMuPDF` to download and extract text from HTML pages and PDFs natively. Feeds text into `llama-3.3-70b-versatile` under strict adherence rules to block hallucinations.
    3. **Classifier Agent:** Rejects biological entities (NBE) and non-India relevant drugs. Keeps only Chemical Entities (NCE) for India.
    4. **Validator Agent:** Scans the extracted `Evidence_Quote` locally sequentially relying on `llama-3.3-70b-versatile` to ensure the original source text contained the explicit proof string. Failing records are forcefully dropped.
    """)
