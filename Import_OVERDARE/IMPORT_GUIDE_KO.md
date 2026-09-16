# Macuahuitl v11 (양손) — OVERDARE 전체 재임포트 가이드

게임 `onlyonetap`(onlyoneshot) 의 `maxico` 직업 뷰모델을 **팔 6 + 무기 3, 9파트 전부 새로** 넣고 클립 32개를 교체한다.
작성 2026-09-14 · 패키지 폴더 `C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand\Import_OVERDARE\`

---

## 0. 먼저 알아둘 것

| 항목 | 내용 |
|---|---|
| 지금 게임 상태 | `Workspace.Macuahuitl_Viewmodel` (9 MeshPart, v03 무기 + 옛 손 메시) · `ReplicatedStorage.ViewmodelAnimMaxico*` 32개 = v10 |
| 바꾸는 것 | 9파트 메시 전부 + 클립 모듈 32개 |
| 안 바꾸는 것 | `ViewmodelConfig` 의 `SOURCE = "Macuahuitl_Viewmodel"` · `PIVOT {1000, 15.7171, 1230}` · `OFFSET` · `YAW` · `CLIPS` (모듈 이름 동일) |
| 삼각형 한도 | OVERDARE 메시 1개당 30,000 — 9파트 모두 통과 (흑요석은 194,120 → 28,420 감축, 원본과 표면 차이 평균 0.5 mm) |
| 색 | MeshPart 는 파트당 색 1개. 몸체만 **텍스처**, 나머지는 단색 |
| 손 메시 | 지금 게임 손은 옛 버전이라 크기가 조금 다르다. 새 손은 v10·v11 애니메이션을 만든 그 손 (위치 차이 R 1.4 cm · L 0.3 cm) |
| Studio FBX Import | 파츠 상대 위치를 보존하지 못한다 (v03 때 확인). 그래서 **파트마다 FBX 를 따로** 만들었고 **위치는 표 값으로 직접 입력**한다 |

## 1. 백업

Studio 저장 후 프로젝트 파일 복사. 예: `onlyoneshot.ovdrjm` → `onlyoneshot_BEFORE_MACUAHUITL_V11_20260914.ovdrjm`

## 2. 기존 모델 치우기

컨트롤러는 **이름으로** 모델을 찾는다 (`ReplicatedStorage` → `Workspace` 순, 첫 번째). 같은 이름이 둘이면 옛것이 잡힐 수 있다.
- 기존 `Workspace.Macuahuitl_Viewmodel` 을 `ZZ_Macuahuitl_Viewmodel_v03` 으로 이름 바꾸고 멀리 옮겨 둔다 (문제없으면 나중에 삭제)

## 3. FBX 9개 임포트

`Meshes\` 의 9개를 Studio **Home > Import** (또는 Bulk Import) 로 가져오고, 에셋마다 **MeshId** (몸체는 **TextureId** 도) 를 기록한다.

| 파일 (`Import_OVERDARE\Meshes\`) | 삼각형 |
|---|---|
| `Macuahuitl_Viewmodel_v11_MAC_R_UpperArm.fbx` | 74 |
| `Macuahuitl_Viewmodel_v11_MAC_R_LowerArm.fbx` | 28 |
| `Macuahuitl_Viewmodel_v11_MAC_R_Hand.fbx` | 114 |
| `Macuahuitl_Viewmodel_v11_MAC_L_UpperArm.fbx` | 68 |
| `Macuahuitl_Viewmodel_v11_MAC_L_LowerArm.fbx` | 56 |
| `Macuahuitl_Viewmodel_v11_MAC_L_Hand.fbx` | 114 |
| `Macuahuitl_Viewmodel_v11_MAC_Handle.fbx` | 18,470 |
| `Macuahuitl_Viewmodel_v11_MAC_Body.fbx` | 1,054 (텍스처 포함) |
| `Macuahuitl_Viewmodel_v11_MAC_Obsidian.fbx` | 28,420 |

몸체 TextureId 가 자동으로 안 붙으면 `Textures\T_MAC_Body_BaseColor_1024.png` 를 이미지로 따로 넣고 그 id 를 쓴다.

## 4. 새 모델 조립

1. `Workspace` 에 **Model** 을 만들고 이름을 정확히 **`Macuahuitl_Viewmodel`** 로
2. 그 안에 **MeshPart 9개**, 이름을 표와 정확히 같게 (`MAC_*`)
3. 각 파트에 아래 값 입력. 전부 **Anchored = true**, **CanCollide = false** 권장, **CastShadow = false** (기존과 같음)

| 파츠 | CFrame Position (X, Y, Z) | Orientation | 예상 Size (cm) | Color | Material | TextureId |
|---|---|---|---|---|---|---|
| `MAC_R_UpperArm` | (1026.9105, 16.4498, 1228.7749) | (0, 0, 0) | (18.304, 16.13, 20.391) | 60, 91, 95 | Plastic | — |
| `MAC_R_LowerArm` | (1029.8732, 14.7293, 1210.1159) | (0, 0, 0) | (17.679, 11.718, 16.937) | 60, 91, 95 | Plastic | — |
| `MAC_R_Hand` | **(1018.8441, 13.3242, 1197.4399)** | (0, 0, 0) | (21.908, 19.282, 15.976) | 60, 91, 95 | Plastic | — |
| `MAC_L_UpperArm` | (973.0896, 14.9843, 1231.2251) | (0, 0, 0) | (21.229, 18.11, 17.289) | 60, 91, 95 | Plastic | — |
| `MAC_L_LowerArm` | (970.5249, 10.7773, 1214.9564) | (0, 0, 0) | (18.248, 10.999, 15.939) | 60, 91, 95 | Plastic | — |
| `MAC_L_Hand` | **(972.7396, 11.8036, 1194.0138)** | (0, 0, 0) | (17.541, 16.924, 25.469) | 60, 91, 95 | Plastic | — |
| `MAC_Handle` | **(1013.3416, −1.6155, 1212.5635)** | (0, 0, 0) | (16.173, 48.839, 43.327) | 58, 54, 50 | Plastic | — |
| `MAC_Body` | **(1027.6355, 57.5089, 1160.9976)** | (0, 0, 0) | (30.209, 76.136, 66.86) | 255, 255, 255 | Plastic | 몸체 텍스처 |
| `MAC_Obsidian` | **(1027.1834, 59.3078, 1159.4515)** | (0, 0, 0) | (37.496, 68.993, 57.393) | 46, 50, 56 | Metal | — |

- 굵은 값 = 지금 게임과 달라지는 위치. 위팔·아래팔 4개는 지금 게임과 같은 값 (0.0001 cm 이내 확인)
- 좌표식 (게임 `ViewmodelConfig` 주석과 같음): `level = 100 × (−x, z, y) + (1000.944095, −92.593801, 1230.791631)`
- 각 FBX 는 메시 중심이 원점이라, Position = 메시 중심 위치다
- Size 는 임포트가 채운다. 표와 크게 다르면 스케일이 틀린 것 (cm 기준 ×100 으로 들어와야 정상)
- 몸체 텍스처가 안 붙으면 Color 를 **120, 72, 44** (나무색)
- 게임 레벨 색은 런타임 칠하기가 안 먹어서 **파츠 Color 필드에 직접** 넣어야 한다 (`docs/japan1_viewmodel.md` 4장)

## 5. 클립 모듈 32개 교체

`Lua\ViewmodelAnimMaxico*.lua` 32개를 `ReplicatedStorage` 의 **같은 이름 ModuleScript** 소스로 통째로 붙여넣는다.
(게임 파일 형식 CRLF · `parts` 9개 · `posScale 240` 그대로)

### 길이가 바뀐 동작 (게임 타이밍 영향)

| 동작 | v10 → v11 | hitAt |
|---|---|---|
| Attack1 · 2, Walk/SprintAttack1 · 2 | 1.0 → **1.8초** | 0.5 → **0.8** |
| Attack3, Walk/SprintAttack3 | 1.3 → **2.333초** | 0.6 → **1.0** |
| CrouchAttack | 1.2 → **2.2초** | 0.467 → **0.8335** |
| Draw · Holster · SprintDraw · SprintTwirl | → **1.833 · 1.133 · 1.667 · 1.967초** | — |
| BlockIn · BlockOut | → **0.433 · 0.567초** | — |
| Idle · Intro · Transform · UltAttack · JumpSlam · RareDraw | 3.9667초 그대로 | UltAttack 1.5821 · JumpSlam 1.795 그대로 |
| 이동 · 웅크리기 진입/대기/해제 · BlockHold | 그대로 | — |

컨트롤러가 `clip.duration` · `clip.hitAt` · `clip.cut` 을 클립에서 읽어 **코드 수정 없이** 반영된다.
콤보 입력 창·공격 쿨다운이 따로 하드코딩돼 있으면 맞춰야 한다.

## 6. 확인 (플레이테스트)

1. 로비에서 `maxico` 선택 → 로그 `[VM] pick=maxico src=Macuahuitl_Viewmodel parts=9 pivot=(1000.0, 15.7, 1230.0)`
   - `source NOT FOUND` 이면 모델 이름 오타 / `parts` 가 9 가 아니면 파트 이름 오타
2. 대기 자세에서 두 손이 손잡이를 쥐고, 무기·팔이 떨어져 있지 않은지
   - 한 조각만 어긋나면 그 파트 Position 오타 / 전체가 커지거나 작으면 Size 스케일
3. 평타 1~3타 · 막기 · 달리기 · 궁(Transform → 클릭 → UltAttack) · RareDraw(공격 길게 누르기)
4. 참고 영상: `..\Motions_v11_4.mp4`

## 7. 이번에 게임에 안 들어가는 것 (후속)

| 항목 | 이유 |
|---|---|
| ~~변신 문양 발광~~ | **이후 게임에 반영됨** — 발광 텍스처 3장 + 몸체 사본 `MAC_Body_Glow1~3` + 컨트롤러 교체 로직 (`..\SPEC_v11_KO.md` 7-2 · 8절) |
| 손 펴기/쥐기 교체, `left_grip_*` · `heavy_windup` 등 새 이벤트 | 컨트롤러가 안 읽음 (`Data\clip_manifest.json`) |
| 전환 클립 20개 | 게임이 전환 모듈을 쓰지 않음. v11 폴더 `Transitions\` |
| 스킨 4종 · Deploy_1~6 | 아직 v10 한손 무기 |
| 손잡이 구리·옥 색 | 파트당 1색이라 합쳐짐 |
| RareDraw 부메랑 최대 4.3 m | 벽 관통 확인 |

## 8. 폴더

```
Import_OVERDARE\
  IMPORT_GUIDE_KO.md      이 문서
  level_placement.json    4장 표의 원본 수치
  Meshes\                 FBX 9개
  Textures\               몸체 텍스처 1024x256 · 발광 마스크
  Lua\                    클립 모듈 32개
  Data\                   clip_manifest · effect_events · mesh_contract (참고)
  QA\                     흑요석 감축 전후 비교
```
생성 스크립트: `..\Scripts\v11_overdare_import.py`
