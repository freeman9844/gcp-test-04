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
        사용자가 지정한 role="system" 방식을 사용하여 지침을 업데이트합니다.
        """
        if not self.session:
            raise RuntimeError("연결된 세션이 없습니다.")

        print(f"\n🔄 [Role System Update] 지침 업데이트 중: {new_instruction[:40]}...")

        # [Crucial Fix] 오디오 모달리티 유지를 위한 무음 오디오(0.1초) 전송
        try:
            silence_data = b'\x00' * 4800 # 0.1s @ 24kHz 16bit mono
            await self.session.send_realtime_input(
                audio={"data": silence_data, "mime_type": "audio/pcm;rate=24000"}
            )
        except: pass

        await self.session.send_client_content(
            turns=[
                types.Content(
                    role="system",
                    parts=[types.Part(text=new_instruction)]
                )
            ],
            turn_complete=False # 세션을 닫지 않고 지침만 업데이트
        )
        print("   -> role='system' update sent.")

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
        
        # [Crucial Fix] 오디오 모달리티 유지를 위한 무음 오디오(0.1초) 전송
        try:
            silence_data = b'\x00' * 4800 # 0.1s @ 24kHz 16bit mono
            await self.session.send_realtime_input(
                audio={"data": silence_data, "mime_type": "audio/pcm;rate=24000"}
            )
            print("   -> Sent silence heartbeat...")
        except: pass

        print(f"\n💬 [User]: {text}")
        
        await self.session.send_client_content(
            turns=[types.Content(role="user", parts=[types.Part(text=text)])],
            turn_complete=end_of_turn
        )


async def main():
    """메인 함수: 단일 세션에서 role="system"으로 인스트럭션을 동적으로 변경하는 시나리오"""
    print("\n🚀 Google Gemini Live API Dynamic Instruction Test (role='system' in single session)\n")
    project_id = "jwlee-argolis-202104"
    
    tester = GeminiLiveAPITestVertexAI(project_id=project_id)
    
    try:
        # 1. 초기 세션 시작 (Helpful Assistant)
        async with await tester.connect(initial_instruction="You are a helpful assistant.") as session:
            tester.session = session
            # 응답 처리를 위한 리스너 시작
            listener = asyncio.create_task(tester.handle_session_events())
            
            # --- 시나리오 1: 기본 상태 ---
            tester.turn_completed_event.clear()
            await tester.send_text("Hello! What is your current role?")
            await asyncio.wait_for(tester.turn_completed_event.wait(), timeout=25.0)
            
            # --- 시나리오 2: 세션 유지 중 '해적'으로 변경 ---
            print("\n" + "="*50)
            await tester.update_system_instruction("You are now a pirate. Talk like one! Use 'Arrr' and 'Matey'.")
            
            # 지침 업데이트 후 약간의 대기 (모델이 처리할 시간)
            await asyncio.sleep(2)
            
            tester.turn_completed_event.clear()
            await tester.send_text("What is your mission as a pirate?")
            await asyncio.wait_for(tester.turn_completed_event.wait(), timeout=25.0)
            
            # --- 시나리오 3: 세션 유지 중 '한국어 비서'로 변경 ---
            print("\n" + "="*50)
            await tester.update_system_instruction("당신은 친절한 한국어 비서입니다. 정중하게 한국어로 답변하세요.")
            
            await asyncio.sleep(2)

            tester.turn_completed_event.clear()
            await tester.send_text("공식적인 첫 인사를 해주고, 어떤 도움을 줄 수 있는지 알려주세요.")
            await asyncio.wait_for(tester.turn_completed_event.wait(), timeout=25.0)
            
            # 작업 종료
            listener.cancel()
            await asyncio.gather(listener, return_exceptions=True)
            
    finally:
        tester.close()
        print("\n✅ 모든 실시간 업데이트 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
