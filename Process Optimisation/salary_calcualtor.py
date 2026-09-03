import os
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables (from .env file if present)
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
app = FastAPI(title="Viruj Pharmaceuticals - Salary API")

# Define API routes FIRST, before mounting the static directory

@app.get("/api/employees")
def get_employees():
    """Fetch employee data from Supabase. Fallback to mock data if not connected."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table("finance_employees").select("*").execute()
            return response.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
    # --- FALLBACK MOCK DATA (Because Supabase is not connected yet) ---
    print("Warning: Supabase credentials not found. Using local mock data.")
    return [
        { "emp_id": "VIRUJ/RD/0008", "name_of_employee": "Srikanth Viswanathan", "designation": "Head - HR", "department": "HR & Administration", "bank": "HDFC Bank" },
        { "emp_id": "VIRUJ/RD/0007", "name_of_employee": "Guruprasad D", "designation": "Assistant Manager", "department": "Analytical R & D", "bank": "IDFC First Bank" },
        { "emp_id": "VIRUJ/RD/0012", "name_of_employee": "Padma Shada", "designation": "Housekeeping Maid", "department": "HR & Administration", "bank": "Kotak Mahindra Bank" },
        { "emp_id": "VIRUJ/RD/0031", "name_of_employee": "Jaipal Danam", "designation": "Lab Assistant", "department": "HR & Administration", "bank": "State Bank of India" },
        { "emp_id": "VIRUJ/RD/0050", "name_of_employee": "R Sandeep", "designation": "Executive", "department": "Analytical R & D", "bank": "IDFC First Bank" },
        { "emp_id": "VIRUJ/RD/0059", "name_of_employee": "Pradip Ashok Dubole", "designation": "Junior Chemist", "department": "Chemical R & D", "bank": "IDFC First Bank" },
        { "emp_id": "VIRUJ/RD/0064", "name_of_employee": "Ravi Lahu Dede", "designation": "Junior Analyst", "department": "Analytical R & D", "bank": "HDFC Bank" },
        { "emp_id": "VIRUJ/RD/0065", "name_of_employee": "Bagirthi Anila", "designation": "Junior Executive - DQA", "department": "Development - QA", "bank": "State Bank of India" }
    ]

# Mount the static frontend AFTER API routes
static_dir = pathlib.Path(__file__).parent / "static"
# Ensure the static directory exists, otherwise the mount will fail
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:
    @app.get("/")
    def root_fallback():
        return {"message": "Static folder missing. Please ensure static/index.html exists."}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Salary Calculator API Server...")
    print("Access the portal at: http://localhost:8000\n")
    uvicorn.run("salary_calcualtor:app", host="0.0.0.0", port=8000, reload=True)
