# RecipeMate AI — Cooking & Meal Planning AI Agent

RecipeMate AI is a conversational recipe-planning and cooking assistant built according to the **RecipeMate AI PRD**.
It functions as a full **AI Agent** rather than a passive chatbot, featuring task planning, tool selection, error recovery, active context retention, memory, step limits, and safety confirmations.

---

## 🌟 Key Features

1. **Think → Act → Look → Learn → Respond Agent Loop**
   - **Think**: Analyzes intent and generates multi-step task plans (`TaskPlan`) before executing complex operations.
   - **Act**: Executes tools with safety step-limits (max 10 actions per request).
   - **Look**: Inspects execution telemetry, detects failures, and retries or selects fallbacks.
   - **Learn**: Persists context (active recipe, current meal plan, servings, dietary constraints).
   - **Respond**: Produces formatted Markdown recipes and plans.

2. **Core Agent Tools (5 Tools)**:
   - 🔍 **Recipe Search Tool (`RecipeSearchTool`)**: Search by ingredients, cuisine, diet (vegan, vegetarian, spicy, high-protein, budget), max cooking time, difficulty, and excluded ingredients with fuzzy matching and scoring.
   - 🧈 **Ingredient & Substitution Tool (`IngredientSubstitutionTool`)**: Suggests culinary alternatives with conversion ratios and flavor/texture impact warnings.
   - 🔢 **Recipe Calculator (`RecipeCalculatorTool`)**: Scales recipe ingredient quantities proportionally to target serving sizes.
   - 📅 **Meal Planner Tool (`MealPlannerTool`)**: Generates 1–14 day daily and weekly meal plans (breakfast, lunch, dinner, snack), balances vegetarian days, and supports in-place meal swaps (e.g. "Change Wednesday dinner").
   - 💾 **Memory Tool (`MemoryTool`)**: Persistent preference storage (`remember`, `recall`, `forget`, `clear`) with user confirmation safety checks.

3. **Safety & Operational Controls**:
   - **User Confirmation**: Asks confirmation before saving personal preferences or wiping memory.
   - **Action Limit**: Enforces a strict step limit (default 10 steps) to prevent runaway execution.
   - **Structured Action Logging**: Records all milestones (`Task started`, `Plan created`, `Recipe search called`, `Recipe modified`, etc.).
   - **Tool Failure Recovery**: Automatic retries and graceful fallback suggestions.

4. **Two-Stage Intelligence**:
   - **Stage 1 (Deterministic Mock Brain)**: Fast, fully offline, testable brain implementing all 8 PRD scenarios without API dependencies.
   - **Stage 2 (Real LLM Integration)**: Pluggable client supporting Gemini API, OpenAI, or local Ollama endpoints with automatic fallback to Mock Brain.

5. **Interactive Web Chat Interface**:
   - Real-time chat with formatted recipe cards and meal plan grids.
   - Quick action chips (🍗 *Use My Ingredients*, 🍳 *Find a Recipe*, 🥗 *Healthy Recipe*, 📅 *Plan My Week*, 🧈 *Find Substitute*).
   - Live sidebar showing **Agent Thinking & Plan checklist**, **Live Action Log stream**, **Active Recipe with Serving Stepper (+/-)**, and **Saved Memory**.

---

## 📁 Project Structure

```
├── data/
│   ├── recipes.json            # Curated recipe database
│   ├── substitutions.json      # Culinary substitutions database
│   └── user_preferences.json   # Persistent memory storage
├── src/
│   ├── models/                 # Pydantic data models (Recipe, MealPlan, AgentState, ActionLog)
│   ├── tools/                  # 5 core tools + BaseTool with error recovery & retry
│   ├── agent/                  # Planner, Executor, Mock Brain, Real LLM Client & Prompts
│   ├── api/                    # FastAPI backend server
│   └── utils/                  # Structured logger
├── static/                     # Web chat application (HTML5, modern CSS, vanilla JS)
├── tests/                      # Pytest automated test suite (27 passing tests)
├── requirements.txt            # Python dependencies
├── run.py                      # Application launcher
└── RecipeMate_AI_PRD.md        # Product Requirements Document
```

---

## 🚀 Getting Started

### 1. Environment Setup
The project uses Python 3.12:
```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements (already installed in .venv)
pip install -r requirements.txt
```

### 2. Run the Automated Test Suite
To verify the complete test suite including all 8 PRD test scenarios:
```powershell
.\.venv\Scripts\pytest.exe -v tests
```
*All 27 unit, integration, and scenario tests pass.*

### 3. Start the Live Web Interface
```powershell
.\.venv\Scripts\python.exe run.py
```
Open your browser to:
- **Chat Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Verified PRD Test Scenarios

| Test Case | User Input | Verified Behavior |
|-----------|------------|-------------------|
| **Test 1 — Basic Recipe** | *"I have eggs and bread."* | Finds and suggests relevant recipes (*Egg Sandwich*, *French Toast*). |
| **Test 2 — Recipe Modification** | *"Make it spicy."* | Modifies active recipe, adds chili, tags spicy, and updates instructions. |
| **Test 3 — Serving Adjustment** | *"Make it for 6 people."* | Calculates 3x proportional scaling on all ingredient quantities. |
| **Test 4 — Missing Ingredient** | *"I don't have butter."* | Suggests substitutes (oil, margarine, coconut oil) with flavor notes. |
| **Test 5 — Meal Plan** | *"Make a 7-day dinner plan."* | Generates 7-day schedule; supports swapping individual meals. |
| **Test 6 — Memory** | *"Remember that I like spicy food."* | Prompts for confirmation; on confirmation, prioritizes spicy dishes. |
| **Test 7 — Tool Failure** | Tool error simulated | Automatically retries and provides graceful fallback alternatives. |
| **Test 8 — Step Limit** | Exceeds 10 steps | Halts safely with standard limit warning message. |

---

## ⚙️ Optional Real LLM Configuration

To connect a live cloud LLM (e.g. Gemini or OpenAI), configure your environment:
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
# or
$env:OPENAI_API_KEY="your_api_key_here"
```
If no key is configured, the agent seamlessly operates using its deterministic Stage 1 brain with 100% functionality offline.
