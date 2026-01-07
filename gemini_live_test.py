"""
Google Gemini Live API 테스트 샘플 코드 (Vertex AI 버전)
검증된 방식: 세션 재시작(Session Restart)을 통한 동적 인스트럭션 업데이트

참고: gemini-live-2.5-flash-native-audio 모델에서 단일 세션 내 role="system" 업데이트는
      현재 안정적으로 작동하지 않습니다. 세션 재시작 방식이 가장 신뢰할 수 있습니다.
"""

import asyncio
from google import genai
from google.genai import types

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False


class GeminiLiveAPITestVertexAI:
    """Gemini Live API 테스트 클래스 (Vertex AI)"""
    
    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "gemini-live-2.5-flash-native-audio"):
        print(f"🔧 Initializing client for Vertex AI...")
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        self.model_name = model_name
        self.session = None
        
        self.audio = None
        self.audio_stream = None
        self.audio_available = HAS_PYAUDIO
        self.turn_completed_event = asyncio.Event()
        
        if self.audio_available:
            try:
                self.audio = pyaudio.PyAudio()
                print("✅ Audio system initialized.")
            except Exception as e:
                print(f"⚠️  Failed to initialize PyAudio: {e}")
                self.audio_available = False
    
    def _setup_audio_stream(self):
        if not self.audio_available or not self.audio:
            return
        try:
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,
                output=True
            )
        except Exception as e:
            print(f"❌ Failed to open audio stream: {e}")
            self.audio_available = False
    
    async def connect(self, system_instruction: str = "You are a helpful assistant."):
        """Live API 세션 연결을 시작합니다."""
        print(f"\n📡 Connecting to Live API (Model: {self.model_name})")
        
        config = types.LiveConnectConfig(
            system_instruction=types.Content(
                parts=[types.Part(text=system_instruction)]
            ),
            response_modalities=["AUDIO"],
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
        )
        
        return self.client.aio.live.connect(
            model=self.model_name,
            config=config
        )

    async def handle_session_events(self):
        """세션으로부터 응답을 수신하고 처리합니다."""
        if not self.session:
            return
            
        self._setup_audio_stream()
        try:
            async for response in self.session.receive():
                if response.server_content:
                    sc = response.server_content
                    
                    if sc.turn_complete:
                        print(f"\n[Turn Complete]")
                        self.turn_completed_event.set()

                    model_turn = sc.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if part.inline_data:
                                if self.audio_available and self.audio_stream:
                                    try:
                                        self.audio_stream.write(part.inline_data.data)
                                    except Exception as e:
                                        print(f"\n❌ Audio Write Error: {e}")

                    if sc.output_transcription:
                        text = sc.output_transcription.text
                        if text:
                            print(f"[Transcript]: {text}", end="", flush=True)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n❌ Receiver Error: {e}")
        finally:
            self._close_audio_stream()

    def _close_audio_stream(self):
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except: pass
            self.audio_stream = None

    def close(self):
        self._close_audio_stream()
        if self.audio:
            try: self.audio.terminate()
            except: pass
            self.audio = None

    async def send_text(self, text: str, end_of_turn: bool = True):
        """텍스트 메시지 전송"""
        if not self.session:
            raise RuntimeError("Session not connected.")
        
        print(f"\n💬 [User]: {text}")
        
        await self.session.send_client_content(
            turns=[types.Content(role="user", parts=[types.Part(text=text)])],
            turn_complete=end_of_turn
        )


async def main():
    """메인 함수: 세션 재시작을 통한 동적 인스트럭션 업데이트 시나리오"""
    print("\n🚀 Google Gemini Live API Dynamic Instruction Test (Session Restart Method)\n")
    project_id = "jwlee-argolis-202104"
    
    tester = GeminiLiveAPITestVertexAI(project_id=project_id)
    
    scenarios = [
        {
            "instruction": "You are a helpful assistant. Reply briefly.",
            "prompt": "Hello! What is your current role?",
            "label": "Helpful Assistant"
        },
        {
            "instruction": "You are now a pirate. Talk like one! Use 'Arrr' and 'Matey'.",
            "prompt": "Who are you now, and what is your pirate mission?",
            "label": "Pirate"
        },
        {
            "instruction": "당신은 친절한 한국어 비서입니다. 정중하게 한국어로 답변하세요.",
            "prompt": "방금 어떤 컨셉이었는지 설명해주고, 현재 어떤 서비스를 제공가능한지 정중히 답변해주세요.",
            "label": "Korean Assistant"
        },
    ]
    
    try:
        for i, scenario in enumerate(scenarios):
            print("\n" + "="*60)
            print(f"📌 Turn {i+1}: {scenario['label']}")
            print(f"   Instruction: {scenario['instruction'][:50]}...")
            
            # 각 턴마다 새 세션 시작 (인스트럭션 적용)
            async with await tester.connect(system_instruction=scenario['instruction']) as session:
                tester.session = session
                tester.turn_completed_event.clear()
                
                listener_task = asyncio.create_task(tester.handle_session_events())
                
                await tester.send_text(scenario['prompt'])
                
                try:
                    await asyncio.wait_for(tester.turn_completed_event.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    print("\n⚠️ Response Timeout.")
                
                listener_task.cancel()
                await asyncio.gather(listener_task, return_exceptions=True)
                
            # 세션 간 안정성을 위한 대기
            await asyncio.sleep(1)

    finally:
        tester.close()
        print("\n\n✅ 모든 실시간 업데이트 테스트 완료 (세션 재시작 방식)!")


if __name__ == "__main__":
    asyncio.run(main())
