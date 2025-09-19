from fastapi import APIRouter, UploadFile, File, Form
import uuid, os
from app.models import UploadResp
from PyPDF2 import PdfReader
from groq import Groq  # Import the Groq module (ensure it's installed)
import dotenv
import logging

dotenv.load_dotenv()  # Load environment variables from a .env file
router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the directory to store uploaded files and OCR results
STORE_DIR = "store"
OCR_DIR = "ocr_results"

# Ensure the directories exist
os.makedirs(STORE_DIR, exist_ok=True)
os.makedirs(OCR_DIR, exist_ok=True)

# Initialize the Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Replace with your actual API key

@router.post("/upload", response_model=UploadResp)
async def upload_file(
    file: UploadFile = File(...),  # Accept a single file
    doc_name: str = Form(...),    # Match the field name "doc_name"
    doc_type: str = Form("nda"),  # Match the field name "doc_type"
):
    uid = str(uuid.uuid4())
    # Generate a unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uid}_{file.filename}"
    file_path = os.path.join(STORE_DIR, unique_filename)

    # Ensure the store directory exists
    if not os.path.exists(STORE_DIR):
        os.makedirs(STORE_DIR)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Perform text extraction if the file is a PDF
    if file_extension.lower() == "pdf":
        extracted_text = extract_text_from_pdf(file_path)
        ocr_file_path = os.path.join(OCR_DIR, f"{uid}.txt")

        # Ensure the OCR directory exists
        if not os.path.exists(OCR_DIR):
            os.makedirs(OCR_DIR)

        with open(ocr_file_path, "w") as ocr_file:
            ocr_file.write(extracted_text)

        # Prepare the Groq prompt
        groq_prompt = prepare_groq_prompt(extracted_text)

        # Call the Groq LLM directly
        groq_response = call_groq_llm(groq_prompt, uid)
        print("Groq Response:", groq_response)
        return UploadResp(uid=uid, status="completed", message=groq_response)

    return UploadResp(uid=uid, status="failed", message="Unsupported file type")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text directly from a PDF file using PyPDF2 and remove extra empty lines.
    """
    extracted_text = ""
    try:
        # Read the PDF file
        reader = PdfReader(pdf_path)
        for page_number, page in enumerate(reader.pages, start=1):
            # Extract text from each page
            text = page.extract_text()
            extracted_text += f"{text}\n"

        # Remove extra empty lines
        lines = extracted_text.splitlines()
        cleaned_lines = []
        empty_line_count = 0

        for line in lines:
            if line.strip():  # Non-empty line
                cleaned_lines.append(line)
                empty_line_count = 0
            else:  # Empty line
                empty_line_count += 1
                if empty_line_count <= 1:  # Allow only one empty line
                    cleaned_lines.append(line)

        extracted_text = "\n".join(cleaned_lines)

    except Exception as e:
        extracted_text = f"Error during text extraction: {str(e)}"
    return extracted_text

def prepare_groq_prompt(extracted_text: str) -> str:
    """
    Prepare a prompt for the Groq LLM using the extracted text.

    Args:
        extracted_text (str): The text extracted from the PDF.

    Returns:
        str: The formatted prompt for the Groq LLM.
    """
    prompt = (
        "You are a clause extractor. "
        "The following text has been extracted from a legal document. "
        "Your task is to extract all the clauses from the document. "
        "DO NOT CHANGE ANY WORDS. Return the clauses exactly as they appear in the document.\n\n"
        f"Document Text:\n{extracted_text}\n\n"
        "Provide the extracted clauses in the following format:\n"
        "1. Clause one text...\n"
        "2. Clause two text...\n"
        "...\n\n"
        "IMPORTANT: Ensure each clause starts with a number followed by a period (e.g., '1.', '2.', etc.). "
        "Do not include any additional text or explanations."
    )
    return prompt

import re

def call_groq_llm(prompt: str, uid: str) -> str:
    """
    Call the Groq LLM using the chat completions API and save the response as individual clause files.

    Args:
        prompt (str): The prompt to send to the Groq LLM.
        uid (str): The unique identifier for the folder structure.

    Returns:
        str: A success message or an error message.
    """
    try:
        # Call the Groq LLM
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # or another Groq-supported model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512
        )

        logger.info("Full Groq Response: %s", response)

        # Extract the content from the response
        if response.choices and response.choices[0].message.content:
            raw_clauses = response.choices[0].message.content.strip()

            # Use regex to extract clauses starting with a number followed by a period
            clauses = re.findall(r"^\d+\.\s.*", raw_clauses, re.MULTILINE)
        else:
            return "No response from Groq LLM"

        # Create a folder for the clauses
        clause_dir = os.path.join(STORE_DIR, uid)
        os.makedirs(clause_dir, exist_ok=True)

        # Save each clause as a separate file
        for idx, clause in enumerate(clauses, start=1):
            clause_file = os.path.join(clause_dir, f"{idx}.txt")
            with open(clause_file, "w") as f:
                f.write(clause)

        return f"Clauses saved successfully in {clause_dir}"

    except Exception as e:
        logger.error("Error calling Groq LLM: %s", str(e))
        return f"Error calling Groq LLM: {str(e)}"
    