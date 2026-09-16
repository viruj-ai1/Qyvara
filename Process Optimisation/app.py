import streamlit as st  # type: ignore # pyright: ignore [reportMissingImports]
import pandas as pd  # type: ignore # pyright: ignore [reportMissingImports]
import uuid
import fitz  # type: ignore # pyright: ignore [reportMissingImports]
import re
import requests  # type: ignore # pyright: ignore [reportMissingImports]
import time
import json
import os
import urllib.parse
from typing import Any, cast

try:
    from dotenv import load_dotenv  # type: ignore # pyright: ignore [reportMissingImports]
    load_dotenv()
except ImportError:
    pass

st.set_page_config(layout="wide", page_title="Chemistry + BMR LLM System", page_icon="🧪")

# =====================================================
# PRINTING OPTIMIZATION CSS
# =====================================================
# This CSS ensures that when the user presses Ctrl+P (Print),
# the entire scrollable chat history and page layout are expanded
# and printed fully without getting cut off.
st.markdown("""
<style>
@media print {
    /* Make the body, html, and main app container expand to full height */
    body, html, .stApp, .main, section[data-testid="stMain"] {
        height: auto !important;
        overflow: visible !important;
        position: static !important;
    }
    
    /* Control width and prevent horizontal cutoff for the main container */
    .block-container, section[data-testid="stMain"], .stApp {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin: 0 !important;
    }

    /* Force all divs and sections to show overflow (removes scrollbars) */
    div, section {
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
    }
    
    /* Ensure long words and text within chat messages wrap inside the container */
    * {
        word-break: break-word !important;
        word-wrap: break-word !important;
    }

    /* Ensure Markdown content wraps properly */
    [data-testid="stMarkdownContainer"] p, [data-testid="stChatMessage"] {
        white-space: pre-wrap !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Prevent images and tables from breaking the layout width */
    img, table, pre, code {
        max-width: 100% !important;
        overflow-x: hidden !important;
        white-space: pre-wrap !important;
    }

    /* Hide elements that shouldn't be printed (sidebar, header, inputs, buttons) */
    header, 
    [data-testid="stSidebar"], 
    [data-testid="stChatInput"], 
    button {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

from azure.ai.documentintelligence import DocumentIntelligenceClient  # type: ignore # pyrefly: ignore [missing-import]
from azure.core.credentials import AzureKeyCredential  # type: ignore # pyrefly: ignore [missing-import]

from groq import Groq, APIStatusError  # type: ignore

try:
    from rdkit import Chem  # type: ignore # pyright: ignore [reportMissingImports]
    from rdkit.Chem import Draw  # type: ignore # pyright: ignore [reportMissingImports]
    from rdkit.Chem.rdChemReactions import ReactionFromSmarts  # type: ignore # pyright: ignore [reportMissingImports]
    RDKIT_AVAILABLE = True
except Exception:
    Chem = None  # type: ignore
    Draw = None  # type: ignore
    ReactionFromSmarts = None  # type: ignore
    RDKIT_AVAILABLE = False

try:
    from duckduckgo_search import DDGS  # type: ignore # pyrefly: ignore [missing-import]
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Credentials setup helper
def get_credential(key_name: str, default: str = "") -> str:
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name])
    except Exception:
        pass
    return os.environ.get(key_name, default)

AZURE_ENDPOINT_ENV = get_credential("AZURE_ENDPOINT", "https://doc-inteligence-service.cognitiveservices.azure.com/")
AZURE_KEY_ENV = get_credential("AZURE_KEY", "")
GROQ_KEY_ENV = get_credential("GROQ_KEY", "") or get_credential("GROQ_API_KEY", "")

st.title("🧪 Chemistry + BMR LLM System")

# =====================================================
# SIDEBAR CREDENTIALS & PROJECT MANAGEMENT
# =====================================================
st.sidebar.header("🔑 API Credentials")
groq_key = st.sidebar.text_input("Groq API Key", value=GROQ_KEY_ENV, type="password", help="Enter your Groq API key")
azure_key = st.sidebar.text_input("Azure Doc Intel Key", value=AZURE_KEY_ENV, type="password", help="Enter your Azure Document Intelligence key")
azure_endpoint = st.sidebar.text_input("Azure Endpoint", value=AZURE_ENDPOINT_ENV, help="Enter your Azure Document Intelligence endpoint")

def get_groq_client():
    active_key = groq_key or GROQ_KEY_ENV
    if not active_key:
        st.sidebar.warning("⚠️ Groq API key missing. Please provide it in the sidebar.")
        return None
    try:
        return Groq(api_key=active_key)
    except Exception as e:
        st.sidebar.error(f"Error initializing Groq client: {e}")
        return None

st.sidebar.markdown("---")
st.sidebar.header("💾 Project Management")
st.sidebar.write("Save your extracted text, summaries, and chat history to a file so you don't have to re-upload PDFs again.")

# Download logic
def get_project_data():
    return {
        "ros_text": st.session_state.get("ros_text", ""),
        "bmr_text": st.session_state.get("bmr_text", ""),
        "bmr_detailed_summary": st.session_state.get("bmr_detailed_summary", ""),
        "messages": st.session_state.get("messages", [])
    }

json_data = json.dumps(get_project_data(), indent=2)
st.sidebar.download_button(
    label="⬇️ Save Analysis to JSON",
    data=json_data,
    file_name="Imeglimin_Analysis_Project.json",
    mime="application/json"
)

uploaded_project = st.sidebar.file_uploader("Upload Saved Project (.json)", type=["json"])

if uploaded_project is not None:
    if st.sidebar.button("⬆️ Load Project Data"):
        try:
            data = json.load(uploaded_project)
            st.session_state.ros_text = data.get("ros_text", "")
            st.session_state.bmr_text = data.get("bmr_text", "")
            st.session_state.bmr_detailed_summary = data.get("bmr_detailed_summary", "")
            st.session_state.messages = data.get("messages", [])
            st.sidebar.success("✅ Project Loaded Successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Failed to load project: {e}")

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "bmr_text" not in st.session_state:
    st.session_state.bmr_text = ""

if "bmr_tables" not in st.session_state:
    st.session_state.bmr_tables = []

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if "last_uploaded_ros_file" not in st.session_state:
    st.session_state.last_uploaded_ros_file = None

if "ros_text" not in st.session_state:
    st.session_state.ros_text = ""

if "ros_tables" not in st.session_state:
    st.session_state.ros_tables = []

if "bmr_detailed_summary" not in st.session_state:
    st.session_state.bmr_detailed_summary = ""

# =====================================================
# DUCKDUCKGO SEARCH FUNCTION
# =====================================================
def search_web(query: str) -> str:
    """Searches DuckDuckGo for optimization evidence."""
    if not DDGS_AVAILABLE:
        return "duckduckgo_search library is not installed."
    results = []
    try:
        with DDGS() as ddgs:
            search_gen = list(ddgs.text(query, max_results=3))
            for r in search_gen:
                title = r.get('title', 'No Title')
                link = r.get('href', '')
                snippet = r.get('body', 'No Snippet')
                results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")
    except Exception as e:
        return f"Search failed or no results found ({e})."
    
    return "\n\n---\n".join(results) if results else "No relevant search results found."

# =====================================================
# PUBCHEM VALIDATION FUNCTION
# =====================================================
def get_pubchem_data(smiles: str):
    if not smiles or not smiles.strip():
        return None
    try:
        encoded_smiles = urllib.parse.quote(smiles.strip())
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{encoded_smiles}/property/MolecularFormula,MolecularWeight/JSON"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()
            props = data["PropertyTable"]["Properties"][0]
            return {
                "Formula": props.get("MolecularFormula"),
                "MolWeight": props.get("MolecularWeight")
            }
    except Exception:
        return None

    return None

# =====================================================
# REACTION INPUT
# =====================================================
st.header("⚗️ Stage Reaction")

col1, col2 = st.columns(2)

with col1:
    stage = st.text_input("Stage", "02")
    reaction_type = st.selectbox(
        "Reaction Type",
        ["Salt Formation", "Diazotization", "Substitution", "Cyclization", "Oxidation"]
    )
    reactant_smiles = st.text_input(
        "Reactant SMILES",
        "C[C@@H]1N=C(NC(=N1)N(C)C)N.Cl"
    )

with col2:
    product_smiles = st.text_input(
        "Product SMILES",
        "C[C@@H]1N=C(NC(=N1)N(C)C)N.O=C(O)[C@H](O)[C@@H](O)C(=O)O"
    )
    reagents_text = st.text_input(
        "Reagents",
        "L(+) Tartaric acid, Triethylamine, Methanol, Water"
    )

st.subheader("🧬 Reaction Scheme")

if RDKIT_AVAILABLE and ReactionFromSmarts is not None and Draw is not None:
    try:
        rxn = ReactionFromSmarts(  # type: ignore # pyright: ignore
            f"{reactant_smiles}>>{product_smiles}",
            useSmiles=True
        )
        st.image(Draw.ReactionToImage(rxn))  # type: ignore # pyright: ignore
    except Exception as e:
        st.warning(f"Could not render reaction scheme for provided SMILES: {e}")
else:
    st.info("RDKit library not installed. Reaction scheme visualization unavailable.")

reaction_text = f"""
Stage: {stage}
Reaction type: {reaction_type}
Reactant SMILES: {reactant_smiles}
Product SMILES: {product_smiles}
Reagents: {reagents_text}
"""

# =====================================================
# PUBCHEM VALIDATION DISPLAY
# =====================================================
st.header("🧪 PubChem Validation")

reactant_info = get_pubchem_data(reactant_smiles)
product_info = get_pubchem_data(product_smiles)

vcol1, vcol2 = st.columns(2)
with vcol1:
    if reactant_info:
        st.write("### Reactant Validation")
        st.json(reactant_info)
    else:
        st.info("Reactant validation data unavailable.")

with vcol2:
    if product_info:
        st.write("### Product Validation")
        st.json(product_info)
    else:
        st.info("Product validation data unavailable.")

# =====================================================
# OCR / DOCUMENT UPLOAD
# =====================================================
st.header("📄 Upload Documents")

col_ros, col_bmr = st.columns(2)

with col_ros:
    st.subheader("Upload ROS / Process Write-up")
    uploaded_ros_file = st.file_uploader("Upload ROS PDF", type=["pdf"])

with col_bmr:
    st.subheader("Upload BMR PDF")
    uploaded_file = st.file_uploader("Upload BMR PDF", type=["pdf"])

def extract_pdf_with_azure(uploaded_file, file_state_key, text_state_key, table_state_key, name="Document"):
    active_azure_key = azure_key or AZURE_KEY_ENV
    active_azure_endpoint = azure_endpoint or AZURE_ENDPOINT_ENV

    if not active_azure_key:
        st.error(f"⚠️ Azure Key is missing. Please provide Azure Doc Intel Key in sidebar to perform OCR.")
        return

    if uploaded_file.name != st.session_state[file_state_key]:
        st.session_state[file_state_key] = uploaded_file.name
        st.session_state[text_state_key] = ""
        st.session_state[table_state_key] = []
        
        try:
            doc_client = DocumentIntelligenceClient(
                endpoint=active_azure_endpoint,
                credential=AzureKeyCredential(active_azure_key)
            )

            file_bytes = uploaded_file.getvalue()
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            
            full_text = ""
            progress_bar = st.progress(0, text=f"Processing {name}...")

            for i in range(len(pdf)):
                single = fitz.open()
                single.insert_pdf(pdf, from_page=i, to_page=i)
                page_bytes = single.tobytes()
                single.close()

                poller = doc_client.begin_analyze_document(
                    "prebuilt-layout",
                    body=page_bytes
                )

                result = poller.result()
                page_text = ""

                if result.tables:
                    for table in result.tables:
                        grid = [["" for _ in range(table.column_count)]
                                for _ in range(table.row_count)]

                        for cell in table.cells:
                            grid[cell.row_index][cell.column_index] = cell.content

                        df = pd.DataFrame(grid)
                        st.session_state[table_state_key].append(df)
                        page_text += df.to_string(index=False) + "\n"

                if result.paragraphs:
                    page_text += "\n".join(p.content for p in result.paragraphs)

                full_text += page_text + "\n"
                progress_bar.progress((i + 1) / len(pdf), text=f"Processing {name}...")
            
            pdf.close()
            st.session_state[text_state_key] = full_text
            st.success(f"✅ {name} OCR complete & Cached")
        except Exception as e:
            st.error(f"Error extracting {name} with Azure: {e}")
    else:
        st.info(f"Using cached {name} data.")

with col_ros:
    if uploaded_ros_file:
        extract_pdf_with_azure(uploaded_ros_file, "last_uploaded_ros_file", "ros_text", "ros_tables", "ROS")

with col_bmr:
    if uploaded_file:
        extract_pdf_with_azure(uploaded_file, "last_uploaded_file", "bmr_text", "bmr_tables", "BMR")

# Show extracted tables across main column width if present
if st.session_state.bmr_tables or st.session_state.ros_tables:
    with st.expander("View Extracted Tables"):
        if st.session_state.ros_tables:
            st.write("### ROS Tables")
            for i, df in enumerate(st.session_state.ros_tables):
                st.write(f"Table {i+1}")
                st.dataframe(df)
        if st.session_state.bmr_tables:
            st.write("### BMR Tables")
            for i, df in enumerate(st.session_state.bmr_tables):
                st.write(f"Table {i+1}")
                st.dataframe(df)

# Extract Yields (Quick Regex check across main body)
if st.session_state.bmr_text:
    clean = st.session_state.bmr_text.replace("\n", " ")
    clean = re.sub(r"\s+", " ", clean)
    clean = clean.replace("–", "-")

    if "yield" in clean.lower() or "batch output" in clean.lower():
        st.success("📌 Yield values extracted:")

        batch_input_match = re.search(r"Batch\s*input[^0-9]*([\d\.]+)", clean, re.I)
        batch_output_match = re.search(r"Batch\s*Output[^0-9]*([\d\.]+)", clean, re.I)
        ratio_match = re.search(r"Theoretical\s*output[^0-9]*1\s*:\s*([\d\.]+)", clean, re.I)
        direct_theo_match = re.search(r"Theoretical\s*output[^0-9]*([\d\.]+)(?!\s*:)", clean, re.I)

        if batch_input_match and batch_output_match:
            try:
                b_in = float(batch_input_match.group(1))
                b_out = float(batch_output_match.group(1))
                
                st.write(f"Batch Input: {b_in} kg")
                st.write(f"Batch Output: {b_out} kg")

                if ratio_match:
                    ratio = float(ratio_match.group(1))
                    theoretical_yield = b_in * ratio
                    actual_yield_percentage = (b_out / theoretical_yield) * 100
                    st.write(f"Theoretical Ratio (Mole Ratio): 1 : {ratio}")
                    st.write(f"Calculated Theoretical Yield: {theoretical_yield:.2f} kg")
                    st.write(f"**Final Yield:** {actual_yield_percentage:.2f}% (Calculated from Input/Output and Ratio)")
                elif direct_theo_match:
                    theo_out = float(direct_theo_match.group(1))
                    if theo_out > 0:
                        actual_yield_percentage = (b_out / theo_out) * 100
                        st.write(f"Theoretical Output: {theo_out} kg")
                        st.write(f"**Final Yield:** {actual_yield_percentage:.2f}% (Calculated from Actual/Theoretical)")
            except Exception as e:
                st.write(f"Error calculating yield from input/output: {e}")
        else:
            theo = re.search(r"Theoretical[^0-9]*([\d\.]+)(?!\s*:)", clean, re.I)
            if theo:
                st.write(f"Theoretical output: {theo.group(1)}")

            yrange = re.search(
                r"Yield\s*Range[^0-9]*([\d\.]+)\s*-\s*([\d\.]+)",
                clean, re.I
            )
            if yrange:
                st.write(f"Yield range: {yrange.group(1)}–{yrange.group(2)}")

            actual = re.search(r"Actual[^0-9]*([\d\.]+)", clean, re.I)
            if actual:
                st.write(f"Actual output: {actual.group(1)}")

            yield_match = re.search(r"Yield.{0,50}[:=]\s*(\d+(?:\.\d+)?)\s*%", clean, re.IGNORECASE)
            
            if yield_match:
                st.write(f"Final yield: {yield_match.group(1)}%")
            else:
                try:
                    if theo and actual:
                        t_val = float(theo.group(1))
                        a_val = float(actual.group(1))
                        if t_val > 0:
                            calc_yield = (a_val / t_val) * 100
                            st.write(f"Final yield: {calc_yield:.2f}% (Calculated)")
                except Exception:
                    pass

# =====================================================
# SUMMARY & AI ANALYSIS
# =====================================================
st.header("🤖 AI Analysis & Chat")

if st.button("Generate Initial Summary"):
    client = get_groq_client()
    if not client:
        st.error("Please provide a valid Groq API Key to generate summary.")
    else:
        short_bmr = st.session_state.bmr_text[:4000]
        short_ros = st.session_state.ros_text[:4000]

        prompt = f"""
        You are a pharma process expert.

        Task: Provide a comprehensive and exhaustive summary that integrates the process summary and reaction analysis. 
        **CRITICAL**: You must capture every single parameter (temperatures, pH, timings, molar equivalents, weights, volumes) and yield data without missing any point. This summary will be used as the sole memory for future yield optimization.
        
        Structure your answer as follows:
        1. **Reaction Scheme Analysis**:
           - Summarize the transformation (Reactant -> Product) and reaction type.
           - **CRITICAL**: Carefully analyze if the starting material is already a salt (e.g., Tartrate). If it is, explicitly state that the reaction involves a **Salt Break** step (e.g., using a base like NaOH to form the free base) followed by a **New Salt Formation** step (e.g., using an acid like HCl). Do not oversimplify it as a direct single-step salt formation.
           - Assess the reagents and their specific roles in each of these steps (e.g., NaOH for breaking the tartrate salt, HCl for forming the hydrochloride salt, solvents for recovery/crystallization).
           
        2. **ROS Process Summary (Write-up - LAB SCALE)**:
           - Summarize the intended chemical write-up and key parameters described in the ROS document.
           - **CRITICAL NOTE:** The ROS document is typically a Lab Scale or Master reference (e.g., based on 100g). Do not get confused by the absolute weight differences between the ROS and the BMR. Focus on understanding the *intended operational steps, temperatures, times, and molar ratios*.

        3. **Detailed BMR Process Summary (Actual execution - PRODUCTION SCALE)**:
           - Exhaustively summarize the reported batch manufacturing process steps from the BMR text. Include all specific values (e.g., temperatures, volumes, times).
           - **CRITICAL NOTE:** The BMR is a Production Scale execution (e.g., hundreds of kgs). 
           - Highlight key deviations from the ROS methodology (e.g., differing temperatures, extended cooling times, or different solvent ratios). Do not list the absolute scale-up of weights as a "deviation."
           
        4. **Critical Parameters & Yields**:
           - Extract and list all critical process parameters exactly as written.
           - Report all yields (Theoretical, Actual, Percentage). Note that the yield range might be provided in mole ratios (e.g. 1:1.59).
           
        5. **Optimization & Risks**:
           - Suggest optimization opportunities based on the reaction type and the actual BMR execution to improve overall yield. Look specifically at extended hold times, scale-up cooling inefficiencies, or solvent volumes.
           - Identify potential safety or quality risks at the production scale.

        Reaction Context:
        {reaction_text}
        
        ROS Content (Process Write-up):
        {short_ros}

        BMR Content (Actual Batch Record):
        {short_bmr}
        """

        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192
            )
            
            summary = resp.choices[0].message.content or ""
            st.markdown(summary)
            st.session_state.bmr_detailed_summary = summary
            st.session_state.messages.append({"role": "assistant", "content": "Initial comprehensive summary generated and saved to memory for reference."})
        
        except APIStatusError as e:
            st.error(f"API Error: {e}. Try reducing document size or waiting a minute.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# =====================================================
# CHAT INTERFACE
# =====================================================
st.subheader("💬 Chat with Process Expert")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask about optimization, parameters, or the BMR..."):
    client = get_groq_client()
    if not client:
        st.error("Please provide a valid Groq API Key in sidebar to chat.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            process_context = st.session_state.bmr_detailed_summary if st.session_state.bmr_detailed_summary else st.session_state.bmr_text[:4000]
            is_optimization_request = any(k in prompt.lower() for k in ["optim", "improve", "better yield", "suggest"])
            
            evidence_text = ""
            
            if is_optimization_request:
                status = st.status("🧠 Analyzing BMR for optimization parameters...", expanded=True)
                
                param_prompt = f"""
                You are a pharma process expert. The user wants to optimize the reaction.
                
                Reaction: {reaction_text}
                BMR Context: {process_context}
                User Question: {prompt}
                
                Task:
                1. Identify 2-3 critical process parameters that should be optimized (e.g., Temperature, pH, Catalyst Conc).
                2. Formulate a specific search query to find external evidence/patents for optimizing this specific reaction type and parameters. 
                
                Output ONLY the search query. Do not output anything else.
                """
                
                try:
                    query_resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": param_prompt}],
                        temperature=0.3
                    )
                    
                    raw_content = query_resp.choices[0].message.content or ""
                    search_query = raw_content.strip().replace('"', '')
                    status.write(f"Generated Parameter Search Query: **{search_query}**")
                    
                    status.update(label="🔍 Searching external evidence...", state="running")
                    evidence = search_web(search_query)
                    evidence_text = f"\n\nEXTERNAL SEARCH EVIDENCE:\n{evidence}\n"
                    
                    status.write("Evidence gathered.")
                    status.update(label="Analysis Complete", state="complete", expanded=False)
                
                except Exception as e:
                    status.write(f"Optimization analysis failed: {e}")
                    status.update(label="Optimization Skipped", state="error", expanded=False)

            history_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
            
            system_prompt = f"""
            You are a pharma expert assisting with BMR analysis and process optimization.
            
            Context:
            - Reaction Scheme: {reaction_text}
            - BMR Summary / Data: {process_context}
            
            Additional External Evidence:
            {evidence_text}
            
            Instructions:
            - Analyze the user's question in the context of both the specific chemical reaction (stoichiometry, mechanism) and the recorded BMR process.
            - If you found evidence, explicitly cite it (e.g., "According to [Title]...") to support your optimization suggestions.
            - If the evidence is not relevant, rely on general chemical principles but mention that specific search results were limited.
            """
            
            messages = [{"role": "system", "content": system_prompt}] + history_msgs
            
            try:
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=cast(Any, messages),
                    stream=True,
                    max_tokens=8192
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except APIStatusError as e:
                st.error(f"API Limit Reached: {e}. Please wait a moment.")
            except Exception as e:
                st.error(f"Error: {e}")