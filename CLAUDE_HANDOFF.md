# v11 인계 — TwoHand 모델 교체 + 한손 → 양손 대검 전환 (v10 기준)

> **현재 상태 기준 문서는 `SPEC_v11_KO.md`** (게임 반영·변신 발광 게임 구현·버그 수정 포함), 과정은 `WORK_LOG_KO.md`. 이 인계서는 Blender 제작 단계(v11.0~v11.4) 세부 기록이다.

> **v11.1 추가 (아래 0절)** — 양손 무게감 리타이밍, 변신 문양 발광, 손잡이 재질 버그 수정, 룩 수정. 1~7절 중 길이·프레임 수치는 0절이 우선한다.

## 0-B. v11.4 변경 사항 (최신 — RareDraw 는 0-A 를 대체)

사용자 피드백 (v11.3 영상): ① 11초 부근(Holster→SprintDraw) 팔 겹침 ② 3타 내려치는데 손이 안 내려감 ③ RareDraw 가 잡을 때만 두 손이고 실제로는 한 손으로 앞으로 던지는데 날아가는 건 옆 ④ 한 손으로 잡음 ⑤ 버서커처럼 더 묵직하게.

| 문제 | 원인 (측정) | 수정 |
|---|---|---|
| ① 팔 겹침 | 왼손을 놓는 구간에 v10 왼손 자리가 1.55 m 무기 몸통을 관통 | 놓은 구간 왼손 목표를 원래 자리에서 (7, 6, −20 cm) 옮겨 화면 아래로 뺌 (`v11_batch.TUCK`, Draw·Holster·SprintDraw·SprintTwirl·Holster 전환) |
| ② 3타 손 | 무게 레이어가 칼만 회전, Attack3 그립 높이는 최고점→타격 42 cm 만 내려감 | **arc + dip 레이어** (`v11_retime.apply_arc_dip`): 무기+오른손을 최고점 +4 cm, 타격 −15 cm · 앞 6 cm, 9개 파트 전체가 타격 3프레임 뒤 −3.5 cm 가라앉음. 평타 10개 + JumpSlam·UltAttack(−12 cm). CrouchAttack 은 −7 cm |
| ③④ RareDraw | v10 비행이 옆으로 수평 회전(회전축 거의 수직, 34°/프레임)인데 던지기는 앞 방향 | **새로 제작** (`Scripts/v11_raredraw.py`): 칼날을 수평으로 눕혀 두 손으로 오른쪽 뒤로 감고(몸 14° 비틀고 3 cm 가라앉음) → 몸을 풀며 오른쪽→왼쪽 수평 휘두르기 → row 40 두 손 동시 놓음. 비행은 휘두르던 속도·회전 그대로 왼쪽 앞으로 수평 회전 → row 60 약 4.3 m 반환 → 오른쪽으로 돌아옴 → row 80–88 회전 멈추며 손잡이를 손 쪽으로 → **두 손 같이 잡음** → 무게에 몸째 끌려 7 cm 들어오고 10 cm 가라앉았다 버팀 |
| ⑤ 묵직함 | — | 히트스톱 3→4프레임, 예비 하중 6°→10°, 밀고 나감 10°→14°, 위 arc+dip |

- RareDraw 이벤트 프레임은 v10 과 같음 (release f41 · whoosh f43 · turnaround f61 · return_whoosh f79 · pitch_up f81 · catch f89). 손 이벤트: f41 양손 `hand_mesh Open` + `left_grip_release`, f89 양손 `hand_mesh Grip` + `left_grip_join`, 추가 `heavy_windup` f29, catch 에 camera_kick 0.8°. 부메랑 최대 약 4.3 m (벽 관통 주의)
- 던진 뒤 빈손: 휘두른 방향으로 따라 돌며 멈춤 → 준비 자세 → row 76–84 앞으로 뻗음 (`author_clip(grip_deltas=…, body=…)` 로 무기와 따로 IK)
- 길이 변화: Attack1·2 계열 54→**55f 1.80초**, Attack3 계열 70→**71f 2.33초**, CrouchAttack 66→**67f 2.20초** (히트스톱 1프레임 추가). hitAt 은 그대로 0.8 · 1.0 · 0.833
- 검증: 과신전 CrouchAttack 11 · Draw 3 · RareDraw 오른팔 4 프레임, 루프 이음새 0, 전환 끝점 0 cm, FBX 되읽기 0, 기본 팔 메시 잘린 끝 화면 노출 합계 R 108 · L 38 (v10 원본 R 1137 · L 176)
- 영상: **`Motions_v11_4.mp4`** (1784프레임, RareDraw 1665 · Attack3 1005 프레임부터). 체크포인트 `v11_09`

## 0-A. v11.3 변경 사항 (RareDraw 부분은 0-B 가 대체)

사용자 피드백: "두 손을 떼지 말라"는 요청이 아니었고, 한 손으로 가볍게 던지던 것을 **두 손으로** 던지라는 뜻. 팔은 **늘리지 말고 기본 메시 그대로** 최대한 안 보이게.

### RareDraw — 두 손으로 무겁게 감아 던지는 부메랑 (`Scripts/v11_raredraw.py` 전면 교체)
| row | 동작 |
|---|---|
| 0–12 | 두 손으로 들어 올림 |
| 12–28 | 오른 어깨 뒤로 크게 감아 짊어짐 (row 22 하중, row 28 가장 뒤에서 멈춤) |
| 28–40 | 두 손으로 몸을 실어 앞으로 던짐. row 40 이 v10 release 자세·속도에 이어짐. 왼손 row 36–40 먼저 놓고 오른손 row 40–42 놓음 |
| 41–87 | **v10 부메랑 비행 그대로** (스탠스만 적용, 무기 위치 오차 0) |
| 88 | v10 catch 자세로 오른손이 받음 (row 84–88 뻗어 잡음) |
| 88–110 | 무게로 칼끝이 12° · 4 cm 가라앉았다(row 93) 돌아옴, 왼손 row 92–100 재파지 → 끝 자세 = v10 끝 + 스탠스 |

- 이벤트: v10 RareDraw 이벤트(release f41 · whoosh · turnaround · return_whoosh · pitch_up · catch f89) **복원** + 손 이벤트 `left_grip_release`·`hand_mesh L Open` (f37), `hand_mesh R Open` (f41), `hand_mesh R Grip` (f89), `left_grip_join`·`hand_mesh L Grip` (f101). effect_events 의 catch 소리 `Audio/Catch_Tak.wav` 도 복원. 부메랑 최대 약 5.85 m — 벽 관통 주의사항 다시 유효
- v11.2 의 8자 휘돌리기는 폐기

### 팔 — 기본 메시 그대로, 어깨 움직임으로 숨김
- v11.2 의 늘린 팔 메시(`V11_ARM_*`) 삭제. FBX 팔 6개는 **v10 메시 그대로** 출력 (되읽기 오차 0)
- `v11_retarget.solve_arm`: IK 로 어깨를 내밀 때 방향을 프레임마다 후보(손목 쪽 / 아래 / 카메라 쪽 섞음, 필요 없으면 3·6 cm 아래·뒤로 살짝 내림) 중에서 고른다. 기준 = 위팔 잘린 어깨 끝 정점이 게임 카메라 화면 안에 들어오는 정도(`v11_batch.setup_visibility()` 가 `VIS` 설정) → 도달 부족 → 이동량 순. 결과는 ±3프레임 평활(루프는 주기 평활)
- 오른쪽 어깨는 스탠스로 옮기지 않고 오른손만 따라감 (v11.2 유지)
- 검증 (`QA/v11_arm_visibility.json`, 클립 32 + 전환 20, 기본 메시): 잘린 끝이 화면에 들어온 프레임 **v10 원본 R 1137 · L 176 → v11.3 R 111 · L 20**. 남은 곳은 FirstDraw(40/120) · Transform(38/120) · RareDraw(16/120) 오른팔, JumpSlam(10/120) 왼팔 — 원래 v10 연출에서 팔을 크게 쓰는 구간
- 관절 겹침(팔꿈치 틈 가리기)도 메시를 건드리는 것이라 되돌림

### 0-4 영상 갱신
- **`Motions_v11_3.mp4`** (최신) — AllClips 1774프레임, 재질 렌더. RareDraw 1655 프레임부터
- `Motions_v11_2_heavy.mp4` 는 폐기된 휘돌리기·늘린 팔 버전

## 0. v11.1 변경 사항

### 0-1. 무겁게 — 리타이밍 (`Scripts/v11_retime.py`)
v10 원본을 먼저 느리게 다시 샘플링(`Work/Source/Clips`)한 뒤 기존 양손 파이프라인을 그대로 돌린다.

| 대상 | 방식 | 길이 (v10 → v11.1) |
|---|---|---|
| Attack1·2, Walk/SprintAttack1·2 | 예비 ×1.8 · 휘두르기 ×1.3 · 타격 뒤 3f 히트스톱 · 회수 ×1.7 + 무게 레이어 | 31f 1.0초 → **54f 1.767초**, hitAt 0.5 → **0.8** |
| Attack3, Walk/SprintAttack3 | 같음 | 40f 1.3초 → **70f 2.3초**, hitAt 0.6 → **1.0** |
| CrouchAttack | 같음 | 37f 1.2초 → **66f 2.167초**, hitAt 0.467 → **0.833** |
| Draw · Holster · SprintDraw · SprintTwirl | 균일 ×1.4 | 1.3→1.833 · 0.8→1.133 · 1.2→1.667 · 1.4→1.967초 |
| BlockIn · BlockOut | 균일 ×1.45 | 0.3→0.433 · 0.4→0.567초 |
| 루프·이동 시작/정지·웅크리기 진입/해제·연출 120f | 그대로 | — |

(v11.2 에서 한 단계 더 무겁게 올린 값. v11.1 은 ×1.5/1.2/2f/1.4, 균일 ×1.25·×1.3 이었다)

- **무게 레이어** (평타 10개, `apply_heft`): 무기 + 오른손을 오른손 그립점 기준으로 스윙 회전축을 따라 돌린다. 타격 전 반대 방향 최대 6° 예비 하중, 타격 뒤 히트스톱 동안 3° → 4프레임 뒤 10° 밀고 나감 → 끝 6프레임 전 0. 첫/끝·타격 프레임에서는 0 (왼팔은 그 뒤 IK 로 다시 풂)

- 시간 곡선 = 매듭점 단조 3차 보간 (속도 튐 없음). 타격 프레임은 원본 타격 프레임과 **행 값 오차 0**, 첫/끝 행 오차 0 (전환 호환)
- 매니페스트 이벤트·`effect_events` 시각(whoosh·impact·fx·camera_kick)·그립 이벤트 모두 같은 곡선으로 옮김
- **게임 영향**: 평타 콤보 한 타가 1.47~1.87초로 길어짐. `cut` 도 옮겨짐 (Attack1 0.967 → 1.42초)
- 매니페스트 규약 확인: 이벤트 `frame` 은 **1부터** (time = (frame−1)/30). v11 1차 그립 이벤트는 0부터 적혀 있었는데 이번에 1부터로 바로잡음

### 0-2. 변신 — 문양 발광 (`Scripts/v11_glow.py`)
몸체 나무의 검은 기하 문양이 **손잡이 쪽부터 칼끝까지 차오르며 금빛 주황으로 빛난다**.

| 구간 | 내용 |
|---|---|
| Transform f0–39 | 꺼짐 |
| f40–45 | 손잡이 쪽 문양에 불씨, 깜빡임 |
| f45–53 | 문양이 칼끝까지 차오름. 채움 값 = `mesh_contract` 변신 단계 비율 (0 · .08 · .22 · .5 · .78 · 1.12 · 1) 을 단계 시각 1.502~1.774초에 그대로 사용 |
| f53 (`transform_lock`) | 섬광 (세기 1.9) 후 강화 상태 맥동 |
| 강화 대기 | `glow_hold` — 세기 0.85 ± 0.1, 주기 1.33초. 게임이 UltAttack 시작까지 유지 |
| UltAttack | 휘두르며 밝아짐 → hitAt(1.582초) 섬광 2.8 → 칼끝부터 손잡이 쪽으로 빠지며 1.5초에 걸쳐 꺼짐 |

- 게임 전달물: `Textures/T_MAC_Body_GlowMask.png` (MAC_Jade_body UV, 흰색 = 문양), `effect_events.json` 의 `glow` 규격(색 (1, 0.42, 0.08)·최대 세기 14·채움 축 정의) + `clips.Transform / UltAttack` 의 `glow_key` 이벤트(2프레임 간격, intensity·fill) + `glow_hold`
- 구리 장식(`MAC_Jade_handle_copper`)도 같은 세기 × 3 으로 은은하게 빛남
- 엔진이 채움(fill)을 못 쓰면 intensity 만 써도 된다
- Blender 미리보기: 재질 노드 `V11_*` 가 `V11_WPN_Ctrl["v11_glow"]`, `["v11_glow_fill"]` 드라이버를 읽고, 씬 컴포지터 `V11_Bloom`(Glare Bloom) 으로 번짐 표현

### 0-3. 버그 수정 · 룩
- **손잡이 재질**: 3파트로 나눌 때 면 재질 번호가 사라져 손잡이 18,470면 전부가 구리였음 (가죽 감개·옥 폼멜이 주황으로 보이던 원인). 원본 오브젝트 순서로 복원(면 중심 오차 0.0004 mm) → FBX 재출력
- **나무 재질**: 원본 glb 가 색 텍스처를 노멀맵에도 꽂아 둬서 나무가 회색 금속처럼 번들거림 → 노멀맵 연결 해제 (노드는 남김). 기본색 텍스처는 sRGB 로
- 전환 경로 편차 수치(최대 36 cm)는 FBX 출력 뒤 계약의 Handle 휴지 위치(측정 기준점)가 바뀐 영향이며, 끝점 오차는 여전히 0

### 0-3b. v11.2 — RareDraw 두 손 휘돌리기 (`Scripts/v11_raredraw.py`)
부메랑 투척(한손 놓기·캐치)을 없애고 **두 손을 끝까지 떼지 않는 무거운 8자 휘돌리기**로 새로 만들었다 (120프레임 유지).

| 프레임 | 동작 |
|---|---|
| 0–22 | 오른 어깨 뒤로 들어 올려 짊어짐 (f14 하중, f22 잠깐 멈춤) |
| 22–42 | 왼쪽 아래로 크게 내리베기 (whoosh f33) |
| 42–58 | 무게에 끌려 몸 왼쪽 뒤로 돌아 왼 어깨 위로 |
| 58–79 | 머리 위를 넘어 오른쪽 아래로 내리베기 (whoosh f71) |
| 79–95 | 몸 오른쪽 뒤로 돌아 머리 위로 |
| 95–119 | 앞으로 무겁게 내려놓음 (impact_thud f104 + camera_kick 0.9°) → f107 한 번 더 가라앉음 → 제자리 |

- 키 = 오른손 그립 위치 + 칼끝 방향, 비균일 Catmull-Rom (멈춤 키 속도 0). 칼 축 둘레 롤은 평행 이동으로 최소 회전 + 날이 앞장서는 방향 30% → 손목 과도한 꼬임 방지
- 양팔 IK (가중치 항상 1, 팔 기준 = Idle), 도달 보정
- 이벤트 교체: `release · turnaround · return_whoosh · pitch_up · catch · catch_recoil` 과 왼손 그립 이벤트 삭제 → `heavy_lift · whoosh ×2 · impact_thud`. **부메랑 5.85 m 벽 관통 주의사항은 더 이상 해당 없음**. `Audio/Catch_Tak.wav` 는 쓰지 않음

### 0-3c. v11.2 — 팔이 떨어져 보이던 문제
- 원인: 양손 스탠스로 오른팔이 화면 가운데로 옮겨지면서 **위팔의 잘린 어깨 쪽 끝이 게임 카메라 화면 안에 들어옴** (v11.1 Idle 120/120 프레임, 거의 전 평타. v10 은 일부 프레임만)
- 1차 시도(팔 축 방향으로 60~100 cm 연장)는 **실패**: 위팔 축이 카메라 쪽을 향해 연장부가 렌즈 6 cm 옆을 지나 화면 절반을 덮었다. 폐기
- 해결 1 — **오른쪽 어깨 고정**: 스탠스 이동을 무기·오른손에만 적용하고, 오른쪽 위팔·아래팔은 원래 어깨에서 IK 로 푼다 (`retarget_left(right_joints=…)`, `author_clip` 오른팔 pre = 항등). 오른손 위치 오차 0.02 cm 이하
- 해결 2 — **아래·뒤로 짧게 연장**: 위팔 어깨 쪽 끝 단면 정점을 카메라에서 멀어지는 방향 (0, 0.35, −1) 으로 **30 cm** 옮긴 v11 전용 메시 `V11_ARM_R_UpperArm` · `V11_ARM_L_UpperArm`. v10 씬 메시는 그대로. FBX 의 위팔 2개가 이 메시로 출력됨 (되읽기 오차 0). 관절·계약 값 불변
- 검증 (`QA/v11_arm_visibility.json`, 클립 32 + 전환 20 전 프레임): 잘린 끝이 화면 안에 들어오는 프레임 연장 전 R 1416 · L 318 → **R 14 · L 31** (거의 JumpSlam 두 팔을 머리 위로 든 구간), 연장부가 렌즈 15 cm 안으로 들어오는 프레임 **0**
- 해결 3 — **관절 겹침**: 팔 조각이 관절에서 딱 맞닿기만 해서 팔꿈치를 굽히면 틈이 보였다 (JumpSlam 원본 메시 기준 팔꿈치 단면 중심 간격 R 3.3 · L 4.1 cm). 위팔 팔꿈치 쪽 끝 +5 cm, 아래팔 팔꿈치 쪽 −4 cm · 손목 쪽 +3 cm 로 늘린 `V11_ARM_*_LowerArm` 메시 추가 → 조각이 서로 파고들어 틈이 가려짐. FBX 아래팔 2개도 이 메시로 출력
- 뷰모델 전용 메시다. 3인칭/그림자 캐스팅에는 쓰지 말 것
- RareDraw 뒤로 돌리는 두 키(f50·f87)는 칼이 화면 밖으로 사라지지 않게 화면 가장자리 쪽으로 옮김 (오른팔 과신전 1프레임, 도달 보정 0)

### 0-3d. v11.2 RareDraw 검증 (`QA/v11_raredraw.json`)
- 첫/끝 무기 오차 0 (전환 호환), 도달 보정 최대 2.5 cm
- 오른팔 과신전 5프레임 (어깨 내밀기 15 cm 상한에 닿음), 손목 틈 최대 2.6 cm / 왼팔 과신전 0, 손목 틈 0.6 cm
- 손목 비틀림: 손↔아래팔 상대 회전 절대값 최대 약 180° — 휘돌리는 구간에서 손목이 크게 돌아간다. 화면에서 어색하면 칼 롤(`EDGE_LEAD`)·키 방향을 조정

### 0-4. 영상
- **`Motions_v11_2_heavy.mp4`** (최신) — AllClips 1774프레임(59.1초), 전체 EEVEE 렌더(재질·조명·블룸), 동작 이름·길이 자막. Transform 1415 · UltAttack 1535 · RareDraw 1655 프레임부터
- `Motions_v11_heavy_glow.mp4` 는 v11.1 (한 단계 덜 무거움, 옛 RareDraw, 팔 끝 보임)
- `Motions_v10_vs_v11.mp4` 는 v11 1차(리타이밍 전) 비교본

### 0-5. 다시 만들 때 순서 (5절 대신)
`v11_retime.build(blend_rows, grip_rest=V11_WPN_Ctrl 휴지 위치)` → `v11_batch.run()` → `v11_block.build()` → `v11_showcase.build()` → `v11_raredraw.build()` → `v11_transitions.build()` → `v11_glow.setup_materials()` → `v11_manifest.update()` → `v11_export.export()` → `v11_preview.make_allclips()` + `v11_glow.key_preview(ranges)` → `v11_video.beauty_async()`
(`blend_rows` = 파트별 `v11_retarget.blend_about` 보간 — `CLAUDE_HANDOFF` 작성 세션의 호출 코드 참고: 행 a·b 의 각 파트 델타를 계약 휴지 위치 기준으로 섞는다)

v10 의 한손 마쿠아휘틀 뷰모델을 **`Macuahuitl_TwoHand.glb` 모델**로 바꾸고, 동작 32개와 전환 20개를 **양손 파지**로 전환했다.
작업은 Higgsfield Blender 브리지(GUI Blender)로 했고, v10 폴더는 건드리지 않았다.

| 구분 | 파일 | 상태 |
|---|---|---|
| 무기 모델 | `Meshes/Deploy_0/Macuahuitl.fbx` · `Macuahuitl_Base.fbx` | **TwoHand 모델로 교체** (0.8배, 1.55 m, 3파트) |
| 메시 계약 | `mesh_contract.json` | 무기 3파트 휴지 위치 갱신 + `v11` 항목 |
| 평타·이동·웅크리기 19개 | `Clips/` | v10 무기 궤적 + 양손 스탠스 + **왼팔 IK** |
| 꺼내기·넣기·SprintDraw·SprintTwirl | `Clips/` | 위와 같음 + **왼손 합류/이탈** 가중치 |
| 막기 3종 | BlockIn · BlockHold · BlockOut | **새 자세로 제작** (양손 대각선 가드), 양팔 IK |
| 연출 6개 (120f) | Idle · FirstDraw(Intro) · Transform · UltAttack · JumpSlam · RareDraw | v10 동작 기반 양손 풀이 (아래 3절) |
| 전환 20개 | `Transitions/` | v10 경로 리타깃 + 끝점을 v11 클립 자세에 **0 cm 고정** |
| 매니페스트·이벤트 | `clip_manifest.json` · `effect_events.json` | 그립 이벤트 추가, 부착점 Tip/Vent/Impact 재계산, role 갱신 |
| **그대로 둔 것** | `Meshes/Deploy_1~6` · `Skins/*` · `Hands/*` · `Effects/*` · `Audio/*` | v10 복사본 — **Deploy_1~6·Skins 는 옛 한손 무기라 v11 과 함께 쓰면 안 됨** |

---

## 1. 모델 교체

- 원본 `Macuahuitl_TwoHand.glb` (1.94 m) 를 **0.8배 = 1.55 m** 로 사용 (v10 무기 0.90 m). 크기는 게임 카메라 비교 렌더 4장으로 사용자 선택
- 오른손을 v10 과 같은 위치에 두고 날 방향·날 폭 방향을 v10 무기 축에 맞춤. 손잡이 반경 2.4 cm (v10 2.7 cm) 라 기존 손 메시가 맞음
- 3파트 (재질·이름 기준으로 나눔, 폴리곤 감축 없음 — 사용자 결정)

| 파트 | 포함 | 정점 | 재질 |
|---|---|---|---|
| `MAC_Handle` | 가죽 감개 · 위/아래 구리 고리 · 옥 폼멜 · 구리 가면 · 나무 코어의 가죽 면 | 11,100 | `MAC_Jade_handle` (감개) · `_copper` · `_jade` · `_leather` |
| `MAC_Body` | 나무 패들 | 1,193 | `MAC_Jade_body` |
| `MAC_Obsidian` | 흑요석 날 10 · 조각 70 | **380,828** | `MAC_Jade_edge` |

- 그립 앵커 (모델 좌표 x): **오른손 0.45 (날 쪽) · 왼손 0.65 (폼멜 쪽)**, 간격 16 cm
- FBX: v10 FBX 를 되읽어 구조를 확인하고 같은 방식(오브젝트 9개, 휴지 위치, 회전·스케일 항등)으로 출력. 13.3 MB. **되읽기 정점 오차 0 cm** (팔 6 + 무기 3)
- 스킨 팔레트는 `arms/body/handle/edge` 4개만 바꾼다. 새로 생긴 `MAC_Jade_handle_copper/_jade/_leather` 는 스킨이 건드리지 않는다

## 2. 좌표 규약 (v10 씬으로 검증, 오차 0) — `Scripts/v11_convention.py`

- 클립 프레임 k = AllClips 씬의 동작 마커 프레임 + k
- Blender 쿼터니언 = Lua (w, −x, z, y), Blender 이동량 = Lua (−px, pz, py)
- 모든 파트가 **공통 회전 중심 P = (0.0094, −0.0079, 1.0831)** 기준 강체 변환: `M = T(P+pos)·R(q)·T(−P)·T(휴지)`
  → 파트 피벗을 어디 두든 결과가 같아서 무기 파트 원점을 바꿔도 클립이 그대로 맞는다

## 3. 양손 전환 방식 — `Scripts/v11_retarget.py`

- **양손 스탠스**: 무기 + 오른팔 전체를 몸 중앙 쪽으로 고정 이동 (6, 2, 3 cm). 왼팔이 폼멜 쪽 손잡이에 닿게 하려는 것. 오른팔은 무기와 상대 자세가 같아 IK 불필요
- **왼팔 IK**: 관절 = v10 과 같은 팔 조각 메시 주축 끝점. 어깨↔손목이 팔 길이를 넘으면 어깨를 최대 15 cm 내밀기(평활, 루프는 주기 평활) → 2본 IK (팔꿈치 방향 = 원래 팔꿈치) → 원래 비틀림 보존
- **그립 가중치**: 파트별로 원래 ↔ IK 를 자기 관절 기준으로 섞음. 0 = v10 그대로, 1 = 손잡이

| 동작 | 처리 |
|---|---|
| 평타·이동·웅크리기 19개 | 전 프레임 가중치 1 |
| Draw | 왼손 f8→f14 합류 · Holster f6→f12 이탈 · SprintDraw f17→f23 합류 |
| SprintTwirl | f4→f9 왼손 놓기 → 회전 → f33→f38 재파지 |
| 막기 3종 | 칼날 화면 오른쪽 위 대각선 + 넓은 면 정면. BlockIn 10f 넘침 정착, BlockHold 미세 흔들림 루프, BlockOut 13f 복귀 (`v11_block.py`) |
| Idle · UltAttack · JumpSlam | 스탠스 + 왼팔 IK |
| Transform · FirstDraw | 전개 순간 한손으로 높이 든 구간에 **도달 보정**(무기를 몸 쪽으로 최대 12.5 cm 당김) + 양팔 IK. FirstDraw 는 오른손 f24→f32 파지, 왼손 f30→f38 합류 |
| RareDraw | 양손 감기 → 왼손 f34→f40 놓기 → f41 투척(오른손 f41→f43 놓기) → f86→f89 오른손 캐치 → 왼손 f96→f104 재파지. 감기 구간 도달 보정 최대 11.3 cm |
| 전환 20개 | v10 전환 리타깃 → 첫/끝 프레임을 v11 자세 행(Idle = Draw 끝, Run = RunStart 끝, Crouch = CrouchIn 끝, Block = BlockIn 끝, Holster = Draw 시작)으로 고정, 보정량을 중간 프레임에 분배. Holster 쪽은 왼손 가중치 1↔0 |

- 길이·프레임 수·`hitAt`·`cut`·`jumpAt`·`airHoldStart`·`loop` 는 **v10 과 전부 같다** (게임 타이밍 불변)

## 4. 검증 (`QA/all_clips_v11.json` 외)

- Lua 52개: 되읽기 텍스트 동일, 행 수 = 매니페스트 프레임 수, 타이밍 필드 v10 과 동일, 루프 이음새 **0** (Idle · RunLoop · WalkLoop · BlockHold · CrouchIdle)
- 리타깃 19개: IK 과신전 1프레임(CrouchAttack), 어깨 내밀기 최대 15 cm, 팔꿈치 틈 1.65 cm · 손목 틈 0.62 cm (v10 원본 Attack1 은 7.24 · 5.68 cm)
- 그립 가중치 클립: 손을 뗀 구간은 v10 원본 그대로라 틈도 원본 수준(약 5.7~6.7 cm)
- 막기: 과신전 0, 어깨 내밀기 오른팔 5.7 · 왼팔 7.6 cm, 이음새 0
- 연출: 첫/끝 무기 오차 0. FirstDraw 오른손 파지 전환 중 손목 틈 최대 9.7 cm, RareDraw 왼팔 과신전 3프레임
- 전환: 끝점 오차 **0 cm**, 무기 경로가 직선에서 벗어난 최대값 **20.6 cm** (Block↔Holster, v6 기준 25.6 cm 이내)
- FBX 되읽기 0 cm
- **측정 안 함**: 날·흑요석 ↔ 팔 메시 간격, `hitAt` 순간 칼끝 위치(리타깃 클립은 스탠스만큼 일정하게 이동)

화면 확인: `QA/V11/*.png` — 크기 비교(`scale_*`), Attack1(`game2_*`), 막기(`block_v2_*`), 꺼내기·Twirl(`grip_draw_twirl_*`), 연출(`showcase_v1_*`)
영상: **`Motions_v10_vs_v11.mp4`** — AllClips 1451프레임(48초) v10(왼쪽)·v11(오른쪽) 나란히, 동작 이름 자막, 게임 카메라 뷰포트 캡처 (`Scripts/v11_video.py`)
Blender: `Macuahuitl_Rework_v11.blend`
- `MAC_V11_Rig` : 무기 3파트(`V11_WPN_Ctrl` 아래) · 그립/부착점 empty · 원본 임포트(숨김) · 미리보기 팔
- `MAC_V11_AllClips` : 32개 동작 1451프레임, 마커·프레임 번호 v10 AllClips 와 동일
- 체크포인트: `Checkpoints/v11_01 ~ v11_05`

## 5. 다시 만들 때 순서 (Blender 안에서 `Scripts` 를 sys.path 에 넣고 import)

1. `v11_batch.run()` — 19개 + 그립 4개 (원본은 항상 v10 폴더에서 읽음)
2. `v11_block.build()` — 막기 3종
3. `v11_showcase.build()` — 연출 6개
4. `v11_transitions.build()` — 전환 20개 (**v11 클립을 읽으므로 1~3 뒤에**)
5. `v11_manifest.update()` — 매니페스트·이벤트·부착점 (다시 돌려도 결과 같음)
6. `v11_export.export()` — FBX + 계약 (되읽기 검사 포함)
7. `v11_preview.make_allclips()` → `v11_video.start_capture_async()` → `v11_video.compose_async()`

필요한 Blender 데이터: v10 씬의 `ALL_MAC_*` 팔 메시, `V11_WPN_Ctrl`(`v11_rest_matrix`), `V11_GRIP_L`(`v11_Lhand_delta_rest`), `V11_ATT_*`.

## 6. 게임 반영 시 주의 (코드 수정 안 함)

- **무기 FBX 는 Deploy_0 만 새것.** 전개 단계(`Deploy_1~6`)와 스킨 4종은 아직 v10 한손 무기 → 변신/스킨을 쓰려면 새로 만들어야 한다
- **흑요석 파트 38만 정점** (경량화 안 함). 뷰모델 성능 확인 필요
- 새 이벤트: `left_grip_join` · `left_grip_release` · `hand_mesh`(`hand: "L"`, `mesh: Open/Grip`) — Draw · Holster · SprintDraw · SprintTwirl · FirstDraw · RareDraw
- 무기가 모든 동작에서 스탠스만큼(6/2/3 cm) 화면 가운데 쪽으로 옮겨졌다. 막기는 칼날 방향이 v10 과 반대(화면 오른쪽)
- 부착점 새 값: Tip (0.3323, 0.7635, −0.9930) · Vent (0.1978, 0.0998, −0.4125) · Impact (0.2834, 0.5224, −0.7821)
- v10 인계서의 주의사항(연출 3.97초, 궁 버튼 후 타격 5.55초, 부메랑 5.85 m 벽 관통, 현재 게임은 최초 패키지 클립 사용)은 그대로 유효

## 7. 계획 대비 달라진 점 / 안 한 것

- 연출 6개는 계획의 "새 키 작업" 대신 **v10 연출 동작을 양손 풀이(IK·도달 보정·그립 가중치)로 전환**했다. 타이밍·이벤트를 그대로 지키려는 선택
- 계획의 "양손 무게감 레이어"(회전 중심을 두 손 사이로, 정점 지연)는 넣지 않았다
- 폴리곤 경량화, Deploy_1~6, 스킨 4종, 게임 코드 연동은 범위 밖
- 작업 환경: Blender 안에서 blender-mcp 애드온 서버와 Higgsfield 브리지가 둘 다 포트 9876 을 써서 브리지가 응답하지 않았다. 이번 세션에서 blender-mcp 서버를 끄고 Higgsfield MCP 를 재시작해 해결 (Blender 를 다시 켜면 재발할 수 있음)
