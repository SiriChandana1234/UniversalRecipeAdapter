import os
import json
from typing import List, Optional, Dict, Any 
from pydantic import BaseModel, Field
from google import genai

# --- CORE DATA STRUCTURES (PYDANTIC MODELS) ---

class Substitution(BaseModel):
    """Defines a single ingredient replacement."""
    original_ingredient: str = Field(description="The exact ingredient name to be replaced.")
    substitute: str = Field(description="The new ingredient for the target cuisine/diet.")
    reason: str = Field(description="A brief explanation for the swap (e.g., 'Dairy-free creamy base').")

class PlanningResult(BaseModel):
    """The complete structured output from the Planner Agent (the Session/Memory)."""
    # Using List[Any] to allow Pydantic to validate the mixed-type dictionary for the tool input
    conversion_list: List[Any] = Field(description="List of units to convert (e.g., {'amount': 2.0, 'unit': 'cups', 'to_unit': 'grams'}).")
    substitution_map: List[Substitution] = Field(description="The comprehensive list of ingredient swaps.")
    
    @staticmethod
    def mock_data():
        """Helper to provide mock data for testing without an API key."""
        return PlanningResult(
            substitution_map=[
                Substitution(original_ingredient="Beef chuck", substitute="Firm Tofu", reason="Vegetarian protein swap."),
                Substitution(original_ingredient="Sour cream", substitute="Full-fat Coconut Milk", reason="Dairy-free creamy base."),
            ],
            conversion_list=[
                {'amount': 2.0, 'unit': 'cups', 'to_unit': 'grams'}
            ]
        )

# --- MOCK CLIENT DEFINITIONS (For robust fallback) ---

class MockResponse:
    """Replicates the structure of the Google API response object."""
    def __init__(self, text: str, parsed: Optional[Any] = None):
        self.text = text
        self.parsed = parsed

class MockModels:
    """Replicates the client.models structure."""
    def generate_content(self, **kwargs):
        if 'response_schema' in kwargs.get('config', {}):
            return MockResponse(
                text="[MOCK OUTPUT: Structured Plan Generated]",
                parsed=PlanningResult.mock_data()
            )
        return MockResponse(text="[MOCK OUTPUT: Final Recipe Text]")

class MockClient:
    """Replicates the main client object structure."""
    def __init__(self):
        self.models = MockModels()

# --- AUTHENTICATION & CLIENT INITIALIZATION (GITHUB/Local FIX) ---

API_MODEL_NAME = "gemini-2.5-flash" 
CONCEPTUAL_MODEL_NAME = "AI_Reasoning_Engine_Flash"

# Get the API key from the standard environment variable
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    try:
        # Client initializes successfully because API_KEY is set in the environment
        client = genai.Client(api_key=API_KEY)
        print(f"✅ Gemini Client initialized successfully with API Key.")
    except Exception as e:
        client = MockClient()
        API_MODEL_NAME = "MOCK_MODEL"
        print(f"❌ API KEY VALIDATION ERROR. Client failed to initialize. Using Mock Mode. Details: {e}")
else:
    client = MockClient()
    API_MODEL_NAME = "MOCK_MODEL"
    print(f"⚠️ API Key not found in environment variable 'GEMINI_API_KEY'. Using Mock Mode.")


# ----------------------------------------------------
# 4. TOOLS
# ----------------------------------------------------

def unit_converter_tool(amount: float, unit: str) -> float:
    """TOOL: A function to convert common cooking units to a standard metric."""
    print(f"⚙️ TOOL ACTIVATED: Converting {amount} {unit}...")
    if unit.lower() in ["cups", "cup"]:
        return amount * 120.0  
    return amount

# ----------------------------------------------------
# 5. AGENT EXECUTION UTILITY
# ----------------------------------------------------

def run_agent(agent_name: str, system_prompt: str, prompt: str, output_schema: Optional[BaseModel] = None):
    """Generic function to run the model and handle structured/text output."""
    
    config = {}
    if output_schema:
        config['response_mime_type'] = "application/json"
        config['response_schema'] = output_schema
        
    full_contents = [
        {"role": "user", "parts": [{"text": f"SYSTEM ROLE ({agent_name}): {system_prompt}\n\nUSER PROMPT:\n{prompt}"}]}
    ]

    response = client.models.generate_content(
        model=API_MODEL_NAME, 
        contents=full_contents,
        config=config,
    )
    
    return response.parsed if output_schema else response.text

# ----------------------------------------------------
# 6. ORCHESTRATION (The Multi-Agent System Workflow)
# ----------------------------------------------------

def run_recipe_adapter_workflow(original_recipe: str, target_style: str):
    """The main Sequential Multi-Agent Workflow."""
    
    # --- AGENT 1: The Planner Agent (Structured Output) ---
    planner_prompt = f"""
    ORIGINAL RECIPE: "{original_recipe}"
    TARGET TRANSFORMATION: "{target_style}"
    Analyze the recipe and generate a comprehensive Substitution Map and a list of necessary Unit Conversions.
    """
    print("\n--- 1. PLANNER AGENT: Generating Substitution Map ---")
    
    planning_result: PlanningResult = run_agent(
        agent_name="Planner_Agent",
        system_prompt=f"You are the expert Recipe Planner, powered by the {CONCEPTUAL_MODEL_NAME}. Your sole job is to identify substitutions to match the target style and output the result in the required JSON schema.",
        prompt=planner_prompt,
        output_schema=PlanningResult
    )

    # --- 2. TOOL EXECUTION (The Unit Converter Tool) ---
    print("\n--- 2. TOOL EXECUTION: Running Unit Converter ---")
    conversion_results = []
    
    conversion_list = planning_result.conversion_list if isinstance(planning_result.conversion_list, list) else []

    for conv in conversion_list:
        if 'amount' in conv and 'unit' in conv and 'to_unit' in conv:
            converted_amount = unit_converter_tool(float(conv['amount']), conv['unit'])
            conversion_results.append(f"Original: {conv['amount']} {conv['unit']}. Standardized: {converted_amount} {conv['to_unit']}.")

    conversion_results_str = "\n".join(conversion_results)
    
    # --- SESSION / MEMORY Management ---
    substitution_map_str = json.dumps([s.model_dump() for s in planning_result.substitution_map], indent=2)
    
    # --- AGENT 2: The Stylist Agent (Text Output) ---
    stylist_prompt = f"""
    ORIGINAL RECIPE: {original_recipe}
    SUBSTITUTION MAP (CRITICAL MEMORY): {substitution_map_str}
    CONVERSION NOTES: {conversion_results_str}

    Your task is to rewrite the ORIGINAL RECIPE entirely, applying all substitutions and conversions. Rewrite the instructions to sound authentic for the '{target_style}' style.
    """
    print("\n--- 3. STYLIST AGENT: Generating Final Recipe Draft ---")

    final_recipe_draft = run_agent(
        agent_name="Stylist_Agent",
        system_prompt=f"You are the expert Technical Recipe Stylist, powered by the {CONCEPTUAL_MODEL_NAME}. Your job is to take the provided context and rewrite the final, well-formatted recipe in the style of '{target_style}' cuisine.",
        prompt=stylist_prompt
    )
    
    print("\n" + "="*70)
    print("✅ WORKFLOW COMPLETE: FINAL OUTPUT")
    print("="*70)
    print(final_recipe_draft)
    print("="*70)

# ----------------------------------------------------
# 7. EXECUTION
# ----------------------------------------------------

ORIGINAL_RECIPE = "Classic Beef Stroganoff: Ingredients: 2 cups Beef chuck, 1 cup sour cream, 2 tablespoons butter, 1 pinch of salt, 4 cups egg noodles. Instructions: 1. Sear beef in butter. 2. Stir in sour cream and salt. 3. Simmer for 15 mins. 4. Serve over egg noodles."
TARGET_STYLE = "Vegetarian Southeast Asian"

if __name__ == "__main__":
    run_recipe_adapter_workflow(ORIGINAL_RECIPE, TARGET_STYLE)
