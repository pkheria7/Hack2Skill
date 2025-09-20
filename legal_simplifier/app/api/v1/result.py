from fastapi import APIRouter, HTTPException
import os
from groq import Groq  # Ensure the Groq module is installed
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Define the directory to store uploaded files
STORE_DIR = "store"

# Initialize the Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Replace with your actual API key

@router.get("/result/{uid}")
async def get_result(uid: str):
    """
    Fetch all .txt files from the store/{uid} folder, send their content to the Groq LLM,
    and return an array of objects with the LLM responses.

    Args:
        uid (str): The unique identifier for the folder.

    Returns:
        list: A list of objects containing the LLM responses.
    """
    folder_path = os.path.join(STORE_DIR, uid)

    # Check if the folder exists
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Folder with UID {uid} not found")

    # Get all .txt files in the folder
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    if not txt_files:
        raise HTTPException(status_code=404, detail=f"No .txt files found in folder {uid}")

    responses = []

    try:
        for txt_file in sorted(txt_files):  # Sort files to process them in order
            file_path = os.path.join(folder_path, txt_file)

            # Read the content of the .txt file
            with open(file_path, "r") as f:
                content = f.read().strip()

            # Prepare the prompt for the Groq LLM
            prompt = prepare_groq_prompt(content)
            # logger.info("Sending prompt to Groq LLM: %s", prompt)

            # Send the content to the Groq LLM
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Replace with the appropriate model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=512
            )

            # logger.info("Groq LLM Response for %s: %s", txt_file, response)

            # Extract the LLM response content
            if response.choices and response.choices[0].message.content:
                llm_response = response.choices[0].message.content.strip()

                # Parse the LLM response JSON
                try:
                    llm_response_json = json.loads(llm_response)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Invalid JSON response from Groq LLM for file {txt_file}"
                    )

                # Add the original clause and file ID to the response
                llm_response_json["original_clause"] = content
                llm_response_json["id"] = txt_file

                responses.append(llm_response_json)
                time.sleep(0.5)  # To avoid hitting rate limits
            else:
                responses.append({
                    "id": txt_file,
                    "original_clause": content,
                    "error": "No response from Groq LLM"
                })

    except Exception as e:
        logger.error("Error processing files in folder %s: %s", uid, str(e))
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

    return responses

def prepare_groq_prompt(extracted_text: str) -> str:
    """
    Prepare a strict legal clause analysis prompt for the Groq LLM.

    Args:
        extracted_text (str): The text extracted from the PDF.

    Returns:
        str: The formatted prompt for the Groq LLM.
    """
    prompt = f"""
You are a strict, conservative clause analyst and legal reviewer. 
Treat the following text as a single clause extracted from a legal document and analyze it with high scrutiny.

Your job:
1. Classify the clause into one of three labels: "green", "yellow", or "red".
   - green → okay and poses no harm.
   - yellow → can cause limited harm or ambiguity; needs review and possible edits.
   - red → definitely poses significant harm or risk to the user; must be flagged.

2. Be conservative: whenever there is any meaningful ambiguity, broad/blanket language, unconstrained unilateral power, or potential for material loss, escalate to the higher-risk rating (i.e., prefer yellow over green, red over yellow). If uncertain, choose the worse rating.

3. Produce output in machine-readable JSON (no extra prose) following the schema below. Keep items concise.

Required JSON schema:
{{
  "rating": "red|yellow|green",
  "severity": integer,            # 1-10 scale (1=low, 10=high) indicating the level of risk/harm
  "detailed_rationale": "concise explanation (<= 200 words) pointing to specific risky language and how it creates harm",
  "risky_phrases": ["exact short quotes or key phrases from the clause that trigger concern"],
  "risk_types": ["Financial","Liability","Privacy","IP","Operational","Regulatory","Reputational","Performance","Other"],
  "confidence": "high|medium|low"
}}

Rules & evaluation cues (apply strictly):
- Red flags (usually -> rate red): unlimited or uncapped indemnity, unlimited liability, waiver of statutory rights, absolute/irrevocable assignment of IP without compensation, permanent/perpetual broad license to exploit user data/content, automatic renewals with penalty, unilateral amendment rights without notice/consent, mandatory broad data sharing or transfers without safeguards, mandatory arbitration + class action waiver (where relevant), criminal/excessive penalties, termination that leaves one party stranded, obligations requiring illegal acts.
- Yellow cues: ambiguous terms (e.g., "reasonable", "appropriate", "as necessary"), open-ended obligations, one-sided obligations without remedies, vague timelines, broad confidentiality carve-outs, lookback/retroactive charges, conditional language that materially affects rights.
- Green cues: plain, narrow, limited, reciprocal, time-bound, capped liability, clear termination and remedy paths, specific confidentiality scopes and data protection safeguards, narrowly scoped licenses.

Formatting & tone:
- Be crisp, factual, and strict. No flowery language.
- Do not give jurisdiction-specific legal advice; if you mention laws/regulations, label them as examples and add "verify with counsel for jurisdiction".
- Do not invent statutes or legal precedent.
- If clause is > 400 words, summarize and list the top 3 concerns only.

Example output (format exactly as JSON):
{{
  "rating": "red",
  "severity": 8,
  "detailed_rationale": "The clause requires assignment of all user-created IP 'without limitation' and includes an uncapped indemnity 'hold harmless' for any claims. This transfers valuable rights with no compensation or termination remedy, and exposes the user to unlimited financial liability. Narrow the IP scope, add compensation/consideration, and cap indemnity to negligent acts.",
  "risky_phrases": ["'assign all rights, title and interest'", "'without limitation'", "'indemnify and hold harmless'"],
  "risk_types": ["IP","Financial","Liability"],
  "confidence": "high"
}}

CLAUSE:
{extracted_text}
"""
    return prompt