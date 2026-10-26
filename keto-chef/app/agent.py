# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.cloud import firestore
from google.genai import types

MODEL = "gemini-3.8-flash"
FIRESTORE_PROJECT = "qwiklabs-gcp-04-6a1522768ff0"

db = firestore.Client(project=FIRESTORE_PROJECT)


def list_pantry_items() -> List[Dict[str, Any]]:
    """Retrieves all ingredients currently stored in the user's keto pantry.

    Returns:
        A list of dictionaries representing ingredients, each with name, quantity,
        category, net_carbs_per_serving, fat_g, protein_g, and notes.
    """
    pantry_ref = db.collection("pantry")
    docs = pantry_ref.stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        items.append(data)
    return items


def get_pantry_item(item_id: str) -> Dict[str, Any]:
    """Fetches details for a specific ingredient in the pantry by its ID or slug name.

    Args:
        item_id: The identifier or slug of the item (e.g. 'almond-flour', 'avocado-oil').

    Returns:
        A dictionary containing the ingredient details, or an error status if not found.
    """
    doc_ref = db.collection("pantry").document(item_id.strip().lower())
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # Fallback search by name if slug didn't match directly
    pantry_ref = db.collection("pantry")
    for d in pantry_ref.stream():
        data = d.to_dict()
        if data.get("name", "").lower() == item_id.strip().lower():
            data["id"] = d.id
            return data

    return {"error": f"Item '{item_id}' not found in pantry."}


def save_pantry_item(
    name: str,
    quantity: str,
    category: str,
    net_carbs_per_serving: float,
    fat_g: float = 0.0,
    protein_g: float = 0.0,
    serving_size: str = "1 serving",
    notes: str = "",
) -> Dict[str, Any]:
    """Adds or updates an ingredient in the user's keto pantry collection.

    Args:
        name: Common name of the ingredient (e.g., 'Heavy Cream', 'Chia Seeds').
        quantity: The quantity or amount on hand (e.g., '1 pint', '200 grams').
        category: Food category (e.g., 'Dairy & Fats', 'Baking', 'Produce', 'Protein').
        net_carbs_per_serving: Net carbs (in grams) per serving.
        fat_g: Fat (in grams) per serving.
        protein_g: Protein (in grams) per serving.
        serving_size: Serving size description.
        notes: Helpful keto notes or substitution tips.

    Returns:
        A dictionary confirming the saved item and its details.
    """
    slug = name.strip().lower().replace(" ", "-").replace("/", "-")
    item_data = {
        "id": slug,
        "name": name.strip(),
        "quantity": quantity.strip(),
        "category": category.strip(),
        "net_carbs_per_serving": float(net_carbs_per_serving),
        "fat_g": float(fat_g),
        "protein_g": float(protein_g),
        "serving_size": serving_size.strip(),
        "is_keto_staple": float(net_carbs_per_serving) <= 5.0,
        "notes": notes.strip(),
    }
    db.collection("pantry").document(slug).set(item_data, merge=True)
    return {"status": "success", "item": item_data}


def search_recipes_online(query: str) -> List[Dict[str, Any]]:
    """Searches a free public culinary database (TheMealDB) for real recipe inspirations.

    Args:
        query: Ingredient or meal keyword to look up (e.g. 'salmon', 'chicken', 'egg', 'beef').

    Returns:
        A list of up to 5 matching recipes containing meal name, category, instructions,
        thumbnail image URL, and a list of ingredients.
    """
    import json
    import urllib.parse
    import urllib.request

    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={encoded_query}"
    req = urllib.request.Request(url, headers={"User-Agent": "KetoChefAgent/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            meals = data.get("meals") or []
            results = []
            for m in meals[:5]:
                # Extract ingredients and measures
                ingredients = []
                for i in range(1, 21):
                    ing = m.get(f"strIngredient{i}")
                    measure = m.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{measure.strip() if measure else ''} {ing.strip()}".strip())

                results.append({
                    "id": m.get("idMeal"),
                    "name": m.get("strMeal"),
                    "category": m.get("strCategory"),
                    "cuisine": m.get("strArea"),
                    "instructions_snippet": (m.get("strInstructions") or "")[:300] + "...",
                    "image_url": m.get("strMealThumb"),
                    "ingredients": ingredients,
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch recipes: {str(e)}"}]


def calculate_keto_macros(fat_g: float, protein_g: float, net_carbs_g: float) -> Dict[str, Any]:
    """Calculates ketogenic caloric breakdown, energy ratios, and keto adherence grade.

    Args:
        fat_g: Total fat in grams.
        protein_g: Total protein in grams.
        net_carbs_g: Total net carbohydrates in grams.

    Returns:
        A dictionary with total calories, percentage breakdown for each macro,
        ketogenic ratio (Fat / (Protein + Carbs)), and a keto verdict.
    """
    fat_cals = float(fat_g) * 9.0
    protein_cals = float(protein_g) * 4.0
    carb_cals = float(net_carbs_g) * 4.0
    total_cals = fat_cals + protein_cals + carb_cals

    if total_cals <= 0:
        return {"error": "Total macronutrient calories must be greater than 0."}

    fat_pct = round((fat_cals / total_cals) * 100.0, 1)
    protein_pct = round((protein_cals / total_cals) * 100.0, 1)
    carb_pct = round((carb_cals / total_cals) * 100.0, 1)

    # Standard keto ratio: grams of fat / (grams of protein + grams of carbs)
    denom = (float(protein_g) + float(net_carbs_g))
    keto_ratio = round(float(fat_g) / denom, 2) if denom > 0 else float(fat_g)

    if fat_pct >= 70.0 and carb_pct <= 10.0:
        verdict = "Strict Keto Optimal (High healthy fat, ultra-low carb)"
    elif fat_pct >= 60.0 and carb_pct <= 15.0:
        verdict = "Moderate Keto / Low Carb Friendly"
    elif carb_pct <= 20.0:
        verdict = "Liberal Low Carb (Watch serving size to maintain ketosis)"
    else:
        verdict = "Non-Keto (Carbohydrate proportion too high)"

    return {
        "total_calories": round(total_cals, 1),
        "fat_percentage": f"{fat_pct}%",
        "protein_percentage": f"{protein_pct}%",
        "net_carbs_percentage": f"{carb_pct}%",
        "ketogenic_ratio": keto_ratio,
        "verdict": verdict,
    }


def search_nearby_places(query: str, place_type: str = "restaurant") -> List[Dict[str, Any]]:
    """Finds restaurants, grocery stores, or dining spots matching a natural query (e.g. 'Austin TX', 'Times Square NY', 'near me').

    Uses Google Places API (New) Text Search so no coordinates or geocoding step are required.

    Args:
        query: Location or search area (e.g., 'Austin, TX', 'Downtown Seattle', 'Brooklyn NY').
        place_type: Type of place to search for (e.g., 'restaurant', 'grocery store', 'steakhouse').

    Returns:
        A list of matching places with name, formatted address, and coordinates.
    """
    import os
    import urllib.request
    import json

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY is not set in environment."}]

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    
    text_query = f"{place_type} in {query.strip()}" if query.strip() else place_type
    payload = {
        "textQuery": text_query,
        "maxResultCount": 5,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            places = data.get("places") or []
            results = []
            for p in places:
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress"),
                    "location": p.get("location"),
                })
            return results
    except Exception as e:
        return [{"error": f"Places text search failed: {str(e)}"}]



from google.adk.tools import ToolContext
from google.cloud import storage

ASSETS_BUCKET_NAME = "keto-chef-assets-qwiklabs-gcp-04-6a1522768ff0"


def generate_dish_image(dish_name: str, visual_description: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Generates a photorealistic culinary image for a keto recipe or dish using gemini-3.1-flash-lite-image in the global region.

    Saves the image into the agent's artifacts so it appears in the playground,
    and uploads the image bytes to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        dish_name: Name of the dish (e.g. 'Crispy Garlic Butter Salmon with Cauliflower Rice').
        visual_description: Detailed visual description of the plated dish and presentation.

    Returns:
        A dictionary containing status, dish_name, public_image_url, and artifact_filename.
    """
    import uuid
    from google import genai
    from google.genai.types import GenerateContentConfig, Modality

    # Initialize Google GenAI client targeting Vertex AI in global region
    image_client = genai.Client(
        vertexai=True,
        project=FIRESTORE_PROJECT,
        location="global",
    )

    prompt = (
        f"A professional, photorealistic food photography shot of a gourmet keto dish: {dish_name}. "
        f"{visual_description}. Perfectly plated on fine tableware, natural restaurant lighting, vibrant appetizing details, 4k food styling."
    )

    try:
        response = image_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=GenerateContentConfig(
                response_modalities=[Modality.TEXT, Modality.IMAGE],
            ),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

        if not image_bytes:
            return {"error": "Image generation completed but no image bytes were returned."}

        ext = "jpg" if "jpeg" in mime_type else "png"
        slug = dish_name.strip().lower().replace(" ", "-").replace("/", "-")[:30]
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{slug}-{unique_id}.{ext}"

        # 1. Save artifact for the Agent Playground UI
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"dish_name": dish_name, "type": "recipe_image"},
        )

        # 2. Upload image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(ASSETS_BUCKET_NAME)
        blob = bucket.blob(f"dishes/{filename}")
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{ASSETS_BUCKET_NAME}/dishes/{filename}"

        return {
            "status": "success",
            "dish_name": dish_name,
            "artifact_filename": filename,
            "public_image_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate and upload dish image: {str(e)}"}


from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


async def generate_memories_callback(callback_context: CallbackContext):
    """Saves session events to Vertex AI Memory Bank for durable fact and preference extraction."""
    await callback_context.add_session_to_memory()
    return None


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

role_description = """You are Keto Chef & Pantry Concierge, an expert culinary assistant specialized in ketogenic cooking and nutrition.

You remember the user's personal profile (e.g., target weight, current weight, daily carb limit, allergies, dietary preferences) across conversations and automatically tailor all recommendations and meal plans to them.

Your responsibilities:
1. Recall and respect user preferences and profile details (e.g. weight goals, net carb targets, disliked foods) stored in your long-term memory.
2. Help the user track, inspect, and update ingredients in their pantry using your tools (list_pantry_items, get_pantry_item, save_pantry_item).
3. Recommend delicious, strict keto recipes based on available pantry items.
4. When creating or presenting a customized keto recipe, generate a mouth-watering visual of the plated dish using generate_dish_image. Always include the resulting public image URL in the A2UI Image component!
5. If the user doesn't have the ingredients they need in their pantry to cook at home, or if they prefer to dine out or grab groceries:
   - Use search_nearby_places to discover restaurants, grocery stores, or supermarkets matching their area or city.
   - Recommend keto-friendly dining options or specific ordering tips to stay in ketosis (e.g., bunless burgers, grilled meats, salads with olive oil dressing).
6. Use search_recipes_online to search real recipes from the culinary database when the user asks for inspiration.
7. Use calculate_keto_macros to verify macro percentages and keto adherence.
8. Keep meals strictly low-carb (aiming for minimal net carbs, prioritizing healthy fats and moderate protein).
"""

workflow_description = "Analyze the keto request, execute any tools needed, and return structured A2UI UI when presenting recipes, dishes, meal recommendations, or places."

ui_description = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms. "
    "When presenting a dish or recipe, include one Image component whenever you have a public https "
    "URL for the image (for example the public_image_url returned by generate_dish_image). Set the Image url to that exact https link, for example "
    "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
    "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
    "not have a public URL, add a short Text line noting the image instead. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "When presenting dishes, output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

instruction = schema_manager.generate_system_prompt(
    role_description=role_description,
    workflow_description=workflow_description,
    ui_description=ui_description,
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_pantry_items,
        get_pantry_item,
        save_pantry_item,
        search_recipes_online,
        calculate_keto_macros,
        search_nearby_places,
        generate_dish_image,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)




