# shootthemoon — Macuahuitl v11 양손 대검 뷰모델

OVERDARE 게임 `onlyoneshot` 의 `maxico` 직업 뷰모델. 한손 → 양손 대검 전환(v11) 결과물.

![양손 파지](docs/grip_twohand.png)

| 무기 모델 (TwoHand 1.55 m) | 변신 — 문양이 손잡이 쪽부터 차오름 | 변신 완료 |
|---|---|---|
| ![모델](docs/model_twohand.png) | ![차오르는 중](docs/transform_glow_half.png) | ![변신 발광](docs/transform_glow.png) |

발광 텍스처 3단계 (채움 35% / 70% / 100%) — 궁 쓰면 이 순서로 바뀐다.

![발광 텍스처](docs/glow_textures.png)

| 문서 | 내용 |
|---|---|
| [SPEC_v11_KO.md](SPEC_v11_KO.md) | **명세서 — 현재 상태 기준** (파트·좌표 규약·클립 32개·변신 발광·게임 반영·OVERDARE 규칙) |
| [WORK_LOG_KO.md](WORK_LOG_KO.md) | 작업 기록 (요청 → 원인 → 조치) |
| [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md) | Blender 제작 단계 세부 수치 (v11.0~v11.4) |
| [SKILL_CATALOG_KO.md](SKILL_CATALOG_KO.md) | 동작 영상 목록 |
| [Import_OVERDARE/IMPORT_GUIDE_KO.md](Import_OVERDARE/IMPORT_GUIDE_KO.md) | Studio 임포트 절차 |

| 폴더 | 내용 |
|---|---|
| `Clips/` `Transitions/` | 동작 32개 · 전환 20개 Lua 클립 |
| `Scripts/` | 제작 스크립트 (Blender 백그라운드 실행) |
| `Import_OVERDARE/` | 게임 임포트 패키지 (Lua · 텍스처 · 배치표) |
| `Game_Integration/` | 게임에 들어간 스크립트 현재본 사본 |

메시(`.blend` `.fbx`), 영상(`.mp4`), 체크포인트, 영상 렌더 프레임은 용량 때문에 제외 — 로컬 폴더와 바탕화면 zip 에 있다.
