class Entity:
    def __init__(self, entity_id, x, y, z=0.0, w=12, h=16, color=0xFFFF):
        self.id = entity_id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = w
        self.h = h
        self.color = color

    @property
    def screen_x(self):
        return self.x

    @property
    def depth_y(self):
        return self.y