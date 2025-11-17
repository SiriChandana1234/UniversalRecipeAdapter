# Universal Recipe Adapter: Cross-Cultural AI Cuisine

The Universal Recipe Adapter is a multi-agent system designed to take any standard recipe and dynamically transform it based on specific constraints, such as a different dietary requirement (e.g., Vegetarian) or a specific target culinary style (e.g., Southeast Asian).

This project demonstrates core principles of agent development, including sequential workflow orchestration, structured output (Pydantic), and tool integration.

## 💡 The Problem & Solution

### Problem
Traditional recipes are rigid and difficult to adapt for dietary restrictions, allergies, or a chef’s desire for cultural fusion (e.g., converting a classic French dish into a vegan, high-protein Indian meal).

### Solution
We use a **two-agent, sequential workflow** to programmatically break down a recipe, modify its chemical structure (ingredients/units), and then rewrite the prose in the appropriate culinary style, creating a completely new, executable recipe.

## ✨ Architecture: Multi-Agent System Workflow

The project's intelligence is divided into two specialized agents connected by a shared memory structure, executing a fixed sequence.



### 1. Planner Agent (Structured Reasoning)
* **Role:** The **Planner Agent** is responsible for structured, technical reasoning.
* **Input:** Original Recipe and Target Style/Diet.
* **Output:** Generates a **`PlanningResult`** object (using Pydantic for guaranteed JSON format). This object contains two crucial lists that serve as the workflow memory:
    * **Substitution Map:** A list of every necessary ingredient swap (e.g., *Beef Chuck* $\rightarrow$ *Firm Tofu*).
    * **Conversion List:** A list of all units that need standardization (e.g., *cups* to *grams*).

### 2. Tool Execution (Unit Converter)
* **Tool:** The `unit_converter_tool()` function runs against the Planner's **Conversion List**.
* **Function:** It standardizes volumetric units (like 'cups') into metric units (like 'grams') for accurate scaling. The results are stored as simple text notes.

### 3. Stylist Agent (Creative Output)
* **Role:** The **Stylist Agent** is responsible for creative and natural language generation.
* **Input:** The combined memory (the Planner's Substitution Map and the Tool's Conversion Notes).
* **Output:** Rewrites the entire recipe (ingredients and instructions) in a natural, well-formatted, and culturally appropriate prose for the target cuisine (e.g., using terms like "wok" or "fragrant").

## 🛠️ Setup and Execution Instructions

### Prerequisites

You must have **Python 3.8+** and **Git** installed.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/SiriChandana1234/UniversalRecipeAdapter.git](https://github.com/SiriChandana1234/UniversalRecipeAdapter.git)
    cd UniversalRecipeAdapter
    ```

2.  **Install Dependencies:**
    ```bash
    pip install google-genai pydantic
    ```

3.  **Authentication (CRUCIAL STEP):**
    The script requires your Gemini API Key to be set as an environment variable named `GEMINI_API_KEY`.

    * **Get your key:** Obtain a key from the Google AI Studio.
    * **Set the variable** (replace `YOUR_API_KEY_HERE` with your actual key):

    ```bash
    # For macOS/Linux/Git Bash:
    export GEMINI_API_KEY="YOUR_API_KEY_HERE"

    # For Windows Command Prompt:
    set GEMINI_API_KEY="YOUR_API_KEY_HERE" 
    ```

### Run the Agent

Execute the main script:

```bash
python recipe_adapter.py

