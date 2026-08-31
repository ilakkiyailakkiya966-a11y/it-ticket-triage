import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # reads the .env file and loads GROQ_API_KEY into the environment

# The API key is read from an environment variable, NOT typed directly in code.
# This keeps your secret key out of GitHub. We'll set this variable in the next step.
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VALID_CATEGORIES = ["Network", "Hardware", "Software", "Account", "Other"]
VALID_URGENCY = ["Low", "Medium", "High"]

def classify_ticket(title, description):
    """
    Sends the ticket text to Groq and asks it to return a category and urgency.
    Returns a dict like: {"category": "Network", "urgency": "Medium"}
    If anything goes wrong, returns safe defaults instead of crashing the app.
    """
    prompt = f"""You are an IT helpdesk triage assistant.

Read this support ticket and classify it.

Title: {title}
Description: {description}

Reply with ONLY a JSON object, nothing else, in this exact format:
{{"category": "one of {VALID_CATEGORIES}", "urgency": "one of {VALID_URGENCY}", "reasoning": "one short sentence explaining why"}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        raw_text = response.choices[0].message.content.strip()
        print(f"RAW AI RESPONSE: {raw_text}")  # temporary debug line

        # Sometimes models wrap JSON in ```json ... ``` — strip that off if present
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw_text)

        category = result.get("category", "Other")
        urgency = result.get("urgency", "Medium")
        reasoning = result.get("reasoning", "No reasoning provided.")

        # Safety check: make sure the AI didn't invent a category we don't support
        if category not in VALID_CATEGORIES:
            category = "Other"
        if urgency not in VALID_URGENCY:
            urgency = "Medium"

        return {"category": category, "urgency": urgency, "reasoning": reasoning}

    except Exception as e:
        print(f"AI classification failed: {e}")
        # If the AI call fails for any reason, don't crash — just return safe defaults
        return {"category": "Other", "urgency": "Medium", "reasoning": "AI classification unavailable."}
