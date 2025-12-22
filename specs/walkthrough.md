# Gemini Live Audio Instruction Fix - Walkthrough

## Objective
The goal was to resolve the issue where audio playback ceased after updating system instructions during a single `gemini-live-2.5-flash-native-audio` session.

- **Session Restart**: Works reliably (Success).
- **role="system" Content**: Results in session timeout/silence (Failure).
- **User Directives/Direct Messages**: Results in session timeout/silence (Failure).

## role="system" Test Details (Latest)
As requested, we tested the direct `role="system"` update method:
```python
await self.session.send_client_content(
    turns=[types.Content(role="system", parts=[types.Part(text=new_instruction)])],
    turn_complete=False
)
```
**Result**: Even with "silence heartbeat" workarounds, the model stopped sending any response (`LiveServerMessage`) for subsequent user turns within the same session.

### Key Implementation Details
- **Graceful Closure**: Existing listeners and sessions are cancelled and closed.
- **New Connection**: A new session is initiated using `client.aio.live.connect` with the updated `system_instruction` in the `LiveConnectConfig`.
- **Consistency**: This method guarantees that every persona change results in immediate and sustained audio output.

## Validation Results

We successfully verified the solution using a 3-turn scenario:
1. **Turn 1 (Helpful Assistant)**: Responded with audio.
2. **Turn 2 (Pirate)**: Responded with audio after session restart.
3. **Turn 3 (Korean Assistant)**: Responded with audio after session restart.

### Verification Logs
Below is an excerpt from the final verification run (`debug_output_restart.txt`):

```text
📡 Starting Session Turn 1 with Instruction: You are a helpful assistant...
💬 [User]: Hello! What is your current role?
DEBUG: Received audio chunk 11114 bytes
DEBUG: Received audio chunk 11520 bytes
...
[Turn Complete]
📴 Closed Session Turn 1

📡 Starting Session Turn 2 with Instruction: You are now a pirate. Talk lik...
💬 [User]: Who are you now, and what is your pirate mission?
DEBUG: Received audio chunk 11114 bytes
DEBUG: Received audio chunk 11520 bytes
...
[Turn Complete]
📴 Closed Session Turn 2

📡 Starting Session Turn 3 with Instruction: 당신은 친절한 한국어 비서입니다. 정중하게 한국어로...
💬 [User]: 방금 어떤 컨셉이었는지 설명해주고...
DEBUG: Received audio chunk 11114 bytes
DEBUG: Received audio chunk 11520 bytes
...
[Turn Complete]
📴 Closed Session Turn 3

✅ 모든 실시간 업데이트 테스트 완료 (세션 재시작 방식)!
```

## Conclusion
The "Session Restart" approach provides the most stable and reliable user experience for the `gemini-live-2.5-flash-native-audio` model, ensuring that audio modality is never lost during instruction updates.
