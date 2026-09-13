# 묘한 명상

고양이와 함께, 숨을 고르는 시간.

유튜브 채널 **묘한 명상**의 전략, 콘텐츠 시스템, 운영 에이전트, 실행 대시보드 저장소입니다.

## 지금 열기

- [운영 대시보드](./index.html) — 제작 파이프라인과 주간 실행
- [STRATEGY.md](./STRATEGY.md) — 전략 요약
- [AGENT.md](./AGENT.md) — 에이전트 사용법
- [DASHBOARD.md](./DASHBOARD.md) — 대시보드 운영 규칙
- [data/board.json](./data/board.json) — 이번 주 보드 원본

## 한 주가 돌는 방식

```
월 09:00 자동화 브리핑
  → 대시보드에서 화/금 프롬프트 복사
  → Grok 스킬 myohan-myeongsang 이 패키지 작성
  → 7단계 파이프라인으로 제작
  → 라이선스 게이트 통과 후 예약 공개
  → 일 한 줄 패치 + board.json 커밋
```
