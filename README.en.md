[한국어 (Korean)](README.md) | [English](README.en.md)

# Gemini Live API Dynamic Instruction Update (Audio Fix)

This project provides a robust solution for dynamically updating system instructions (personas/roles) in a **Google Gemini Live API (Vertex AI)** session without losing audio modality.

## 🚀 The Challenge: Audio Interruption
When using the `gemini-live-2.5-flash-native-audio` model, standard methods for updating system instructions during an active session (e.g., sending `role="system"` content or user directives) often lead to the model becoming silent or the session timing out after the first update.

## ✅ The Solution: Session Restart (Wait & Reset)
Through extensive testing of various workarounds (including silence injection and merged directives), the most reliable method for the current preview model is the **Session Restart** strategy. This ensure:
1. **Audio Continuity**: Every response starts with fresh audio generation.
2. **Persona Integrity**: The model strictly follows the new instruction from the first turn of the new session.
3. **Session Stability**: Avoids long-term cache or state issues that cause "Native Audio" models to hang.

## 🛠 Features
- **Dynamic Role Playing**: Switch from a Helpful Assistant to a Pirate or a Korean translator seamlessly.
- **Multimodal Support**: Handles both text and audio output via `pyaudio`.
- **Robust Synchronization**: Uses `asyncio.Event` to ensure turns are completed before starting new ones.
- **Verbose Debugging**: Integrated logging to track raw server responses and audio chunk reception.

## 📋 Prerequisites
- Python 3.9+
- Google Cloud Project with Vertex AI API enabled.
- System dependencies (for PyAudio):
  - macOS: `brew install portaudio`
  - Linux: `sudo apt-get install libportaudio2`

## ⚙️ Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/freeman9844/gcp-test-04.git
   cd gcp-test-04
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage
Update the `project_id` in `gemini_live_test.py` and run:
```bash
python gemini_live_test.py
```

### Script Scenario:
1. **Turn 1**: Hello! (Helpful Assistant Role)
2. **Update**: Changes to Pirate role.
3. **Turn 2**: Who are you? (Responding as a Pirate)
4. **Update**: Changes to Korean Assistant role.
5. **Turn 3**: 안녕하세요. (Responding in Korean)

## 📁 Project Structure
- `gemini_live_test.py`: Main test script with robust session management.
- `requirements.txt`: Python package dependencies.
- `/specs`: Detailed technical documentation.
  - `walkthrough.md`: Comparative analysis of failed vs. successful approaches.
  - `implementation_plan.md`: Technical architecture and verification details.

## ⚠️ Known Limitations
The `gemini-live-2.5-flash-native-audio` is a preview model. While `role="system"` updates are technically supported, they are currently unstable for continuous audio. The "Session Restart" method is the recommended production-safe workaround.

## 📜 License
MIT License
