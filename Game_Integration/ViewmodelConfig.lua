-- 뷰모델 조정값 모음.
-- 이 파일 숫자만 고치고 Play 를 다시 누르면 바로 반영된다.
--
-- ※ 주의(AI 포함): 아래 값들은 사용자가 실제 화면을 보며 맞춘 확정값이다.
--   애니메이션을 추가하거나 스크립트를 갱신할 때 임의로 되돌리지 말 것.
return {
	-- 카메라 기준 뷰모델 위치 (cm)
	--   X : 오른쪽(+) / 왼쪽(-)
	--   Y : 위(+)     / 아래(-)
	--   Z : 앞(-)     / 뒤(+)
	OFFSET_X = -10,   -- 확정값. 건드리지 말 것
	OFFSET_Y = -35,
	OFFSET_Z = -55,

	-- 뷰모델 확대 배율
	SCALE = 2.4,

	-- 스폰 후 뷰모델을 숨겨두는 시간(초). 카메라가 자리를 잡을 때까지 기다린다.
	INTRO_DELAY = 1,

		-- 뷰모델 중심으로 삼을 기준점. 임포트된 파츠 좌표 기준이며,
		-- 지금은 Wakizashi_Viewmodel_Split 안의 양팔(Right_Arm_Mesh, Left_Arm_Mesh)의 중점이다.
		-- 이 X 를 키우면 뷰모델이 오른쪽으로, 줄이면 왼쪽으로 간다.
		--
		-- ★ 2026-08-24 재실측. 레벨의 Wakizashi_Viewmodel_Split 에서 직접 뽑았다.
		--   Right_Arm_Mesh (871.558594, 75.402748, 4607.296875)
		--   Left_Arm_Mesh  (832.898987, 70.655594, 4611.125488)
		--   -> 중점        (852.228790, 73.029171, 4609.211182)
		--
		--   옛 값은 792.228790 / 23.029174 / 4679.211182 로, 중점에서 정확히
		--   (-60, -50, +70) 벗어나 있었다. SCALE 2.4 를 타면 화면에서
		--   (144, 120, -168) cm 짜리 이동이 된다 — 뷰모델이 화면 오른쪽으로
		--   쳐박혀 보이던 원인이다. OFFSET_X(-10) 보다 14배 큰 항이라
		--   좌우 위치를 실제로 지배하는 건 OFFSET 이 아니라 여기다.
		--
		--   되돌리려면 아래 세 줄을 792.228790 / 23.029174 / 4679.211182 로.
		--   모델을 다시 임포트하거나 레벨에서 옮기면 여기를 다시 재야 한다.
		PIVOT_X = 852.228790,
		PIVOT_Y = 73.029171,
		PIVOT_Z = 4609.211182,

	-- 연타할 때 이어질 공격 순서.
	-- 이름은 ViewmodelAnimData 안의 항목이거나,
	-- ReplicatedStorage 의 "ViewmodelAnim<이름>" 모듈이면 자동으로 찾는다.
	COMBO = { "Attack1", "Attack2", "Attack3" },

	-- ===== 캐릭터별 뷰모델 =====
	-- 로비 LOADOUT 에서 고른 나라에 따라 다른 뷰모델을 쓴다.
	--   SOURCE : Workspace 에 있는 원본 모델 이름
	--   PIVOT  : 그 모델 안 양팔(Right_Arm_Mesh, Left_Arm_Mesh) CFrame 의 중점
	--   OFFSET : 카메라 기준 화면 위치 { X, Y, Z } cm. 없으면 위 전역 OFFSET_* 을 쓴다
	--   ANIM   : false 면 클립 포즈를 아예 안 먹인다
	--
	-- ★★ PIVOT 은 반드시 "레벨에 임포트된 뒤" 다시 재라. 절대 좌표라서
	--   모델을 다시 임포트하거나 레벨에서 옮기면 그 즉시 무효가 된다.
	--   2026-08-24 에 이걸로 크게 헤맸다 — 와키자시 PIVOT 이 실제 중점에서
	--   (-60, -50, +70) 벗어나 있었고, SCALE 2.4 를 타면 화면에서 144cm 라
	--   뷰모델이 화면 오른쪽으로 쳐박혀 보였다. OFFSET_X(-10) 의 14배 항이라
	--   좌우 위치를 지배하는 건 OFFSET 이 아니라 PIVOT 이다.
	CHARACTERS = {

		-- ★ 2026-09-12 : 마쿠아위틀 (Macuahuitl v03 패키지).
		--   아래 japan1 / japan / korea 는 한 줄도 건드리지 않았다. 완전히 별개 직업이다.
		--   파츠는 9개 — 팔 6 (ODA 기본 아바타 팔을 본별로 자른 것) + 무기 3 (재질별로 묶음).
		--
		-- ★ 임포트 주의 : Studio 의 FBX Import 가 파츠 상대 위치를 보존하지 못했다.
		--   9조각이 제각각 흩어진 채로 들어와서, 블렌더 좌표에서 계산한 값을
		--   9개 CFrame 에 직접 박아넣었다. 다시 임포트하면 또 흩어진다.
		--   매핑 : level = 100 x (-x, z, y) + (1000.944095, -92.593801, 1230.791631)
		--   (평행이동은 두 윗팔로 최소제곱한 뒤 GND_Base 위로 옮긴 값. 잔차 0.000179 cm)
		maxico = {
			SOURCE = "Macuahuitl_Viewmodel",

			-- ★ 2026-09-12 GND_Base 위(japan1 팔 옆)로 옮긴 뒤 다시 잰 값.
			--   절대좌표라 모델을 또 옮기면 그 즉시 무효다.
			--   MAC_R_UpperArm (1026.9105, 16.4498, 1228.7749)
			--   MAC_L_UpperArm ( 973.0896, 14.9843, 1231.2251)
			--   -> 중점         (1000.0000, 15.7171, 1230.0000)
			-- ★ 이 값이 바뀌면 9개 클립의 델타 기준도 같이 어긋난다.
			--   클립은 이 피벗을 원점으로 하는 공간에서 뽑혀 있다.
			PIVOT = { 1000.0000, 15.7171, 1230.0000 },

			-- japan1 값에서 출발한다. 화면 보고 맞출 것.
			--   X 오른쪽(+)/왼쪽(-) · Y 위(+)/아래(-) · Z 앞(-)/뒤(+), 단위 cm.
			OFFSET = { -10, -70, -75 },
			ANIM = true,

			-- ★ 화면 방향 보정. japan1 과 같은 블렌더 파이프라인(축 매핑 (x,y,z)->(-x,z,y))으로
			--   뽑아서 이미 카메라 앞을 보고 있다. 전역 기본값 180 을 타면 두 번 돌아 뒤를 본다.
			--   뷰모델이 뒤통수로 보이면 이 값을 180 으로 바꾸면 된다.
			YAW = 0,

			-- ★ 이 표에 적힌 것만 재생된다. 여기 없는 이름은 nil 로 돌아가서
			--   와키자시/국궁 클립이 이 팔을 몰고 가지 않는다.
			--   (파츠 이름이 MAC_* 라 다른 나라와 하나도 안 겹치기도 한다)
			CLIPS = {
				-- Macuahuitl V10: 32 clips. Model/part contract remains unchanged from V3.
				Intro = "MaxicoIntro",
				Idle = "MaxicoIdle",
				Holster = "MaxicoHolster",
				Draw = "MaxicoDraw",
				SprintDraw = "MaxicoSprintDraw",
				RareDraw = "MaxicoRareDraw",

				Attack1 = "MaxicoAttack1",
				Attack2 = "MaxicoAttack2",
				Attack3 = "MaxicoAttack3",
				WalkAttack1 = "MaxicoWalkAttack1",
				WalkAttack2 = "MaxicoWalkAttack2",
				WalkAttack3 = "MaxicoWalkAttack3",
				SprintAttack1 = "MaxicoSprintAttack1",
				SprintAttack2 = "MaxicoSprintAttack2",
				SprintAttack3 = "MaxicoSprintAttack3",

				BlockIn = "MaxicoBlockIn",
				BlockHold = "MaxicoBlockHold",
				BlockOut = "MaxicoBlockOut",
				CrouchIn = "MaxicoCrouchIn",
				CrouchIdle = "MaxicoCrouchIdle",
				CrouchAttack = "MaxicoCrouchAttack",
				CrouchOut = "MaxicoCrouchOut",

				WalkStart = "MaxicoWalkStart",
				WalkLoop = "MaxicoWalkLoop",
				WalkStop = "MaxicoWalkStop",
				RunStart = "MaxicoRunStart",
				RunLoop = "MaxicoRunLoop",
				RunStop = "MaxicoRunStop",
				SprintTwirl = "MaxicoSprintTwirl",
				KunaiThrow = "MaxicoSprintTwirl",

				JumpSlam = "MaxicoJumpSlam",
				Ryunochi = "MaxicoJumpSlam",
				Transform = "MaxicoTransform",
				UltAttack = "MaxicoUltAttack",
			},
			-- CHARGE_TIME 을 넣지 않는다 -> 공격 버튼이 유지형이 아니라 근접 콤보가 된다.
		},

		-- ★ 2026-09-10 : 새 3분할 팔 뷰모델 (Japan1_Arms).
		--   아래 japan(기존 와키자시)은 한 줄도 건드리지 않았다. 완전히 별개 직업이다.

		-- ★ 2026-09-13 : 와키자시 리메이크 이식 완료.
		--   이 칸의 알맹이는 예전 japan1 그대로다 (Japan1_Arms_v3 + Japan1* 클립).
		--   로비 진열장만 옛 모델(Wakizashi_Viewmodel_Split)로 남겨뒀다 — LobbyUI.DATA.japan 참고.
		--   그래서 보이는 건 옛 칼, 고르면 리메이크가 나온다.
		--   예전 japan 설정은 이랬다 :
		--     SOURCE = "Wakizashi_Viewmodel_Split"
		--     PIVOT = { 852.228790, 73.029171, 4609.211182 }
		--     OFFSET = { -10, -35, -55 } / ANIM = true / CLIPS 없음
		japan = {
			SOURCE = "Japan1_Arms_v3",

			-- ★ 임포트된 뒤 레벨에서 직접 잰 값. 절대좌표라 모델을 옮기면 그 즉시 무효다.
			--   Japan1_Arms_v3 배치 기준 (2026-09-13 재실측. 쿠나이 포함 19파츠)
--   R_UpperArm (655.6750, 60.2743, 1248.7010)
--   L_UpperArm (578.8401, 47.1053, 1251.6146)
--   -> 중점     (617.2576, 53.6898, 1250.1578)
			-- ★ 이 값이 바뀌면 인트로·달리기·공격 클립의 델타 기준도 같이 어긋난다.
			--   클립은 이 피벗을 원점으로 하는 공간에서 뽑혀 있다.
			PIVOT = { 617.2576, 53.6898, 1250.1578 },

			-- ★ 2026-09-11 : 사용자가 화면 보며 맞춘 확정값. 임의로 되돌리지 말 것.
			--   X 오른쪽(+)/왼쪽(-) · Y 위(+)/아래(-) · Z 앞(-)/뒤(+), 단위 cm.
			--   -35 -> -60 -> -70 으로 두 번 내렸다 (뷰모델이 화면 위로 떠 보여서).
			OFFSET = { -10, -70, -75 },
			ANIM = true,

			-- ★ 화면 방향 보정. 이 모델은 이미 카메라 앞을 보고 있어서
			--   전역 기본값 180 을 타면 두 번 돌아 뒤를 보게 된다. 0 이 맞다.
			YAW = 0,

			-- ★ 이 표에 적힌 것만 재생된다. 여기 없는 이름은 nil 로 돌아가서
			--   와키자시 클립이 이 팔을 몰고 가지 않는다 (korea 와 같은 수법).
			--   지금은 인트로 하나뿐이다. 공격·막기 클립을 만들면 여기 한 줄씩 추가.
			CLIPS = {
				Intro = "Japan1Intro",

				-- 기본공격 1타. 블렌더 10~73 (30fps).
				--   cut  프레임53 (1.4333초) : 연타하면 여기서 끊고 2타로
				--   full 프레임73 (2.1000초) : 연타 안 하면 여기까지 가서 대기자세 복귀
				-- ★ Attack2 / Attack3 이 이 표에 없으면 연타해도 안 넘어가고
				--   1타가 끝까지 재생된다. 2타를 만들면 여기 한 줄 추가하면 된다.
				Attack1 = "Japan1FirstTap",

				-- 2타. 블렌더 10~73 (30fps).
				--   cut  프레임45 (1.1667초) : 타격 직후. 연타하면 회수 동작을 건너뛰고 3타로
				--   full 프레임73 (2.1000초) : 연타 안 하면 회수까지 돌고 대기자세 복귀
				-- ★ 1타 cut(53) 자세와 2타 첫 프레임이 0.00 cm 로 일치한다 (실측).
				--   그래서 1타에서 2타로 넘어갈 때 손이 안 튄다.
				--   Attack3 이 아직 없어서 2타에서 연타하면 73까지 가고 끝난다.
				Attack2 = "Japan1SecondTap",

				-- 3타 (콤보 마지막). 블렌더 10~80 (30fps).
				--   cut 이 없어서 항상 끝까지 재생되고 대기자세로 복귀한다.
				--   참격(X-blade)은 COMBO 의 "Attack3" 자리에서만 나간다.
				--   2타 cut(45) ↔ 3타 시작(10) 이 0.00 cm 로 일치한다 (실측).
				Attack3 = "Japan1ThirdTap",

				-- ===== 아직 전용 애니가 없는 기술들 =====
				-- ★ 이 표에 이름이 없으면 getClip 이 nil 을 돌려주는데,
				--   궁극기와 비뢰신은 nil 이면 발동 자체를 포기한다
				--   (onUltPressed / onFlyingRaijinPressed 의 `if not getClip(...) then return end`).
				--   그래서 와키자시 클립을 그대로 물려서 로직이 돌게 한다.
				-- ★ 그 클립들의 파츠 이름(Right_Arm_Mesh / Wakizashi_Blade_R …)은
				--   이 모델의 파츠 이름(R_UpperArm / WKZ_R_Blade …)과 하나도 안 겹친다.
				--   그래서 pose[item.PoseName] 이 전부 nil 이 되어 자세는 안 먹고,
				--   피해·이펙트·투사체 같은 로직만 와키자시와 똑같이 돈다.
				--   전용 애니를 만들면 오른쪽 값만 Japan1... 으로 바꾸면 된다.
				Ryunochi = "Japan1Ryunochi",  -- 궁극기 (용). 블렌더 10~115 (30fps)
				-- 비뢰신 (쿠나이 투척 + 순간이동). 블렌더 10~80 (30fps).
				--   throwAt / kunaiHide = 2.1000초 (프레임73) : 쿠나이가 손을 떠난다
				--   holdAt 도 같은 시각 -- 던진 뒤 그 자세로 정지한다
				-- ★ 클립에 쿠나이 파츠가 들어 있다 (Japan1_Arms_v3 에 쿠나이 포함).
				--   28프레임에 왼손에 붙고 73프레임에 손을 떠난다.
				KunaiThrow = "Japan1KunaiThrow",
				-- 막기 : 블렌더 10~20 (30fps). Out 은 In 을 그대로 되감은 것이다.
				BlockIn = "Japan1BlockIn",   -- 막기 시작 (마지막 자세에서 정지)
				BlockOut = "Japan1BlockOut", -- 막기 해제 (평상시 자세로 복귀)
				Draw = "Japan1Draw",        -- 비뢰신 TP 직후 준비모션 (블렌더 10~80, 30fps)

				-- 달리기 : 준비동작 1회 -> 무한반복 -> 멈추면 마무리 1회.
				--   블렌더 10~44 / 45~93 / 94~105 (30fps).
				--   45 와 93 의 자세가 정확히 같아서 반복 이음새가 안 보인다 (실측 0.0000).
				RunStart = "Japan1RunStart",
				RunLoop  = "Japan1RunLoop",
				RunStop  = "Japan1RunStop",
			},
		},

		korea = {
			-- 2026-08-24 임포트 (Gukgung_Viewmodel_Merged.fbx).
			-- 활/화살은 하나로 합쳐져 있고 시위만 따로다 (17링, 애니메이팅용).
			-- 배율 검증 : 양팔 간격 블렌더 0.26014 -> 레벨 26.02 = 정확히 100배.
			SOURCE = "Gukgung_Viewmodel_Merged",
			PIVOT = { -790.620941, 18.364028, -878.147003 },
			-- 사용자가 화면 보며 맞춘 값. X 는 오른쪽(+) / 왼쪽(-), 단위 cm.
			-- japan 과 완전히 별개다 (japan 은 -10 그대로).
			OFFSET = { 30, -35, -55 },

			-- ===== 이 나라가 쓸 클립 목록 =====
			-- 왼쪽이 컨트롤러가 부르는 이름, 오른쪽이 ReplicatedStorage 의 모듈 이름이다
			-- (실제 인스턴스 이름은 "ViewmodelAnim" + 오른쪽 값).
			--
			-- ★ 여기 없는 이름은 "국궁엔 아직 없는 동작"이라 아예 재생되지 않는다.
			--   이 표를 지우면 와키자시 공격/막기 클립이 국궁 팔을 그대로 몰고 간다 —
			--   팔 파츠 이름이 나라끼리 같아서 이름만으로는 안 걸러지기 때문이다.
			--   Attack1/2/3, BlockIn, BlockOut, Draw, KunaiThrow, Ryunochi 를
			--   일부러 안 넣었다. 국궁 클립을 만들면 그때 여기에 한 줄씩 추가하면 된다.
			CLIPS = {
				-- 기준(rest) 프레임 블렌더 60, 회전중심 (0.106209, 0.218530, -0.140583)
				Intro = "GukgungIntro",

				-- 기본공격 = 시위를 놓는 순간. 버튼을 떼면 재생된다.
				-- Attack2 / Attack3 을 일부러 안 넣었다 -> 콤보가 안 이어진다.
				-- 활은 3연타로 휘두르는 무기가 아니라 한 발씩 쏘는 무기다.
				Attack1 = "GukgungFire",   -- 블렌더 f30~60, 1.25초 (발사 + 재장전. 잠금은 MELEE.fireLock 1초)

				-- 버튼을 누르고 있는 동안 재생. 시간이 아니라 차징 게이지로
				-- 재생 위치를 정한다 (0% = 첫 프레임, 100% = 마지막 프레임).
				BowDraw = "GukgungDraw",   -- 블렌더 f10~30

				-- 블로우 애로우에서 2초를 더 끌어 실패했을 때. 화살은 안 나간다.
				BowFail = "GukgungFail",   -- 블렌더 f84~114, 1.25초

				-- 궁극기 : 파멸의 빛. 화살은 f50 에 손을 떠난다.
				Ult = "GukgungUlt",        -- 블렌더 f10~54, 1.833초

				-- 막기. 로직은 와키자시와 완전히 같다.
				--   누르면 BlockIn 을 재생하고 마지막 자세(블렌더 f15)에서 멈춘다
				--   풀면 BlockOut 이 재생되어 대기 자세로 돌아온다
				BlockIn = "GukgungBlockIn",   -- 블렌더 f10~15
				BlockOut = "GukgungBlockOut", -- 블렌더 f15~20

				-- 당기기~발사가 한 덩어리인 옛 클립. 지금은 안 쓴다.
				-- 차징을 끄고 예전처럼 한 방에 돌리고 싶으면
				-- 아래 CHARGE_TIME 을 지우고 Attack1 을 이걸로 바꾸면 된다.
				-- BowWhole = "GukgungAttack",
			},

			-- ★ 이 값이 있으면 기본공격 버튼이 '유지형' 이 된다.
			--   꾹 누르는 동안 BowDraw 가 게이지를 따라 재생되고, 떼면 Attack1 이 나간다.
			--   0% -> 100% 까지 걸리는 시간(초). 이 줄을 지우면 예전처럼 눌렀다 떼면 한 방이다.
			--   기획 : 0~50% 는 얼마 못 가 땅에 박히고, 51~100% 는 포물선으로 제대로 날아간다.
			--   떼는 순간의 세기(0~1)는 _G.BowPower 로 나간다. 아직 읽는 쪽은 없다.
			CHARGE_TIME = 1.2,

			-- 인트로 재생 속도. 1 = 클립 원래 속도(2.08초).
			--   0.5 -> 절반 속도라 4.17초 (느리게)
			--   0.8 -> 2.60초
			--   2   -> 1.04초            (빠르게)
			-- 클립을 다시 뽑을 필요 없이 이 숫자만 고치고 Play 를 다시 누르면 된다.
			INTRO_SPEED = 0.8,

			-- ★ 국궁 전용 클립이 아직 하나도 없다.
			--   ViewmodelAnimData.PART_ORDER 에 "Right_Arm_Mesh" / "Left_Arm_Mesh" 가 있는데
			--   국궁 팔 이름도 똑같아서, 그냥 두면 와키자시 팔 모션이 국궁 팔에 먹는다.
			--   팔만 칼 휘두르듯 움직이고 활은 제자리에 멈춰 있게 된다.
			--   false 면 클립 포즈를 안 먹이고 idle 자세를 유지한다.
			--   (호흡/흔들림은 카메라 기준이라 그대로 살아 있다)
			--
			--   2026-08-25 : 인트로 클립(ViewmodelAnimGukgungIntro)이 생겨서 풀었다.
			--   false 로 두면 prepareViewmodelParts 가 모든 파츠의 PoseName 을 "__noanim"
			--   으로 박아버려서, 포즈 조회 `pose[item.PoseName]` 가 항상 nil 이 된다.
			--   국궁 전용 클립까지 통째로 안 나오므로 클립이 하나라도 있으면 true 여야 한다.
			--
			--   2026-08-26 : 위 CLIPS 표로 해결됐다. 공격/막기 버튼을 눌러도
			--   와키자시 모션이 안 나온다 (국궁 클립이 없으니 아무 모션도 안 나온다).
			--   단, 뷰모델만 그렇다 — 3인칭 아바타는 AvatarAnimServer 가 아직
			--   무기 구분 없이 wakizashiattack 을 재생한다. 남들 눈엔 칼을 휘두른다.
			--
			--   추출 기준값 : 기준 프레임 60 (1 이나 10 이 아니다)
			--     회전중심 (0.106209, 0.218530, -0.140583) / posScale 240
			--     R = (x,y,z) -> (-x, z, y)
			ANIM = true,
		},
	},

	-- ===== 파츠 색상 =====
	-- 블렌더 머티리얼 색을 sRGB 로 변환한 값이다.
	-- nil 로 두거나 항목을 지우면 그 파츠는 색을 건드리지 않는다.
	--
	-- 참고: MeshPart 는 파츠당 색을 하나만 가질 수 있다.
	--   팔은 블렌더에서도 단색이라 정확히 같지만,
	--   칼은 블렌더에서 7개 머티리얼(칼날/하몬/츠바/손잡이끈/황동...)로 나뉘어 있어
	--   여기서는 가장 넓은 면적인 칼날색으로 대표시켰다.
	--
	-- ★★ 이 표는 런타임에 part.Color 를 칠하는 경로인데, 이 엔진에서는
	--   그 경로가 화면에 안 나온다 (에러도 안 난다). 실제로 보이는 색은
	--   레벨 파츠의 Color 필드에 박아넣은 값이다. 이 표는 기록용으로 둔다.
		COLORS = {
			-- ===== maxico (Macuahuitl v03) =====
			-- 블렌더 Principled BSDF 의 Base Color 를 sRGB 로 변환한 실측값이다.
			--   팔      Avatar_Graphite_Teal        linear (0.045, 0.105, 0.115)
			--   손잡이  M_Macuahuitl_Material_003   linear (0.0488, 0.3806, 0.0607), metal 0.66
			--   몸통    M_Macuahuitl_Material_002   텍스처 평균 x 0.908 (MULTIPLY 노드)
			--   흑요석  M_Macuahuitl_Material_004   linear 0.0725, metal 0.91
			-- 무기가 3파츠뿐인 건 재질이 3개라서다. MeshPart 는 파츠당 색이 하나다.
			MAC_R_UpperArm      = { 60, 91, 95 },
			MAC_R_LowerArm      = { 60, 91, 95 },
			MAC_R_Hand          = { 60, 91, 95 },
			MAC_L_UpperArm      = { 60, 91, 95 },
			MAC_L_LowerArm      = { 60, 91, 95 },
			MAC_L_Hand          = { 60, 91, 95 },
			MAC_Handle          = { 62, 166, 70 },    -- 기계 손잡이 (녹색 금속)
			MAC_Body            = { 188, 164, 134 },  -- 목재 몸통
			MAC_Obsidian        = { 76, 76, 76 },     -- 흑요석 날

			-- ===== japan (와키자시 리메이크 / Japan1_Arms_v3) =====
			-- 팔은 블렌더에서도 단색(Viewmodel_Suit)이라 값이 정확히 같다.
			-- 칼은 MeshPart 하나에 7개 머티리얼이라 색을 하나만 줄 수 있어
			-- 면적이 가장 넓은 칼날 강철색으로 대표시켰다.
			R_UpperArm          = { 63, 63, 69 },
			R_LowerArm          = { 63, 63, 69 },
			R_Hand              = { 63, 63, 69 },
			L_UpperArm          = { 63, 63, 69 },
			L_LowerArm          = { 63, 63, 69 },
			L_Hand              = { 63, 63, 69 },
			WKZ_R_Blade         = { 182, 182, 182 },
			WKZ_R_Hamon         = { 230, 230, 230 },
			WKZ_R_Guard         = { 36, 36, 38 },
			WKZ_R_Wrap          = { 22, 22, 24 },
			WKZ_R_Brass         = { 180, 132, 55 },
			WKZ_R_RaySkin       = { 210, 210, 200 },
			WKZ_L_Blade         = { 182, 182, 182 },
			WKZ_L_Hamon         = { 230, 230, 230 },
			WKZ_L_Guard         = { 36, 36, 38 },
			WKZ_L_Wrap          = { 22, 22, 24 },
			WKZ_L_Brass         = { 180, 132, 55 },
			WKZ_L_RaySkin       = { 210, 210, 200 },
			Kunai               = { 176, 179, 184 },

			Right_Arm_Mesh      = { 63, 63, 69 },     -- 검은 슈트 (블렌더 Viewmodel_Suit)
			Left_Arm_Mesh       = { 63, 63, 69 },
			Wakizashi_R_Blade   = { 182, 182, 182 },  -- 칼날 강철색
			Wakizashi_L_Blade   = { 182, 182, 182 },
			Wakizashi_R_Hamon   = { 230, 230, 230 },
			Wakizashi_L_Hamon   = { 230, 230, 230 },
			Wakizashi_R_Guard   = { 36, 36, 38 },
			Wakizashi_L_Guard   = { 36, 36, 38 },
			Wakizashi_R_Wrap    = { 22, 22, 24 },
			Wakizashi_L_Wrap    = { 22, 22, 24 },
			Wakizashi_R_Brass   = { 180, 132, 55 },
			Wakizashi_L_Brass   = { 180, 132, 55 },
			Wakizashi_R_RaySkin = { 210, 210, 200 },
			Wakizashi_L_RaySkin = { 210, 210, 200 },

			-- 쿠나이는 임포트할 때 머티리얼이 안 쪼개져서 MeshPart 하나로 들어왔다.
			-- 색을 하나만 줄 수 있어서 면적이 넓은 칼날 강철색으로 대표시켰다.
			-- (검은 손잡이 끈까지 살리려면 블렌더에서 재질별로 분리해 다시 임포트해야 한다)
			Kunai               = { 176, 179, 184 },
			-- 재질별로 쪼개서 다시 임포트하면 손잡이 끈을 따로 검게 줄 수 있다
			Kunai_Steel         = { 176, 179, 184 },  -- 칼날 + 고리
			Kunai_Wrap          = { 20, 20, 23 },     -- 손잡이 끈 (검정)

			-- ===== 국궁 (korea) =====
			-- 합쳐진 MeshPart 라 파츠당 색이 하나다. 넓은 면적 기준으로 대표색을 골랐다.
			Gukgung_Bow         = { 190, 172, 157 },  -- 활 몸통
			Gukgung_String      = { 227, 218, 211 },  -- 시위
			Arrow_Gukgung       = { 120, 96, 62 },    -- 화살 (대나무 대)
		},

		-- 색과 함께 적용할 재질. nil 이면 건드리지 않는다.
		-- 금속 느낌을 주려면 "Metal", 무광이면 "Plastic".
		MATERIALS = {
			MAC_R_UpperArm      = "Plastic",
			MAC_R_LowerArm      = "Plastic",
			MAC_R_Hand          = "Plastic",
			MAC_L_UpperArm      = "Plastic",
			MAC_L_LowerArm      = "Plastic",
			MAC_L_Hand          = "Plastic",
			MAC_Handle          = "Metal",
			MAC_Body            = "Plastic",
			MAC_Obsidian        = "Metal",

			R_UpperArm          = "Plastic",
			R_LowerArm          = "Plastic",
			R_Hand              = "Plastic",
			L_UpperArm          = "Plastic",
			L_LowerArm          = "Plastic",
			L_Hand              = "Plastic",
			WKZ_R_Blade         = "Metal",
			WKZ_R_Hamon         = "Metal",
			WKZ_R_Guard         = "Metal",
			WKZ_R_Wrap          = "Plastic",
			WKZ_R_Brass         = "Metal",
			WKZ_R_RaySkin       = "Plastic",
			WKZ_L_Blade         = "Metal",
			WKZ_L_Hamon         = "Metal",
			WKZ_L_Guard         = "Metal",
			WKZ_L_Wrap          = "Plastic",
			WKZ_L_Brass         = "Metal",
			WKZ_L_RaySkin       = "Plastic",
			Kunai               = "Metal",

			Right_Arm_Mesh      = "Plastic",
			Left_Arm_Mesh       = "Plastic",
			Wakizashi_R_Blade   = "Metal",
			Wakizashi_L_Blade   = "Metal",
			Wakizashi_R_Hamon   = "Metal",
			Wakizashi_L_Hamon   = "Metal",
			Wakizashi_R_Guard   = "Metal",
			Wakizashi_L_Guard   = "Metal",
			Wakizashi_R_Wrap    = "Plastic",
			Wakizashi_L_Wrap    = "Plastic",
			Wakizashi_R_Brass   = "Metal",
			Wakizashi_L_Brass   = "Metal",
			Wakizashi_R_RaySkin = "Plastic",
			Wakizashi_L_RaySkin = "Plastic",
			Kunai               = "Metal",
			Kunai_Steel         = "Metal",
			Kunai_Wrap          = "Plastic",

			Gukgung_Bow         = "Plastic",
			Gukgung_String      = "Plastic",
			Arrow_Gukgung       = "Plastic",
		},
}
