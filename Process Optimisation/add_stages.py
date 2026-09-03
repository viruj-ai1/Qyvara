import sys

file_path = r'c:\Users\HP\Desktop\Process Optimisation\Epoxy_myselate.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """st.header("⚗️ Reaction & Documents")

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

new_block = """st.header("⚗️ Reaction & Documents")

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
             reagents_text = st.text_input("Reagents", default_reagents, key=f"reagents_{i}")"""

# We need to indent everything that comes after new_block down to line ~366
# In string format, we can split by lines.
lines = text.splitlines()

# Find start and end of the area
start_idx = -1
for idx in range(len(lines)):
    if 'st.header("⚗️ Reaction & Documents")' in lines[idx]:
        start_idx = idx
        break

end_idx = -1
for idx in range(start_idx, len(lines)):
    if 'st.header("🤖 AI Analysis & Chat")' in lines[idx]:
        end_idx = idx
        break

# Extracted part
block_to_replace = "\n".join(lines[start_idx:start_idx+31]) # The old block is 28 lines long
lines_to_indent = []

found_try = False
indent_start_idx = -1
for idx in range(start_idx, end_idx):
    if 'st.subheader(f"🧬 Reaction Scheme' in lines[idx]:
        indent_start_idx = idx
        break

for idx in range(indent_start_idx, end_idx):
    if lines[idx].strip() == "":
        lines_to_indent.append("")
    else:
        lines_to_indent.append("    " + lines[idx])

# Reassemble
new_content = "\n".join(lines[:start_idx]) + "\n" + new_block + "\n\n" + "\n".join(lines_to_indent) + "\n\n" + "\n".join(lines[end_idx:])

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done")
