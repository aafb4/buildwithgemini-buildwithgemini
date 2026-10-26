# My agent: Keto Chef & Pantry Concierge

One-liner: A conversational agent that helps keto dieters track pantry inventory, stay strictly in ketosis, and cook creative low-carb meals with a catalog of keto-friendly recipes and ingredients.

Tool coverage:
- Memory: Personal profile (e.g. weight, health/target goals), net carb targets (e.g. <20g/day), favorite keto staples, food allergies, past cooked dishes, fasting preferences
- Tools: Pantry ingredient lookup/updater, keto substitution finder (e.g., cauliflower rice for rice, almond flour for wheat), net carb lookup
- Catalog/UI: Keto recipe catalog with net carb / fat / protein breakdown tables and ingredient cards (rendered with A2UI)
- Image gen: Photorealistic plated photos of customized keto dishes
- Sandbox: Net carb and macronutrient ratio calculator (fat/protein/carb % energy splits)

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for macro/ketone index calculations, Firestore for persistent pantry tracking
