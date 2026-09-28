import thumby

COLOR_SKY = 0x18A3
COLOR_BG_BUILDING = 0x3165
COLOR_WALL = 0x52AA
COLOR_STREET = 0x4A49
COLOR_TILE_LINE = 0x2965
COLOR_SHADOW = 0x10A2
COLOR_HITBOX_RED = 0xF800
COLOR_HURTBOX_GREEN = 0x07E0

class Renderer:
    def render_scene(self, camera, entities):
        thumby.display.fill(COLOR_SKY)

        int_cam = int(camera.x)

        # Parallax Background
        bg_offset = int(camera.x * 0.4)
        for bx in range(- (bg_offset % 32), 128, 32):
            thumby.display.drawRectangle(bx, 15, 28, 30, COLOR_BG_BUILDING)

        # Main Street Floor
        thumby.display.drawRectangle(0, 45, 128, 12, COLOR_WALL)
        thumby.display.drawRectangle(0, 57, 128, 71, COLOR_STREET)

        for tx in range(- (int_cam % 24), 128, 24):
            thumby.display.drawLine(tx, 57, tx, 128, COLOR_TILE_LINE)

        # Y-Sorting
        sorted_entities = sorted(entities, key=lambda e: e.y)

        for ent in sorted_entities:
            ex = int(ent.x - int_cam)
            ey = int(ent.y)
            ez = int(ent.z)
            ew, eh = ent.w, ent.h

            if -ew <= ex <= 128 + ew:
                # Shadow
                shadow_w = max(4, ew - int(abs(ez) * 0.4))
                thumby.display.drawLine(ex + (ew - shadow_w) // 2, ey + eh - 1, ex + (ew + shadow_w) // 2, ey + eh - 1, COLOR_SHADOW)

                # Entity Body
                draw_y = ey + ez
                thumby.display.drawRectangle(ex, draw_y, ew, eh, ent.color)

                # Hurtbox Visualizer (Green Box)
                thumby.display.drawRectangle(ex, draw_y, ew, eh, COLOR_HURTBOX_GREEN)

                # Active Attack Hitbox Visualizer (Red Box)
                if getattr(ent, 'is_attacking', False) and hasattr(ent, 'hitbox'):
                    dir_offset = 12 if getattr(ent, 'facing_right', True) else -14
                    atk_x = ex + dir_offset
                    thumby.display.drawRectangle(atk_x, draw_y, 14, 12, COLOR_HITBOX_RED)