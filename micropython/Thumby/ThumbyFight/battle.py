def is_in_range(attacker, defender, reach=12, height_limit=8):
    # 공격하는 쪽의 몸 중앙 x 좌표
    ax = attacker.x + attacker.w // 2

    # 맞는 쪽의 몸 중앙 x 좌표
    dx = defender.x + defender.w // 2

    # 가로 거리 차이 계산
    x_distance = abs(ax - dx)

    # 세로 거리 차이 계산
    y_distance = abs(attacker.y - defender.y)

    # 가로 거리와 세로 거리가 둘 다 조건 안에 들어오면 맞았다고 판정
    return x_distance <= reach and y_distance < height_limit


def resolve_attack(attacker, defender):
    # -----------------------------
    # 1. 서서 기본 손 공격 판정
    # -----------------------------
    if attacker.state == "punch" and attacker.attack_timer == 6:
        # 사거리 12 안에 들어오면 피격
        if is_in_range(attacker, defender, reach=12, height_limit=8):
            defender.take_hit(8)

    # -----------------------------
    # 2. 서서 기본 발 공격 판정
    # -----------------------------
    elif attacker.state == "kick" and attacker.attack_timer == 8:
        # 손보다 조금 더 길게 닿는다고 가정
        if is_in_range(attacker, defender, reach=14, height_limit=8):
            defender.take_hit(12)

    # -----------------------------
    # 3. 앉아 손 공격 판정
    # -----------------------------
    elif attacker.state == "crouch_punch" and attacker.attack_timer == 6:
        # 낮은 자세 공격이라 높이 범위를 조금 줄임
        if is_in_range(attacker, defender, reach=11, height_limit=6):
            defender.take_hit(7)

    # -----------------------------
    # 4. 앉아 발 공격 판정
    # -----------------------------
    elif attacker.state == "crouch_kick" and attacker.attack_timer == 8:
        # 하단 발은 손보다 길고 낮게 닿는 느낌
        if is_in_range(attacker, defender, reach=13, height_limit=6):
            defender.take_hit(10)

    # -----------------------------
    # 5. 점프 손 공격 판정
    # -----------------------------
    elif attacker.state == "air_punch" and attacker.attack_timer == 6:
        # 점프 공격은 높이 차가 좀 있어도 맞게 범위를 넓힘
        if is_in_range(attacker, defender, reach=12, height_limit=14):
            defender.take_hit(9)

    # -----------------------------
    # 6. 점프 발 공격 판정
    # -----------------------------
    elif attacker.state == "air_kick" and attacker.attack_timer == 8:
        # 점프 발은 점프 손보다 약간 더 강하고 길게
        if is_in_range(attacker, defender, reach=14, height_limit=14):
            defender.take_hit(13)

    # -----------------------------
    # 7. 특수기 판정
    # state는 special 하나지만
    # special_type으로 어떤 기술인지 구분
    # -----------------------------
    elif attacker.state == "special":

        # ↓↓ + A : 초필 손
        if attacker.special_type == "SUPER_A" and attacker.attack_timer == 18:
            # 강한 기술이므로 사거리와 데미지를 크게
            if is_in_range(attacker, defender, reach=20, height_limit=10):
                defender.take_hit(28)

        # ↓↓ + B : 초필 발
        elif attacker.special_type == "SUPER_B" and attacker.attack_timer == 18:
            # 초필 발은 손보다 약간 더 멀리 닿게 해도 됨
            if is_in_range(attacker, defender, reach=22, height_limit=10):
                defender.take_hit(30)

        # →→ + A : 잡기 손
        elif attacker.special_type == "GRAB_A" and attacker.attack_timer == 8:
            # 잡기는 아주 가까이에서만 맞도록 설정
            if is_in_range(attacker, defender, reach=8, height_limit=8):
                defender.take_hit(16)

        # →→ + B : 잡기/돌진 발
        elif attacker.special_type == "GRAB_B" and attacker.attack_timer == 8:
            # 손 잡기보다 약간 세게
            if is_in_range(attacker, defender, reach=10, height_limit=8):
                defender.take_hit(18)

        # ←← + A : 장풍 손
        elif attacker.special_type == "FIRE_A" and attacker.attack_timer == 12:
            # 아직 진짜 장풍 오브젝트는 없으니
            # 우선은 긴 사거리 공격처럼 처리
            if is_in_range(attacker, defender, reach=26, height_limit=10):
                defender.take_hit(14)

        # ←← + B : 장풍/돌진 변형 발
        elif attacker.special_type == "FIRE_B" and attacker.attack_timer == 12:
            # 발 쪽은 약간 더 멀리 닿게 설정
            if is_in_range(attacker, defender, reach=28, height_limit=10):
                defender.take_hit(15)

        # ↑↑ + A : 승룡 손
        elif attacker.special_type == "UPPER_A" and attacker.attack_timer == 10:
            # 승룡은 위쪽 타격 느낌을 위해 높이 범위를 넓힘
            if is_in_range(attacker, defender, reach=12, height_limit=16):
                defender.take_hit(20)

        # ↑↑ + B : 승룡 발
        elif attacker.special_type == "UPPER_B" and attacker.attack_timer == 10:
            # 승룡 발은 조금 더 강하게
            if is_in_range(attacker, defender, reach=13, height_limit=16):
                defender.take_hit(22)