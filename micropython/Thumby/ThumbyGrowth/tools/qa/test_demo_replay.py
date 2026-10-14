"""PC tooling checks; Pillow is intentionally outside the device test suite."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from replay_demo import Replay, Button, MemorySave


class DemoReplayTests(unittest.TestCase):
    def test_consumed_edges_and_memory_save_are_independent(self):
        button=Button();button.held=True;button.edge=True
        self.assertTrue(button.justPressed())
        self.assertFalse(button.justPressed())
        self.assertTrue(button.pressed())
        memory=MemorySave();value={'owned':[False]*4}
        memory.setItem('state',value);value['owned'][0]=True
        self.assertFalse(memory.getItem('state')['owned'][0])
        read=memory.getItem('state');read['owned'][1]=True
        self.assertFalse(memory.getItem('state')['owned'][1])

    def test_repeated_direction_edges_require_a_release_frame(self):
        replay=Replay();before=deepcopy(replay.state)
        replay.step(D=True);replay.step(D=True)
        self.assertEqual(replay.state['menu_selection'],2)
        self.assertEqual(replay.inputs,[{'D':True},{},{'D':True}])
        self.assertEqual(before['menu_selection'],0)
        self.assertEqual(replay.memory.writes,0)

    def test_complete_replay_is_deterministic_and_uses_only_earned_resources(self):
        first=Replay();report=first.run()
        second=Replay();again=second.run()
        self.assertEqual(report,again)
        self.assertEqual(first.inputs,second.inputs)
        self.assertEqual(report['cleared_stages'],list(range(1,16)))
        self.assertEqual(report['route'],[0,1,2])
        self.assertEqual(report['earned_money']-sum(p['price'] for p in report['purchases']),45)
        self.assertEqual(report['final_money'],45)
        self.assertTrue(report['skill_used'] and report['healed'])
        self.assertEqual(report['save_load_round_trips'],2)
        self.assertEqual(report['restart_progress'],0)
        self.assertGreater(report['audio_api_calls'],0)
        self.assertTrue(all(0<=p['money_after'] for p in report['purchases']))
        self.assertTrue(all(isinstance(v,bool) for keys in first.inputs for v in keys.values()))
        self.assertTrue(all(image.size==(72,40) for _,image,_ in first.frames))


if __name__=='__main__': unittest.main()
