# Wan 모델 매칭 및 생성 스모크 테스트

## 검증 대상 매칭

| 프로그램 프리셋 | Hugging Face 모델 ID | 태스크 | 참조 GPU/메모리 | 비고 |
|---|---|---|---|---|
| `local_preview` | `Wan-AI/Wan2.1-T2V-1.3B` | Text-to-Video | RTX 3070 8GB | 공식 모델 카드가 약 8.19GB VRAM을 언급하므로 8GB 카드는 기준 미달 가능성이 있습니다. CPU offload/T5 CPU를 사용해도 OOM을 배제할 수 없어 기본 실행은 차단됩니다. |
| `standard_scene` | `Wan-AI/Wan2.2-TI2V-5B` | Text/Image-to-Video | A100 MIG 40GB | 공식 실행 안내의 최소 단일 GPU 기준은 24GB VRAM입니다. 실제 MIG 가시 메모리와 여유 메모리를 사전 점검합니다. |
| `premium_scene` | `Wan-AI/Wan2.2-I2V-A14B` | Image-to-Video | H100 SXM 80GB | 요청하신 I2V 14B에 해당하는 공식 모델 ID는 `A14B` 표기입니다. 공식 안내는 단일 GPU에서 최소 80GB VRAM을 지정합니다. 입력 이미지가 필수입니다. |

정확한 출처: [Wan2.1 T2V 1.3B 모델 카드](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B), [Wan2.2 TI2V 5B 모델 카드](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B), [Wan2.2 I2V A14B 모델 카드](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B), [Wan 공식 추론 코드](https://github.com/Wan-Video/Wan2.2).

모델 카드의 Apache-2.0 표기와 별개로, 실제 가중치 파일·추론 코드·의존성의 사용 조건을 배포/수익화 전에 다시 확인하세요. 이 매칭은 **검증 대상 지정**이며, 세 모델을 다운로드하거나 이 환경에서 추론 성공을 확인했다는 뜻은 아닙니다.

## 입력한 로컬 GPU 환경에서 준비

추론 코드는 저장소에서 지정한 Python 환경과 별도로 CUDA가 활성화된 PyTorch 및 Wan 공식 코드 의존성이 필요할 수 있습니다. CUDA/FlashAttention 의존성은 OS에 따라 설치 가능성이 달라집니다. GPU가 있는 Linux 환경 또는 검증된 CUDA 개발 환경에서 먼저 준비하고, 같은 Python 실행 파일로 아래 스크립트를 호출하세요. 전체 14B 가중치와 3개 체크포인트를 한 번에 받을 필요는 없습니다. 각 GPU에서 해당 모델 하나만 준비합니다.

프로젝트 루트의 PowerShell에서 필요한 조합만 실행합니다. 모델 파일은 Git에 올리지 마세요.

```powershell video_app/MODEL_VALIDATION.md
# RTX 3070 호스트: Wan2.1 코드와 T2V 1.3B 가중치
New-Item -ItemType Directory -Force runtime/wan | Out-Null
git clone https://github.com/Wan-Video/Wan2.1.git runtime/wan/Wan2.1
hf download Wan-AI/Wan2.1-T2V-1.3B --local-dir runtime/models/Wan2.1-T2V-1.3B

# A100 MIG 또는 H100 호스트: Wan2.2 코드
New-Item -ItemType Directory -Force runtime/wan | Out-Null
git clone https://github.com/Wan-Video/Wan2.2.git runtime/wan/Wan2.2

# A100 MIG 40GB 호스트에서 실행할 때만 다운로드
hf download Wan-AI/Wan2.2-TI2V-5B --local-dir runtime/models/Wan2.2-TI2V-5B

# H100 80GB 호스트에서 실행할 때만 다운로드
hf download Wan-AI/Wan2.2-I2V-A14B --local-dir runtime/models/Wan2.2-I2V-A14B
```

`hf` 명령을 찾을 수 없다면 해당 Wan 추론용 Python 환경에서 Hugging Face Hub CLI를 설치하세요. 저장소 코드는 가능하면 테스트 완료한 Git 커밋으로 고정하고, 가중치 revision/다운로드 시점과 파일 해시를 테스트 기록에 남기는 것을 권장합니다.

## 사전 점검과 실제 생성 테스트

`wan_smoke_test.py`는 `nvidia-smi`, PyTorch CUDA, 공식 저장소 경로, 체크포인트 디렉터리 및 필요한 I2V 입력 이미지를 확인합니다. 기본 실행은 **사전 점검만** 하며 영상 생성은 하지 않습니다. `--run`을 붙였을 때만 17프레임짜리 짧은 공식 추론 명령을 실행합니다. 결과 MP4, 로그, JSON 리포트는 `runtime/model-tests/` 아래에 저장됩니다.

```powershell video_app/MODEL_VALIDATION.md
# 먼저 사전 점검만 (실제 추론 안 함)
py video_app/wan_smoke_test.py --preset local_preview --repo-dir runtime/wan/Wan2.1 --checkpoint-dir runtime/models/Wan2.1-T2V-1.3B

# RTX 3070: 모델 카드의 VRAM 기준보다 낮을 수 있음을 알고 실제 시도를 허용할 때만 추가
py video_app/wan_smoke_test.py --preset local_preview --repo-dir runtime/wan/Wan2.1 --checkpoint-dir runtime/models/Wan2.1-T2V-1.3B --run --allow-vram-risk

# A100 MIG 40GB
py video_app/wan_smoke_test.py --preset standard_scene --repo-dir runtime/wan/Wan2.2 --checkpoint-dir runtime/models/Wan2.2-TI2V-5B --run

# H100 SXM 80GB: 공식 저장소의 예시 이미지를 시작 이미지로 이용
py video_app/wan_smoke_test.py --preset premium_scene --repo-dir runtime/wan/Wan2.2 --checkpoint-dir runtime/models/Wan2.2-I2V-A14B --image runtime/wan/Wan2.2/examples/i2v_input.JPG --run
```

GPU 메모리가 부족하거나 CUDA 환경이 맞지 않으면 테스트는 실패하며, 자동으로 VRAM을 초과 실행하거나 무한 재시도하지 않습니다. RTX 3070에서 `--allow-vram-risk`는 OOM 가능성을 수락하는 명시적 선택입니다. 클라우드 GPU를 이 저장소에서 원격 호출하지는 않습니다. 각 호스트에서 로컬로 실행하세요.

## 이번 스모크 테스트의 통과 조건

1. 사전 점검 리포트가 올바른 GPU/가중치/공식 코드 경로를 표시한다.
2. 실제 실행 결과가 0 종료 코드이고 결과 MP4가 비어 있지 않다.
3. 영상 파일을 재생해 고양이 형태, 깜빡임, 프레임 깨짐, 프롬프트 반영을 사람이 확인한다.
4. JSON 리포트, 실행 로그, 저장소 commit, 다운로드한 가중치의 식별 정보를 보관한다.

이것은 **짧은 추론 연결 테스트**이지 품질 승인이나 상업적 사용 허가가 아닙니다. 대시보드 API는 아직 Wan 워커를 자동 실행하지 않습니다.
