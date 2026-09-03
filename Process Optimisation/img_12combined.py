import streamlit as st
import pandas as pd
import uuid
import fitz
import re
import requests
# from playwright.sync_api import sync_playwright # Removing playwright
from duckduckgo_search import DDGS
import time
import json
import os
from typing import Any, cast

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

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from groq import Groq, APIStatusError

from rdkit.Chem.rdChemReactions import ReactionFromSmarts
from rdkit.Chem import Draw

AZURE_ENDPOINT = "https://doc-inteligence-service.cognitiveservices.azure.com/"
AZURE_KEY = os.environ.get("AZURE_KEY", "")

GROQ_KEY = os.environ.get("GROQ_KEY", "")

client = Groq(api_key=GROQ_KEY)

st.title("🧪 Chemistry + BMR LLM System")

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stages" not in st.session_state:
    st.session_state.stages = {}

if "bmr_detailed_summary" not in st.session_state:
    st.session_state.bmr_detailed_summary = ""

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
        "bmr_detailed_summary": st.session_state.get("bmr_detailed_summary", ""),
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
            if "bmr_tables" not in st.session_state.stages[stage_name]:
                st.session_state.stages[stage_name]["bmr_tables"] = []
        st.session_state.bmr_detailed_summary = data.get("bmr_detailed_summary", "")
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
            
            poller = doc_client.begin_analyze_document("prebuilt-layout", body=page_bytes)
            result = poller.result()
            
            # The entire page sequentially parsed in correct reading order
            full_text += result.content + "\n\n"
            
            if result.tables:
                for table in result.tables:
                    grid = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]
                    for cell in table.cells:
                        if cell.row_index < table.row_count and cell.column_index < table.column_count:
                            grid[cell.row_index][cell.column_index] = cell.content
                    df = pd.DataFrame(grid)
                    tables_list.append(df)
                
            progress_bar.progress((i + 1) / len(pdf), text=f"Processing {name} (Page {i+1} of {len(pdf)})...")
            
        st.success(f"✅ {name} OCR complete")
        return full_text, tables_list
        
    except Exception as e:
        st.error(f"❌ Error processing {name}: {str(e)}")
        return "", []

# =====================================================
# REACTION INPUT MULTI-STAGE
# =====================================================
st.header("⚗️ Multi-Stage Reactions & Documents")
num_stages = st.number_input("Number of Stages", min_value=1, max_value=5, value=2)

for i in range(int(num_stages)):
    stage_name = f"Stage {i+1}"
    if stage_name not in st.session_state.stages:
         st.session_state.stages[stage_name] = {
             "ros_text": "",
             "bmr_text": "",
             "ros_tables": [],
             "bmr_tables": [],
             "last_uploaded_ros_file": None,
             "last_uploaded_bmr_file": None,
             "reaction_text": ""
         }
         
    with st.container():
        if i > 0:
            st.markdown("---")
        st.subheader(f"🔹 {stage_name} Configuration")
        col1, col2 = st.columns(2)
        with col1:
             default_type_idx = 3 if i==0 else 0 # 3 = Cyclization, 0 = Salt Formation
             reaction_type = st.selectbox("Reaction Type", ["Salt Formation", "Diazotization", "Substitution", "Cyclization", "Oxidation"], index=default_type_idx, key=f"rxn_type_{i}")
             
             if i == 0:
                 default_reactants = "CN(C)C(=N)NC(=N)N.Cl.CC1OC(C)OC(C)O1"
             elif i == 1:
                 # Racemic Imeglimin HCl + L(+) Tartaric Acid
                 default_reactants = "CC1N=C(NC(=N1)N(C)C)N.Cl.O=C(O)[C@H](O)[C@@H](O)C(=O)O"
             else:
                 default_reactants = ""
             reactant_smiles = st.text_input("Reactant SMILES", default_reactants, key=f"rect_smiles_{i}")
             
        with col2:
             if i == 0:
                 default_product = "CC1N=C(NC(=N1)N(C)C)N.Cl"
                 default_reagents = "PTSA, n-Butanol, Acetone"
             elif i == 1:
                 default_product = "C[C@@H]1N=C(NC(=N1)N(C)C)N.O=C(O)[C@H](O)[C@@H](O)C(=O)O"
                 default_reagents = "TEA, Methanol, Water"
             else:
                 default_product = ""
                 default_reagents = ""
                 
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
        
        # Moved Upload Documents immediately below the Reaction Scheme
        st.subheader("📄 Upload Documents")
        col_ros, col_bmr = st.columns(2)
        with col_ros:
            uploaded_ros_file = st.file_uploader(f"Upload ROS PDF", type=["pdf"], key=f"ros_up_{i}")
        with col_bmr:
            uploaded_file = st.file_uploader(f"Upload BMR PDF", type=["pdf"], key=f"bmr_up_{i}")
            
        st.subheader("🧪 PubChem Validation")
        reactant_info = get_pubchem_data(reactant_smiles)
        product_info = get_pubchem_data(product_smiles)

        if reactant_info:
            st.write("### Reactant Validation", reactant_info)
        if product_info:
            st.write("### Product Validation", product_info)
        if uploaded_ros_file:
            if uploaded_ros_file.name != st.session_state.stages[stage_name]["last_uploaded_ros_file"]:
                 st.session_state.stages[stage_name]["last_uploaded_ros_file"] = uploaded_ros_file.name
                 st.session_state.stages[stage_name]["ros_text"], st.session_state.stages[stage_name]["ros_tables"] = extract_pdf_with_azure_helper(uploaded_ros_file, f"ROS {stage_name}")
        
        if uploaded_file:
            if uploaded_file.name != st.session_state.stages[stage_name]["last_uploaded_bmr_file"]:
                 st.session_state.stages[stage_name]["last_uploaded_bmr_file"] = uploaded_file.name
                 st.session_state.stages[stage_name]["bmr_text"], st.session_state.stages[stage_name]["bmr_tables"] = extract_pdf_with_azure_helper(uploaded_file, f"BMR {stage_name}")
                 
        if st.session_state.stages[stage_name]["bmr_tables"] or st.session_state.stages[stage_name]["ros_tables"]:
             with st.expander(f"View Extracted Tables"):
                  if st.session_state.stages[stage_name]["ros_tables"]:
                      st.write("### ROS Tables")
                      for idx, df in enumerate(st.session_state.stages[stage_name]["ros_tables"]):
                          st.write(f"Table {idx+1}")
                          st.dataframe(df)
                  if st.session_state.stages[stage_name]["bmr_tables"]:
                      st.write("### BMR Tables")
                      for idx, df in enumerate(st.session_state.stages[stage_name]["bmr_tables"]):
                          st.write(f"Table {idx+1}")
                          st.dataframe(df)

        if st.session_state.stages[stage_name]["bmr_text"] or st.session_state.stages[stage_name]["ros_text"]:
             with st.expander(f"View Extracted Text"):
                  if st.session_state.stages[stage_name]["ros_text"]:
                      st.write("### ROS Extracted Text")
                      st.text(st.session_state.stages[stage_name]["ros_text"])
                  if st.session_state.stages[stage_name]["bmr_text"]:
                      st.write("### BMR Extracted Text")
                      st.text(st.session_state.stages[stage_name]["bmr_text"])

        clean = st.session_state.stages[stage_name]["bmr_text"].replace("\n"," ")
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


# =====================================================
# SUMMARY
# =====================================================
st.header("🤖 AI Analysis & Chat")

if st.button("Generate Multi-Stage Summary"):

    combined_prompt = f"""
    You are a pharma process expert.

    Task: Provide a comprehensive and exhaustive summary that integrates the process summary and reaction analysis across MULTIPLE STAGES.
    **CRITICAL**: You must capture every single parameter (temperatures, pH, timings, molar equivalents, weights, volumes) and yield data without missing any point. This summary will be used as the sole memory for future yield optimization.
    
    Structure your answer as follows:
    1. **Multi-Stage Reaction Scheme Analysis**:
       - Summarize the transformations across all stages and their reaction types.
       - Assess the reagents and their specific roles in each stage (e.g., salt breaks, new salt formations).
    2. **Stage-by-Stage Process Summary (ROS vs BMR)**:
       - Detailed summary of each stage's intended ROS write-up and actual BMR execution.
       - Highlight key deviations from the ROS methodology per stage.
    3. **Critical Parameters & Yields**:
       - Extract and list all critical process parameters exactly as written for all stages.
       - Report all yields (Theoretical, Actual, Percentage) per stage.
    4. **Optimization & Risks**:
       - Suggest overall optimization opportunities across the multi-stage process.
       - Identify potential safety or quality risks at the production scale.
    """

    for stage_name, data in st.session_state.stages.items():
        combined_prompt += f"\n\n=== {stage_name} ===\n"
        combined_prompt += f"Reaction Context:\n{data.get('reaction_text','')}\n"
        combined_prompt += f"ROS Content:\n{data.get('ros_text','')[:4000]}\n"
        combined_prompt += f"BMR Content:\n{data.get('bmr_text','')[:4000]}\n"

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":combined_prompt}],
            max_tokens=8192
        )
        
        summary = resp.choices[0].message.content
        st.write(summary)
        
        # Save as the detailed memory
        st.session_state.bmr_detailed_summary = summary
        
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
if prompt := st.chat_input("Ask about optimization, parameters, or the BMR..."):
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
        if st.session_state.bmr_detailed_summary:
            process_context = st.session_state.bmr_detailed_summary
        else:
            process_context = ""
            for k, v in st.session_state.stages.items():
                process_context += f"=== {k} ===\nBMR: {v.get('bmr_text','')[:2000]}\n"
                
        reaction_context = ""
        for k, v in st.session_state.stages.items():
            reaction_context += f"=== {k} ===\n{v.get('reaction_text','')}\n"
        
        # Determine if optimization/evidence is needed - Simple heuristic
        # If user asks for optimization, we trigger the 2-step process
        is_optimization_request = any(k in prompt.lower() for k in ["optim", "improve", "better yield", "suggest"])
        
        evidence_text = ""
        
        if is_optimization_request:
            status = st.status("🧠 Analyzing BMR for optimization parameters...", expanded=True)
            
            # Step 1: Ask LLM for optimization parameters and search query
            param_prompt = f"""
            You are a pharma process expert. The user wants to optimize the multi-stage reaction.
            
            Reactions Context: 
            {reaction_context}
            BMR Context: {process_context}
            User Question: {prompt}
            
            Task:
            1. Identify 2-3 critical process parameters that should be optimized across the stages (e.g., Temperature, pH, Catalyst Conc).
            2. Formulate a specific search query to find external evidence/patents for optimizing these specific reaction types and parameters. 
            
            Output ONLY the search query. Do not output anything else.
            """
            
            try:
                query_resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"user","content":param_prompt}],
                    temperature=0.3
                )
                
                raw_content = query_resp.choices[0].message.content or ""
                search_query = raw_content.strip().replace('"', '')
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
        You are a pharma expert assisting with multi-stage BMR analysis and process optimization.
        
        Context:
        - Reaction Schemes: 
        {reaction_context}
        - BMR Summary / Data: {process_context}
        
        Additional External Evidence:
        {evidence_text}
        
        Instructions:
        - Analyze the user's question in the context of both the specific chemical reactions (stoichiometry, mechanism) and the recorded BMR processes.
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