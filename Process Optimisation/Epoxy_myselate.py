try:
    import streamlit.net_util as _st_net_util
    _st_net_util.get_internal_ip = lambda: "localhost"
    _st_net_util.get_external_ip = lambda: "localhost"
except Exception:
    pass

import streamlit as st  # type: ignore # pyrefly: ignore [missing-import]
import pandas as pd
import uuid
import fitz  # type: ignore # pyrefly: ignore [missing-import]
import re
import requests
# from playwright.sync_api import sync_playwright # Removing playwright
from duckduckgo_search import DDGS  # type: ignore # pyrefly: ignore [missing-import]
import time
import json
import os
import time
import io
from typing import cast, Any

st.set_page_config(layout="wide")

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

from rdkit.Chem.rdChemReactions import ReactionFromSmarts  # type: ignore # pyrefly: ignore [missing-import]
from rdkit.Chem import Draw  # type: ignore # pyrefly: ignore [missing-import]

AZURE_ENDPOINT = "https://nihithreddydocumentintelligence.cognitiveservices.azure.com/"
AZURE_KEY = os.environ.get("AZURE_KEY", "")

GROQ_KEY = os.environ.get("GROQ_KEY", "")

client = Groq(api_key=GROQ_KEY)

st.title("🧪 Chemistry + ROS Optimization System")

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stages" not in st.session_state:
    st.session_state.stages = {}

if "ros_detailed_summary" not in st.session_state:
    st.session_state.ros_detailed_summary = ""

# =====================================================
# PROJECT MANAGEMENT (SAVE / LOAD)
# =====================================================
st.sidebar.header("💾 Project Management")
st.sidebar.write("Save your extracted text, summaries, and chat history to a file so you don't have to re-upload PDFs again.")

# Download logic
def get_project_data():
    stages_save = {}
    for k, v in st.session_state.get("stages", {}).items():
        stages_save[k] = {
            "ros_text": v.get("ros_text", ""),
            "bmr_text": v.get("bmr_text", ""),
            "reaction_text": v.get("reaction_text", ""),
            "last_uploaded_ros_file": v.get("last_uploaded_ros_file", None),
            "last_uploaded_bmr_file": v.get("last_uploaded_bmr_file", None)
        }
    return {
        "stages": stages_save,
        "ros_detailed_summary": st.session_state.get("ros_detailed_summary", ""),
        "messages": st.session_state.get("messages", [])
    }

json_data = json.dumps(get_project_data())
st.sidebar.download_button(
    label="⬇️ Save Analysis to JSON",
    data=json_data,
    file_name="Multi_Stage_Analysis_Project.json",
    mime="application/json"
)

st.sidebar.markdown("---")
uploaded_project = st.sidebar.file_uploader("Upload Saved Project (.json)", type=["json"])

if uploaded_project is not None:
    if st.sidebar.button("⬆️ Load Project Data"):
        data = json.load(uploaded_project)
        st.session_state.stages = data.get("stages", {})
        for stage_name in st.session_state.stages:
            if "ros_tables" not in st.session_state.stages[stage_name]:
                st.session_state.stages[stage_name]["ros_tables"] = []
        st.session_state.ros_detailed_summary = data.get("ros_detailed_summary", "")
        st.session_state.messages = data.get("messages", [])
        st.sidebar.success("✅ Project Loaded Successfully!")
        time.sleep(1)
        st.rerun()

# =====================================================
# DUCKDUCKGO SEARCH FUNCTION
# =====================================================
def search_web(query):
    """Searches DuckDuckGo for optimization evidence."""
    results = []
    try:
        with DDGS() as ddgs:
             # Use html backend to avoid rate limits
            search_gen = ddgs.text(query, max_results=3, backend="html")
            for r in search_gen:
                title = r.get('title', 'No Title')
                link = r.get('href', '')
                snippet = r.get('body', 'No Snippet')
                results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")
                
    except Exception as e:
        print(f"Search failed: {e}")
        return "Search failed or no results found."
    
    return "\n\n---\n".join(results)

# =====================================================
# PUBCHEM VALIDATION FUNCTION
# =====================================================
def get_pubchem_data(smiles):

    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/property/MolecularFormula,MolecularWeight/JSON"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()
            props = data["PropertyTable"]["Properties"][0]

            return {
                "Formula": props.get("MolecularFormula"),
                "MolWeight": props.get("MolecularWeight")
            }
    except:
        return None

    return None


def parse_pdf_page_with_doc_intelligence(doc_client: Any, page_bytes: bytes):
    """Analyzes a single PDF page using Azure Document Intelligence."""
    page_stream = io.BytesIO(page_bytes)
    poller = doc_client.begin_analyze_document("prebuilt-layout", body=page_stream)
    result_doc = poller.result()
    
    page_text = (getattr(result_doc, "content", "") or "") + "\n\n"
    extracted_dfs: list[pd.DataFrame] = []
    
    page_tables = getattr(result_doc, "tables", None) or []
    for table_item in page_tables:
        col_count = getattr(table_item, "column_count", 0)
        row_count = getattr(table_item, "row_count", 0)
        grid = [["" for _ in range(col_count)] for _ in range(row_count)]
        cells = getattr(table_item, "cells", []) or []
        for cell_item in cells:
            r_idx = getattr(cell_item, "row_index", 0)
            c_idx = getattr(cell_item, "column_index", 0)
            if r_idx < row_count and c_idx < col_count:
                grid[r_idx][c_idx] = getattr(cell_item, "content", "") or ""
        extracted_dfs.append(pd.DataFrame(grid))
        
    return page_text, extracted_dfs


def generate_search_query_from_llm(groq_client: Any, prompt_text: str) -> str:
    """Invokes LLM to generate search query from parameter prompt."""
    query_resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.3
    )
    if query_resp and query_resp.choices:
        msg = query_resp.choices[0].message
        raw_text = (getattr(msg, "content", "") or "").strip()
        return raw_text.replace('"', '')
    return ""


def extract_pdf_with_azure_helper(uploaded_file, name="Document"):
    doc_client = DocumentIntelligenceClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_KEY)
    )
    
    # Reset stream to beginning just in case
    uploaded_file.seek(0)
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    full_text = ""
    tables_list = []
    
    progress_bar = st.progress(0, text=f"Processing {name} page by page...")
    
    try:
        for i in range(len(pdf)):
            single = fitz.open()
            single.insert_pdf(pdf, from_page=i, to_page=i)
            page_bytes = single.tobytes()
            
            p_text, p_tables = parse_pdf_page_with_doc_intelligence(doc_client, page_bytes)
            full_text += p_text
            tables_list.extend(p_tables)
                
            progress_bar.progress((i + 1) / len(pdf), text=f"Processing {name} (Page {i+1} of {len(pdf)})...")
            
        st.success(f"✅ {name} OCR complete")
        return full_text, tables_list
        
    except Exception as e:
        st.error(f"❌ Error processing {name}: {str(e)}")
        return "", []

# =====================================================
# REACTION INPUT TARGET
# =====================================================
st.header("⚗️ Reaction & Documents")

num_stages = 2
for i in range(num_stages):
    stage_name = f"Stage {i+1}"
    if stage_name not in st.session_state.stages:
         st.session_state.stages[stage_name] = {
             "ros_text": "",
             "ros_tables": [],
             "last_uploaded_ros_file": None,
             "reaction_text": ""
         }
         
    with st.container():
        if i > 0:
            st.markdown("---")
        st.subheader(f"🔹 {stage_name} Configuration")
        col1, col2 = st.columns(2)
        with col1:
             default_type_idx = 5 if i == 0 else 0
             reaction_type = st.selectbox("Reaction Type", ["Salt Formation", "Diazotization", "Substitution", "Cyclization", "Oxidation", "Epoxidation"], index=default_type_idx, key=f"rxn_type_{i}")
             
             if i == 0:
                 default_reactants = "O=C(Cn1cncn1)c1ccc(F)cc1F"
             else:
                 default_reactants = "FC1=CC=C(C2(CO2)CN3C=NC=N3)C(F)=C1"
             reactant_smiles = st.text_input("Reactant SMILES", default_reactants, key=f"rect_smiles_{i}")
             
        with col2:
             if i == 0:
                 default_product = "FC1=CC=C(C2(CO2)CN3C=NC=N3)C(F)=C1"
                 default_reagents = "Trimethylsulfoxonium bromide, Cetyltrimethylammonium bromide, NaOH, Toluene"
             else:
                 default_product = "CS(=O)(=O)O.FC1=CC=C(C2(CO2)CN3C=NC=N3)C(F)=C1"
                 default_reagents = "Methanesulfonic acid, Ethyl acetate, IPA"
                 
             product_smiles = st.text_input("Product SMILES", default_product, key=f"prod_smiles_{i}")
             reagents_text = st.text_input("Reagents", default_reagents, key=f"reagents_{i}")

        st.subheader(f"🧬 Reaction Scheme ({stage_name})")

        try:
            rxn = ReactionFromSmarts(f"{reactant_smiles}>>{product_smiles}", useSmiles=True)
            st.image(Draw.ReactionToImage(rxn))
        except:
            if reactant_smiles or product_smiles:
                st.warning("Invalid SMILES")

        reaction_text = f"Stage: {stage_name}\nReaction type: {reaction_type}\nReactant SMILES: {reactant_smiles}\nProduct SMILES: {product_smiles}\nReagents: {reagents_text}"
        st.session_state.stages[stage_name]["reaction_text"] = reaction_text




    # =====================================================
    # SUMMARY
    # =====================================================

st.markdown("---")
st.subheader("📄 Upload Global Process Document (ROS)")
uploaded_ros_file = st.file_uploader("Upload ROS PDF (Applies to entire process)", type=["pdf"], key="global_ros_up")

if uploaded_ros_file:
    if "global_last_ros_file" not in st.session_state or st.session_state.global_last_ros_file != uploaded_ros_file.name:
        st.session_state.global_last_ros_file = uploaded_ros_file.name
        
        with st.spinner("Processing global document..."):
            global_text, global_tables = extract_pdf_with_azure_helper(uploaded_ros_file, "ROS Document")
            
            # Assign to all stages to keep chat/summary logic happy
            for sn in st.session_state.stages:
                st.session_state.stages[sn]["ros_text"] = global_text
                st.session_state.stages[sn]["ros_tables"] = global_tables
                st.session_state.stages[sn]["last_uploaded_ros_file"] = uploaded_ros_file.name

# Display tables/text once (using Stage 1's copy which is identical to the rest)
if st.session_state.stages.get("Stage 1", {}).get("ros_tables"):
     with st.expander("View Extracted Tables"):
          st.write("### ROS Tables")
          for idx, df in enumerate(st.session_state.stages["Stage 1"]["ros_tables"]):
              st.write(f"Table {idx+1}")
              st.dataframe(df)

if st.session_state.stages.get("Stage 1", {}).get("ros_text"):
     with st.expander("View Extracted Text"):
          st.write("### ROS Extracted Text")
          st.text(st.session_state.stages["Stage 1"]["ros_text"])

     clean = st.session_state.stages["Stage 1"]["ros_text"].replace("\n"," ")
     clean = re.sub(r"\s+"," ",clean).replace("–","-")
     
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
                     st.write(f"Theoretical Ratio: 1 : {ratio}")
                     st.write(f"Calculated Theoretical Yield: {theoretical_yield:.2f} kg")
                     st.write(f"**Final Yield:** {actual_yield_percentage:.2f}%")
                 elif direct_theo_match:
                     theo_out = float(direct_theo_match.group(1))
                     if theo_out > 0:
                         actual_yield_percentage = (b_out / theo_out) * 100
                         st.write(f"Theoretical Output: {theo_out} kg")
                         st.write(f"**Final Yield:** {actual_yield_percentage:.2f}%")
             except Exception as e:
                 st.write(f"Error calculating yield: {e}")
         else:
             theo = re.search(r"Theoretical[^0-9]*([\d\.]+)(?!\s*:)", clean,re.I)
             if theo: st.write(f"Theoretical output: {theo.group(1)}")
             yrange = re.search(r"Yield\s*Range[^0-9]*([\d\.]+)\s*-\s*([\d\.]+)", clean,re.I)
             if yrange: st.write(f"Yield range: {yrange.group(1)}–{yrange.group(2)}")
             actual = re.search(r"Actual[^0-9]*([\d\.]+)", clean,re.I)
             if actual: st.write(f"Actual output: {actual.group(1)}")
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


st.header("🤖 AI Analysis & Chat")

if st.button("Generate ROS Summary"):

    combined_prompt = f"""
    You are a pharma process expert.

    Task: Provide a comprehensive and exhaustive summary that integrates the process summary and reaction analysis for the given reaction route based on ROS (Process Write-up).
    **CRITICAL**: You must capture every single parameter (temperatures, pH, timings, molar equivalents, weights, volumes) and yield data without missing any point. This summary will be used as the sole memory for future yield optimization.
    
    Structure your answer as follows:
    1. **Reaction Scheme Analysis**:
       - Summarize the transformations and reaction types.
       - Assess the reagents and their specific roles (e.g., epoxidation, salt formation).
    2. **Process Summary (ROS)**:
       - Detailed summary of the intended ROS write-up.
    3. **Critical Parameters & Yields**:
       - Extract and list all critical process parameters exactly as written.
       - Report all yields (Theoretical, Actual, Percentage) mentioned in ROS.
    4. **Optimization & Risks**:
       - Suggest overall optimization opportunities to improve the process.
       - Identify potential safety or quality risks at the production scale.
    """

    for stage_name, data in st.session_state.stages.items():
        combined_prompt += f"\n\n=== Context ===\n"
        combined_prompt += f"Reaction Context:\n{data.get('reaction_text','')}\n"
        combined_prompt += f"ROS Content:\n{data.get('ros_text','')[:6000]}\n"

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":combined_prompt}],
            max_tokens=8192
        )
        
        summary = resp.choices[0].message.content
        st.write(summary)
        
        # Save as the detailed memory
        st.session_state.ros_detailed_summary = summary
        
        # Add to history
        st.session_state.messages.append({"role": "assistant", "content": "Initial multi-stage summary generated and saved to memory for reference."})
    
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
if prompt := st.chat_input("Ask about optimization, parameters, or the ROS process write-up..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Use the stored detailed summary if available, otherwise truncate raw BMR
        if st.session_state.ros_detailed_summary:
            process_context = st.session_state.ros_detailed_summary
        else:
            process_context = ""
            for k, v in st.session_state.stages.items():
                process_context += f"ROS: {v.get('ros_text','')[:2000]}\n"
                
        reaction_context = ""
        for k, v in st.session_state.stages.items():
            reaction_context += f"=== {k} ===\n{v.get('reaction_text','')}\n"
        
        # Determine if optimization/evidence is needed - Simple heuristic
        # If user asks for optimization, we trigger the 2-step process
        is_optimization_request = any(k in prompt.lower() for k in ["optim", "improve", "better yield", "suggest"])
        
        evidence_text = ""
        
        if is_optimization_request:
            status = st.status("🧠 Analyzing Process Write-up for optimization parameters...", expanded=True)
            
            # Step 1: Ask LLM for optimization parameters and search query
            param_prompt = f"""
            You are a pharma process expert. The user wants to optimize the reaction.
            
            Reactions Context: 
            {reaction_context}
            ROS Process Context: {process_context}
            User Question: {prompt}
            
            Task:
            1. Identify 2-3 critical process parameters that should be optimized across the stages (e.g., Temperature, pH, Catalyst Conc).
            2. Formulate a specific search query to find external evidence/patents for optimizing these specific reaction types and parameters. 
            
            Output ONLY the search query. Do not output anything else.
            """
            
            try:
                search_query = generate_search_query_from_llm(client, param_prompt)
                status.write(f"Generated Parameter Search Query: **{search_query}**")
                
                # Step 2: Search
                status.update(label="🔍 Searching external evidence...", state="running")
                evidence = search_web(search_query)
                evidence_text = f"\n\nEXTERNAL SEARCH EVIDENCE:\n{evidence}\n"
                
                status.write("Evidence gathered.")
                status.update(label="Analysis Complete", state="complete", expanded=False)
            
            except Exception as e:
                status.write(f"Optimization analysis failed: {e}")
                status.update(label="Optimization Skipped", state="error", expanded=False)

        
        # Step 3: Final Answer
        # Construct history for API
        history_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        
        system_prompt = f"""
        You are a pharma expert assisting with chemical process analysis and process optimization.
        
        Context:
        - Reaction Schemes: 
        {reaction_context}
        - Process Summary / Data: {process_context}
        
        Additional External Evidence:
        {evidence_text}
        
        Instructions:
        - Analyze the user's question in the context of both the specific chemical reactions (stoichiometry, mechanism) and the recorded ROS processes.
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
        
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except APIStatusError as e:
            st.error(f"API Limit Reached: {e}. Please wait a moment.")
        except Exception as e:
            st.error(f"Error: {e}")