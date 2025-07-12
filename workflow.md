Workflow - Smart Recipe Assistant
This document outlines the typical user interaction workflows and the corresponding internal processing steps of the "Smart Recipe Assistant."

1. User Interaction Workflows
   The Smart Recipe Assistant supports several primary workflows, driven by multimodal input.
   1.1. Workflow 1: Suggest Recipes from Ingredients (Image Input)
   User Action: User navigates to the "Smart Recipe Assistant" web application.
   User Action: User clicks an "Upload Ingredients Photo" button.
   User Action: User selects and uploads an image containing various food ingredients from their device.
   System Response: The application displays a "Processing image..." or "Identifying ingredients..." loading indicator.
   System Response: After processing, the application presents a list of identified ingredients (e.g., "I see: chicken breast, bell peppers, onion, canned tomatoes").
   System Response: The application then suggests a list of recipes that can be made with these ingredients, potentially asking for further preferences (e.g., "Would you like a quick meal, or something more elaborate?").
   User Action: User selects a recipe from the suggested list or provides additional text input (e.g., "Show me a vegetarian option").
   System Response: The application displays the detailed, step-by-step recipe.
   1.2. Workflow 2: Search for a Specific Recipe (Text Input)
   User Action: User navigates to the "Smart Recipe Assistant" web application.
   User Action: User types a recipe query into a text input field (e.g., "pasta carbonara," "easy chicken dinner," "vegan curry").
   User Action: User presses Enter or clicks a "Search" button.
   System Response: The application displays a "Searching for recipes..." loading indicator.
   System Response: The application presents a detailed recipe matching the query, or a list of top matching recipes if the query was broad.
   User Action (Optional): User asks a follow-up question about the recipe (e.g., "What kind of pasta should I use?").
   System Response: The application provides a direct answer to the follow-up question.
   1.3. Workflow 3: Get Cooking Clarifications (Text Input)
   User Action: User navigates to the "Smart Recipe Assistant" web application.
   User Action: User types a question about a cooking term, technique, or ingredient into the text input field (e.g., "What does 'blanching' mean?", "How do I zest a lemon?", "Can I substitute butter for oil in this recipe?").
   User Action: User presses Enter or clicks a "Ask" button.
   System Response: The application displays a "Thinking..." loading indicator.
   System Response: The application provides a clear and concise explanation or answer to the user's question.
   1.4. Workflow 4: Generate Shopping List (Text/Recipe Selection)
   Prerequisite: User has selected or generated a recipe (e.g., from Workflow 1 or 2).
   User Action: User clicks a "Generate Shopping List" button associated with the displayed recipe.
   System Response: The application displays a "Generating list..." loading indicator.
   System Response: The application presents a list of all ingredients required for the recipe.
   Optional Enhancement: If the user previously uploaded ingredients, the list could highlight missing ingredients.
   User Action (Optional): User can copy the shopping list to their clipboard.
2. Internal System Workflow (LangChain Agent Logic)
   This section describes the high-level steps the LangChain agent takes internally for each user interaction.
   2.1. Request Reception & Initial Parsing
   Frontend Request: The backend server receives an HTTP request from the React frontend. The request payload contains either a text string or a Base64 encoded image.
   Input Type Detection: The LangChain agent's entry point determines if the input is primarily text or an image.
   2.2. Image Input Processing Path
   Image Decoding: If an image is detected, the Base64 string is decoded into a format suitable for the vision model.
   Vision Model Call (Gemini API): The image data is sent to the Gemini API (via the LangChain "Image Recognition Tool") with a prompt like "Identify the food ingredients in this image."
   Ingredient Extraction: The Gemini API returns a textual description of the identified ingredients.
   LLM Integration & Recipe Suggestion:
   The identified ingredients are fed into the main LLM (Gemini API) via a prompt (e.g., "Based on these ingredients: [list of ingredients], suggest 3-5 recipes. Consider [user preferences from memory/profile if available].").
   The LLM generates recipe suggestions.
   Response Formatting: The generated recipe suggestions are formatted into a structured response (e.g., JSON or Markdown) for the frontend.
   2.3. Text Input Processing Path
   Intent Recognition (LLM): The user's text query is sent to the LLM (Gemini API) to determine the user's intent (e.g., "recipe search," "ingredient clarification," "general cooking question," "shopping list request").
   Memory Integration: The current conversation history (from LangChain's memory) is also provided to the LLM to maintain context.
   Tool Selection (LangChain Agent): Based on the identified intent, the LangChain agent selects the most appropriate tool:
   Recipe Database Lookup Tool: If the intent is "recipe search." This tool might query external APIs or Firestore.
   LLM Tool (Direct Generation): If the intent is "ingredient clarification" or a general cooking question that the LLM can directly answer.
   Shopping List Tool: If the intent is "shopping list request" (requires a previously selected recipe).
   Tool Execution: The selected tool executes its specific logic (e.g., making an API call, querying the database, generating text directly).
   Response Integration & Refinement (LLM): The output from the tool is often passed back to the LLM for final refinement, formatting, or to generate a conversational response.
   Response Formatting: The final response is formatted for the frontend.
   2.4. Response Delivery
   Backend to Frontend: The formatted response is sent back to the React frontend.
   Frontend Rendering: The React frontend updates the UI to display the information to the user.
   2.5. Memory Management
   LangChain Memory: Throughout all text-based interactions, LangChain's memory component is updated with the user's input and the agent's response, ensuring the conversation has context for subsequent turns. This allows the agent to remember dietary preferences, previously identified ingredients, or the current recipe being discussed.
   Firestore (for long-term preferences): User-specific preferences (e.g., default dietary restrictions) can be persistently stored in Firestore and retrieved at the start of a session.
