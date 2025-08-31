import os
import fitz  # PyMuPDF
import hashlib
from huggingface_hub import InferenceClient

# Setup Hugging Face client
HF_TOKEN = os.environ.get("HF_TOKEN", "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")  # fallback to your token
client = InferenceClient(
    provider="novita",
    api_key=HF_TOKEN
)

# Simple tokenizer approximation
def estimate_token_count(text):
    return len(text.split())

def truncate_text_to_tokens(text, max_tokens):
    words = text.split()
    return " ".join(words[:max_tokens])

# Cache dictionary for already processed PDFs
_pdf_cache = {}

# Utility: Cache PDF parsing to avoid re-processing
def extract_pdf_text(file_path):
    file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
    if file_hash in _pdf_cache:
        return _pdf_cache[file_hash]
    with fitz.open(file_path) as doc:
        full_text = "\n".join([page.get_text() for page in doc])
    _pdf_cache[file_hash] = full_text
    return full_text

# Utility: Format nutrient data
def format_nutrition_data(product_info):
    return "\n".join(f"{k}: {v}" for k, v in product_info.items() if k != "Product")

# Prompt generator
def generate_prompt(age, weight, height, bmi, health_conditions, dietary_preferences, goal, product_info, diet_knowledge):
    age = age or "Unknown"
    weight = weight or "Unknown"
    height = height or "Unknown"
    bmi = bmi or "Unknown"
    health_conditions = health_conditions or "None"
    dietary_preferences = dietary_preferences or "None"
    goal = goal or "General health"
    nutrients = "\n".join([f"{k}: {v}" for k, v in product_info.get('nutriments', {}).items()])

    # Truncate PDF background knowledge for context safety
    truncated_diet_knowledge = truncate_text_to_tokens(diet_knowledge, 3000)

    prompt = f"""
You are a helpful and reliable AI nutrition assistant evaluating the suitability of a food product for a specific user based on evidence-based dietary principles and the user's personal profile.

USEFUL BACKGROUND DIETARY GUIDANCE:
------------------------------------
{truncated_diet_knowledge}

USER PROFILE:
- Age: {age}
- Weight: {weight} kg
- Height: {height} cm
- BMI: {bmi}
- Health Conditions: {health_conditions}
- Dietary Preferences: {dietary_preferences}
- Health Goal: {goal}

PRODUCT INFORMATION:
- Name: {product_info.get('product_name', 'Unknown')}
- Nutri-Score: {product_info.get('nutriscore_grade', 'N/A')}
- Nutrients (per 100g):
{nutrients}

TASK:
Based on the user profile and product information, is this food product advisable for the user?

- Respond in this JSON format:
{{
  "advisability": "Yes" or "No",
  "summary": "A short and practical explanation in under 100 words, highlighting the key nutrients/ingredients relevant to the user's profile."
}}

- DO NOT reference the WHO or any external organizations explicitly.
- Use the dietary guidance above silently.
- Provide advice in a clear, helpful, and practical tone.
"""
    return prompt.strip()

# Main analysis function
def analyze_nutrition(age, weight, height, bmi, health_conditions, dietary_preferences, goal, product_info, pdf_path):
    if not isinstance(product_info, dict) or 'nutriments' not in product_info:
        return {"error": "Invalid product_info format"}

    if not os.path.exists(pdf_path):
        return {"error": "PDF file not found"}

    try:
        diet_knowledge = extract_pdf_text(pdf_path)
        prompt = generate_prompt(age, weight, height, bmi, health_conditions, dietary_preferences, goal, product_info, diet_knowledge)

        # Hugging Face Inference API call (chat_completion)
        response = client.chat_completion(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=[
                {"role": "system", "content": "You are a helpful AI nutrition assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )

        return response.choices[0].message["content"].strip()

    except Exception as e:
        return {"error": str(e)}
