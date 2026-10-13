import gc
# gc = garbage collector
# 메모리 정리용 모듈
# Thumby는 메모리가 매우 작아서, 필요 없는 메모리를 정리할 때 쓴다.

import thumby
# Thumby 기기 전용 라이브러리
# 화면, 버튼, FPS 같은 기능을 여기서 사용한다.

from fighter import Fighter
# fighter.py 파일 안에 있는 Fighter 클래스를 가져온다.
# Fighter는 "캐릭터 하나"를 뜻한다고 보면 된다.
# 플레이어도 Fighter, 적도 Fighter로 만들고 있다.

from battle import resolve_attack
# battle.py 안의 resolve_attack 함수를 가져온다.
# 이 함수는 "공격이 실제로 맞았는지"를 처리하는 역할이다.

from hud import draw_hp
# hud.py 안의 draw_hp 함수를 가져온다.
# HUD는 화면 위에 보이는 체력바 같은 UI를 뜻한다.

from inputbuffer import InputBuffer
# inputbuffer.py 안의 InputBuffer 클래스를 가져온다.
# 이건 최근 입력 기록을 저장하는 용도다.
# 예: ↓↓ 입력 같은 특수 커맨드 판정에 필요하다.

# -------------------------
# 플레이어 스프라이트 (졸라맨)
# -------------------------
player_sprite = bytearray([
    0b00000000,
    0b00111000,
    0b01000100,
    0b01000100,
    0b00111000,
    0b00010000,
    0b00111000,
    0b00010000,
    0b00010000,
    0b00101000,
    0b01000100,
    0b01000100,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
])

gc.collect()
# 지금 시점에서 한번 메모리 정리
# 큰 의미는 "게임 시작 전에 불필요한 메모리 비우기"

thumby.display.setFPS(20)
# 게임 루프를 초당 20번 정도 돌게 설정
# 즉, 1초에 20프레임 정도 갱신

floor_y = 30
# 바닥 기준 y값
# 캐릭터가 착지하는 기준 높이로 사용한다.
# 다만 실제 바닥선은 아래에서 floor_y + 16으로 그리고 있어서
# 이 값은 "캐릭터의 y 기준점"이라고 이해하면 된다.

frame_count = 0
# 현재 몇 프레임이 지났는지 세는 변수
# 입력 버퍼에서 "짧은 시간 안에 두 번 눌렀는지" 판정할 때 사용

player = Fighter(10, floor_y, facing=1, is_player=True)
# 플레이어 캐릭터 생성
# x=10 위치, y=floor_y 위치에서 시작
# facing=1 은 오른쪽을 본다는 뜻으로 보통 사용
# is_player=True 는 이 캐릭터가 플레이어라는 표시

enemy = Fighter(50, floor_y, facing=-1, is_player=False)
# 적 캐릭터 생성
# x=50 위치, y=floor_y 위치에서 시작
# facing=-1 은 왼쪽을 본다는 뜻으로 보통 사용
# is_player=False 는 적 캐릭터라는 표시

input_buffer = InputBuffer()
# 입력 기록 저장용 객체 생성
# ↓↓ 입력 같은 걸 체크하기 위해 만든다.

def update_player():
# 플레이어 입력을 처리하는 함수
# 이 함수 안에서 버튼을 읽고, 플레이어 상태를 바꾼다.

    global frame_count
    # 이 함수 안에서 바깥에 있는 frame_count 값을 사용하겠다는 뜻
    # 여기서는 읽기만 하고 있지만, 바깥 변수를 참조한다는 걸 명확히 한 셈

    moved = False
    # 이번 프레임에 플레이어가 이동했는지 기록하는 변수
    # 나중에 "가만히 있으면 idle 상태로 되돌리기"에 사용

    # ← 왼쪽 입력
    if thumby.buttonL.pressed():
    # 왼쪽 버튼이 현재 눌려 있는 동안 계속 True
    # justPressed()와 다르게 "누르고 있는 내내" 작동한다.

        player.move_left()
        # Fighter 클래스 안에 정의된 move_left() 실행
        # 실제로는 x 좌표가 줄어들어서 왼쪽으로 이동한다.

        input_buffer.push("L", frame_count)
        
        moved = True
        # 이번 프레임에 이동했음을 기록

    # → 오른쪽 입력
    if thumby.buttonR.pressed():
    # 오른쪽 버튼이 눌려 있는지 확인

        player.move_right()
        # 오른쪽 이동 처리
        # 보통 x 좌표가 증가한다.

        input_buffer.push("R", frame_count)

        moved = True
        # 이번 프레임에 이동했다는 표시

    # ↑ 점프 입력
    if thumby.buttonU.justPressed():
    # 위 버튼을 "막 눌렀을 때 1번만" True
    # 점프처럼 한 번만 발동해야 하는 입력에 적합

        player.jump()
        # Fighter 안의 jump() 실행
        # 보통 vy를 음수로 줘서 위로 뜨게 만든다.

        input_buffer.push("U", frame_count)

    if thumby.buttonD.justPressed():
    # 아래 버튼을 막 눌렀을 때

        input_buffer.push("D", frame_count)
        # 입력 버퍼에 "D"와 현재 프레임 번호를 저장
        # 즉 "이 프레임에 아래를 눌렀다"는 기록을 남긴다.

        player.crouch()
        # 앉기 상태로 전환
        # state를 crouch로 바꾸는 역할일 가능성이 높다.

    # A 버튼 (손 공격)
    if thumby.buttonA.justPressed():
    # A 버튼을 막 눌렀을 때

        command = input_buffer.get_command(frame_count)
        # 최근 커맨드 가져오기 ("DD", "RR", "LL", "UU" 등)

        if command == "DD":
        # 최근 입력 기록을 보고 ↓↓ 입력이 성립하는지 확인
        # current frame 기준으로 일정 시간 내에 D가 2번 있었는지 보는 함수

            player.special("SUPER_A") # ↓↓ + A 이면 필살기 발동
            input_buffer.clear_command() # 커맨드 사용했으니 제거

        elif command == "RR":
            player.special("GRAB_A") # →→ + A → 전진 기술   
            input_buffer.clear_command()

        elif command == "LL":
            player.special("FIRE_A") # ←← + A → 후진 기술
            input_buffer.clear_command()

        elif command == "UU":
            player.special("UPPER_A") # ↑↑ + A → 상승 기술
            input_buffer.clear_command()

        else:
            if not player.on_ground:
                player.air_punch()      # 점프 공격
            elif player.state == "crouch":
                player.crouch_punch()   # 앉아 공격
            else:
                player.punch()          # 기본 공격

    # B 버튼 (발 공격)
    if thumby.buttonB.justPressed():
    # B 버튼을 막 눌렀을 때

        command = input_buffer.get_command(frame_count)
        # 최근 커맨드 확인

        if command == "DD":
            player.special("SUPER_B")             # ↓↓ + B → 다른 초필 (나중에 분리)
            input_buffer.clear_command()

        elif command == "RR":
            player.special("GRAB_B")              # →→ + B
            input_buffer.clear_command()

        elif command == "LL":
            player.special("FIRE_B")             # ←← + B
            input_buffer.clear_command()

        elif command == "UU":
            player.special("UPPER_B")              # ↑↑ + B
            input_buffer.clear_command()

        else:
            if not player.on_ground:
                player.air_kick()       # 점프 킥
            elif player.state == "crouch":
                player.crouch_kick()    # 앉아 킥
            else:
                player.kick()           # 기본 킥

    if not moved and player.on_ground and player.can_control() and player.state not in ["crouch"]:
    # 이 조건은 "아무 이동 안 했고, 땅에 있고, 조작 가능한 상태고, 앉은 상태도 아니면" 이라는 뜻
    #
    # not moved                -> 이번 프레임에 좌우 이동 안 함
    # player.on_ground         -> 공중이 아님
    # player.can_control()     -> 공격/피격/KO 등 조작불가 상태가 아님
    # state not in ["crouch"]  -> 앉아있는 중도 아님

        player.state = "idle"
        # 그러면 기본 대기 상태(idle)로 되돌림
        # 즉, 아무것도 안 하고 서 있는 상태


def update_enemy_ai():
# 적 캐릭터의 AI를 처리하는 함수
# 지금은 아주 단순한 AI
# "거리 맞추고 가까우면 공격" 정도만 한다.

    if enemy.state in ["hit", "ko", "punch", "kick", "special"]:
    # 적이 이미 피격 중이거나, 죽었거나, 공격 동작 중이면
    # 이번 프레임에는 AI가 새 행동을 하지 않게 막는다.

        return
        # 함수 즉시 종료
        # 아래 이동/공격 로직은 실행하지 않음

    if enemy.x > player.x + 12:
    # 적이 플레이어보다 오른쪽에 너무 멀리 있으면
    # 왼쪽으로 다가오게 만든다.
    # +12는 "너무 딱 붙진 말고 어느 정도 거리 기준"이라고 보면 된다.

        enemy.move_left()
        # 적을 왼쪽으로 이동

    elif enemy.x < player.x - 12:
    # 반대로 적이 플레이어보다 너무 왼쪽에 있으면

        enemy.move_right()
        # 오른쪽으로 이동해서 가까워짐

    else:
        enemy.punch()
        # 충분히 가까우면 펀치 공격
        # 즉, 지금 AI는 "거리 맞추기 + 가까우면 펀치" 뿐이다.


while True:
# 게임 메인 루프
# 게임이 실행되는 동안 계속 반복된다.

    frame_count += 1
    # 프레임 수 1 증가
    # 이 값은 입력 버퍼 시간 판정에 사용됨

    thumby.display.fill(1)
    # 화면 전체를 흰색으로 지움
    # 매 프레임 초기화하는 개념
    # 안 하면 이전 프레임 그림이 남는다.

    update_player()
    # 플레이어 입력 처리
    # 버튼을 읽고 플레이어 상태를 바꾼다.

    update_enemy_ai()
    # 적 AI 처리
    # 적이 이동하거나 공격하게 함

    player.update(floor_y)
    # 플레이어 상태 업데이트
    # 보통 여기서:
    # - 공격 타이머 감소
    # - 피격 타이머 감소
    # - 중력 적용
    # - 점프/착지 처리
    # - 화면 경계 처리
    # 같은 걸 한다.

    enemy.update(floor_y)
    # 적도 같은 방식으로 상태 업데이트

    resolve_attack(player, enemy)
    # 플레이어의 현재 공격 상태를 보고
    # 적에게 맞았는지 판정
    # 맞으면 enemy.take_hit(...) 같은 게 내부에서 실행될 수 있다.

    resolve_attack(enemy, player)
    # 반대로 적의 공격도 플레이어에게 판정
    # 즉, 양쪽 공격 판정을 각각 따로 한다.

    thumby.display.drawLine(0, floor_y + 16, 71, floor_y + 16, 0)
    # 바닥선 그리기
    # x=0에서 x=71까지 가로선
    # y는 floor_y + 16
    #
    # 여기서 주의:
    # 캐릭터 y와 바닥선 y가 다르다.
    # 아마 캐릭터 높이(h=16)를 고려해서
    # "캐릭터의 발이 닿는 선"처럼 보이게 하려고 +16을 더한 것 같다.

    # -------------------------
    # 플레이어 캐릭터 그리기
    # facing 값에 따라 좌우 반전
    # -------------------------
    player_flip = 0 if player.facing == 1 else 1
    thumby.display.blit(player_sprite, int(player.x), int(player.y), 8, 16, -1, player_flip, 0)
    # 플레이어를 검은 사각형으로 그림
    # int()를 쓰는 이유는 위치가 계산 중 float가 될 수도 있어서
    # 화면 그릴 때는 정수 좌표로 맞춰 주려는 것
    #
    # x, y      -> 위치
    # player.w  -> 너비
    # player.h  -> 높이
    # 0         -> 검은색

    # -------------------------
    # 적 캐릭터 그리기
    # 일단 같은 스프라이트 사용
    # -------------------------
    enemy_flip = 0 if enemy.facing == 1 else 1
    thumby.display.blit(player_sprite, int(enemy.x), int(enemy.y), 8, 16, -1, enemy_flip, 0)

    draw_hp(thumby.display, 2, 2, player.hp)
    # 플레이어 체력바 그리기
    # 화면 좌상단 쪽 (2,2)에 그림
    # hp 값에 따라 체력 길이가 달라질 것

    draw_hp(thumby.display, 46, 2, enemy.hp)
    # 적 체력바 그리기
    # 화면 오른쪽 위 쪽에 그림

    thumby.display.update()
    # 지금까지 그린 내용을 실제 화면에 반영
    # 이게 있어야 유저가 보게 된다.