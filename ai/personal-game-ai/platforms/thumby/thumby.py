"""検査用の疑似thumbyモジュール。

元祖Thumby(72x40モノクロ)のMicroPython APIをCPython上で再現し、
生成ゲームの固定テストを実機なしで実行するために使う。
実機の描画速度・メモリ・音質は再現しない。

テストからは `thumby.sim` で入力の注入と描画結果の確認を行う。
"""

WIDTH = 72
HEIGHT = 40
BUTTON_NAMES = ("A", "B", "U", "D", "L", "R")


class _Sim:
    """テスト専用の操作と記録。ゲームコードからは使わない。"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.held = set()
        self.out_of_bounds = 0
        self.text_boxes = []
        self.frames = 0
        self.fps = None
        self.sounds = []
        self.resets = 0
        self.link_outbox = []
        self.link_inbox = []

    def press(self, *names):
        """指定ボタンを押した状態にする。それ以外は離す。"""
        for name in names:
            if name not in BUTTON_NAMES:
                raise ValueError("unknown button: " + str(name))
        self.held = set(names)

    def release_all(self):
        self.held = set()

    def text_overlaps(self):
        """同じフレーム内で重なった文字列の組を返す。"""
        found = []
        boxes = [box for box in self.text_boxes if box[5] == self.frames]
        for i, first in enumerate(boxes):
            for second in boxes[i + 1:]:
                if _intersects(first[1:5], second[1:5]):
                    found.append((first[0], second[0]))
        return found

    def screen_text(self):
        """現在の画面を '#' と '.' の行で返す。失敗時の確認用。"""
        rows = []
        for y in range(HEIGHT):
            rows.append("".join(
                "#" if display.getPixel(x, y) else "."
                for x in range(WIDTH)
            ))
        return "\n".join(rows)


def _intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


sim = _Sim()


class _Display:
    width = WIDTH
    height = HEIGHT

    def __init__(self):
        self.buffer = bytearray(WIDTH * HEIGHT)
        self.font_width = 5
        self.font_height = 7
        self.font_space = 1
        self.brightness_value = 127

    def _plot(self, x, y, color):
        x = int(x)
        y = int(y)
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.buffer[y * WIDTH + x] = 1 if color else 0
        else:
            # 実機では切り捨てられるが、配置ミスの手掛かりとして数える。
            sim.out_of_bounds += 1

    def fill(self, color):
        value = 1 if color else 0
        for i in range(len(self.buffer)):
            self.buffer[i] = value

    def setPixel(self, x, y, color):
        self._plot(x, y, color)

    def getPixel(self, x, y):
        x = int(x)
        y = int(y)
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            return self.buffer[y * WIDTH + x]
        return 0

    def drawLine(self, x1, y1, x2, y2, color):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        error = dx + dy
        while True:
            self._plot(x1, y1, color)
            if x1 == x2 and y1 == y2:
                return
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x1 += sx
            if doubled <= dx:
                error += dx
                y1 += sy

    def drawRectangle(self, x, y, w, h, color):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        for i in range(w):
            self._plot(x + i, y, color)
            self._plot(x + i, y + h - 1, color)
        for j in range(1, h - 1):
            self._plot(x, y + j, color)
            self._plot(x + w - 1, y + j, color)

    def drawFilledRectangle(self, x, y, w, h, color):
        x, y, w, h = int(x), int(y), int(w), int(h)
        for j in range(h):
            for i in range(w):
                self._plot(x + i, y + j, color)

    def setFont(self, fontFilePath, width, height, space):
        self.font_width = int(width)
        self.font_height = int(height)
        self.font_space = int(space)

    def drawText(self, string, x, y, color):
        string = str(string)
        step = self.font_width + self.font_space
        width = len(string) * step - self.font_space if string else 0
        x = int(x)
        y = int(y)
        sim.text_boxes.append(
            (string, x, y, width, self.font_height, sim.frames)
        )
        if width and (
            x < 0 or y < 0 or x + width > WIDTH
            or y + self.font_height > HEIGHT
        ):
            sim.out_of_bounds += 1
        # 字形は再現せず、文字の占有範囲だけを塗る。
        for index in range(len(string)):
            if string[index] == " ":
                continue
            left = x + index * step
            for j in range(self.font_height):
                for i in range(self.font_width):
                    px = left + i
                    py = y + j
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        self.buffer[py * WIDTH + px] = 1 if color else 0

    def blit(self, bitmapData, x, y, width, height, key=-1,
             mirrorX=0, mirrorY=0):
        self._blit(bitmapData, 0, x, y, width, height, key,
                   mirrorX, mirrorY, None)

    def blitWithMask(self, bitmapData, x, y, width, height, key,
                     mirrorX, mirrorY, maskBitmapData):
        self._blit(bitmapData, 0, x, y, width, height, key,
                   mirrorX, mirrorY, maskBitmapData)

    def _blit(self, data, offset, x, y, width, height, key,
              mirrorX, mirrorY, mask):
        # VLSB: 1バイトが縦8画素、最下位ビットが上端。
        width = int(width)
        height = int(height)
        x = int(x)
        y = int(y)
        pages = (height + 7) // 8
        if offset + width * pages > len(data):
            raise ValueError("bitmapData is shorter than width*height")
        for row in range(height):
            for column in range(width):
                index = offset + (row // 8) * width + column
                bit = (data[index] >> (row % 8)) & 1
                if mask is not None and not (mask[index] >> (row % 8)) & 1:
                    continue
                if bit == key:
                    continue
                px = x + (width - 1 - column if mirrorX else column)
                py = y + (height - 1 - row if mirrorY else row)
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    self.buffer[py * WIDTH + px] = bit
                else:
                    sim.out_of_bounds += 1

    def drawSprite(self, sprite):
        self._blit(sprite.bitmap, sprite._offset(), sprite.x, sprite.y,
                   sprite.width, sprite.height, sprite.key,
                   sprite.mirrorX, sprite.mirrorY, None)

    def drawSpriteWithMask(self, sprite, maskSprite):
        mask = maskSprite.bitmap
        offset = sprite._offset()
        self._blit(sprite.bitmap, offset, sprite.x, sprite.y,
                   sprite.width, sprite.height, sprite.key,
                   sprite.mirrorX, sprite.mirrorY,
                   mask[maskSprite._offset():] if mask is not None else None)

    def update(self):
        sim.frames += 1

    def setFPS(self, fps):
        sim.fps = fps

    def brightness(self, value):
        self.brightness_value = int(value)


class Sprite:
    def __init__(self, width, height, bitmapData, x=0, y=0, key=-1,
                 mirrorX=0, mirrorY=0):
        self.width = int(width)
        self.height = int(height)
        self.bitmap = bitmapData
        self.x = x
        self.y = y
        self.key = key
        self.mirrorX = mirrorX
        self.mirrorY = mirrorY
        self.frameSize = self.width * ((self.height + 7) // 8)
        if self.frameSize <= 0 or len(bitmapData) < self.frameSize:
            raise ValueError("bitmapData is shorter than one frame")
        self.frameCount = len(bitmapData) // self.frameSize
        self.currentFrame = 0

    def getFrame(self):
        return self.currentFrame

    def setFrame(self, frame):
        self.currentFrame = int(frame) % self.frameCount

    def _offset(self):
        return self.currentFrame * self.frameSize


class _Button:
    def __init__(self, name):
        self.name = name
        self._was_down = False

    def pressed(self):
        return self.name in sim.held

    def justPressed(self):
        down = self.name in sim.held
        just = down and not self._was_down
        self._was_down = down
        return just


class _Audio:
    def __init__(self):
        self.enabled = True

    def play(self, freq, duration):
        sim.sounds.append((int(freq), int(duration)))

    def playBlocking(self, freq, duration):
        sim.sounds.append((int(freq), int(duration)))

    def set(self, freq):
        sim.sounds.append((int(freq), None))

    def stop(self):
        sim.sounds.append((0, 0))

    def setEnabled(self, setting):
        self.enabled = bool(setting)


class _SaveData:
    def __init__(self):
        self.name = None
        self.items = {}
        self.saved = {}

    def setName(self, subdirectoryName):
        self.name = str(subdirectoryName)

    def getName(self):
        return self.name

    def _need_name(self):
        if self.name is None:
            raise RuntimeError("saveData.setName() must be called first")

    def setItem(self, key, value):
        self._need_name()
        self.items[key] = value

    def getItem(self, key):
        self._need_name()
        return self.items[key]

    def hasItem(self, key):
        self._need_name()
        return key in self.items

    def delItem(self, key):
        self._need_name()
        del self.items[key]

    def save(self):
        self._need_name()
        self.saved = dict(self.items)


class _Link:
    def send(self, data):
        sim.link_outbox.append(bytes(data))
        return True

    def receive(self):
        if sim.link_inbox:
            return sim.link_inbox.pop(0)
        return None


display = _Display()
audio = _Audio()
saveData = _SaveData()
link = _Link()
buttonA = _Button("A")
buttonB = _Button("B")
buttonU = _Button("U")
buttonD = _Button("D")
buttonL = _Button("L")
buttonR = _Button("R")
_DPAD = (buttonU, buttonD, buttonL, buttonR)
_ACTION = (buttonA, buttonB)


def _any(buttons, just):
    # justPressedは全ボタンの状態を更新するため、短絡評価しない。
    results = [b.justPressed() if just else b.pressed() for b in buttons]
    return any(results)


def inputPressed():
    return _any(_DPAD + _ACTION, False)


def inputJustPressed():
    return _any(_DPAD + _ACTION, True)


def dpadPressed():
    return _any(_DPAD, False)


def dpadJustPressed():
    return _any(_DPAD, True)


def actionPressed():
    return _any(_ACTION, False)


def actionJustPressed():
    return _any(_ACTION, True)


def reset():
    sim.resets += 1
    raise SystemExit("thumby.reset() called")


def _reset_for_test():
    """テストのsetUpで呼び、前のテストの状態を消す。"""
    sim.reset()
    display.__init__()
    audio.__init__()
    saveData.__init__()
    for button in _DPAD + _ACTION:
        button._was_down = False
