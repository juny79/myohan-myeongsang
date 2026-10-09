# 영상 생성 프로그램 개발 현황 보고서

> **문서 버전:** v1.0  
> **작성일:** 2026-09-13  
> **상태:** 1차 개발 정리 완료 · 실제 GPU 추론 검증 대기

## 1. 요약

대시보드의 GPU 프리셋을 요청된 Wan 모델 후보와 연결하고, 모델별 공식 출처·기준 VRAM·위험 요소를 명세에 포함하도록 정리했다. 공식 Wan 추론 코드를 이용해 사전 환경 점검과 짧은 생성 시도를 수행할 수 있는 로컬 스모크 테스트 CLI 및 실행 안내도 추가했다.

이번 작업에서 **모델과 실행 절차는 지정했지만 실제 모델 파일을 다운로드하거나 GPU 추론 및 영상 생성을 완료하지는 않았다.** 이 실행 환경은 `powershell.exe`를 시작할 수 없어 단위 테스트 실행도 확인하지 못했다. 따라서 현재 상태는 “검증 준비”이며 “모델 생성 검증 성공”이 아니다.

## 2. GPU별 모델 매칭

| 프리셋 | 매칭 모델 | Hugging Face ID | 태스크·테스트 해상도 | 참조 메모리 및 주의사항 |
|---|---|---|---|---|
| RTX 3070 8GB · `local_preview` | Wan2.1 T2V 1.3B | [`Wan-AI/Wan2.1-T2V-1.3B`](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B) | Text-to-Video, 832×480 또는 480×832 | 모델 카드는 약 8.19GB VRAM을 안내한다. 8GB는 경계/부족일 수 있어 CPU offload와 T5 CPU를 사용하고, VRAM 위험을 명시적으로 허용하기 전에는 부족 판정 시 실행을 차단한다. OOM 가능성은 남는다. |
| A100 MIG 40GB · `standard_scene` | Wan2.2 TI2V 5B | [`Wan-AI/Wan2.2-TI2V-5B`](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B) | Text/Image-to-Video, 1280×704 또는 704×1280 | 공식 단일 GPU 실행 안내는 최소 24GB VRAM을 지정한다. MIG 프로파일에서 실제로 보이는 메모리를 확인해야 한다. |
| H100 SXM 80GB · `premium_scene` | Wan2.2 I2V A14B | [`Wan-AI/Wan2.2-I2V-A14B`](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B) | Image-to-Video, 1280×720 또는 720×1280 | 요청된 I2V 14B의 공식 모델 ID는 `A14B`로 표기된다. 공식 단일 GPU 실행 안내는 최소 80GB VRAM을 지정하며 입력 이미지가 필요하다. |

출처는 각 Hugging Face 모델 카드와 [Wan2.1 공식 저장소](https://github.com/Wan-Video/Wan2.1), [Wan2.2 공식 저장소](https://github.com/Wan-Video/Wan2.2)다. 모델 카드에 Apache-2.0이 표시되어 있어도 배포·수익화 전에는 특정 체크포인트, 코드, 의존성의 조건을 별도로 확인한다.

## 3. 코드 변경 내역

- `video_app/models.py`
  - 프리셋별 모델 ID, 모델 카드·공식 저장소 링크, 태스크, 권장 해상도, 프레임률, 참조 VRAM, 체크포인트 경로, 실행 태스크 인자와 위험 정보를 등록했다.
  - `describe_compatibility()`가 VRAM 적합성(`below_reference`, `meets_reference`, `unknown`)을 구분한다.
- `video_app/manifest.py`
  - 명세 스키마를 1.2로 올리고, 선택한 모델 ID·출처·참조 GPU·VRAM·검증 상태(`not_run`)를 포함한다.
  - 프리셋 타깃 해상도와 프레임률을 해당 모델 실행 설정에 맞췄다.
  - 추론이 실행된 것처럼 표시하지 않고 `inferenceStarted: false` 및 초안 상태를 유지한다.
- `video_app/server.py`와 `index.html`
  - 작업 목록 및 프리셋 선택 화면에 매칭 모델 정보를 표시한다.
  - 로컬 API는 여전히 명세 저장·조회·취소만 수행하며 추론 워커를 실행하지 않는다.
- `video_app/wan_smoke_test.py`
  - NVIDIA GPU, PyTorch CUDA, 코드 저장소, 체크포인트 폴더, I2V 입력 이미지 사전 점검을 추가했다.
  - 기본 동작은 사전 점검이며, `--run`을 명시할 때만 17프레임 테스트 명령을 호출한다.
  - Wan2.1과 Wan2.2의 서로 다른 공식 CLI 옵션을 구분한다. 결과 MP4, 로그, JSON 리포트는 `runtime/model-tests/` 아래에 저장하도록 했다.
  - RTX 3070의 기준 VRAM 위험을 기본 허용하지 않으며 `--allow-vram-risk`를 명시한 경우에만 실행을 시도한다.
- `video_app/test_manifest.py`, `video_app/test_wan_runner.py`
  - 모델 매핑, VRAM 판정, 모델별 해상도·프레임률, 공식 CLI 인자 구성을 확인하는 테스트를 추가했다.
- `video_app/MODEL_VALIDATION.md`, `video_app/README.md`, 저장소 `README.md`
  - 모델 출처, 준비 방법, 실행 절차, 알려진 제한사항을 문서화하고 관련 링크를 추가했다.

## 4. 테스트 및 생성 검증 현황

| 검증 항목 | 상태 | 비고 |
|---|---|---|
| 모델 ID와 공식 출처 확인 | 조사·기록 완료 | 공식 Hugging Face 모델 카드 기준 |
| 코드 수준 모델·프리셋 매핑 | 구현 완료 | 회귀 테스트에 포함, 단 현재 환경에서 실행 확인은 못함 |
| RTX 3070 사전점검/생성 | 미실행 | GPU·가중치·CUDA 환경에 접근 불가. 메모리 위험 때문에 명시적 동의 옵션 필요 |
| A100 MIG 40GB 사전점검/생성 | 미실행 | 실제 MIG 호스트에서 가시 VRAM 확인 필요 |
| H100 SXM 80GB 사전점검/생성 | 미실행 | 실제 H100 및 입력 이미지가 필요 |
| 생성 MP4의 육안 품질 검수 | 미실행 | 아직 생성 결과물이 없음 |

단위 테스트 실행 명령은 프로젝트 루트에서 다음과 같다.

```powershell docs/DEVELOPMENT_REPORT_v1.0.md
py -m unittest video_app.test_manifest video_app.test_wan_runner -v
```

이번 작업 중 실행을 시도했으나 도구 환경에서 `powershell.exe`를 찾지 못해 명령을 시작할 수 없었다. 테스트 통과로 보고하지 않는다.

## 5. 실제 GPU 호스트에서 진행할 절차

실행 상세와 가중치 준비 명령은 [`video_app/MODEL_VALIDATION.md`](../video_app/MODEL_VALIDATION.md)에 있다. 각 대상 GPU 호스트에서 해당 모델 하나만 준비한다.

1. CUDA가 동작하는 Python 환경에 공식 Wan 저장소 의존성을 설치하고 가중치를 내려받는다.
2. 먼저 `wan_smoke_test.py`를 `--run` 없이 실행해 GPU·PyTorch·경로·체크포인트를 확인한다.
3. `--run`을 붙여 17프레임 스모크 테스트를 실행한다. RTX 3070은 OOM 가능성을 인지한 경우에만 `--allow-vram-risk`를 추가한다.
4. JSON 리포트, 로그, MP4와 실행한 Wan 저장소 커밋·가중치 버전을 보관한다.
5. MP4를 재생해 형상, 깜빡임, 프롬프트 반영을 사람이 확인한다. 성공 결과가 있어야 그 GPU/모델 조합을 검증 통과로 판정한다.

이 스모크 테스트는 추론 연결 여부를 보는 짧은 클립이다. 프리셋 명세의 6–8초 장면 목표나 긴 최종 영상을 생성하지 않는다.

## 6. 남은 작업 및 다음 단계

1. 실제 RTX 3070, A100 MIG 40GB, H100 80GB 환경에서 환경 사전 점검과 추론 테스트를 각각 수행한다.
2. VRAM 사용량, 실행 시간, 실패 원인, 영상 품질을 기록하고 필요하면 모델 또는 GPU 프리셋을 재조정한다.
3. 생성에 성공한 모델만 API 작업 큐와 GPU 워커에 연결한다.
4. 진행률·취소·오류 복구, 검수 승인 절차, FFmpeg 조립, 권리 확인된 음원 처리를 추가한다.

**운영 상태:** 검증 대상과 반복 가능한 테스트 절차는 준비되었으나, 실제 모델 생성 테스트는 후속 작업이다.
