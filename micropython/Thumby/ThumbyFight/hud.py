def draw_hp(display, x, y, hp):
    width = 24
    current = int((hp / 100) * width)

    display.drawRectangle(x, y, width, 4, 0)
    display.drawFilledRectangle(x + 1, y + 1, current - 2 if current > 2 else 0, 2, 0)