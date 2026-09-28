class Entity:
    def __init__(self, entity_id, x, y, z=0.0, w=12, h=16, color=0xFFFF):
        self.id = entity_id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = w
        self.h = h
        self.color = color
        
        # Combat State Vars
        self.vx = 0.0
        self.facing_right = True
        self.hitstun = 0
        self.hp = 100

    def apply_hit(self, damage, knockback_x, hitstun):
        self.hp = max(0, self.hp - damage)
        self.vx = knockback_x
        self.hitstun = hitstun

    def update_physics(self):
        # Apply Knockback Friction & Hitstun decay
        if self.hitstun > 0:
            self.hitstun -= 1
            self.x += self.vx
            self.vx *= 0.8  # Friction slowdown
        else:
            self.vx = 0.0