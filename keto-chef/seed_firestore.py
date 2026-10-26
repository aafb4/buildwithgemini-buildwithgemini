# Copyright 2026 Google LLC
# Seed script for Keto Chef & Pantry Concierge

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-6a1522768ff0"

db = firestore.Client(project=PROJECT_ID)

# Initial seed data for keto pantry ingredients
INITIAL_INGREDIENTS = [
    {
        "id": "almond-flour",
        "name": "Almond Flour",
        "category": "Baking",
        "quantity": "2 cups",
        "net_carbs_per_serving": 3.0,
        "serving_size": "1/4 cup (28g)",
        "fat_g": 14.0,
        "protein_g": 6.0,
        "is_keto_staple": True,
        "notes": "Great low-carb replacement for wheat flour"
    },
    {
        "id": "avocado-oil",
        "name": "Avocado Oil",
        "category": "Oils & Fats",
        "quantity": "500 ml",
        "net_carbs_per_serving": 0.0,
        "serving_size": "1 tbsp (15ml)",
        "fat_g": 14.0,
        "protein_g": 0.0,
        "is_keto_staple": True,
        "notes": "High smoke point, pure healthy monounsaturated fat"
    },
    {
        "id": "grass-fed-butter",
        "name": "Grass-fed Butter",
        "category": "Dairy & Fats",
        "quantity": "2 blocks (500g)",
        "net_carbs_per_serving": 0.1,
        "serving_size": "1 tbsp (14g)",
        "fat_g": 11.0,
        "protein_g": 0.1,
        "is_keto_staple": True,
        "notes": "Rich in CLA and fat-soluble vitamins"
    },
    {
        "id": "cauliflower-rice",
        "name": "Cauliflower Rice",
        "category": "Produce",
        "quantity": "3 bags (frozen)",
        "net_carbs_per_serving": 2.0,
        "serving_size": "1 cup (100g)",
        "fat_g": 0.3,
        "protein_g": 2.0,
        "is_keto_staple": True,
        "notes": "Direct substitute for grain rice"
    },
    {
        "id": "wild-salmon-fillets",
        "name": "Wild Salmon Fillets",
        "category": "Protein",
        "quantity": "4 fillets (600g)",
        "net_carbs_per_serving": 0.0,
        "serving_size": "1 fillet (150g)",
        "fat_g": 18.0,
        "protein_g": 34.0,
        "is_keto_staple": True,
        "notes": "High omega-3 fatty acids and clean protein"
    },
    {
        "id": "eggs-pasture-raised",
        "name": "Pasture-Raised Eggs",
        "category": "Dairy & Eggs",
        "quantity": "12 eggs",
        "net_carbs_per_serving": 0.6,
        "serving_size": "1 large egg",
        "fat_g": 5.0,
        "protein_g": 6.0,
        "is_keto_staple": True,
        "notes": "Perfect keto fat-to-protein ratio"
    }
]

def seed():
    print(f"Seeding pantry collection in Firestore project: {PROJECT_ID}...")
    batch = db.batch()
    for item in INITIAL_INGREDIENTS:
        doc_ref = db.collection("pantry").document(item["id"])
        batch.set(doc_ref, item)
    batch.commit()
    print(f"Successfully seeded {len(INITIAL_INGREDIENTS)} items into 'pantry' collection.")

if __name__ == "__main__":
    seed()
