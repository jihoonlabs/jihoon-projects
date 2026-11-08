"""CPython stand-in for the thumby module, used only by tests and previews.

The display keeps a real 72x40 pixel buffer so tests can check what is
drawn and whether anything is drawn off screen. Text is drawn as its
5x7 bounding box (6 px advance), which is enough for layout checks.
"""
import types

WIDTH, HEIGHT = 72, 40


class FakeDisplay:
    def __init__(self):
        self.pixels = bytearray(WIDTH * HEIGHT)
        self.texts = []
        self.out_of_bounds = []
        self.fps = None
        self.updates = 0

    def _set(self, x, y, color):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.pixels[y * WIDTH + x] = 1 if color else 0
        else:
            self.out_of_bounds.append((x, y))

    def get(self, x, y):
        return self.pixels[y * WIDTH + x]

    def setFPS(self, fps):
        self.fps = fps

    def update(self):
        self.updates += 1

    def fill(self, color):
        value = 1 if color else 0
        for i in range(len(self.pixels)):
            self.pixels[i] = value
        self.texts = []

    def setPixel(self, x, y, color):
        self._set(x, y, color)

    def drawFilledRectangle(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self._set(xx, yy, color)

    def drawRectangle(self, x, y, w, h, color):
        for xx in range(x, x + w):
            self._set(xx, y, color)
            self._set(xx, y + h - 1, color)
        for yy in range(y, y + h):
            self._set(x, yy, color)
            self._set(x + w - 1, yy, color)

    def drawLine(self, x1, y1, x2, y2, color):
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            self._set(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def drawText(self, text, x, y, color):
        self.texts.append((text, x, y, color))
        # Bounding box of the 5x7 glyphs only (the trailing gap is not drawn).
        right = x + len(text) * 6 - 2
        for corner in ((x, y), (right, y + 6)):
            if not (0 <= corner[0] < WIDTH and 0 <= corner[1] < HEIGHT):
                self.out_of_bounds.append(corner)

    def blit(self, data, x, y, w, h, key, mirror_x, mirror_y):
        for yy in range(h):
            for xx in range(w):
                bit = (data[(yy // 8) * w + xx] >> (yy % 8)) & 1
                if bit != key:
                    self._set(x + xx, y + yy, bit)


class FakeButton:
    def __init__(self):
        self.down = False
        self.was_down = False

    def pressed(self):
        return self.down

    def justPressed(self):
        fresh = self.down and not self.was_down
        self.was_down = self.down
        return fresh


class FakeAudio:
    def __init__(self):
        self.calls = []

    def play(self, freq, duration):
        self.calls.append(('play', freq, duration))

    def stop(self):
        self.calls.append(('stop',))


class FakeSave:
    def __init__(self):
        self.items = {}
        self.saved = {}
        self.name = None
        self.save_count = 0

    def setName(self, name):
        self.name = name

    def hasItem(self, key):
        return key in self.saved

    def getItem(self, key):
        return self.saved[key]

    def setItem(self, key, value):
        self.items[key] = value

    def save(self):
        self.saved.update(self.items)
        self.save_count += 1


def make_module():
    module = types.ModuleType('thumby')
    module.display = FakeDisplay()
    module.audio = FakeAudio()
    module.saveData = FakeSave()
    for name in ('U', 'D', 'L', 'R', 'A', 'B'):
        setattr(module, 'button' + name, FakeButton())
    return module
