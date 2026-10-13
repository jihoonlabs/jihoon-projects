class Fighter:
    def __init__(self, x, y, facing=1, is_player=True):
        # 캐릭터의 현재 x 위치
        self.x = x

        # 캐릭터의 현재 y 위치
        self.y = y

        # x축 속도
        # 지금은 거의 안 쓰지만 나중에 넉백/대시 느낌 낼 때 쓸 수 있음
        self.vx = 0

        # y축 속도
        # 점프/중력 처리에 사용
        self.vy = 0

        # 캐릭터 너비
        self.w = 10

        # 캐릭터 높이
        self.h = 16

        # 바라보는 방향
        # 1 = 오른쪽, -1 = 왼쪽
        self.facing = facing

        # 플레이어인지 적인지 구분
        self.is_player = is_player

        # 현재 상태
        # idle, walk, jump, crouch, punch, kick, special, hit, ko 같은 값이 들어감
        self.state = "idle"

        # 바닥에 서 있는지 여부
        self.on_ground = True

        # 체력
        self.hp = 100

        # 일반 공격/특수기 지속 시간 카운터
        self.attack_timer = 0

        # 피격 경직 시간 카운터
        self.hit_timer = 0

        # 현재 사용 중인 특수기 종류
        # 예: "SUPER_A", "GRAB_B", "FIRE_A", "UPPER_B"
        # 아직 특수기를 안 썼으면 None
        self.special_type = None

    def move_left(self):
        # 조작 가능한 상태일 때만 왼쪽 이동 가능
        if self.can_control():
            self.x -= 1
            self.facing = -1

            # 공중이 아니라면 걷기 상태로 변경
            if self.on_ground:
                self.state = "walk"

    def move_right(self):
        # 조작 가능한 상태일 때만 오른쪽 이동 가능
        if self.can_control():
            self.x += 1
            self.facing = 1

            # 공중이 아니라면 걷기 상태로 변경
            if self.on_ground:
                self.state = "walk"

    def jump(self):
        # 조작 가능하고 바닥에 있을 때만 점프 가능
        if self.can_control() and self.on_ground:
            self.vy = -4
            self.on_ground = False
            self.state = "jump"
    
    def crouch(self):
        # 조작 가능하고 바닥에 있을 때만 앉기 가능
        if self.can_control() and self.on_ground:
            self.state = "crouch"
        
    def punch(self):
        # 조작 가능할 때만 일반 펀치 가능
        if self.can_control():
            self.state = "punch"
            self.attack_timer = 8  # 펀치 동작이 유지되는 시간
            self.special_type = None # 일반 공격이므로 특수기 종류는 비움

    def air_punch(self):
        # 점프 손 공격
        if self.can_control():
            self.state = "air_punch"
            self.attack_timer = 8
            self.special_type = None

    def crouch_punch(self):
        # 앉아 손 공격
        if self.can_control():
            self.state = "crouch_punch"
            self.attack_timer = 8
            self.special_type = None

    def kick(self):
        # 조작 가능할 때만 일반 킥 가능
        if self.can_control():
            self.state = "kick"
            self.attack_timer = 10 # 킥 동작 유지 시간
            self.special_type = None  # 일반 공격이므로 특수기 종류는 비움
    
    def air_kick(self):
        # 점프 발 공격
        if self.can_control():
            self.state = "air_kick"
            self.attack_timer = 10
            self.special_type = None

    def crouch_kick(self):
        # 앉아 발 공격
        if self.can_control():
            self.state = "crouch_kick"
            self.attack_timer = 10
            self.special_type = None

    def special(self, special_type):
        # 조작 가능할 때만 특수기 가능
        if self.can_control():
            # 상태는 special로 통일
            self.state = "special"

            # 어떤 특수기인지 따로 저장
            # 예: "DD_A", "RR_B"
            self.special_type = special_type

            if special_type == "SUPER_A":
                self.attack_timer = 25

            elif special_type == "SUPER_B":
                self.attack_timer = 25

            elif special_type == "GRAB_A":
                self.attack_timer = 12

            elif special_type == "GRAB_B":
                self.attack_timer = 12

            elif special_type == "FIRE_A":
                self.attack_timer = 18

            elif special_type == "FIRE_B":
                self.attack_timer = 18

            elif special_type == "UPPER_A":
                self.attack_timer = 14

            elif special_type == "UPPER_B":
                self.attack_timer = 14

            else:
                # 혹시 모르는 값이 들어오면 기본값
                self.attack_timer = 16

    def take_hit(self, damage):
        # 이미 맞는 중이거나 KO 상태면 추가 피격 무시
        if self.hit_timer > 0 or self.state == "ko":
            return

        # 체력 감소
        self.hp -= damage

        # 체력이 0 이하가 되면 KO
        if self.hp <= 0:
            self.hp = 0
            self.state = "ko"

            # KO 되면 기술 정보도 비움
            self.special_type = None
        else:
            # 살아 있으면 피격 상태로 변경
            self.state = "hit"
            self.hit_timer = 8

            # 피격되면 현재 특수기 정보도 비움
            self.special_type = None

    def can_control(self):
        # 아래 상태일 때는 플레이어 입력을 받지 않음
        return self.state not in [
            "punch",
            "kick",
            "crouch_punch",
            "crouch_kick",
            "air_punch",
            "air_kick",
            "special",
            "hit",
            "ko",
        ]

    def update(self, floor_y):
        # 피격 경직 시간이 남아 있으면 1씩 줄임
        if self.hit_timer > 0:
            self.hit_timer -= 1

            # 피격 경직이 끝나고 살아 있으면 idle로 복귀
            if self.hit_timer == 0 and self.hp > 0:
                self.state = "idle"

        # 공격 시간이 남아 있으면 1씩 줄임
        if self.attack_timer > 0:
            self.attack_timer -= 1

            # 공격이 끝나면 살아 있는 경우 idle로 복귀
            if self.attack_timer == 0 and self.hp > 0:
                self.state = "idle"

                # 공격이 끝났으니 특수기 종류도 비움
                self.special_type = None

        # 공중 상태면 중력 적용
        if not self.on_ground:
            # 매 프레임 아래로 당기는 힘
            self.vy += 1

            # y 위치에 속도 반영
            self.y += self.vy

            # 바닥까지 내려왔으면 착지
            if self.y >= floor_y:
                self.y = floor_y
                self.vy = 0
                self.on_ground = True

                # 살아 있으면 착지 후 idle 복귀
                if self.hp > 0:
                    self.state = "idle"

        # 화면 왼쪽 경계 제한
        if self.x < 0:
            self.x = 0

        # 화면 오른쪽 경계 제한
        if self.x > 72 - self.w:
            self.x = 72 - self.w