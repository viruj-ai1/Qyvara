
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcExactMolWt

candidates = [
    # Attempt 1: N1-substituted 4-amino-1,2,4-triazole
    "Fc1ccc(F)cc1C(=O)Cn1cn(N)cn1", 
    # Attempt 2: Explicit single/double bonds (assuming 1H-form pattern)
    "Fc1ccc(F)cc1C(=O)Cn1cn(N)cn1", 
    # Attempt 3: 4-amino-1H-1,2,4-triazole attached at N1
    "Nc1ncnn1CC(=O)c2ccc(F)cc2F", # Try ordering differently
    # Attempt 4: Using [nH] equivalent for N-substitution
    "Fc1ccc(F)cc1C(=O)Cn1c[n+](N)cn1", # Cationic?
    # Attempt 5: 4-amino-4H-1,2,4-triazole backbone
    "Fc1ccc(F)cc1C(=O)Cn1cncn1.N", # Dot disconnected?
]

print(f"Testing {len(candidates)} candidates...")

def check(s):
    print(f"\nChecking: {s}")
    try:
        mol = Chem.MolFromSmiles(s)
        if mol:
            Chem.SanitizeMol(mol)
            f = Chem.rdMolDescriptors.CalcMolFormula(mol)
            mw = Chem.rdMolDescriptors.CalcExactMolWt(mol)
            print(f"  -> VALID. Formula: {f}, MW: {mw}")
            if "N4" in f and "F2" in f and "O" in f and mw > 230 and mw < 280:
                print("  -> *** MATCH CANDIDATE ***")
        else:
            print("  -> INVALID (MolFromSmiles returned None)")
    except Exception as e:
        print(f"  -> ERROR: {e}")

for s in candidates:
    check(s)

# Try identifying 4-amino-1,2,4-triazole properly
print("\nChecking 4-amino-1,2,4-triazole base:")
base = "Nn1cncn1" # 4-amino-4H-1,2,4-triazole
check(base)

# Re-construct reactant manually
# Phenacyl: Fc1ccc(F)cc1C(=O)C
# Triazole: n1cn(N)cn1
# Combined: Fc1ccc(F)cc1C(=O)Cn1cn(N)cn1

