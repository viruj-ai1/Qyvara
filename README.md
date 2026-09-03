# Chemistry + BMR LLM System (Process Optimization)

An AI-powered Streamlit web application designed for analyzing Batch Manufacturing Records (BMR) and optimizing chemical processes. This tool leverages Large Language Models, OCR (Azure Document Intelligence), and RDKit to extract reaction parameters, calculate yields, and suggest optimization strategies.

## Features
- **PDF Data Extraction**: Upload BMR and ROS (Route of Synthesis) PDFs to automatically extract text and tabular data using Azure Document Intelligence.
- **Yield Calculation**: Automatically parses inputs, outputs, and theoretical ratios to compute and display batch yields.
- **Chemical Reactions**: Visualizes the reaction scheme (Reactant to Product) using RDKit based on SMILES strings.
- **AI-Driven Analysis**: Uses Groq (LLaMA 3.3 70B) to generate comprehensive process summaries highlighting deviations and critical parameters.
- **Optimization Expert Chat**: A built-in chatbot that can search for external patents and evidence to suggest yield improvements and analyze potential safety risks.
- **Session Management**: Save and load your entire analysis session (including extracted texts and chat history) to a JSON file.

## Setup & Installation

### Prerequisites
- Python 3.9+
- A valid Groq API Key
- A valid Azure Document Intelligence API Key and Endpoint

### Running Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/viruj-ai1/Process-Optimization.git
   cd Process-Optimization
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r "Process Optimisation/requirements.txt"
   ```
4. Start the application:
   ```bash
   streamlit run "Process Optimisation/app.py"
   ```

## Deployment
This application is recommended to be deployed on platforms that support long-lived WebSocket connections, such as **Render** or **Streamlit Community Cloud**.

### Deploying on Render
1. Create a new Web Service on [Render](https://render.com/).
2. Connect this GitHub repository.
3. Set the Build Command: `pip install -r "Process Optimisation/requirements.txt"`
4. Set the Start Command: `streamlit run "Process Optimisation/app.py" --server.port $PORT`
5. Add your API keys (`GROQ_KEY`, etc.) to the Environment Variables.

## Technologies Used
- Frontend & State Management: **Streamlit**
- OCR: **Azure Document Intelligence**
- LLM: **Groq (LLaMA)**
- Chemistry: **RDKit**, **PubChem API**
- Web Search: **DuckDuckGo Search**
