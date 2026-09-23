# Macuahuitl v11 — TwoHand 모델 교체 + 양손 대검 전환 계획

## Context
- 현재 완성본 `Macuahuitl_Rework_v10/` 은 **한손 파지** 뷰모델(팔 6조각 + 무기 3파트 `MAC_Handle/Body/Obsidian`, Lua 클립 31+RareDraw, 전환 20, Deploy_0~6 FBX, 스킨 4종)이다.
- 루트 폴더에 새 모델 3종이 추가됐고, 사용자는 **`Macuahuitl_TwoHand.glb/.blend`**(전장 1.94 m, 가죽 감개 손잡이 x 0.35–0.934 = 58 cm, 위/아래 구리 고리, 약 39만 버텍스)로 교체하고 **양손 대검**으로 완전히 바꾸길 원한다.
- 결정 사항(질문 답변): 모델 = TwoHand / 애니 = **하이브리드**(26개 궤적 유지 + 왼손 IK, 연출 6개 새 키) / RareDraw = **양손 회전 투척** / 메시 = **경량화 없음**(원본 폴리곤으로 3파트 분리만).
- 작업 도구: **Higgsfield Blender 브리지(`bl_*`, GUI Blender)**. 생성(크레딧) 기능은 쓰지 않는다.

## 사전 조건 (작업 시작 전)
1. **Blender GUI 브리지 응답 없음** — 탐색 중 `bl_get_scene_summary`/`bl_execute` 가 타임아웃. Blender 에서 Higgsfield 패널이 Connected 인지, 렌더·모달 작업이 돌고 있지 않은지 확인 필요.
2. `plugin:moai-media:higgsfield` MCP 는 인증 전 상태 — 이번 작업은 생성이 없어 필수 아님.
3. v10 인계서가 가리키는 `Scripts/rework_v10_*.py`, `bake_maxico_clips.py` 는 **디스크에 없음** → Lua 입출력·리그·QA 스크립트를 새로 만든다. 이번엔 `Scripts/` 파일 + blend 내부 Text 데이터블록에 **둘 다** 저장한다.
4. 스킬 모듈 읽기 순서: `blender-scene`(완료) → `blender-scene-spec` → `blender-modeling` → `blender-animation` → `blender-lookdev` → `blender-audit-finalize`.

## 산출 위치
- 새 폴더 **`C:\Users\29\Desktop\Macuahuitl\Macuahuitl_Rework_v11_TwoHand\`** (v10 은 건드리지 않음, 폴더 구조·파일명 동일)
- blend: v10 blend 를 복사한 `Macuahuitl_Rework_v11.blend` 에 씬 추가 (`MAC_V11_Rig`, `MAC_V11_AllClips`, `MAC_V11_Review`). 파괴적 단계 전 체크포인트 복사본 저장.

---

## Phase 1 — 모델 교체 (메시 계약)
1. v11 blend 에 `Macuahuitl_TwoHand.glb` 임포트 (glTF Y-up → Z-up, 길이축 = 모델 X).
2. v10 `MAC_Handle/Body/Obsidian` 의 주축·손잡이 위치를 측정해 새 무기를 **같은 뷰모델 공간 방향**으로 정렬. 크기는 월드 스케일 유지(1.94 m) 후 게임 카메라에서 화면 점유율 확인, 필요 시 루트 스케일 1회만 조정.
3. 3파트로 분리·조인(이름/재질 기준 선택, 좌표 박스 선택 금지):
   - `MAC_Handle` = Long two hand leather wrap + Upper/Lower grip copper ferrule + Jade square pommel + Copper 가면 6조각
   - `MAC_Body` = Hardwood paddle and integral handle
   - `MAC_Obsidian` = Obsidian left/right 01–05 + Obsidian flake 70개
   - 재질 슬롯 유지, 폴리곤 감축 없음(사용자 결정).
4. 그립 앵커 empty (무기 자식): **`GRIP_R`**(위 손, 날 쪽 ≈ x 0.45) · **`GRIP_L`**(아래 손, 폼멜 쪽 ≈ x 0.78), 손 간격은 게임 카메라에서 조정. 그립 반경(≈2.7–3 cm)에 `Hands/Grip.fbx` 주먹 쥠이 맞는지 확인, 안 맞으면 Grip 손 포즈만 수정.
5. 이펙트 부착점 `Tip / Vent / Impact` 를 새 Body 기준으로 재계산.
6. 출력: `Macuahuitl_Base.fbx`, `Meshes/Deploy_0/Macuahuitl.fbx`, 새 `mesh_contract.json`(파트 행렬·level_origin 재계산).
   - **Deploy_1~6 · 스킨 4종은 이번 범위 밖**(후속 작업으로 분리). v10 파일은 모델이 달라 그대로 쓰면 안 된다는 점을 인계서에 명시.

## Phase 2 — 양손 리그 (`Scripts/v11_rig.py`)
1. **Lua 입출력 모듈 `Scripts/v11_io.py`**: 행 = `t` + 9파트 × (pos 3 · quat wxyz 4), `posScale=240`, 파트 휴지 행렬 = `mesh_contract.json`. v10 Lua 를 읽어 `MAC_V10_AllClips` 씬 값과 대조 → 오차 ≤ 0.05 cm 확인 후 진행.
2. 팔 조각 메시 주축 끝점(= v10 관절 정의)으로 좌/우 **2본 IK 체인**(어깨→팔꿈치→손목) 아마추어 생성, 팔 메시를 본에 부모 연결.
3. 구동 구조:
   - 무기 = 클립별 v10 무기 트랙(Handle) 그대로
   - 오른손 = `GRIP_R` 에 고정(Child Of), 왼손 = `GRIP_L` IK 타깃 + 손 회전 복사, 팔꿈치 폴 타깃은 바깥·아래
   - 어깨(UpperArm 루트) 위치 = v10 트랙
   - 좌/우 그립 **influence 커스텀 속성**(0/1, constant 보간) — 손 떼기·다시 잡기 구간용
4. 과신전 감지: 타깃 거리 > 체인 길이×0.98 인 프레임 목록화.

## Phase 3 — 애니메이션
### 3-A. 궤적 유지 + 양손 리타깃 (25개)
Draw · Holster · SprintDraw · RunStart/Loop/Stop · WalkStart/Loop/Stop · Attack1–3 · Walk/SprintAttack1–3 · BlockIn/Hold/Out · CrouchIn/Idle/Attack/Out
- 무기 궤적·길이·`hitAt`·`cut`·첫/끝·루프 이음새 **고정 프레임은 v10 과 동일**(게임 타이밍 불변).
- **양손 무게감 레이어**: 휘두르기 회전 중심을 손목 → 두 손 중간점으로 옮기고, 정점에서 1–2프레임 지연·작은 넘침. 손목 스냅은 줄임. 고정 프레임에서는 0.
- 과신전 프레임은 무기를 몸 쪽으로 당겨 해결(고정 프레임 제외), 그래도 안 되면 해당 클립만 수동 키 보정.
- 막기 3종: 양손 수평 막기 자세로 무기 회전만 재설정(진입/해제 첫·끝은 전환과 맞춤).
- Draw/SprintDraw: 오른손으로 뽑고 중간 프레임에 **왼손 합류**(`left_grip_join` 이벤트). Holster: 반대로 `left_grip_release`.
### 3-B. SprintTwirl (1개, 특수)
- 양손으로는 손 안 회전 불가 → f10 왼손 놓기 → 오른손 회전(기존 회전 유지) → `catch` f35 에서 왼손 재파지. `hand_mesh` 이벤트로 왼손 Open↔Grip 교체.
### 3-C. 연출 6개 — 양손 동작으로 새 키 (120f, 3.9667초, 이벤트 프레임 유지)
| 동작 | 새 구성 | 유지할 값 |
|---|---|---|
| Idle | 양손 중단 자세 4초 루프, 호흡·좌우 주기 다른 흔들림 | 루프 이음새 0 |
| FirstDraw(Intro) | 등에서 한손 인출 → 왼손 합류 → 전개 | `deploy_start` f54, `transform_lock` f62 |
| Transform | 양손으로 세워 들고 변신 | 이벤트 f46/f54, 단계 1.502–1.774초 |
| UltAttack | 양손 머리 위 대형 내리치기 | `hitAt` 1.5821, 손목 제한 35° |
| JumpSlam | 양손 도약 내리찍기 | `jumpAt` 1.2543, `airHoldStart`·`hitAt` 1.795 |
| RareDraw | **양손으로 크게 감아 회전 투척** → 부메랑 선회(최대 ≈5.85 m) → 오른손 캐치 → 왼손 재파지 | release f41, whoosh f43, turnaround f61, return_whoosh f79, pitch_up f81, catch f89 |
- 예비동작 → 본동작 → 넘침/정착 구조, 베지어 보간, 쿼터니언(뒤집힘 방지).
### 3-D. 전환 20개 재베이크
- 클립 끝/시작 자세가 바뀌므로 v6 전환 파일은 더 이상 맞지 않음 → 5프레임 재생성.
- v10 에서 실패한 원인(피벗 공간 보간 시 경로 98 cm 휨)을 피해 **무기는 무기-로컬 slerp, 팔은 매 프레임 IK 재풀이**로 보간. 목표: 중간 경로 편차 ≤ v6 수준(25.6 cm).

## Phase 4 — 출력 (v10 스키마 그대로)
- `Clips/ViewmodelAnimMaxico*.lua` 32개, `Transitions/*.lua` 20개: 파트 목록 9개·`posScale 240`·`duration/full/loop/hitAt/cut` 동일 형식, 헤더 주석 `v11 two-hand`.
- `clip_manifest.json`: 이벤트 `left_grip_join` / `left_grip_release` / 왼손 `hand_mesh` 추가, role 문자열 갱신. `effect_events.json`: 부착점·RareDraw 갱신.
- `CLAUDE_HANDOFF.md`(v11), `SKILL_CATALOG_KO.md` 갱신. 게임(`onlyonetap`) 코드는 수정하지 않음 — 반영 주의점만 기록.

## Phase 5 — 검증
- `QA/all_clips_v11.json` (클립별):
  - 고정 프레임 무기 오차 vs v10 = 0 cm (연출 6개는 이벤트 시각 일치), `Tip` 의 `hitAt` 위치 편차
  - 루프 이음새 0, 손↔그립 앵커 오차 ≤ 0.3 cm(잡은 구간), IK 과신전 0프레임, 팔꿈치 뒤집힘 0
  - 날·흑요석 ↔ 팔 메시 최소 간격 ≥ 1 cm, Lua 되읽기 ≤ 0.05 cm, 행 수 = 프레임 수
- 화면: 클립별 게임 카메라 컷 시트 `QA/Sheet_v11_*.png` (`bl_screenshot`/렌더로 직접 확인), 모션 오디트 샘플(첫·출발·최고속·정착·끝·이음새).
- 영상: `Motions_v10_vs_v11.mp4` — 32개 동작 v10(왼쪽)·v11(오른쪽) 나란히.
- Blender: `MAC_V11_AllClips` 씬에 전 동작 이어 붙인 타임라인 + 동작 이름 마커.

## 범위 밖 / 후속
- Deploy_1~6 전개 단계 메시, 스킨 4종(Jade·Crimson·AcidViolet·Porcelain) 재출력
- 폴리곤 경량화(현재 39만 버텍스 — 게임 성능 이슈 나오면 재검토)
- `onlyonetap` 게임 코드 연동
