
from rdkit import Chem
from rdkit.Chem import Draw
from rdkit.Chem.rdChemReactions import ReactionFromSmarts
import sys

reactant = "Fc1ccc(F)cc1C(=O)Cn1c[n+](N)cn1"
product = "Fc1ccc(F)cc1C(=O)Cn2ncnc2"

print(f"Testing reaction visualization for:\n{reactant} >> {product}")

try:
    rxn = ReactionFromSmarts(f"{reactant}>>{product}", useSmiles=True)
    if rxn:
        img = Draw.ReactionToImage(rxn)
        print("Successfully generated reaction image.")
        # Optional: Save to verify manually if needed, but success here means app won't crash
        img.save("test_reaction.png")
    else:
        print("Failed to parse reaction.")
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
