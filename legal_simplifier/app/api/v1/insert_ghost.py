import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import groq
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = groq.Groq(api_key=groq_api_key)
groq_model = "llama-3-8b-8192"  # Replace with your preferred Groq model

# Define the router
router = APIRouter()

# Define the input model
class InsertGhostRequest(BaseModel):
    uid: str

# Prompt generation function
def generate_prompt(contract_text: str) -> str:
    """
    Generate a prompt for the Groq LLM to analyze missing clauses in a contract.
    """
    return (
        "You are a legal contract analyzer. Analyze the following text and identify clauses that are missing but "
        "should be present in a standard contract which can help the user not fall into trouble."
        "give at max 5 missing clauses only."
        "Make sure not to repeat any clause."
        "give only important clauses.When in doubt, leave it out."
        "Reply ONLY in a LIST OF JSON objects with the missing clauses.\n\n"
        f"Contract Text:\n{contract_text}"  # Limit the input to the first 6000 characters if needed
        "\n\nRespond in the following JSON format:\n"
        "[\n"
        "  {\n"
        "    \"clause_name\": \"Name of the missing clause\",\n"
        "    \"description\": \"Brief description of the clause\",\n"
        "    \"reason\": \"Reason why this clause is important\"\n"
        "  },\n"
        "  ...\n"
        "]\n"
        "IMPORTANT: Ensure the response is a valid JSON array. Do not include any text outside the JSON array. "
        "Do not include explanations, headers, or any other content."
    )

# Define the endpoint
@router.post("/insert-ghost")
async def insert_ghost(request: InsertGhostRequest):
    uid = request.uid
    ocr_result_folder = Path("ocr_results")
    file_path = ocr_result_folder / f"{uid}.txt"

    # Check if the file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {uid}.txt not found in ocr_result folder")

    # Read the content of the file
    with file_path.open("r") as file:
        text_content = file.read()

    # Generate the prompt
    prompt = generate_prompt(text_content)

    # Send the request to Groq LLM
    try:
        response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Replace with the appropriate model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512
            )
        logging.info(f"Groq LLM full response for {uid}: {response.choices[0].message.content}")
        result = json.loads(response.choices[0].message.content)
        logging.info(f"Groq LLM response for {uid}: {result}")
    except Exception as e:
        logging.error(f"Error communicating with Groq LLM: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error communicating with Groq LLM: {str(e)}")

    # Return the JSON response
    return {"uid": uid, "missing_clauses": result}