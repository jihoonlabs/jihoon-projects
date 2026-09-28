class AABB:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.w = width
        self.h = height

    def overlaps(self, other):
        return (self.x < other.x + other.w and
                self.x + self.w > other.x and
                self.y < other.y + other.h and
                self.y + self.h > other.y)

class Player:
    def __init__(self, x, y):
        # Position & Velocity (Fixed point logic compatible)
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0

        # Bounding Box (8x12 px for 128x128 viewport)
        self.width = 8
        self.height = 12

        # Physics Constants
        self.SPEED = 1.2
        self.GRAVITY = 0.25
        self.JUMP_FORCE = -4.0
        
        # State Flags
        self.is_grounded = False
        self.facing_right = True

    def get_bbox(self):
        return AABB(self.x, self.y, self.width, self.height)

    def update(self, btn_left, btn_right, btn_jump, tilemap):
        # 1. Horizontal Movement
        self.vx = 0.0
        if btn_left:
            self.vx = -self.SPEED
            self.facing_right = False
        if btn_right:
            self.vx = self.SPEED
            self.facing_right = True

        # 2. Vertical Movement & Gravity
        if btn_jump and self.is_grounded:
            self.vy = self.JUMP_FORCE
            self.is_grounded = False

        self.vy += self.GRAVITY

        # 3. Apply Horizontal Physics & Collision
        self.x += self.vx
        self.collide_x(tilemap)

        # 4. Apply Vertical Physics & Collision
        self.y += self.vy
        self.collide_y(tilemap)

    def collide_x(self, tilemap):
        p_box = self.get_bbox()
        for tile in tilemap.get_nearby_solid_tiles(p_box):
            if p_box.overlaps(tile):
                if self.vx > 0: # Moving Right
                    self.x = tile.x - self.width
                elif self.vx < 0: # Moving Left
                    self.x = tile.x + tile.w
                self.vx = 0.0

    def collide_y(self, tilemap):
        p_box = self.get_bbox()
        self.is_grounded = False
        for tile in tilemap.get_nearby_solid_tiles(p_box):
            if p_box.overlaps(tile):
                if self.vy > 0: # Falling
                    self.y = tile.y - self.height
                    self.vy = 0.0
                    self.is_grounded = True
                elif self.vy < 0: # Jumping Up
                    self.y = tile.y + tile.h
                    self.vy = 0.0


class TileMap:
    def __init__(self, tile_size=8):
        self.tile_size = tile_size
        # Simple 16x16 Grid for 128x128 room (1: Solid, 0: Empty)
        self.grid = [
            [0]*16 for _ in range(15)
        ] + [[1]*16] # Floor on bottom row

    def get_nearby_solid_tiles(self, bbox):
        """Returns AABB objects of surrounding solid tiles only (Performance Optimization)"""
        start_x = max(0, int(bbox.x // self.tile_size))
        end_x = min(15, int((bbox.x + bbox.w) // self.tile_size))
        start_y = max(0, int(bbox.y // self.tile_size))
        end_y = min(15, int((bbox.y + bbox.h) // self.tile_size))

        tiles = []
        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                if self.grid[ty][tx] == 1:
                    tiles.append(AABB(
                        tx * self.tile_size, 
                        ty * self.tile_size, 
                        self.tile_size, 
                        self.tile_size
                    ))
        return tiles