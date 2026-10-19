"""Small, hardware-independent rules for the Thumby SRPG prototype."""

MAP_WIDTH = 15
MAP_HEIGHT = 10
BASE_TILE = (0, 0)
BASE_MAX_HP = 100
BASE_GUARD = 5
MAP_TERRAIN = (
    "...............",
    "..#.......#....",
    "...............",
    "....##.........",
    "...............",
    ".........##....",
    "...............",
    "...#...........",
    "...............",
    "...............",
)

MISSIONS = (
    ("기지 방어", "적 부대를 격파하고 기지를 지킨다."),
    ("적 기지 공격", "적 기지의 방어선을 돌파한다."),
    ("봉쇄 돌파", "아군 부대를 포위망 밖으로 이동시킨다."),
    ("최종 점령", "최종 목표 지점을 점령한다."),
)


def create_units():
    """Return a fresh M1 roster; sprites differ while core stats stay balanced."""
    allies = []
    roster = (
        ("RV", "REAL", 1, 2), ("SG", "SUPER", 1, 4),
        ("RZ", "REAL", 2, 3), ("SM", "SUPER", 2, 5),
        ("RF", "REAL", 3, 1), ("ST", "SUPER", 3, 6),
    )
    for unit_id, kind, x, y in roster:
        if kind == "REAL":
            weapons = [
                {"name": "VULCAN", "short": "VUL", "power": 14, "range": 2, "style": "shot"},
                {"name": "SABER", "short": "SAB", "power": 21, "range": 1, "style": "blade"},
                {"name": "BEAM GUN", "short": "BEAM", "power": 24, "range": 3, "style": "beam"},
            ]
            signature = {
                "RV": ("RAIL", 34, 4),
                "RZ": ("LANCE", 32, 2),
                "RF": ("SCOPE", 30, 5),
            }[unit_id]
            weapons.append({"name": signature[0], "short": signature[0][:4],
                            "power": signature[1], "range": signature[2],
                            "style": "beam", "finisher": True})
            en, armor, mobility = 30, 5, 24
        else:
            weapons = [
                {"name": "PUNCH", "short": "PCH", "power": 20, "range": 1, "style": "fist"},
                {"name": "ARM BLAST", "short": "ARM", "power": 22, "range": 2, "style": "beam"},
                {"name": "SHOULDER", "short": "SHO", "power": 24, "range": 3, "style": "shot"},
            ]
            signature = {
                "SG": (("HORN BEAM", "HOR", 32, 4, "beam"),
                       ("TITAN HIT", "TIT", 40, 2, "blade")),
                "SM": (("CROSS RAY", "CRS", 32, 4, "beam"),
                       ("CROSS RAM", "RAM", 40, 2, "blade")),
                "ST": (("TRIAD SHOT", "TRI", 32, 4, "beam"),
                       ("SPIRAL HIT", "SPI", 40, 2, "blade")),
            }[unit_id]
            for name, short, power, weapon_range, style in signature:
                weapons.append({"name": name, "short": short, "power": power,
                                "range": weapon_range,
                                "style": style,
                                "finisher": True})
            en, armor, mobility = 40, 8, 15
        allies.append({"id": unit_id, "team": "ally", "kind": kind,
                       "x": x, "y": y, "hp": 50, "max_hp": 50,
                       "en": en, "max_en": en, "armor": armor,
                       "mobility": mobility, "attack": 20, "move": 3,
                       "range": 2, "guard": armor, "weapons": weapons,
                       "moved": False, "acted": False})
    # The battleship doubles as the protected base and a long-range support unit.
    allies.append({"id": "SH", "team": "ally", "kind": "SHIP",
                   "x": BASE_TILE[0], "y": BASE_TILE[1], "hp": BASE_MAX_HP,
                   "max_hp": BASE_MAX_HP, "en": 60, "max_en": 60,
                   "armor": 10, "mobility": 0, "attack": 26, "move": 0,
                   "range": 5, "guard": 10,
                   "weapons": [{"name": "CANNON", "short": "CANN",
                                "power": 26, "range": 5, "style": "beam"}],
                   "moved": False, "acted": False})
    enemies = [
        {"id": "E1", "team": "enemy", "kind": "ENEMY", "x": 8, "y": 1},
        {"id": "E2", "team": "enemy", "kind": "ENEMY", "x": 9, "y": 3},
        {"id": "E3", "team": "enemy", "kind": "ENEMY", "x": 8, "y": 5},
        {"id": "E4", "team": "enemy", "kind": "ENEMY", "x": 10, "y": 4},
        {"id": "E5", "team": "enemy", "kind": "ENEMY", "x": 11, "y": 1},
        {"id": "E6", "team": "enemy", "kind": "ENEMY", "x": 12, "y": 3},
        {"id": "E7", "team": "enemy", "kind": "ENEMY", "x": 11, "y": 6},
        {"id": "E8", "team": "enemy", "kind": "ENEMY", "x": 13, "y": 5},
    ]
    for enemy in enemies:
        enemy.update({"hp": 50, "max_hp": 50, "en": 20, "max_en": 20,
                      "armor": 5, "mobility": 12, "attack": 20, "move": 3,
                      "range": 2, "guard": 5, "moved": False,
                      "acted": False})
    return allies + enemies


def alive_units(units, team=None):
    return [unit for unit in units
            if unit["hp"] > 0 and (team is None or unit["team"] == team)]


def unit_at(units, x, y):
    for unit in units:
        if unit["hp"] > 0 and unit["x"] == x and unit["y"] == y:
            return unit
    return None


def tile_is_open(x, y, units, moving_unit=None):
    if x < 0 or y < 0 or x >= MAP_WIDTH or y >= MAP_HEIGHT:
        return False
    if (x, y) == BASE_TILE:
        return False
    if MAP_TERRAIN[y][x] == "#":
        return False
    for unit in units:
        if (unit is not moving_unit and unit["hp"] > 0
                and unit["x"] == x and unit["y"] == y):
            return False
    return True


def reachable_tiles(unit, units):
    """Breadth-first movement range, respecting terrain and occupied tiles."""
    reached = {(unit["x"], unit["y"]): 0}
    queue = [(unit["x"], unit["y"])]
    cursor = 0
    while cursor < len(queue):
        x, y = queue[cursor]
        cursor += 1
        distance = reached[(x, y)]
        if distance >= unit["move"]:
            continue
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            point = (nx, ny)
            if point not in reached and tile_is_open(nx, ny, units, unit):
                reached[point] = distance + 1
                queue.append(point)
    return reached


def in_range(attacker, defender, weapon=None):
    distance = abs(attacker["x"] - defender["x"]) + abs(attacker["y"] - defender["y"])
    weapon_range = weapon["range"] if weapon is not None else attacker["range"]
    return distance <= weapon_range


def resolve_attack(attacker, defender, special=False, weapon=None):
    """Apply a deterministic hit so the prototype can focus on readable combat."""
    power = weapon["power"] if weapon is not None else attacker["attack"] + (10 if special else 0)
    armor = defender.get("armor", defender["guard"])
    damage = max(1, power - armor)
    defender["hp"] = max(0, defender["hp"] - damage)
    attacker["acted"] = True
    return damage


def resolve_base_attack(attacker, base_hp):
    """Apply one deterministic strike to the fixed home base."""
    damage = max(1, attacker["attack"] - BASE_GUARD)
    return max(0, base_hp - damage)


def mission_result(units, base_hp=BASE_MAX_HP):
    mobile_allies = [unit for unit in alive_units(units, "ally")
                     if unit["kind"] != "SHIP"]
    ship = next((unit for unit in units if unit["kind"] == "SHIP"), None)
    if base_hp <= 0 or (ship is not None and ship["hp"] <= 0) or not mobile_allies:
        return "defeat"
    if not alive_units(units, "enemy"):
        return "victory"
    return None


def reset_turn(units):
    for unit in units:
        unit["moved"] = False
        unit["acted"] = False
