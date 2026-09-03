import sys

file_path = r'c:\Users\HP\Desktop\Process Optimisation\Epoxy myselate.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace titles and basic states
content = content.replace('st.title("🧪 Chemistry + BMR LLM System")', 'st.title("🧪 Chemistry + ROS Optimization System")')
content = content.replace('bmr_detailed_summary', 'ros_detailed_summary')

old_get_project_data = """def get_project_data():
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
    }"""

new_get_project_data = """def get_project_data():
    stages_save = {}
    for k, v in st.session_state.get("stages", {}).items():
        stages_save[k] = {
            "ros_text": v.get("ros_text", ""),
            "reaction_text": v.get("reaction_text", ""),
            "last_uploaded_ros_file": v.get("last_uploaded_ros_file", None)
        }
    return {
        "stages": stages_save,
        "ros_detailed_summary": st.session_state.get("ros_detailed_summary", ""),
        "messages": st.session_state.get("messages", [])
    }"""

content = content.replace(old_get_project_data, new_get_project_data)

old_load = """        for stage_name in st.session_state.stages:
            if "ros_tables" not in st.session_state.stages[stage_name]:
                st.session_state.stages[stage_name]["ros_tables"] = []
            if "bmr_tables" not in st.session_state.stages[stage_name]:
                st.session_state.stages[stage_name]["bmr_tables"] = []"""

new_load = """        for stage_name in st.session_state.stages:
            if "ros_tables" not in st.session_state.stages[stage_name]:
                st.session_state.stages[stage_name]["ros_tables"] = []"""

content = content.replace(old_load, new_load)

old_loop_start = """# =====================================================
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
             reagents_text = st.text_input("Reagents", default_reagents, key=f"reagents_{i}")"""

new_loop_start = """# =====================================================
# REACTION INPUT TARGET
# =====================================================
st.header("⚗️ Reaction & Documents")

stage_name = "Stage 1"
i = 0
if stage_name not in st.session_state.stages:
     st.session_state.stages[stage_name] = {
         "ros_text": "",
         "ros_tables": [],
         "last_uploaded_ros_file": None,
         "reaction_text": ""
     }
     
with st.container():
    st.subheader(f"🔹 Configuration")
    col1, col2 = st.columns(2)
    with col1:
         reaction_type = st.selectbox("Reaction Type", ["Salt Formation", "Diazotization", "Substitution", "Cyclization", "Oxidation", "Epoxidation"], index=5, key=f"rxn_type_{i}")
         
         default_reactants = "O=C(Cn1cncn1)c1ccc(F)cc1F"
         reactant_smiles = st.text_input("Reactant SMILES", default_reactants, key=f"rect_smiles_{i}")
         
    with col2:
         default_product = "CS(=O)(=O)O.FC1=CC=C(C2(CO2)CN3C=NC=N3)C(F)=C1"
         default_reagents = "Trimethylsulfoxonium bromide, Cetyltrimethylammonium bromide, NaOH, Toluene, Methanesulfonic acid, Ethyl acetate, IPA"
             
         product_smiles = st.text_input("Product SMILES", default_product, key=f"prod_smiles_{i}")
         reagents_text = st.text_input("Reagents", default_reagents, key=f"reagents_{i}")"""

content = content.replace(old_loop_start, new_loop_start)


# upload
old_upload = """        # Moved Upload Documents immediately below the Reaction Scheme
        st.subheader("📄 Upload Documents")
        col_ros, col_bmr = st.columns(2)
        with col_ros:
            uploaded_ros_file = st.file_uploader(f"Upload ROS PDF", type=["pdf"], key=f"ros_up_{i}")
        with col_bmr:
            uploaded_file = st.file_uploader(f"Upload BMR PDF", type=["pdf"], key=f"bmr_up_{i}")
            
        st.subheader("🧪 PubChem Validation")"""

new_upload = """        # Moved Upload Documents immediately below the Reaction Scheme
        st.subheader("📄 Upload Documents")
        uploaded_ros_file = st.file_uploader(f"Upload ROS PDF", type=["pdf"], key=f"ros_up_{i}")
            
        st.subheader("🧪 PubChem Validation")"""

content = content.replace(old_upload, new_upload)

old_processing = """        if uploaded_ros_file:
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

        clean = st.session_state.stages[stage_name]["bmr_text"].replace("\\n"," ")"""

new_processing = """        if uploaded_ros_file:
            if uploaded_ros_file.name != st.session_state.stages[stage_name]["last_uploaded_ros_file"]:
                 st.session_state.stages[stage_name]["last_uploaded_ros_file"] = uploaded_ros_file.name
                 st.session_state.stages[stage_name]["ros_text"], st.session_state.stages[stage_name]["ros_tables"] = extract_pdf_with_azure_helper(uploaded_ros_file, "ROS Document")
                 
        if st.session_state.stages[stage_name]["ros_tables"]:
             with st.expander("View Extracted Tables"):
                  st.write("### ROS Tables")
                  for idx, df in enumerate(st.session_state.stages[stage_name]["ros_tables"]):
                      st.write(f"Table {idx+1}")
                      st.dataframe(df)

        if st.session_state.stages[stage_name]["ros_text"]:
             with st.expander("View Extracted Text"):
                  st.write("### ROS Extracted Text")
                  st.text(st.session_state.stages[stage_name]["ros_text"])

        clean = st.session_state.stages[stage_name]["ros_text"].replace("\\n"," ")"""

content = content.replace(old_processing, new_processing)

old_combined_prompt = """    Task: Provide a comprehensive and exhaustive summary that integrates the process summary and reaction analysis across MULTIPLE STAGES.
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
       - Suggest overall optimization opportunities across the multi-stage process."""

new_combined_prompt = """    Task: Provide a comprehensive and exhaustive summary that integrates the process summary and reaction analysis for the given reaction route based on ROS (Process Write-up).
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
       - Suggest overall optimization opportunities to improve the process."""

content = content.replace(old_combined_prompt, new_combined_prompt)

old_comb_loop = """    for stage_name, data in st.session_state.stages.items():
        combined_prompt += f"\\n\\n=== {stage_name} ===\\n"
        combined_prompt += f"Reaction Context:\\n{data.get('reaction_text','')}\\n"
        combined_prompt += f"ROS Content:\\n{data.get('ros_text','')[:4000]}\\n"
        combined_prompt += f"BMR Content:\\n{data.get('bmr_text','')[:4000]}\\n\""""

new_comb_loop = """    for stage_name, data in st.session_state.stages.items():
        combined_prompt += f"\\n\\n=== Context ===\\n"
        combined_prompt += f"Reaction Context:\\n{data.get('reaction_text','')}\\n"
        combined_prompt += f"ROS Content:\\n{data.get('ros_text','')[:6000]}\\n\""""

content = content.replace(old_comb_loop.replace('bmr_text', 'ros_detailed_summary'), new_comb_loop) # It might have bmr_text from early stages, actually let's just do it cleanly

old_comb_loop_real = """    for stage_name, data in st.session_state.stages.items():
        combined_prompt += f"\\n\\n=== {stage_name} ===\\n"
        combined_prompt += f"Reaction Context:\\n{data.get('reaction_text','')}\\n"
        combined_prompt += f"ROS Content:\\n{data.get('ros_text','')[:4000]}\\n"
        combined_prompt += f"BMR Content:\\n{data.get('bmr_text','')[:4000]}\\n\""""
content = content.replace(old_comb_loop_real, new_comb_loop)

content = content.replace('if st.button("Generate Multi-Stage Summary"):', 'if st.button("Generate ROS Summary"):')

content = content.replace('bmr_detailed_summary', 'ros_detailed_summary') # One more pass just to be safe for remaining variables

old_chat_context = """        # Use the stored detailed summary if available, otherwise truncate raw BMR
        if st.session_state.ros_detailed_summary:
            process_context = st.session_state.ros_detailed_summary
        else:
            process_context = ""
            for k, v in st.session_state.stages.items():
                process_context += f"=== {k} ===\\nBMR: {v.get('ros_text','')[:2000]}\\n\""""
content = content.replace(old_chat_context, old_chat_context.replace('BMR: {v.get(\'ros_text\',', 'ROS: {v.get(\'ros_text\','))

old_chat_c2 = """        # Use the stored detailed summary if available, otherwise truncate raw BMR
        if st.session_state.ros_detailed_summary:
            process_context = st.session_state.ros_detailed_summary
        else:
            process_context = ""
            for k, v in st.session_state.stages.items():
                process_context += f"=== {k} ===\\nBMR: {v.get('bmr_text','')[:2000]}\\n" """

new_chat_c2 = """        # Use the stored detailed summary if available, otherwise truncate raw ROS
        if st.session_state.ros_detailed_summary:
            process_context = st.session_state.ros_detailed_summary
        else:
            process_context = ""
            for k, v in st.session_state.stages.items():
                process_context += f"ROS: {v.get('ros_text','')[:2000]}\\n\""""
content = content.replace(old_chat_c2, new_chat_c2)

content = content.replace('Ask about optimization, parameters, or the BMR', 'Ask about optimization, parameters, or the ROS process write-up')
content = content.replace('BMR Context:', 'ROS Process Context:')
content = content.replace('Analyzing BMR for optimization parameters...', 'Analyzing Process Write-up for optimization parameters...')
content = content.replace('BMR Summary / Data', 'Process Summary / Data')
content = content.replace('multi-stage BMR analysis', 'chemical process analysis')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
