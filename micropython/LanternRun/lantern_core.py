"""LanternRun rules. Integer-only, fixed enemy pool; no device imports."""

LEFT, RIGHT, UP, DOWN, ATTACK, DODGE = 1, 2, 4, 8, 16, 32
PLAY, WON, LOST = 0, 1, 2
ROOM_WIDTH = 112
MIN_Y, MAX_Y = 22, 37
MAX_HP = 10


def clamp(value, low, high):
    return max(low, min(high, value))


class Actor:
    def __init__(self):
        self.reset(0, 28, 0, 0)

    def reset(self, x, y, hp, kind):
        self.x, self.y, self.hp, self.kind = x, y, hp, kind
        self.facing = -1
        self.stun = 0
        self.cooldown = 0
        self.wind = 0
        self.flash = 0


class Game:
    def __init__(self):
        self.player = Actor()
        self.enemies = [Actor(), Actor(), Actor()]
        self.reset()

    def reset(self):
        self.player.reset(12, 30, MAX_HP, -1)
        self.player.facing = 1
        self.room = 0
        self.state = PLAY
        self.frame = 0
        self.previous = 0
        self.attack = 0
        self.buffer = 0
        self.combo = 0
        self.combo_window = 0
        self.dodge = 0
        self.dodge_cooldown = 0
        self.dodge_x, self.dodge_y = 1, 0
        self.invulnerable = 0
        self.hitstop = 0
        self.sound = 0
        self.kills = 0
        self.load_room()

    def load_room(self):
        base = self.room * ROOM_WIDTH
        count = 2 if self.room == 0 else 3
        for i in range(3):
            heavy = self.room == 2 and i == 2
            hp = (6 if heavy else 3) if i < count else 0
            self.enemies[i].reset(base + 48 + i * 22, 24 + i * 5,
                                  hp, 1 if heavy else 0)
            self.enemies[i].cooldown = 12 + i * 8

    def remaining(self):
        return sum(1 for enemy in self.enemies if enemy.hp > 0)

    def camera(self):
        base = self.room * ROOM_WIDTH
        return clamp(self.player.x - 32, base, base + ROOM_WIDTH - 72)

    def bound(self, actor):
        base = self.room * ROOM_WIDTH
        actor.x = clamp(actor.x, base + 4, base + ROOM_WIDTH - 5)
        actor.y = clamp(actor.y, MIN_Y, MAX_Y)

    def strike(self):
        player = self.player
        damage = 2 if self.combo == 3 else 1
        reach = 15 if self.combo == 3 else 12
        for enemy in self.enemies:
            dx = (enemy.x - player.x) * player.facing
            if enemy.hp > 0 and 0 <= dx <= reach and abs(enemy.y - player.y) <= 4:
                enemy.hp = max(0, enemy.hp - damage)
                enemy.stun = 12 if self.combo == 3 else 7
                enemy.wind = 0
                enemy.flash = 4
                enemy.x += player.facing * (7 if self.combo == 3 else 3)
                self.bound(enemy)
                self.hitstop = 2
                self.sound = 2
                if enemy.hp == 0:
                    self.kills += 1

    def hurt_player(self, enemy):
        player = self.player
        if self.invulnerable or self.dodge or player.hp <= 0:
            return
        dx = (player.x - enemy.x) * enemy.facing
        if 0 <= dx <= 11 and abs(player.y - enemy.y) <= 4:
            player.hp = max(0, player.hp - (2 if enemy.kind else 1))
            player.stun = 5
            player.x += enemy.facing * 5
            self.bound(player)
            self.invulnerable = 20
            self.attack = self.buffer = self.combo = self.combo_window = 0
            self.hitstop = 2
            self.sound = 3
            if player.hp == 0:
                self.state = LOST

    def update_enemy(self, enemy, slot):
        if enemy.hp <= 0:
            return
        if enemy.flash:
            enemy.flash -= 1
        if enemy.stun:
            enemy.stun -= 1
            return
        if enemy.wind:
            enemy.wind -= 1
            if enemy.wind == 0:
                self.hurt_player(enemy)
                enemy.cooldown = 24 if enemy.kind else 18
            return
        if enemy.cooldown:
            enemy.cooldown -= 1
        player = self.player
        dx, dy = player.x - enemy.x, player.y - enemy.y
        enemy.facing = 1 if dx >= 0 else -1
        # Wind-up fixes facing and location, giving a real sidestep window.
        if abs(dx) <= 10 and abs(dy) <= 3:
            if enemy.cooldown == 0:
                enemy.wind = 13 if enemy.kind else 10
            return
        # Stagger movement; the player is faster than either enemy type.
        if (self.frame + slot) % (3 if enemy.kind else 2):
            return
        if abs(dy) > 2:
            enemy.y += 1 if dy > 0 else -1
        elif abs(dx) > 8:
            enemy.x += 1 if dx > 0 else -1
        # Keep the small mob legible without dynamic pathfinding structures.
        for other in self.enemies:
            if other is not enemy and other.hp > 0:
                if abs(enemy.x - other.x) < 6 and abs(enemy.y - other.y) < 3:
                    enemy.y += 1 if slot % 2 else -1
        self.bound(enemy)

    def step(self, keys):
        self.sound = 0
        if self.state != PLAY:
            return
        edge = keys & ~self.previous
        self.previous = keys
        if edge & ATTACK:
            self.buffer = 6
        if self.hitstop:
            self.hitstop -= 1
            return
        self.frame = (self.frame + 1) % 120
        player = self.player
        if self.invulnerable:
            self.invulnerable -= 1
        if self.dodge_cooldown:
            self.dodge_cooldown -= 1
        if self.combo_window:
            self.combo_window -= 1
        if player.stun:
            player.stun -= 1
        elif self.dodge:
            player.x += self.dodge_x * 2
            player.y += self.dodge_y * 2
            self.dodge -= 1
        else:
            mx = int(bool(keys & RIGHT)) - int(bool(keys & LEFT))
            my = int(bool(keys & DOWN)) - int(bool(keys & UP))
            if edge & DODGE and self.dodge_cooldown == 0:
                self.dodge_x = mx if mx or my else player.facing
                self.dodge_y = my
                self.dodge = 6
                self.dodge_cooldown = 26
                self.invulnerable = max(self.invulnerable, 7)
                self.attack = self.buffer = 0
                self.sound = 1
            elif self.attack == 0:
                if mx:
                    player.facing = mx
                if self.buffer:
                    self.combo = self.combo % 3 + 1 if self.combo_window else 1
                    self.combo_window = 22
                    self.attack = 8
                    self.buffer = 0
                else:
                    player.x += mx
                    # Diagonals alternate axes to avoid a speed advantage.
                    if not mx or self.frame % 2 == 0:
                        player.y += my
        self.bound(player)
        if self.attack:
            self.attack -= 1
            if self.attack == 5:
                self.strike()
        if self.buffer:
            self.buffer -= 1
        for i in range(3):
            if self.state == PLAY:
                self.update_enemy(self.enemies[i], i)
        if self.state == PLAY and self.remaining() == 0:
            if player.x >= (self.room + 1) * ROOM_WIDTH - 7:
                if self.room == 2:
                    self.state = WON
                    self.sound = 4
                else:
                    self.room += 1
                    player.x = self.room * ROOM_WIDTH + 8
                    player.hp = min(MAX_HP, player.hp + 2)
                    self.attack = self.buffer = self.dodge = 0
                    self.combo = self.combo_window = 0
                    self.load_room()
                    self.sound = 4
