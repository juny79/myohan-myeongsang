# 묘한 명상

고양이와 함께, 숨을 고르는 시간.

유튜브 채널 **묘한 명상**의 전략, 콘텐츠 시스템, 운영 에이전트, 실행 대시보드 저장소입니다.

## 지금 열기

- [운영 대시보드](./index.html) — 제작 파이프라인과 주간 실행
- [STRATEGY.md](./STRATEGY.md) — 전략 요약
- [AGENT.md](./AGENT.md) — 에이전트 사용법
- [DASHBOARD.md](./DASHBOARD.md) — 대시보드 운영 규칙
- [영상 생성 종합계획](./docs/VIDEO_GENERATION_PLAN.md) — RTX 3070·A100 MIG·H100 및 대시보드 연동 로드맵
- [영상 생성 컨트롤러 사용법](./video_app/README.md) — 로컬 실행 방법과 현재 구현 범위
- [Wan 모델 검증 안내](./video_app/MODEL_VALIDATION.md) — 모델 매칭·GPU 사전 점검·짧은 생성 테스트
- [개발 현황 보고서 v1.0](./docs/DEVELOPMENT_REPORT_v1.0.md) — 현재 구현, 검증 상태, 다음 단계
- [data/board.json](./data/board.json) — 이번 주 보드 원본

## 영상 생성 프로그램 (초기 구현)

프로젝트 루트에서 `py video_app/server.py`를 실행하고 `http://127.0.0.1:8765/`를 열면 로컬 작업 컨트롤러와 대시보드 연동 패널을 확인할 수 있습니다. Python 런처가 없으면 `python video_app/server.py`를 사용하세요.

현재는 RTX 3070/A100 MIG/H100 프리셋에 Wan2.1·Wan2.2 모델 ID를 매칭하고, 로컬 GPU 호스트에서 공식 추론 코드의 사전 점검 및 짧은 생성 테스트를 실행할 CLI를 제공합니다. 테스트를 통과한 모델을 대시보드 API 작업 큐에 연결하는 단계와 실제 렌더링은 아직 구현되지 않았습니다. GitHub Pages는 정적 대시보드만 제공하며 GPU 작업 API를 실행하지 않습니다.

## 한 주가 돌는 방식

```
월 09:00 자동화 브리핑
  → 대시보드에서 화/금 프롬프트 복사
  → Grok 스킬 myohan-myeongsang 이 패키지 작성
  → 7단계 파이프라인으로 제작
  → 라이선스 게이트 통과 후 예약 공개
  → 일 한 줄 패치 + board.json 커밋
```
