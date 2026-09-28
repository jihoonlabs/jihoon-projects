import struct

class SaveSystem:
    SAVE_FILE_PATH = "save_data.bin"

    # Struct Format:
    # H: uint16 (hp, max_hp, mp, max_mp, weapon_id, armor_id, luck) -> 7 * 2 = 14 bytes
    # B: uint8 (acc_slot_count) -> 1 byte
    # 3H: uint16 * 3 (acc_slots) -> 6 bytes
    # I: uint32 (map_explored_bitmask) -> 4 bytes
    STRUCT_FORMAT = "<7HB3HI"

    @classmethod
    def save_game(cls, player, streamer):
        data = struct.pack(
            cls.STRUCT_FORMAT,
            int(player.hp),
            int(player.max_hp),
            int(player.mp),
            int(player.max_mp),
            int(player.equipped_weapon_id),
            int(player.equipped_armor_id),
            int(player.luck),
            int(player.unlocked_acc_slots),
            int(player.acc_slots[0]),
            int(player.acc_slots[1]),
            int(player.acc_slots[2]),
            int(streamer.get_map_bitmask())
        )
        with open(cls.SAVE_FILE_PATH, "wb") as f:
            f.write(data)

    @classmethod
    def load_game(cls, player, streamer):
        try:
            with open(cls.SAVE_FILE_PATH, "rb") as f:
                data = f.read()

            unpacked = struct.unpack(cls.STRUCT_FORMAT, data)
            player.hp = unpacked[0]
            player.max_hp = unpacked[1]
            player.mp = unpacked[2]
            player.max_mp = unpacked[3]
            player.equipped_weapon_id = unpacked[4]
            player.equipped_armor_id = unpacked[5]
            player.luck = unpacked[6]
            player.unlocked_acc_slots = unpacked[7]
            player.acc_slots = [unpacked[8], unpacked[9], unpacked[10]]
            streamer.set_map_bitmask(unpacked[11])
            return True
        except Exception:
            return False