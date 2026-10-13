import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyGrowth as fixtures
import ThumbyGrowth

class AdapterReview(fixtures.TestAdapter):
    # 상속된 고정 테스트를 다시 세지 않도록 별도 suite에서 이 메서드만 선택한다.
    def test_end_to_end_purchase_equip_save_load(self):
        memory={}
        device=fixtures.fake_thumby
        device.saveData.setItem.side_effect=lambda key,value: memory.__setitem__(key,deepcopy(value))
        device.saveData.hasItem.side_effect=lambda key:key in memory
        device.saveData.getItem.side_effect=lambda key:deepcopy(memory[key])
        state=fixtures.state(money=40)
        for keys in (fixtures.inputs(D=True),fixtures.inputs(A=True),fixtures.inputs(A=True),
                     fixtures.inputs(B=True),fixtures.inputs(D=True),fixtures.inputs(D=True),
                     fixtures.inputs(A=True),fixtures.inputs(A=True),fixtures.inputs(B=True),
                     fixtures.inputs(D=True),fixtures.inputs(D=True),fixtures.inputs(D=True),
                     fixtures.inputs(A=True)):
            with patch.object(ThumbyGrowth,'handle_inputs',return_value=keys):
                state=ThumbyGrowth.step_frame(state)
        self.assertEqual((state['money'],state['attack'],state['equipped_weapon'],state['save_status']),(0,4,0,'SAVED'))
        self.assertEqual(device.saveData.save.call_count,1)
        restored=ThumbyGrowth.load_save_data()
        self.assertEqual((restored['money'],restored['attack'],restored['equipped_weapon'],restored['HP']),(0,4,0,10))

    def test_render_ownership_and_equipped_are_visible(self):
        device=fixtures.fake_thumby
        renders=[]
        for owned,equipped in ((False,None),(True,None),(True,0)):
            device.display.reset_mock()
            ThumbyGrowth.draw_game(fixtures.state(screen_state='equip_detail',owned=[owned,False,False,False],equipped_weapon=equipped))
            renders.append(tuple(self.texts()))
        self.assertNotEqual(renders[0],renders[1])
        self.assertNotEqual(renders[1],renders[2])

    def test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep(self):
        device=fixtures.fake_thumby
        ThumbyGrowth.draw_game(fixtures.state(screen_state='battle',active_enemy=True,player_x=16,enemy_x=112))
        calls=device.display.drawFilledRectangle.call_args_list
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].args[:4],(16,32,8,8))
        device.saveData.hasItem.return_value=True
        device.saveData.getItem.side_effect=OSError('읽기 오류')
        with patch.object(ThumbyGrowth.time,'sleep') as sleep:
            result=ThumbyGrowth.load_save_data()
        self.assertEqual(result['screen_state'],'safe')
        self.assertEqual(sleep.call_count,0)

if __name__=='__main__':
    suite=unittest.TestSuite(AdapterReview(name) for name in (
        'test_end_to_end_purchase_equip_save_load',
        'test_render_ownership_and_equipped_are_visible',
        'test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep'))
    runner=unittest.TextTestRunner(verbosity=2)
    raise SystemExit(not runner.run(suite).wasSuccessful())
