class RoomStreamer:
    def __init__(self, room_width=128, room_height=128):
        self.room_w = room_width
        self.room_h = room_height
        self.current_room_id = 0
        self.visited_rooms = set()

    def check_room_transition(self, player):
        if player.x < 0:
            player.x = self.room_w - player.width - 2
            self.change_room(self.current_room_id - 1)
        elif player.x + player.width > self.room_w:
            player.x = 2
            self.change_room(self.current_room_id + 1)

    def change_room(self, new_room_id):
        self.current_room_id = new_room_id
        self.visited_rooms.add(new_room_id)

    def get_exploration_rate(self, total_rooms):
        if total_rooms == 0:
            return 0.0
        return (len(self.visited_rooms) / total_rooms) * 100.0