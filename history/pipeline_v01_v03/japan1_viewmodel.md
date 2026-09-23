# japan1 뷰모델 작업 기록

새 3분할 팔 뷰모델을 `japan1` 이라는 **새 직업**으로 붙인 기록이다.
기존 `japan`(와키자시) · `korea`(국궁) 은 한 글자도 건드리지 않았다.

작성 2026-09-11.

---

## 1. 무엇이 들어갔나

| 항목 | 값 |
|---|---|
| 직업 id | `japan1` (로비 카드 `JAPAN 1`) |
| 모델 | `Japan1_Arms_v2` — Workspace |
| 파츠 | 18개 (팔 6 + 칼 12) |
| 원본 블렌더 | `C:\Users\banav\Documents\카카오톡 받은 파일\Wakizashi_NewArms_Idle.blend` |
| 내보낸 FBX | `C:\Users\banav\Desktop\Viewmodel_WIP\Export\Japan1_Arms_v2.fbx` |

### 파츠 이름

```
팔   R_UpperArm  R_LowerArm  R_Hand
     L_UpperArm  L_LowerArm  L_Hand

칼   WKZ_R_Blade  WKZ_R_Hamon  WKZ_R_Guard  WKZ_R_Wrap  WKZ_R_Brass  WKZ_R_RaySkin
     WKZ_L_(같음)
```

칼을 6조각으로 쪼갠 이유는 **MeshPart 가 파츠당 색을 하나만 가질 수 있어서다.**
한 덩어리면 칼 전체가 한 색이 된다. 기존 와키자시도 같은 이유로 쪼개져 있다.

---

## 2. 좌표계 — 이 문서에서 제일 중요한 부분

블렌더와 레벨 사이 변환을 **추측하지 않고 실측**했다.
레벨 파츠 CFrame 과 블렌더 bbox 중심을 최소제곱으로 맞춘 결과:

```
level = 100 × (−x, z, y) + (670.000, −100.741, 1250.000)
최대잔차 0.000 cm
```

* 배율 **100** (블렌더 m → 레벨 cm)
* 축 매핑 **(x, y, z) → (−x, z, y)**
* 평행이동은 모델을 레벨 어디에 놓았느냐에 따라 바뀐다. 위 값은 현재 배치 기준.

### 피벗

```lua
PIVOT = { 667.2576, 12.0464, 1230.1578 }   -- 양 윗팔 CFrame 의 중점
```

이 피벗에 대응하는 **블렌더 좌표는 `O = (0.0274, −0.1984, 1.1279)`** 다.
PIVOT 을 "양 윗팔 중점" 으로 정하는 규칙이 같으면 **모델을 어디에 놓든 O 는 안 변한다.**
그래서 모델을 재배치해도 애니메이션을 다시 뽑을 필요가 없다 — PIVOT 숫자만 다시 재면 된다.

### 클립 델타가 사는 공간

레벨의 적용식이

```lua
part.CFrame = baseCFrame * delta * RestCFrame
```

인데 `RestCFrame` 이 `SOURCE_PIVOT` 상대 좌표다. 따라서 **delta 도 피벗을 원점으로 하는 공간의 값**이어야 한다.
블렌더 월드 원점 기준으로 뽑으면 회전이 있는 파츠마다 `(I − R) × O` 만큼 어긋난다.
처음에 이걸 놓쳐서 인트로가 이상하게 나왔었다.

```
POS_SCALE = 100 × 2.4(VIEWMODEL_SCALE) = 240
```

---

## 3. 화면 배치

```lua
OFFSET = { -10, -70, -75 }   -- 확정값. 사용자가 화면 보며 맞췄다
YAW    = 0
```

`YAW` 는 새로 만든 값이다. 전역 상수 `VIEWMODEL_DIRECTION_FIX` 가 모든 뷰모델을 180도 돌리는데,
이 모델은 이미 카메라 앞을 보고 있어서 **두 번 돌아 뒤를 보는 문제**가 있었다.

```lua
-- ViewmodelController : 최상위 local 을 안 늘리고 값만 다시 넣는다
VIEWMODEL_DIRECTION_FIX = CFrame.Angles(0, math.rad((ch and ch.YAW) or 180), 0)
```

값이 없는 나라는 예전 그대로 180 이라 **japan / korea 는 무영향.**

---

## 4. 색 — 런타임이 아니라 레벨에 박아야 한다

`ViewmodelConfig.COLORS` 로 실행 중에 `part.Color` 를 칠하는 구조가 있는데,
**그 경로는 이 엔진에서 화면에 안 나온다.** 에러도 안 난다(로그에 실패 한 줄 없음).
그래서 기존 와키자시·국궁도 전부 하얗게 나오고 있었다.

레벨을 통째로 훑어본 결과:

```
색이 들어간 MeshPart  1948개   ← 창덕궁 건물 등. 전부 레벨 파일에 색이 박혀 있다
흰색 MeshPart           51개   ← 뷰모델들
```

엔진이 MeshPart 색을 못 그리는 게 아니라, **런타임 칠하기가 안 먹는 것**이다.
그래서 japan1 은 레벨 파츠의 `Color` 필드에 직접 써넣었다.

| 파츠 | RGB |
|---|---|
| 팔 6개 | 63, 63, 69 |
| Blade | 182, 182, 182 |
| Hamon | 230, 230, 230 |
| Guard | 36, 36, 38 |
| Wrap | 22, 22, 24 |
| Brass | 180, 132, 55 |
| RaySkin | 210, 210, 200 |

값은 기존 와키자시 표와 동일하다.

> **기존 와키자시·국궁도 같은 방법으로 색을 살릴 수 있다.** `COLORS` 에 값은 이미 다 있고,
> 레벨 파츠에 박아넣기만 하면 된다. 아직 안 했다.

---

## 5. 애니메이션

전부 같은 블렌더 파일을 덮어쓰며 만들었고, 넘길 때마다 사본을 떴다.

| 클립 | 블렌더 프레임 | 길이 | 사본 |
|---|---|---|---|
| `Japan1Intro` | 10 ~ 80 | 2.3333초 | — |
| `Japan1RunStart` | 10 ~ 44 | 1.1333초 | `Japan1_Run.blend` |
| `Japan1RunLoop` | 45 ~ 93 | 1.6000초 | 〃 |
| `Japan1RunStop` | 94 ~ 105 | 0.3667초 | 〃 |
| `Japan1FirstTap` | 10 ~ 73 (cut 53) | full 2.1000 / cut 1.4333 | `Japan1_FirstTap.blend` |
| `Japan1SecondTap` | 10 ~ 73 (cut 45) | full 2.1000 / cut 1.1667 | `Japan1_SecondTap.blend` |
| `Japan1ThirdTap` | 10 ~ 80 (cut 없음) | full 2.3333 | `Japan1_ThirdTap.blend` |

사본은 전부 `C:\Users\banav\Documents\카카오톡 받은 파일\` 에 있다.
모두 30fps.

### 이음새 실측 (전부 0)

| 이음새 | 위치 | 회전 |
|---|---|---|
| 인트로 마지막 ↔ 기본자세 | 0.00 cm | 0.0000 |
| 달리기 루프 93 ↔ 45 | 0.00 cm | 0.0000 |
| 1타 cut(53) ↔ 2타 시작(10) | 0.00 cm | 0.0000 |
| 2타 cut(45) ↔ 3타 시작(10) | 0.00 cm | 0.0000 |
| 3타 끝(80) ↔ 기본자세 | 0.00 cm | 0.0000 |

### 기준(rest) 자세를 잡는 법

인게임 모델은 **예전 80프레임 자세로 구워서** 임포트했다. 그런데 그 뒤로 같은 파일을
계속 덮어쓰며 애니를 만들어서 **지금 80프레임은 기준이 아니다.**

그래서 프레임을 찾지 않고 **`Japan1_Arms_v2.fbx` 를 같은 씬에 임포트해 그 행렬을 직접 읽는다.**
이게 곧 인게임 모델의 자세다. 새 애니를 뽑을 때도 이 방법을 그대로 쓰면 된다.

### 칼은 손에 고정돼 있다

`WKZ_R` / `WKZ_L` 의 손 기준 로컬 변환이 프레임마다 **1e-4 미만**으로만 변한다 = 사실상 고정.
그래서 칼 12조각은 **손 델타를 그대로 복사**한다. 파츠는 18개인데 실제 궤적은 8개다.

---

## 6. 달리기 상태 기계

`ViewmodelController` 에 새로 넣었다.

```lua
MELEE.RUN = { ON = 250, OFF = 120 }   -- cm/s
```

* 준비동작 1회 → 무한반복 → 멈추면 마무리 1회
* 멈추면 루프 어디에 있든 **즉시** 마무리로 넘어간다
* 달리는지는 **루트 파츠의 수평(XZ) 이동**으로 잰다. 이 엔진에 `MoveDirection` 이 있는지
  확인된 적이 없어서, 이미 검증된 점프 판정(`jumongStep`)과 같은 수법을 썼다
* 켜는 문턱과 끄는 문턱을 다르게 뒀다(히스테리시스). 같으면 경계에서 덜덜 떤다
* 우선순위 맨 아래 — 공격·막기·스킬 중엔 안 나온다

> `ViewmodelController` 는 최상위 `local` 이 **194/200** 이다. 하나만 늘려도
> "Out of local registers" 로 스크립트가 통째로 로드에 실패한다.
> 그래서 상태는 전부 `MELEE` 테이블에 얹었다.

---

## 7. 기술 (궁극기 · 비뢰신 · 막기)

전용 애니가 아직 없는데도 **로직은 와키자시와 똑같이 나가야** 해서 이렇게 했다.

문제는 이 두 줄이었다:

```lua
if not getClip(RYUNOCHI_CLIP_NAME) then ... return end    -- onUltPressed
if not getClip(FLYINGRAIJIN_CLIP_NAME) then return end    -- onFlyingRaijinPressed
```

클립이 없으면 **발동 자체를 포기**한다. 그래서 와키자시 클립을 그대로 물렸다.

```lua
Ryunochi   = "Ryunochi",      -- 궁극기 (용)
KunaiThrow = "KunaiThrow",    -- 비뢰신 (쿠나이 + 순간이동)
BlockIn    = "BlockIn",
BlockOut   = "BlockOut",
Draw       = "Draw",
```

와키자시 클립의 파츠 이름(`Right_Arm_Mesh`, `Wakizashi_Blade_R` …)은 이 모델의
이름(`R_UpperArm`, `WKZ_R_Blade` …)과 **하나도 안 겹친다.** 그래서
`pose[item.PoseName]` 이 전부 nil 이 되어 **자세는 안 먹고 로직만 돈다.**

전용 애니를 만들면 오른쪽 값만 `Japan1...` 으로 바꾸면 된다.

### 참격 (X-blade)

```lua
XBLADE_ON_CLIP = "Attack3"
COMBO = { "Attack1", "Attack2", "Attack3" }
```

COMBO **자리 이름**으로 판정하므로 japan1 도 3타에서 참격이 나간다.
(한때 COMBO 가 2개로 줄어 있어서 3타가 안 이어졌다. 되돌려놨다.)

---

## 8. 작업 파이프라인

MCP 쓰기 도구(`studio_update_part`, `studio_delete`)는 **이 인스턴스들에 안 먹는다.**
성공이라고 답하는데 값이 안 남고, GUID 를 못 찾는다. 그래서 전부 이 경로로 했다:

```
1. .ovdrjm 를 UTF-16LE → UTF-8 로 변환
2. 파이썬으로 패치 (앵커가 정확히 1개인지 검사, 아니면 중단)
3. UTF-8 → UTF-16LE 로 되돌려 덮어쓰기
4. studio_apply → studio_save
5. 다시 변환해서 grep 으로 확인
```

* 롤트립이 바이트 단위로 같은지 매번 확인했다 (md5 일치)
* 파이썬은 Windows 스토어 스텁이라 안 된다. **블렌더 내장 파이썬**을 쓴다:
  `blender.exe --background --factory-startup --python 스크립트.py`
* 스크립트는 **Write 도구로 직접 쓴다.** 셸 heredoc 이나 sed 로 만들면 백슬래시가 깨진다

### 스튜디오 프로젝트 경로

```
C:\Users\banav\Documents\OverdareStudio\owt\onlyoneshot.ovdrjm   ← 진짜
D:\only one shot\                                                 ← 옛 사본. 안 씀
```

한동안 `D:` 를 고치고 있어서 아무것도 반영이 안 됐던 적이 있다.
스튜디오 프로세스 이름은 **`Sandbox-Win64-Shipping`** 이다.

---

## 9. 남은 것 / 알려진 문제

* **로비 UI 가 진입 2~4초 만에 스스로 닫힌다.** 내 변경을 전부 되돌려도 재현돼서 별개 원인이다.
  `toBattle` 과 `_G.VoteOpen` 켜지는 자리에 `print` 한 줄씩 박으면 금방 갈린다.
  (`PerfProbe` 의 `로비/전장` 표시는 클라 플래그 `_G.InLobby` 를 본다)
* **`LobbyUI` 의 `for i = 1, 3`** — 로드아웃을 4개로 늘리면서 `#ORDER` 로 고쳤다.
  안 고치면 4번째 나라에서 `RAIL.rows[이름]` 이 nil 이 되어 로비 UI 가 통째로 죽는다
* 기존 와키자시·국궁 색 (5장 참고)
* japan1 전용 기술 애니메이션
* 뷰모델 쿠나이는 이 모델에 파츠가 없어서 손에 안 보인다. 날아가는 쿠나이는 런타임 생성이라 정상
* 레벨에 `ZZ_*_DUP` 같은 중복 모델이 남아 있으면 스튜디오에서 지울 것
  (`studio_delete` 가 못 지워서 이름만 바꿔두는 식으로 처리했었다)

---

## 10. 백업

```
owt\onlyoneshot_BEFORE_JAPAN1_20260910.ovdrjm
owt\onlyoneshot_BEFORE_JAPAN1CFG_20260910.ovdrjm
owt\onlyoneshot_BEFORE_J1V2_20260910.ovdrjm
owt\onlyoneshot_BEFORE_RUN_20260911.ovdrjm
owt\onlyoneshot_BEFORE_TAP_20260911.ovdrjm
owt\onlyoneshot_BEFORE_TAP2_20260911.ovdrjm
owt\onlyoneshot_BEFORE_TAP3_20260911.ovdrjm
```
