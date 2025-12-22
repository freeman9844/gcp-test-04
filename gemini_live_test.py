"""
Google Gemini Live API 테스트 샘플 코드 (Vertex AI 버전) - 동적 인스트럭션 업데이트 적용
"""

import asyncio
import os
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
        
        # 오디오 관련 초기화
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
    
    async def connect(self, initial_instruction: str = "You are a helpful assistant."):
        """Live API 세션 연결을 시작합니다."""
        print(f"\n📡 Connecting to Live API (Model: {self.model_name})")
        
        config = types.LiveConnectConfig(
            system_instruction=types.Content(
                parts=[types.Part(text=initial_instruction)]
            )
        )
        
        return self.client.aio.live.connect(
            model=self.model_name,
            config=config
        )

    async def update_system_instruction(self, new_instruction: str):
        """
        [가장 신뢰할 수 있는 방식] 세션을 종료하고 새로운 인스트럭션으로 다시 연결합니다.
        2.5-flash-native-audio 모델의 현재 한계를 극복하기 위한 'Wait & Reset' 전략입니다.
        """
        print(f"\n🔄 [Session Restart] 새 지침으로 세션 재시작 중: {new_instruction[:40]}...")
        
        # 1. 기존 리스너 및 세션 종료
        if hasattr(self, '_listener_task'):
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        self._close_audio_stream()
        # 세션 닫기는 context manager가 처리하지만, 명시적으로 None 처리
        self.session = None

        # 2. 새로운 세션 연결 및 타이머 대기 (안정성을 위해 1초 대기)
        self._next_instruction = new_instruction

    async def handle_session_events(self):
        """세션으로부터 응답을 수신하고 처리합니다."""
        if not self.session:
            return
            
        self._setup_audio_stream()
        try:
            async for response in self.session.receive():
                # Verbose debug logging for EVERY response
                print(f"DEBUG: Raw response type: {type(response)}")
                
                if response.server_content:
                    print(f"DEBUG: Server Content received (turn_complete={response.server_content.turn_complete})")
                    model_turn = response.server_content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if part.text:
                                print(f"[Model]: {part.text}", end="", flush=True)
                            if part.inline_data:
                                print(f"DEBUG: Received audio chunk {len(part.inline_data.data)} bytes")
                                if self.audio_available and self.audio_stream:
                                    try:
                                        self.audio_stream.write(part.inline_data.data)
                                    except Exception as e:
                                        print(f"\n❌ Audio Write Error: {e}")
                    
                    if response.server_content.turn_complete:
                        print("\n[Turn Complete Signal Received]")
                        self.turn_completed_event.set()
                
                elif response.tool_call:
                    print(f"\n🔧 Tool call: {response.tool_call}")
                
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
        """텍스트 메시지 전송 (표준 send_client_content 사용)"""
        if not self.session:
            raise RuntimeError("Session not connected.")
        
        # [Crucial Fix] 오디오 모달리티 유지의 안정성을 위해 무음 오디오(0.1초) 전송 시도
        try:
            silence_data = b'\x00' * 4800 # 0.1s @ 24kHz 16bit mono
            await self.session.send_realtime_input(
                audio={"data": silence_data, "mime_type": "audio/pcm;rate=24000"}
            )
        except: pass

        print(f"\n💬 [User]: {text}")
        
        await self.session.send_client_content(
            turns=[types.Content(role="user", parts=[types.Part(text=text)])],
            turn_complete=end_of_turn
        )


async def main():
    """메인 함수: 세션 재시작을 통한 지침 업데이트 증명 시나리오"""
    print("\n🚀 Google Gemini Live API Dynamic Instruction Test (Reliable Session Restart)\n")
    project_id = "jwlee-argolis-202104"
    
    tester = GeminiLiveAPITestVertexAI(project_id=project_id)
    current_instruction = "You are a helpful assistant. Reply briefly."
    
    try:
        for turn_idx in range(3):
            if turn_idx == 1:
                current_instruction = "You are now a pirate. Talk like one! Arrr!"
            elif turn_idx == 2:
                current_instruction = "당신은 친절한 한국어 비서입니다. 정중하게 한국어로 답변하세요."

            print(f"\n" + "="*60)
            print(f"📡 Starting Session Turn {turn_idx+1} with Instruction: {current_instruction[:30]}...")
            
            async with await tester.connect(initial_instruction=current_instruction) as session:
                tester.session = session
                tester.turn_completed_event.clear()
                
                # 응답 처리를 위한 리스너 시작
                tester._listener_task = asyncio.create_task(tester.handle_session_events())
                
                if turn_idx == 0:
                    await tester.send_text("Hello! What is your current role?")
                elif turn_idx == 1:
                    await tester.send_text("Who are you now, and what is your pirate mission?")
                else:
                    await tester.send_text("방금 어떤 컨셉이었는지 설명해주고, 현재 어떤 서비스를 제공가능한지 정중히 답변해주세요.")
                
                # 응답 완료 대기
                try:
                    await asyncio.wait_for(tester.turn_completed_event.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    print("\n⚠️ Response Timeout.")
                
                # 다음 턴을 위해 리스너 종료 및 세션 닫기
                tester._listener_task.cancel()
                await asyncio.gather(tester._listener_task, return_exceptions=True)
                print(f"📴 Closed Session Turn {turn_idx+1}")
            
            await asyncio.sleep(1) # 안정적인 재연결을 위한 간격

    finally:
        tester.close()
        print("\n✅ 모든 실시간 업데이트 테스트 완료 (세션 재시작 방식)!")


if __name__ == "__main__":
    asyncio.run(main())
