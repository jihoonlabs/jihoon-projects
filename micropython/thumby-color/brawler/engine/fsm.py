class State:
    def __init__(self, name):
        self.name = name

    def enter(self, entity): pass
    def update(self, entity): pass
    def exit(self, entity): pass

class StateMachine:
    def __init__(self, owner):
        self.owner = owner
        self.current_state = None
        self.states = {}

    def add_state(self, state):
        self.states[state.name] = state

    def change_state(self, state_name):
        if self.current_state and self.current_state.name == state_name:
            return
        if self.current_state:
            self.current_state.exit(self.owner)
        
        self.current_state = self.states.get(state_name)
        if self.current_state:
            self.current_state.enter(self.owner)

    def update(self):
        if self.current_state:
            self.current_state.update(self.owner)