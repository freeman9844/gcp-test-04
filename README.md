[한국어 (Korean)](README.md) | [English](README.en.md)

# Gemini Live API 동적 인스트럭션 업데이트 (오디오 이슈 해결)

이 프로젝트는 **Google Gemini Live API (Vertex AI)** 세션 중 오디오 모달리티를 유지하면서 시스템 인스트럭션(페르소나/역할)을 동적으로 업데이트하기 위한 견고한 솔루션을 제공합니다.

## 🚀 과제: 오디오 중단 이슈
`gemini-live-2.5-flash-native-audio` 모델을 사용할 때, 활성 세션 중에 시스템 인스트럭션을 업데이트하는 일반적인 방법(예: `role="system"` 콘텐츠 전송 또는 사용자 지시문)은 첫 번째 업데이트 이후 모델이 침묵하거나 세션이 타임아웃되는 현상을 자주 발생시킵니다.

## ✅ 해결책: 세션 재시작 (대기 및 재설정)
다양한 해결 방법(무음 주입, 메시지 병합 등)을 광범위하게 테스트한 결과, 현재 프리뷰 모델에서 가장 신뢰할 수 있는 방법은 **세션 재시작(Session Restart)** 전략입니다. 이 방식은 다음을 보장합니다:
1. **오디오 연속성**: 모든 응답이 새로운 오디오 생성과 함께 시작됩니다.
2. **페르소나 무결성**: 모델이 새 세션의 첫 번째 턴부터 새로운 지침을 엄격하게 따릅니다.
3. **세션 안정성**: "Native Audio" 모델이 멈추게 만드는 장기 캐시나 상태 문제를 방지합니다.

## 🛠 주요 기능
- **동적 역할극**: 도우미 비서에서 해적, 또는 한국어 번역가로 끊김 없이 전환됩니다.
- **멀티모달 지원**: `pyaudio`를 통해 텍스트와 오디오 출력을 모두 처리합니다.
- **견고한 동기화**: `asyncio.Event`를 사용하여 새 턴을 시작하기 전에 이전 응답이 완료되었는지 확인합니다.
- **상세 디버깅**: 원시 서버 응답 및 오디오 청크 수신을 추적하기 위한 통합 로깅.

## 📋 사전 요구사항
- Python 3.9 이상
- Vertex AI API가 활성화된 Google Cloud 프로젝트
- 시스템 종속성 (PyAudio용):
  - macOS: `brew install portaudio`
  - Linux: `sudo apt-get install libportaudio2`

## ⚙️ 설치 방법
1. 저장소 복제:
   ```bash
   git clone https://github.com/freeman9844/gcp-test-04.git
   cd gcp-test-04
   ```
2. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. 종속성 설치:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 사용법
`gemini_live_test.py` 파일의 `project_id`를 수정하고 실행하세요:
```bash
python gemini_live_test.py
```

### 스크립트 시나리오:
1. **턴 1**: Hello! (도우미 비서 역할)
2. **업데이트**: 해적 역할로 변경.
3. **턴 2**: Who are you? (해적으로 응답)
4. **업데이트**: 한국어 비서 역할로 변경.
5. **턴 3**: 안녕하세요. (한국어로 응답)

## 📁 프로젝트 구조
- `gemini_live_test.py`: 견고한 세션 관리가 포함된 메인 테스트 스크립트.
- `requirements.txt`: Python 패키지 종속성.
- `/specs`: 상세 기술 문서.
  - `walkthrough.md`: 실패한 접근 방식과 성공한 접근 방식의 비교 분석.
  - `implementation_plan.md`: 기술 아키텍처 및 검증 세부 정보.

