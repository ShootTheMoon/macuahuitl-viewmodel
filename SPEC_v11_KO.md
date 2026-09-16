# Macuahuitl v11 양손 대검 뷰모델 — 명세서

작성 2026-09-14 · 대상 게임 `C:\Users\29\Desktop\onlyonetap` (`onlyoneshot.ovdrjm`, 직업 `maxico`)
작업 폴더 `C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand\`

> 이 문서가 **현재 상태의 기준**이다. 과정·버전별 변경 이유는 `WORK_LOG_KO.md`, Blender 제작 세부 수치는 `CLAUDE_HANDOFF.md`, Studio 수동 임포트 절차는 `Import_OVERDARE/IMPORT_GUIDE_KO.md` 에 있다. 수치가 서로 다르면 이 문서가 우선한다.

---

## 1. 한눈에 보기

| 항목 | 현재 상태 |
|---|---|
| 무기 모델 | `Macuahuitl_TwoHand.glb` 를 **0.8배 (전장 1.55 m)** 로 사용, 3파트 (Handle · Body · Obsidian) |
| 파지 | 한손 → **양손 대검**. 오른손 날 쪽(모델 x 0.45), 왼손 폼멜 쪽(x 0.65), 간격 16 cm |
| 뷰모델 파트 | 팔 6 + 무기 3 = 9파트 (게임 레벨에는 변신 발광용 몸체 사본 3개 추가 → 12) |
| 애니메이션 | 동작 32개 + 전환 20개. 무겁게 리타이밍(버서커 느낌), RareDraw 새로 제작 |
| 변신(궁) | Transform 중 몸체 문양이 손잡이 쪽부터 칼끝까지 차오르며 빛남 → UltAttack 타격 뒤 꺼짐 |
| 게임 반영 | **완료** — 레벨 9파트 교체 + 발광 파트 3개, 클립 모듈 32개 교체, 컨트롤러 수정 3건 |
| 사용자 확인 대기 | 궁 변신 발광이 실제로 보이는지 · 궁 사용 시 화질 저하가 해결됐는지 (제작 측에서는 궁 버튼을 누를 수 없어 미확인) |

---

## 2. 무기 모델 · 파트

### 2-1. 원본과 분할
- 원본 `Macuahuitl_TwoHand.glb` 전장 1.94 m → **×0.8 = 1.55 m** (v10 한손 무기 0.90 m). 크기는 게임 카메라 비교 렌더 4장 중 사용자 선택
- 오른손을 v10 과 같은 위치에 두고 날 방향·폭 방향을 v10 무기 축에 맞춤. 손잡이 반경 2.4 cm (v10 2.7 cm) → 기존 손 메시가 맞음

| 파트 | 포함 | Blender 정점 | 게임용 삼각형 |
|---|---|---|---|
| `MAC_Handle` | 가죽 감개 · 위/아래 구리 고리 · 옥 폼멜 · 구리 가면 | 11,100 | 18,470 |
| `MAC_Body` | 나무 패들 (문양 텍스처) | 1,193 | 1,054 |
| `MAC_Obsidian` | 흑요석 날 10 · 조각 70 | 380,828 | **28,420** (194,120 → 감축, 원본 표면과 평균 차이 0.5 mm) |
| 팔 6개 | v10 기본 팔 메시 그대로 (늘리지 않음) | — | 28 ~ 114 |

- OVERDARE 메시 1개당 삼각형 한도 30,000 → 흑요석만 감축 (사용자 결정)
- MeshPart 는 파트당 색 1개 → 몸체만 텍스처, 손잡이는 단색(구리·옥 색은 감개 색으로 합쳐짐)

### 2-2. 게임 레벨 파트 (`Workspace.Macuahuitl_Viewmodel`, Model GUID `31D1C07741E8683FCA03859CFC230616`)

전부 Orientation (0,0,0) · Anchored · CastShadow false. 좌표식 `level = 100 × (−x, z, y) + (1000.944095, −92.593801, 1230.791631)` (Blender 휴지 월드 → 레벨 cm)

| 파트 | MeshId (STATIC_MESH) | Position | Size (cm) | Color | Material | TextureId | GUID |
|---|---|---|---|---|---|---|---|
| MAC_R_UpperArm | 45721500 | (1026.9105, 16.4498, 1228.7749) | (18.304, 16.13, 20.391) | 60,91,95 | Plastic | — | 3B0AFDA04E99F7163EE737A2993AD3F9 |
| MAC_R_LowerArm | 45721400 | (1029.8732, 14.7293, 1210.1159) | (17.679, 11.718, 16.937) | 60,91,95 | Plastic | — | 6D33A1C94893F5E17A2A43BBF16932F5 |
| MAC_R_Hand | 45720400 | (1018.8441, 13.3242, 1197.4399) | (21.908, 19.282, 15.976) | 60,91,95 | Plastic | — | E02B74E840BCD41EC5968CBCFE2FFCD9 |
| MAC_L_UpperArm | 45720300 | (973.0896, 14.9843, 1231.2251) | (21.229, 18.11, 17.289) | 60,91,95 | Plastic | — | 92FF6F6D48F75B5A3D370A8797335B20 |
| MAC_L_LowerArm | 45720200 | (970.5249, 10.7773, 1214.9564) | (18.248, 10.999, 15.939) | 60,91,95 | Plastic | — | 8318A426466D8890F8BA8CACA001CE37 |
| MAC_L_Hand | 45721200 | (972.7396, 11.8036, 1194.0138) | (17.541, 16.924, 25.469) | 60,91,95 | Plastic | — | DB90FFBA41994F08403E719A671C61B5 |
| MAC_Handle | 45721300 | (1013.3416, −1.6155, 1212.5635) | (16.173, 48.839, 43.327) | 58,54,50 | Plastic | — | 7DA62A0740F225C83271B7902650D941 |
| MAC_Body | 45721100 | (1027.6355, 57.5089, 1160.9976) | (30.209, 76.136, 66.86) | 255,255,255 | Plastic | 45720100 | F22AF6CF40AA51F71AD42AAE66499FF9 |
| MAC_Obsidian | 45720500 | (1027.1834, 59.3078, 1159.4515) | (37.496, 68.993, 57.393) | 46,50,56 | Metal | — | 3878C84C40CFC30D35705D889669F5D7 |
| **MAC_Body_Glow1** | 45721100 | = MAC_Body | = MAC_Body | 255,255,255 | Plastic | **45724100** (채움 35%) | 4EDA260F4A694479113261A38962C6F0 |
| **MAC_Body_Glow2** | 45721100 | = MAC_Body | = MAC_Body | 255,255,255 | Plastic | **45724200** (채움 70%) | 5A2D50BB46A2D46861B0D3BF439B2DEB |
| **MAC_Body_Glow3** | 45721100 | = MAC_Body | = MAC_Body | 255,255,255 | Plastic | **45725100** (채움 100%) | D1B2D4FA4E30F7B8327529A6CC293545 |

- 로비 진열대(`LobbyUI.lua` `maxico.groups`)는 `MAC_Handle / MAC_Body / MAC_Obsidian` 이름만 복제 → 발광 사본은 로비에 안 나옴
- 게임 원본 수치: `Import_OVERDARE/level_placement.json`

---

## 3. 좌표 · 클립 형식 규약

| 항목 | 값 |
|---|---|
| Lua 클립 행 | `{ t, 파트1(px,py,pz, qw,qx,qy,qz), … 파트9 }` = 64개 값, 30 fps |
| 파트 순서 | `MAC_R_UpperArm, MAC_R_LowerArm, MAC_R_Hand, MAC_L_UpperArm, MAC_L_LowerArm, MAC_L_Hand, MAC_Handle, MAC_Body, MAC_Obsidian` |
| `posScale` | 240 |
| 클립 헤더 | `duration`, `full`, `loop`, (`hitAt`, `cut`, `jumpAt`, `airHoldStart`), `posScale`, `parts`, `frames` |
| Lua → Blender | 쿼터니언 (w, −x, z, y) · 이동 (−px, pz, py) |
| 강체 변환 | 모든 파트가 공통 회전 중심 **P = (0.0094, −0.0079, 1.0831)** 기준: `M = T(P+pos)·R(q)·T(−P)·T(휴지)` (`Scripts/v11_convention.py`, v10 씬 대조 오차 0) |
| 게임 설정 (`ViewmodelConfig` maxico) | `SOURCE "Macuahuitl_Viewmodel"` · `PIVOT {1000, 15.7171, 1230}` (양 위팔 중점) · `OFFSET {-10,-70,-75}` · `YAW 0` · `ANIM true` |
| 런타임 | 컨트롤러가 모델을 `Wakizashi_Viewmodel_Runtime` 으로 복제, 크기 ×`Config.SCALE`(2.4) |
| 모듈 이름 | `ReplicatedStorage.ViewmodelAnimMaxico<이름>` (`ViewmodelConfig.CLIPS` 표로 매핑, v10 과 동일) |
| 줄바꿈 | 게임 모듈 CRLF, 들여쓰기 탭 |

---

## 4. 애니메이션 클립 32개 (`Clips/`, 게임 `ReplicatedStorage`)

| 모듈 | 프레임 | 길이(초) | 루프 | hitAt | 양손 처리 · 주요 이벤트 (프레임은 1부터, time=(f−1)/30) |
|---|---|---|---|---|---|
| MaxicoIdle | 120 | 3.9667 | ✔ | — | 양손 대기 |
| MaxicoIntro (FirstDraw) | 120 | 3.9667 | | — | 오른손 파지 → 왼손 합류 f39 · deploy_start f54 · transform_lock f62 |
| MaxicoDraw | 56 | 1.8333 | | — | 왼손 합류 f21 |
| MaxicoHolster | 35 | 1.1333 | | — | 왼손 이탈 f9 |
| MaxicoSprintDraw | 51 | 1.6667 | | — | 왼손 합류 f33 |
| MaxicoRunStart / RunLoop / RunStop | 13 / 25 / 13 | 0.4 / 0.8 / 0.4 | RunLoop ✔ | — | 양손 |
| MaxicoWalkStart / WalkLoop / WalkStop | 7 / 25 / 7 | 0.2 / 0.8 / 0.2 | WalkLoop ✔ | — | 양손 |
| MaxicoSprintTwirl | 60 | 1.9667 | | — | 왼손 놓기 f7 → 회전 → 재파지 f54 (이동 중 자동 장식 회전) |
| MaxicoAttack1 · 2 | 55 | 1.8 | | 0.8 | whoosh f19 · impact f25 |
| MaxicoAttack3 | 71 | 2.3333 | | 1.0 | whoosh f23 · impact f31 |
| MaxicoWalkAttack1 · 2 / SprintAttack1 · 2 | 55 | 1.8 | | 0.8 | 같음 |
| MaxicoWalkAttack3 / SprintAttack3 | 71 | 2.3333 | | 1.0 | 같음 |
| MaxicoCrouchIn / CrouchIdle / CrouchOut | 19 / 61 / 19 | 0.6 / 2.0 / 0.6 | CrouchIdle ✔ | — | 양손 |
| MaxicoCrouchAttack | 67 | 2.2 | | 0.8333 | whoosh f23 · impact f26 |
| MaxicoBlockIn / BlockHold / BlockOut | 14 / 31 / 18 | 0.4333 / 1.0 / 0.5667 | BlockHold ✔ | — | 양손 대각선 가드 (칼날 화면 오른쪽, 넓은 면 정면) |
| MaxicoJumpSlam | 120 | 3.9667 | | 1.7951 | jumpAt 1.2543 · whoosh f40 · impact f55 |
| MaxicoTransform | 120 | 3.9667 | | — | 변신. 발광 glow_key 2프레임 간격 (7절) |
| MaxicoUltAttack | 120 | 3.9667 | | 1.5821 | 궁 타격. 타격 섬광 후 발광 꺼짐 |
| MaxicoRareDraw | 120 | 3.9667 | | — | 버서커식 두 손 수평 휘둘러 던지는 부메랑 (4-1) |

- 컨트롤러는 클립의 `duration / full / hitAt / cut / jumpAt / airHoldStart` 만 읽는다. `hand_mesh`, `left_grip_*`, `heavy_windup`, `glow_key` 등 매니페스트 이벤트는 읽지 않는다
- 게임 타이밍 영향: 평타 한 타 1.8~2.33초 (v10 1.0~1.3초), 궁 버튼 → 타격 약 5.55초 (Transform 3.97 + hitAt 1.58)

### 4-1. RareDraw (공격 길게 누르기, 장식 동작)
| row | 동작 |
|---|---|
| 0–40 | 칼날을 수평으로 눕혀 두 손으로 오른쪽 뒤로 감음 (몸 14° 비틀고 3 cm 가라앉음, heavy_windup f29) → 몸을 풀며 오른쪽→왼쪽 수평 휘두르기 |
| 40 | **두 손 동시 놓음** (release f41, 양손 hand_mesh Open) |
| 41–87 | 휘두르던 속도·회전 그대로 왼쪽 앞으로 수평 회전 비행 → row 60 약 4.3 m 반환 (turnaround f61) → 오른쪽으로 돌아옴 (return_whoosh f79, pitch_up f81) |
| 88 | 회전 멈추며 손잡이를 손 쪽으로 → **두 손 같이 잡음** (catch f89, camera_kick 0.8°) |
| 88–119 | 무게에 몸째 끌려 7 cm 들어오고 10 cm 가라앉았다 버팀 |

### 4-2. 무게감 (리타이밍 `Scripts/v11_retime.py`)
- 평타 10개: 예비 ×1.8 · 휘두르기 ×1.3 · 타격 뒤 **4프레임 히트스톱** · 회수 ×1.7 + 무게 레이어(예비 하중 10°, 밀고 나감 14°) + **arc/dip 레이어**(무기+손이 최고점 +4 cm, 타격 −15 cm·앞 6 cm, 전체 −3.5 cm 가라앉음. CrouchAttack −7 cm, JumpSlam·UltAttack −12 cm)
- Draw · Holster · SprintDraw · SprintTwirl 균일 ×1.4, BlockIn · BlockOut ×1.45
- 타격 프레임·첫/끝 프레임 행 값은 원본과 오차 0 (전환 호환)

## 5. 전환 20개 (`Transitions/`)
- Idle · Run · Crouch · Block · Holster 사이 5프레임(0.1333초) 전환 20종
- v10 경로 리타깃 + 끝점을 v11 자세 행에 0 cm 고정
- **현재 게임은 전환 모듈을 쓰지 않는다** (게임에 넣지 않음)

---

## 6. 이벤트 · 효과 계약 (`effect_events.json`, `clip_manifest.json`)

| 항목 | 내용 |
|---|---|
| 부착점 (MAC_Body 기준, 피벗 상대 m, ×240) | Tip (0.3323, 0.7635, −0.9930) · Vent (0.1978, 0.0998, −0.4125) · Impact (0.2834, 0.5224, −0.7821) |
| 궁 순서 `ultimate_order` | 궁 버튼 → Transform 3.9667초 (피해 없음) → 자동으로 UltAttack (추가 입력 없음), hitAt 1.5821, 첫 타격 확정 시 소모 |
| 입력 `input_contract` | 서서 장착 Draw · 이동 중 장착 SprintDraw · 공격 유지 RareDraw · 걷기/달리기 평타 Walk/SprintAttack1~3 |
| SprintTwirl | 이동 4초 지속 시 자동, 8초 간격, 피해·버프 없음, 이동 멈춤/공격/장착 변경 시 취소 |
| 변신 단계 `transform_states` | stage 0~6 = 1.5024 · 1.5476 · 1.5929 · 1.6381 · 1.6833 · 1.7286 · 1.7738초 |
| 손 주의 `hand_warning` | 엔진에서 양손이 뒤집혀 보인다는 보고 이력 — 회전으로 해결 표시 금지, 임포트 형상 먼저 확인 |
| 효과 에셋 | `Effects/` Flame · Shockwave · Slash · Sparks FBX, `Audio/Catch_Tak.wav` (자리표시 소리) — 게임 미연동 |

---

## 7. 변신 문양 발광

### 7-1. 디자인 (Blender, `Scripts/v11_glow.py` — 영상 기준)
- 색 선형 RGB (1.0, 0.42, 0.08) 금빛 주황, 몸체 최대 방출 14, 구리 장식 × 3
- Transform: f0–39 꺼짐 → f40–45 손잡이 쪽 불씨 → 단계 시각 1.502~1.774초에 칼끝까지 차오름 → f53 섬광 → 강화 맥동
- UltAttack: 휘두르며 밝아짐 → hitAt 섬광 → 칼끝부터 손잡이 쪽으로 빠지며 꺼짐
- 마스크 `Textures/T_MAC_Body_GlowMask.png` (2048×512, MAC_Body UV, 흰색=문양 15%)

### 7-2. 게임 구현 (OVERDARE)
엔진 제약: MeshPart 색을 런타임에 칠해도 화면에 안 나오고, 투명도를 바꾸면 하얗게 날아간다. → **텍스처를 미리 구운 몸체 사본을 바꿔 끼우는 방식**

| 요소 | 내용 |
|---|---|
| 텍스처 | `Import_OVERDARE/Textures/T_MAC_Body_Glow1/2/3_1024.png` (1024×256) — 문양 발광 채움 0.35 / 0.70 / 1.00, 채움 앞머리 밝은 색, 채운 구간 나무결 ×0.72. 생성 `Scripts/v11_glow_game.py` (채움 방향 = 몸체 정점 속성 `v11_blade_t`, 0 손잡이 · 1 칼끝) |
| 에셋 | TEXTURE 45724100 · 45724200 · 45725100 |
| 파트 | `MAC_Body_Glow1~3` (2-2 표). 재질 Plastic (Unlit 은 궁 때 화질이 낮아 보여 교체) |
| 단계 함수 | 컨트롤러 `MELEE.glowStage()` → 0(원래 몸체) / 1 / 2 / 3 |
| Transform 단계 | `MELEE.GLOW_T = {1.45, 1.62, 1.774}` 초를 넘을 때마다 1→2→3 |
| UltAttack 단계 | hitAt+0.6초까지 3 → +0.9초까지 2 → +1.2초까지 1 → 0 (칼끝부터 꺼짐) |
| 교체 | 매 프레임 `MELEE.glowNow` 에 맞는 몸체 하나만 제자리, 나머지(원래 MAC_Body 포함)는 `baseCFrame * CFrame.new(0, -400, 0)` (카메라 바로 아래 시야 밖). 사본이 레벨에 없으면 원래 몸체가 그대로 나옴 |
| 자세 | `POSE_ALIAS_BY_PART` 에서 `MAC_Body_Glow1~3 → "MAC_Body"` — 클립 수정 없이 몸체 자세를 따라감 |
| 미구현 | 강화 맥동·섬광 밝기 변화, 구리 장식 발광 (런타임 색·투명도 불가) |

---

## 8. 게임(onlyonetap)에 반영한 내용

### 8-1. 레벨 `onlyoneshot.ovdrjm`
1. `Workspace.Macuahuitl_Viewmodel` 9 MeshPart 를 **같은 GUID 로 교체** — MeshId(STATIC_MESH) · Position · Size · UnitExtent · Color · Material · 몸체 TextureId (2-2 표)
2. `ReplicatedStorage.ViewmodelAnimMaxico*` ModuleScript 32개 소스를 v11 로 교체 (32/32 확인)
3. `MAC_Body_Glow1~3` 추가 (Studio 에 실시간 생성 후 저장)
4. `ViewmodelConfig` 는 수정 안 함 (SOURCE · PIVOT · OFFSET · YAW · CLIPS 그대로 유효)

### 8-2. `ViewmodelController` (게임 모듈 이름 `ViewmodelController`, 사본 `Lua/ViewmodelController_2.lua` · `Game_Integration/`)
| # | 수정 | 위치 | 이유 |
|---|---|---|---|
| 1 | `updateUltMovement` 가드에 `and ultMotion.dir` 추가 | `local function updateUltMovement` | maxico 궁은 제자리 변신이라 `dir` 가 없음 → 2221행 `nil * number` 에러가 매 프레임 나서 **궁 쓰면 팔이 멈춤** |
| 2 | 변신 발광: `POSE_ALIAS_BY_PART` 3줄, `MELEE.GLOW_T` · `MELEE.glowStage()`, 렌더 루프 `MELEE.glowNow`, 몸체 교체 분기 | 파일 상단 · `updateUlt` 뒤 · 렌더 루프 | 7-2 |
| 3 | 몸체 숨김 위치 −9000 → **카메라 아래 −400** | 몸체 교체 분기 | 멀리 치우면 텍스처가 저해상도로 내려가 궁 때 흐리게 보임 |

- 지역변수 한도(최상위 200 근처) 때문에 새 값은 전부 `MELEE` 테이블 필드로 둠
- 타입 검사(luau-lsp): 추가한 줄에서 오류 0 (기존 경고는 원래 있던 것)

### 8-3. 확인 결과
- 플레이테스트 로그: `[VM] pick=maxico src=Macuahuitl_Viewmodel parts=12`, 파트 12개 `LoadMesh` (다운로드 요청 없음), 출격 후까지 Lua 에러 0
- 저장 파일 검사: STATIC_MESH id 9/9, v11 클립 32/32, 발광 파트 3 (크기·위치·텍스처·재질 일치), 컨트롤러 수정 3건 모두 존재, 게임 컨트롤러 소스 = `Lua/ViewmodelController_2.lua` 사본과 동일
- **미확인**: 궁 버튼이 테스트 도구로 클릭 불가 영역(화면 밖)이라 궁 사용 장면은 직접 못 봄

### 8-4. 게임 쪽 백업 (`C:\Users\29\Desktop\onlyonetap\`)
| 파일 | 시점 |
|---|---|
| `onlyoneshot_BEFORE_MACUAHUITL_V11_20260914.ovdrjm` | v11 반영 전 (v10 상태) |
| `onlyoneshot_BEFORE_ULTFIX_20260914.ovdrjm` | 궁 팔 멈춤 수정 전 |
| `onlyoneshot_BEFORE_GLOW_20260914.ovdrjm` | 변신 발광 추가 전 |
| `onlyoneshot_BEFORE_GLOWQUALITY_20260914.ovdrjm` | 발광 화질 수정(재질·숨김 위치) 전 |

---

## 9. OVERDARE 작업 규칙 (이번에 확인한 것)

| 규칙 | 내용 |
|---|---|
| 메시 삼각형 | 1개당 30,000 이하 |
| FBX 임포트 | 여러 오브젝트 FBX 는 파트 상대 위치가 흩어짐 → 파트마다 FBX, 위치는 직접 입력 |
| **MeshId 는 STATIC_MESH** | 임포트 1회에 에셋 2개 등록 (`UGCLocalAssetTable.json`, UTF-16): `STATIC_MESH` (`/Asset/TempImportedAssetDir/…`) 와 `MODEL`. **MODEL id 는 에디터에선 보이지만 플레이 중 안 보임** (로그 `RequestWorldAssetDownloadInSandbox`). 이 때문에 한때 팔·무기가 통째로 사라졌음 |
| 색 | MeshPart 색은 런타임에 칠해도 안 나옴 → 레벨 Color 필드에 직접 |
| 투명도 | MeshPart 투명도를 런타임에 바꾸면 하얗게 날아감 → 숨길 때는 위치를 옮김 (가까이) |
| 이미지 | `overdare_image_import` 는 TEXTURE 1개만 등록 (id 그대로 TextureId) |
| `.ovdrjm` | UTF-16 LE JSON. 스크립트 Source 는 `\r\n`·`\t` 이스케이프 문자열 |
| `level.apply` | 파일을 다시 읽어 **기존 인스턴스 속성·스크립트만 갱신**하고 파일을 Studio 상태로 다시 씀. 파일에 직접 추가한 **새 인스턴스는 무시되고 지워진다** → 새 파트는 `overdare_instance_create` 로 실시간 생성 후 저장. 26 MB 파일이라 RPC 가 10초 타임아웃돼도 재로드는 진행됨 → 로그가 멈출 때까지 기다린 뒤 저장 |
| 실시간 속성 | `overdare_instance_update` 의 Vector3 는 `{ "ObjectType": "Vector3", "X", "Y", "Z" }` 형식이어야 함 (배열은 거부, create 때는 Size 가 무시돼 100 으로 들어감) |
| 플레이테스트 | 편집·임포트 전에 반드시 정지. PIE 스크린샷에 클라이언트가 만든 오브젝트(뷰모델·로비 진열대)는 안 나옴 → 로그로 확인 |
| 입력 | 로비 출격 = Space. 궁은 `UltimateButton` 클릭뿐 (키 바인딩 없음) |

---

## 10. 폴더 구조

```
Macuahuitl_Rework_v11_TwoHand\
  SPEC_v11_KO.md              ★ 이 명세서 (현재 상태 기준)
  WORK_LOG_KO.md              ★ 작업 기록 (요청 → 조치, 버전별)
  CLAUDE_HANDOFF.md           Blender 제작 인계 (v11.0~v11.4 세부 수치)
  SKILL_CATALOG_KO.md         동작 영상 목록 (AllClips 시작 프레임)
  CREDITS.md
  Macuahuitl_Rework_v11.blend  작업 blend (씬 MAC_V11_Rig · MAC_V11_AllClips · V11_Video · V11_BeautyVideo)
  Macuahuitl_Base.fbx          무기+팔 기본 FBX
  Motions_v11_4.mp4            ★ 최신 전 동작 렌더 영상 (1784프레임)
  Motions_v11_3.mp4 · Motions_v11_2_heavy.mp4 · Motions_v11_heavy_glow.mp4 · Motions_v10_vs_v11.mp4   이전 버전 영상
  clip_manifest.json          클립 52개 (동작 32 + 전환 20) 프레임·길이·이벤트
  effect_events.json          부착점 · 궁 순서 · 입력 · 발광 규격 등
  mesh_contract.json          파트 휴지 행렬 · 변신 단계
  palettes.json · preview_schedule.json
  Clips\          v11 동작 Lua 32개
  Transitions\    v11 전환 Lua 20개
  Meshes\         Deploy_0 (v11 무기) · Deploy_1~6 (★ 아직 v10 한손 무기)
  Skins\          스킨 4종 (★ 아직 v10 한손 무기)
  Hands\ Effects\ Audio\   손 Open/Grip · 효과 메시 · 캐치 소리 (v10 복사본)
  Textures\       발광 마스크
  Scripts\        제작 스크립트 (11절)
  Work\Source\    리타이밍한 원본 클립 + timemap.json
  QA\             검사 결과 json · 컷 시트 · V11 화면 확인 이미지 · Video (영상 렌더 프레임 캐시)
  Checkpoints\    작업 단계별 blend 사본 v11_01 ~ v11_09
  Import_OVERDARE\   게임 임포트 패키지
    IMPORT_GUIDE_KO.md · level_placement.json
    Meshes\   파트별 FBX 9개      Textures\  몸체 텍스처 · 발광 마스크 · 발광 텍스처 3장
    Lua\      클립 모듈 32개 (CRLF)   Data\  매니페스트 · 이벤트 · 계약 사본   QA\  흑요석 감축 비교 · 발광 텍스처 미리보기
  Game_Integration\   게임에 들어간 스크립트 현재본 사본 (ViewmodelController · ViewmodelConfig)
```

바탕화면 zip (`Macuahuitl_Rework_v11_TwoHand_20260914.zip`) 에는 `QA\Video` (렌더 프레임 캐시 1.07 GB) 와 `Checkpoints\` (458 MB) 를 넣지 않았다. 원본 폴더에는 그대로 있다.

---

## 11. 스크립트 · 다시 만드는 순서 (`Scripts/`)

| 스크립트 | 역할 |
|---|---|
| `v11_io.py` | Lua 클립 입출력 (v10 52개 되읽기 바이트 동일) |
| `v11_convention.py` | Lua 행 ↔ Blender 행렬 규약 |
| `v11_retime.py` | 무게감 리타이밍 · 무게/arc-dip 레이어 → `Work/Source/Clips` |
| `v11_retarget.py` | 양손 팔 IK (어깨 오프셋을 카메라 가시성 기준으로 선택) |
| `v11_batch.py` | 리타깃 일괄 (평타·이동·그립 클립), 왼손 TUCK |
| `v11_block.py` | 막기 3종 |
| `v11_showcase.py` | 연출 (Idle · FirstDraw · Transform · UltAttack · JumpSlam) |
| `v11_raredraw.py` | RareDraw v11.4 |
| `v11_transitions.py` | 전환 20개 |
| `v11_glow.py` | Blender 발광 재질·키 (영상용) |
| `v11_glow_game.py` | 게임용 발광 텍스처 3장 |
| `v11_manifest.py` | 매니페스트 · 이벤트 |
| `v11_export.py` | FBX · 메시 계약 |
| `v11_overdare_import.py` | 게임 임포트 패키지 (파트별 FBX · 흑요석 감축 · 배치표) |
| `v11_overdare_compare.py` | 흑요석 감축 전후 비교 |
| `v11_preview.py` · `v11_video.py` | AllClips 씬 · 영상 |

순서: `v11_retime.build` → `v11_batch.run` → `v11_block.build` → `v11_showcase.build` → `v11_raredraw.build` → `v11_transitions.build` → `v11_glow.setup_materials` → `v11_manifest.update` → `v11_export.export` → `v11_overdare_import.run` → `v11_glow_game.run` → `v11_preview.make_allclips` + `v11_glow.key_preview` → `v11_video.beauty_async`

백그라운드 실행: `"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" --background Macuahuitl_Rework_v11.blend --factory-startup --python Scripts\<스크립트>.py`

---

## 12. 검증 수치

| 항목 | 결과 |
|---|---|
| Lua 52개 | 되읽기 동일, 행 수 = 매니페스트, 루프 이음새 0, 64값/행, NaN 없음 |
| 전환 | 끝점 오차 0 cm |
| FBX 되읽기 | 정점 오차 0 cm |
| 팔 잘린 끝 화면 노출 (클립 32 + 전환 20 전 프레임) | v10 원본 R 1137 · L 176 → **v11.4 R 108 · L 38** |
| IK 과신전 | CrouchAttack 11 · Draw 3 · RareDraw 오른팔 4 프레임 |
| 흑요석 감축 | 194,120 → 28,420 삼각형, 표면 평균 차이 0.5 mm (`Import_OVERDARE/QA/`) |
| 발광 텍스처 | 원본 텍스처 재현 오차 0.0012, 문양 점등 비율 46% / 76% / 100% |

---

## 13. 남은 과제 · 알려진 문제

| 구분 | 내용 |
|---|---|
| 확인 필요 | 궁 변신 발광이 보이는지, 궁 사용 시 화질 저하 해결 여부 (사용자 플레이 확인) |
| 발광 한계 | 맥동·섬광 밝기 변화 없음 (단계 3장 교체만). 더 밝게 하려면 텍스처 색을 더 밝게 굽거나 재질 Neon 시험 |
| 런타임 색 표 | `ViewmodelConfig.COLORS` 에 옛 v03 무기 색(Handle 62,166,70 · Body 188,164,134 · Obsidian 76,76,76)이 남아 있음. 런타임 칠하기가 안 먹어서 화면 영향은 없지만 혼동 주의 |
| 안 쓰는 에셋 | 첫 임포트 때 생긴 MODEL 에셋 9개 (45722100~45723300 대, 45720600) 가 프로젝트에 남음 |
| 테스트 코드 | 컨트롤러 4525행 근처 `[VMTEST]` 자동 궁 발동은 `_G.InLobby ~= false` 조건 때문에 절대 실행 안 됨 (로비는 nil 로 설정). 필요 없으면 삭제 |
| 미연동 이벤트 | `hand_mesh`(손 펴기/쥐기), `left_grip_*`, `heavy_windup`, `whoosh/impact` 소리·효과, 전환 클립 |
| 옛 자산 | `Meshes/Deploy_1~6`, `Skins/` 4종은 v10 한손 무기 — v11 과 함께 쓰면 안 됨 |
| 동작 세부 | Draw row 15 왼손 한 프레임 0.53 m 튐, 과신전 프레임(12절), RareDraw 부메랑 최대 4.3 m 벽 관통 가능 |
| 타이밍 | 평타가 길어짐(1.8~2.33초), 궁 버튼→타격 5.55초 — 콤보 입력 창·쿨다운이 따로 하드코딩돼 있으면 조정 필요 |
| 도구 | Blender 에서 blender-mcp 애드온과 Higgsfield 브리지가 둘 다 포트 9876 을 써서 충돌 → blender-mcp 서버 정지 후 `bpy.ops.higgsfield.restart_mcp()` |
