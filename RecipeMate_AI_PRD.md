# Product Requirements Document (PRD)
# Recipe Planner & Assistant AI Agent

## 1. Product Overview

**Product Name:** RecipeMate AI

RecipeMate AI is a live AI chatbot that helps users discover recipes, plan meals, modify recipes, and create personalized cooking plans.

The user can have a natural conversation such as:

> "I have chicken, rice and eggs. What can I make?"

The assistant can suggest recipes, ask follow-up questions, adjust recipes based on preferences, scale ingredient quantities, create meal plans, suggest substitutions, and remember useful preferences when permitted.

The product should behave as an **AI agent**, not just a simple chatbot. It should plan tasks, use tools, observe results, recover from failures, use memory, and adapt its responses.

## 2. Main Goals

- Suggest recipes from available ingredients.
- Recommend recipes based on preferences.
- Create daily and weekly meal plans.
- Modify recipes through conversation.
- Scale recipes for different serving sizes.
- Suggest ingredient substitutions.
- Calculate ingredient quantities.
- Provide cooking instructions.
- Remember useful user preferences when permitted.
- Handle unavailable ingredients.
- Provide a live chatbot experience.

## 3. Target Users

- Students
- Home cooks
- Busy people
- Beginners learning to cook
- People trying to use ingredients they already have
- Users looking for meal-planning ideas

## 4. Core User Experience

The main interface should be a **live chatbot**.

Example:

```text
User:
I have chicken, rice, onion and tomato.

AI:
You can make several dishes:
1. Chicken Tomato Rice
2. Chicken Fried Rice
3. One-Pot Chicken Rice

Do you want something quick, spicy, healthy, or filling?

User:
Make it spicy and for 4 people.

AI:
Sure. I've adjusted the recipe for 4 people and made it spicier.
```

## 5. Core Features

### 5.1 Recipe Suggestions

Suggest recipes based on:

- Available ingredients
- Cuisine
- Meal type
- Cooking time
- Difficulty
- Dietary preferences
- User preferences
- Number of servings

### 5.2 Recipe Planner

Create daily and weekly meal plans.

Daily example:

```text
Breakfast: Egg sandwich
Lunch: Chicken rice
Snack: Fruit yogurt
Dinner: Vegetable noodles
```

Weekly plans should support Monday–Sunday and breakfast, lunch, dinner, and optional snacks.

Users should be able to change individual meals through chat.

Example:

```text
User:
Change Wednesday dinner. I don't want chicken.

AI:
Sure. I'll replace it with a vegetarian option.
```

### 5.3 Live Chatbot

Support:

- Real-time conversation
- Follow-up questions
- Current conversation context
- Recipe modifications
- Meal-plan modifications
- Ingredient substitutions
- Serving-size changes
- Cooking-time changes

## 6. AI Agent Loop

The agent should follow:

**Think → Act → Look → Learn → Respond**

```text
User Request
     ↓
   THINK
     ↓
 Create Plan
     ↓
    ACT
     ↓
 Use Tool
     ↓
    LOOK
     ↓
 Check Result
     ↓
   LEARN
     ↓
  RESPOND
```

For simple requests, the agent may answer directly. For tasks requiring tools, it should use the appropriate tool and inspect the result before responding.

## 7. Planning Before Acting

For complex requests, create a task plan before using tools.

Example:

```text
User:
Make me a 7-day dinner plan using chicken twice,
vegetarian meals three times, and keep everything under
30 minutes.

Plan:
1. Identify requirements.
2. Select 7 recipes.
3. Ensure chicken appears twice.
4. Ensure vegetarian meals appear at least three times.
5. Check cooking times.
6. Create the weekly plan.
7. Present the plan.
```

The agent should update the plan if the user changes requirements.

## 8. Required Tools

The initial version should use **4–5 tools**.

### Tool 1 — Recipe Search Tool

**Purpose:** Find recipes based on ingredients and requirements.

Inputs:

```text
ingredients
cuisine
meal_type
diet
max_cooking_time
difficulty
```

Example:

```text
search_recipes(
    ingredients=["chicken", "rice"],
    max_cooking_time=30
)
```

Output should contain recipe name, cooking time, ingredients, difficulty, and instructions or a recipe reference.

### Tool 2 — Ingredient & Substitution Tool

**Purpose:** Find alternatives when an ingredient is unavailable.

Example:

```text
find_substitute("butter")
```

Possible result:

```text
Oil
Margarine
Coconut oil
```

The assistant should explain that substitutions can change taste or texture.

### Tool 3 — Recipe Calculator

**Purpose:** Scale ingredient quantities and perform unit conversions.

Example:

```text
Original:
Servings: 2
Chicken: 300 g
Rice: 200 g

User:
Make it for 6 people.

Result:
Chicken: 900 g
Rice: 600 g
```

### Tool 4 — Meal Planner Tool

**Purpose:** Create and modify meal plans.

Inputs:

```text
number_of_days
meals_per_day
diet
preferences
excluded_foods
budget
max_cooking_time
```

Example:

```text
create_meal_plan(
    days=7,
    meals=["breakfast", "lunch", "dinner"],
    vegetarian_days=3
)
```

### Tool 5 — Memory Tool

**Purpose:** Store and retrieve useful user preferences.

Examples:

```text
remember("User prefers spicy food.")
recall("food preferences")
```

Memory should be used only for useful information and should respect user control.

## 9. Optional Future Tools

### Nutrition Tool
Provides estimated calories, protein, carbohydrates, and fat.

### Shopping List Tool
Creates a shopping list from a meal plan.

Example:

```text
Chicken — 1.5 kg
Rice — 2 kg
Onion — 1 kg
Tomato — 1 kg
```

### Grocery Price Tool
Estimates ingredient costs.

### Image Recognition Tool
Allows users to upload an ingredient photo and identify ingredients.

## 10. Recipe Modification

Users should be able to say:

```text
Make it vegetarian.
Make it spicy.
Remove onions.
I don't have milk.
Make it healthier.
Make it cheaper.
Make it for 5 people.
Reduce the cooking time.
```

The assistant should modify the current recipe while preserving conversation context.

## 11. Recipe Output Format

Example:

```text
## Spicy Chicken Rice

Servings: 4
Prep time: 10 minutes
Cooking time: 25 minutes
Difficulty: Easy

### Ingredients
- 600 g chicken
- 400 g rice
- 2 onions
- 3 tomatoes
- 3 garlic cloves
- 1–2 tsp chili powder
- Salt
- Oil

### Instructions
1. Wash and prepare the ingredients.
2. Heat oil in a pan.
3. Add onion and garlic.
4. Add chicken and spices.
5. Add tomatoes.
6. Add rice and water.
7. Cover and cook until the rice is done.

### Tips
Add more chili if you prefer a hotter dish.
```

## 12. Dietary Preferences

Support:

- Vegetarian
- Vegan
- Non-vegetarian
- High-protein
- Low-calorie
- Quick meals
- Budget meals

For allergies, the assistant should clearly warn users to verify ingredient labels and cross-contamination risks. It should avoid unsupported medical claims.

## 13. Memory Between Tasks

Example:

```text
User:
I like spicy food.

AI:
Would you like me to remember that for future recipes?

User:
Yes.
```

Later:

```text
User:
Suggest a chicken recipe.

AI:
Since you prefer spicy food, here are some spicy chicken options...
```

Users should be able to change or delete saved preferences.

## 14. Tool Failure Handling

Tools can fail because of network errors, invalid input, server errors, missing information, timeouts, or unavailable services.

Recovery flow:

```text
Tool Failure
     ↓
Identify Error
     ↓
Can it be retried?
     ↓
 YES → Retry
     ↓
Still failing?
     ↓
Try alternative approach
     ↓
Still failing?
     ↓
Tell user / ask for input
```

The agent must not call a failed tool indefinitely.

## 15. Safety

### User Confirmation

Ask before:

- Saving personal preferences when appropriate
- Deleting saved data
- Performing purchases or other external actions
- Sending information externally

### Step Limit

Set a maximum number of agent actions per task.

Example:

```text
Maximum agent steps = 10
```

If reached:

```text
I've reached the action limit for this request.
I'll stop here rather than continuing unexpectedly.
```

### Action Logging

Record important events such as:

```text
Task started
Plan created
Recipe search called
Recipe search completed
Recipe calculator called
Recipe modified
Response generated
Task completed
```

## 16. Chatbot UI Requirements

The application should have a clean chat interface.

```text
------------------------------------------------
| RecipeMate AI                                |
------------------------------------------------
|                                              |
| AI: What would you like to cook today?       |
|                                              |
| You: I have chicken and rice.                |
|                                              |
| AI: Here are 3 recipes you can make...       |
|                                              |
| You: Make option 2 spicy.                    |
|                                              |
| AI: Sure! I've modified the recipe...        |
|                                              |
------------------------------------------------
| Type a message...                     [Send] |
------------------------------------------------
```

Suggested quick actions:

```text
🍳 Find a Recipe
🥗 Healthy Recipe
🍗 Use My Ingredients
📅 Plan My Week
🛒 Make Shopping List
```

## 17. Conversation Context

The chatbot must maintain the current conversation context.

Example:

```text
User:
Give me a pasta recipe.

AI:
Here's a tomato pasta recipe.

User:
Make it spicy.

AI:
[Modifies the same recipe]

User:
For 4 people.

AI:
[Scales the same recipe]
```

The user should not need to repeat the recipe name every time.

## 18. Data Model

Example recipe object:

```json
{
  "name": "Chicken Rice",
  "servings": 2,
  "prep_time": 10,
  "cook_time": 25,
  "difficulty": "easy",
  "ingredients": [
    {
      "name": "chicken",
      "quantity": 300,
      "unit": "g"
    },
    {
      "name": "rice",
      "quantity": 200,
      "unit": "g"
    }
  ],
  "instructions": [
    "Prepare the ingredients",
    "Cook the chicken",
    "Add rice",
    "Cook until ready"
  ]
}
```

## 19. Meal Plan Data Model

```json
{
  "week": {
    "monday": {
      "breakfast": "Egg Sandwich",
      "lunch": "Chicken Rice",
      "dinner": "Vegetable Pasta"
    },
    "tuesday": {
      "breakfast": "Oatmeal",
      "lunch": "Chicken Wrap",
      "dinner": "Dal Rice"
    }
  }
}
```

## 20. System Architecture

```text
                    USER
                      │
                      ▼
              ┌───────────────┐
              │    CHAT UI    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   AI AGENT    │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │    PLANNER    │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │  LLM / BRAIN  │
              └───────┬───────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Recipe Search   Calculator     Memory
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
                TOOL RESULTS
                      │
                      ▼
                   LOOK
                      │
                      ▼
                 EVALUATE
                      │
                      ▼
                  RESPOND
                      │
                      ▼
                    USER
```

## 21. Agent State

Example:

```text
Current Goal:
Create a spicy chicken recipe.

Current Recipe:
Chicken Rice

Servings:
4

Preferences:
Spicy

Excluded Ingredients:
Coriander

Current Step:
Recipe modification

Previous Tool:
Recipe Calculator

Last Result:
Ingredients successfully scaled.
```

## 22. Testing Strategy

Development should start with a **fake/mock LLM** before connecting to a real LLM.

### Stage 1 — Fake LLM

Use predefined responses to test:

- Agent planning
- Tool selection
- Tool execution
- Tool failure recovery
- Memory
- Recipe modification
- Step limits
- Safety confirmation
- Logging
- Conversation state

Example:

```text
Input:
Make a recipe using chicken and rice.

Fake LLM:
{
  "action": "search_recipe",
  "ingredients": ["chicken", "rice"]
}
```

### Stage 2 — Real LLM

After mock tests pass, connect a real LLM.

Test:

- Natural language understanding
- Planning quality
- Tool selection
- Recipe modifications
- Conversation context
- Memory
- Error recovery
- Safety behavior
- Unexpected requests

## 23. Important Test Cases

### Test 1 — Basic Recipe

```text
User:
I have eggs and bread.

Expected:
Suggest relevant recipes.
```

### Test 2 — Recipe Modification

```text
User:
Make it spicy.

Expected:
Modify the current recipe.
```

### Test 3 — Serving Adjustment

```text
User:
Make it for 6 people.

Expected:
Scale ingredient quantities.
```

### Test 4 — Missing Ingredient

```text
User:
I don't have butter.

Expected:
Suggest a suitable substitute.
```

### Test 5 — Meal Plan

```text
User:
Make a 7-day dinner plan.

Expected:
Generate a weekly plan.
```

### Test 6 — Memory

```text
User:
Remember that I like spicy food.

Later:
Suggest a chicken recipe.

Expected:
Spicy recipes should be prioritized.
```

### Test 7 — Tool Failure

```text
Recipe Search:
FAIL

Expected:
Agent retries or uses an alternative method.
```

### Test 8 — Step Limit

```text
Maximum steps:
10

Expected:
Agent stops after reaching the limit.
```

## 24. Functional Requirements

The system must:

- Understand user goals.
- Create a plan before acting.
- Follow the Think → Act → Look loop.
- Select appropriate tools.
- Execute tools.
- Observe tool results.
- Detect tool failures.
- Recover from failures.
- Maintain memory between tasks.
- Learn from feedback.
- Ask for confirmation when required.
- Enforce a step limit.
- Maintain action logs.
- Maintain conversation context.
- Modify existing recipes through chat.
- Generate meal plans.
- Scale ingredient quantities.
- Support fake LLM testing.
- Support real LLM integration.

## 25. Non-Functional Requirements

### Performance
Chat responses should feel interactive.

### Reliability
The application should gracefully handle tool failures.

### Scalability
The architecture should allow additional tools to be added later.

### Security
User data and saved preferences should be protected.

### Usability
The chatbot should be simple for first-time users.

### Maintainability
Tools, agent logic, memory, and UI should be modular.

## 26. MVP Scope

The first version should include:

- Live chatbot
- Recipe suggestions
- Ingredient-based recipe search
- Recipe modification
- Serving-size calculator
- Basic memory
- Meal-plan generation
- 3–5 tools
- Think → Act → Look agent loop
- Error recovery
- Step limit
- Action logs
- Fake LLM testing
- Real LLM integration

Do not include initially:

- Grocery ordering
- Advanced image recognition
- Advanced nutrition analysis
- Grocery price comparison
- Voice assistant
- Multi-agent system
- Automated shopping

## 27. Example End-to-End Interaction

```text
User:
I have chicken, rice, onion and tomato.

AI:
I found 3 recipes you can make:

1. Chicken Tomato Rice — 30 min
2. One-Pot Chicken Rice — 25 min
3. Spicy Chicken Fried Rice — 20 min

Which one would you like?

User:
3.

AI:
Great. How many people are you cooking for?

User:
4.

AI:
I'll scale the recipe for 4 servings.

[Recipe Calculator Tool]

AI:
## Spicy Chicken Fried Rice

Servings: 4
Time: 20 minutes

Ingredients:
- 600 g chicken
- 4 cups cooked rice
- 2 onions
- 3 tomatoes
- Chili according to taste

User:
I don't have soy sauce.

AI:
No problem. I can suggest a substitute, although the flavor may differ.

User:
Make it more spicy.

AI:
Sure. I've increased the chili and adjusted the seasoning.

Would you like me to remember that you prefer spicy recipes?

User:
Yes.

AI:
Saved. I'll prioritize spicier recipes in future suggestions.
```

## 28. Success Metrics

The MVP should be considered successful if:

- Users can start a recipe conversation naturally.
- The agent suggests appropriate recipes.
- Users can modify recipes without restarting.
- Ingredient quantities can be scaled correctly.
- The agent creates basic meal plans.
- The agent remembers permitted preferences.
- Tool failures are handled gracefully.
- The agent does not exceed its step limit.
- Safety confirmations work correctly.
- The chatbot maintains conversation context.
- The system passes fake LLM tests.
- The system works with a real LLM.

## 29. Future Enhancements

### Version 2
- Nutrition information
- Shopping-list generation
- Grocery price estimation
- Recipe ratings
- Favorite recipes
- Recipe history

### Version 3
- Ingredient photo recognition
- Voice conversation
- Personalized nutrition goals
- Automated weekly grocery lists
- Calendar integration

### Version 4
- Multiple specialized agents
- Grocery shopping integrations
- Advanced personalization
- Smart pantry management

## 30. Final Product Definition

RecipeMate AI is a conversational recipe-planning and cooking assistant combining:

- **Live AI Chat**
- **Recipe Discovery**
- **Ingredient-Based Suggestions**
- **Meal Planning**
- **Recipe Modification**
- **Ingredient Substitution**
- **Serving-Size Calculation**
- **Memory**
- **Planning**
- **Think → Act → Look**
- **Tool Usage**
- **Error Recovery**
- **Safety Controls**
- **Step Limits**
- **Action Logging**
- **Fake LLM Testing**
- **Real LLM Integration**

The primary MVP goal is to make the user feel like they are having a conversation with a helpful cooking assistant that understands changes and continuously adapts recipes and meal plans without making the user start over.
