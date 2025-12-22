# Gemini Live API Dynamic Instruction Update Sample Implementation Plan

## Goal Description
Create a Python sample application `gemini_live_test.py` that demonstrates how to use the Google Gemini Live API (Vertex AI) to dynamically update system instructions during an active session without disconnecting.

## User Review Required
- **Audio Dependencies**: The sample uses `pyaudio`. Ensure `portaudio` is installed on the system (e.g., via `brew install portaudio` on Mac) for `pyaudio` to install correctly.
- **Project ID**: The code uses a hardcoded project ID `jwlee-argolis-202104`. This should be replaced with the user's actual project ID or set via environment variable.

## Proposed Changes

### [New Project]
#### [NEW] [gemini_live_test.py](file:///Users/jungwoonlee/gemini_live_02/gemini_live_test.py)
- Implement the `GeminiLiveAPITestVertexAI` class as provided in the request.
- Ensure `update_system_instruction` method sends `LiveClientMessage(setup=config)` as per documentation.
- Include a `main` function to run the scenario (Assistant -> Pirate -> Korean Assistant).

#### [NEW] [requirements.txt](file:///Users/jungwoonlee/gemini_live_02/requirements.txt)
- `google-genai`
- `pyaudio`

## Verification Plan  Summary of how you will verify that your changes have the desired effects.  

### role="system" Testing
- Revert the "Session Restart" loop to a single persistent session.
- Implement `update_system_instruction` using `send_client_content` with `role="system"` and `turn_complete=False`.
- Verify if Turn 2 and Turn 3 still produce audio without session interruption.

### Previous verification (Session Restart)
- Verified that closing and reopening the session works reliably for multiple personas.
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Script**:
   ```bash
   python3 gemini_live_test.py
   ```
3. **Observation**:
   - Verify connection to Gemini Live API.
   - Speak/Type to the assistant.
   - Observe the console output for "Updating system instruction".
   - Verify the persona changes from Helpful Assistant -> Pirate -> Korean Assistant effectively while keeping the session alive.
