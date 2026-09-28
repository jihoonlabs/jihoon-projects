class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = float(x)
        self.y = float(y)
        self.w = 8
        self.h = 12
        self.hp = 20
        self.state = "PATROL"  # PATROL, CHASE, ATTACK
        self.type = enemy_type
        self.vx = 0.5
        self.facing_right = True

    def update(self, player):
        dist_x = abs((player.x + player.width/2) - (self.x + self.w/2))
        
        # State Machine
        if dist_x < 32:
            self.state = "CHASE"
        else:
            self.state = "PATROL"

        if self.state == "PATROL":
            self.x += self.vx
        elif self.state == "CHASE":
            if player.x > self.x:
                self.x += 0.8
                self.facing_right = True
            else:
                self.x -= 0.8
                self.facing_right = False