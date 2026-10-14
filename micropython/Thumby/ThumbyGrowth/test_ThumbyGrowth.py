import sys
import types
import unittest
import importlib
from copy import deepcopy
from unittest.mock import Mock, patch

fake_thumby = types.ModuleType('thumby')
for name in ('L','R','A','B','U','D'):
    button = Mock(spec=['pressed','justPressed'])
    button.pressed.return_value = False
    button.justPressed.return_value = False
    setattr(fake_thumby,'button'+name,button)
fake_thumby.display = Mock(spec=['fill','drawFilledRectangle','drawText','update','setFPS'])
fake_thumby.saveData = Mock(spec=['setName','setItem','getItem','hasItem','save'])
fake_thumby.saveData.hasItem.return_value = False
fake_thumby.saveData.getItem.side_effect = KeyError('저장 없음')
sys.modules['thumby'] = fake_thumby
import ThumbyGrowth


def state(**changes):
    value = dict(HP=10,maxHP=10,money=0,attack=2,defense=0,progress=0,
        owned=[False]*4,equipped_weapon=None,equipped_armor=None,
        player_x=16,enemy_x=112,player_y=28,enemy_y=28,screen_state='safe',menu_selection=0,
        menu_scroll=0,direction='R',player_attack_cooldown=0,
        enemy_attack_cooldown=0,active_enemy=False,enemy_hp=0,
        enemy_attack=0,enemy_defense=0,combat_frame=0,
        save_requested=False,save_status='',menu_r_held=False)
    value.update(changes)
    from rules import legacy_route
    value.setdefault('route', legacy_route(value['progress']))
    value.setdefault('attack_kind', 'punch')
    if value['progress'] in (5,10) and 'screen_state' not in changes:
        value['screen_state']='country_select'
    return value


def inputs(**changes):
    value = dict.fromkeys(('L','R','A','B','U','D','U_held','D_held','A_held','B_held'),False)
    value.update(changes)
    return value


class TestAdapter(unittest.TestCase):
    def setUp(self):
        sys.modules['thumby'] = fake_thumby
        for name in ('L','R','A','B','U','D'):
            button = getattr(fake_thumby,'button'+name)
            button.reset_mock(return_value=True,side_effect=True)
            button.pressed.return_value = False
            button.justPressed.return_value = False
        fake_thumby.display.reset_mock(return_value=True,side_effect=True)
        fake_thumby.saveData.reset_mock(return_value=True,side_effect=True)
        fake_thumby.saveData.hasItem.return_value = False
        fake_thumby.saveData.getItem.side_effect = KeyError('저장 없음')

    def texts(self):
        return [str(call.args[0]) for call in fake_thumby.display.drawText.call_args_list]

    def test_case_1(self):
        # Vertical held input moves in battle; edges still navigate menus.
        for key in ('L','R','A','B','U','D','U_held','D_held','A_held','B_held'):
            button = getattr(fake_thumby, 'button'+key.split('_')[0])
            method = 'pressed' if key in ('L','R','U_held','D_held','A_held','B_held') else 'justPressed'
            getattr(button,method).return_value = True
            result = ThumbyGrowth.handle_inputs()
            self.assertEqual(result,inputs(**{key:True}))
            self.assertTrue(all(type(value) is bool for value in result.values()))
            self.assertGreater(getattr(button,method).call_count,0)
            getattr(button,method).return_value = False
        for key in ('U','D'):
            button = getattr(fake_thumby, 'button'+key)
            button.pressed.return_value = True
            button.justPressed.return_value = True
            self.assertEqual(ThumbyGrowth.handle_inputs(),inputs(**{key:True,key+'_held':True}))
            button.pressed.return_value = False
            button.justPressed.return_value = False
        self.assertEqual(ThumbyGrowth.handle_inputs(),inputs())
        self.assertEqual(fake_thumby.saveData.mock_calls,[])

    def test_case_2(self):
        original = state(screen_state='battle',player_x=100,enemy_x=116,
            active_enemy=True,enemy_hp=6,enemy_attack=2)
        snapshot = deepcopy(original)
        ThumbyGrowth.draw_game(original)
        self.assertEqual(original,snapshot)
        rectangles = fake_thumby.display.drawFilledRectangle.call_args_list
        self.assertTrue(any(32 <= c.args[0] < 40 and c.args[1] == 32 for c in rectangles))
        self.assertTrue(any(0 <= c.args[2] <= 8 and 0 <= c.args[3] <= 8 for c in rectangles))
        self.assertTrue(any(0 <= c.args[2] <= 7 for c in fake_thumby.display.drawText.call_args_list))
        self.assertGreater(fake_thumby.display.update.call_count,0)
        for screen in ('shop','equip'):
            seen = set()
            for selected,scroll in ((0,0),(3,1)):
                fake_thumby.display.reset_mock()
                current = state(screen_state=screen,menu_selection=selected,menu_scroll=scroll)
                ThumbyGrowth.draw_game(current)
                seen.update(self.texts())
                rows = {c.args[2] for c in fake_thumby.display.drawText.call_args_list}
                self.assertTrue({0,10,20,30}.issubset(rows))
                self.assertEqual((current['menu_selection'],current['menu_scroll']),(selected,scroll))
            rendered = ' '.join(seen)
            for name in ('Blade','Sword','Vest','Armor'): self.assertIn(name,rendered)
        for screen in ('shop_detail','equip_detail'):
            for selected,name,price in ((0,'Blade',40),(1,'Sword',80),(2,'Vest',40),(3,'Armor',80)):
                fake_thumby.display.reset_mock()
                current = state(screen_state=screen,menu_selection=selected,
                    menu_scroll=1,money=123456,owned=[True]*4,
                    equipped_weapon=1,equipped_armor=3,attack=6,defense=2)
                before = deepcopy(current)
                ThumbyGrowth.draw_game(current)
                rendered = ' '.join(self.texts())
                self.assertIn(name,rendered)
                self.assertIn(str(price),rendered)
                self.assertIn('123456',rendered)
                self.assertTrue(all(text.isascii() for text in self.texts()))
                self.assertEqual(current,before)
        for status in ('SAVED','SAVE ERR'):
            fake_thumby.display.reset_mock()
            ThumbyGrowth.draw_game(state(save_status=status))
            self.assertIn(status,' '.join(self.texts()))
        self.assertEqual(fake_thumby.saveData.mock_calls,[])

    def test_case_3(self):
        paths = list(sys.path)
        importlib.reload(ThumbyGrowth)
        self.assertEqual(sys.path, paths)
        for name in ('L','R','A','B','U','D'):
            self.assertEqual(getattr(fake_thumby,'button'+name).mock_calls,[])
        self.assertEqual(fake_thumby.saveData.mock_calls,[])
        self.assertEqual(fake_thumby.display.update.call_count,0)

    def test_case_4(self):
        original = state(money=40)
        snapshot = deepcopy(original)
        returned = state(money=41)
        keys = inputs(R=True)
        order = []
        def read(): order.append('입력'); return keys
        def rule(s,i):
            self.assertEqual((s,i),(original,keys)); order.append('규칙'); return deepcopy(returned)
        def draw(s): self.assertEqual(s,returned); order.append('그리기')
        with patch.object(ThumbyGrowth,'handle_inputs',side_effect=read), \
             patch.object(ThumbyGrowth,'update_state',side_effect=rule), \
             patch.object(ThumbyGrowth,'draw_game',side_effect=draw), \
             patch.object(ThumbyGrowth,'save_game') as save:
            result = ThumbyGrowth.step_frame(original)
        self.assertEqual(order,['입력','규칙','그리기'])
        self.assertEqual(result,returned)
        self.assertEqual(save.call_count,0)
        self.assertEqual(original,snapshot)
        for before_screen,after_screen,expected in (('safe','safe','SAVED'),('safe','shop','')):
            original = state(screen_state=before_screen,save_status='SAVED')
            returned = state(screen_state=after_screen,save_status='SAVED')
            with patch.object(ThumbyGrowth,'handle_inputs',return_value=inputs()), \
                 patch.object(ThumbyGrowth,'update_state',return_value=returned), \
                 patch.object(ThumbyGrowth,'draw_game'), \
                 patch.object(ThumbyGrowth,'save_game') as save:
                result = ThumbyGrowth.step_frame(original)
            self.assertEqual(result['save_status'],expected)
            self.assertEqual(save.call_count,0)

    def test_case_5(self):
        for screen,selection in (('safe',3),('pause',1)):
            original = state(screen_state=screen,menu_selection=selection,money=55)
            before = deepcopy(original)
            captured = []
            def saved(value):
                captured.append(deepcopy(value))
                return 'SAVED'
            with patch.object(ThumbyGrowth,'handle_inputs',return_value=inputs(A=True)), \
                 patch.object(ThumbyGrowth,'draw_game') as draw, \
                 patch.object(ThumbyGrowth,'save_game',side_effect=saved) as save:
                result = ThumbyGrowth.step_frame(original)
                self.assertEqual(save.call_count,1)
                self.assertTrue(captured[0]['save_requested'])
                self.assertEqual(result['save_status'],'SAVED')
                self.assertFalse(result['save_requested'])
                self.assertEqual(draw.call_args.args[0],result)
                self.assertEqual(original,before)
                with patch.object(ThumbyGrowth,'handle_inputs',return_value=inputs()):
                    later = ThumbyGrowth.step_frame(result)
                self.assertEqual(save.call_count,1)
                self.assertEqual(later['save_status'],'SAVED')
        original = state(money=55)
        before = deepcopy(original)
        self.assertEqual(ThumbyGrowth.save_game(original),'SAVED')
        self.assertEqual(original,before)
        self.assertEqual(fake_thumby.saveData.save.call_count,1)
        self.assertGreater(fake_thumby.saveData.setItem.call_count,0)
        for call in fake_thumby.saveData.setItem.call_args_list:
            value = call.args[1]
            self.assertNotIsInstance(value,dict)
            if isinstance(value,list):
                self.assertTrue(not value or all(type(v) is type(value[0]) for v in value))

    def test_case_6(self):
        original = state(money=55,screen_state='safe',menu_selection=3,menu_scroll=1)
        before = deepcopy(original)
        fake_thumby.saveData.save.side_effect = OSError('저장 실패')
        with patch.object(ThumbyGrowth,'handle_inputs',return_value=inputs(A=True)), \
             patch.object(ThumbyGrowth,'draw_game'):
            result = ThumbyGrowth.step_frame(original)
        self.assertEqual(result['save_status'],'SAVE ERR')
        self.assertFalse(result['save_requested'])
        for key in before:
            if key not in ('save_status','save_requested'):
                self.assertEqual(result[key],before[key])
        self.assertEqual(original,before)
        self.assertEqual(fake_thumby.saveData.save.call_count,1)
        with patch.object(ThumbyGrowth,'encode_save_data',side_effect=ValueError('인코딩 실패')):
            self.assertEqual(ThumbyGrowth.save_game(original),'SAVE ERR')
        self.assertEqual(original,before)
        self.assertEqual(fake_thumby.saveData.save.call_count,1)

    def test_case_7(self):
        for kind in ('없음','읽기실패','손상'):
            fake_thumby.saveData.reset_mock(return_value=True,side_effect=True)
            fake_thumby.display.reset_mock()
            fake_thumby.saveData.hasItem.return_value = kind != '없음'
            fake_thumby.saveData.getItem.side_effect = OSError('읽기 실패') if kind == '읽기실패' else None
            fake_thumby.saveData.getItem.return_value = '손상된 값'
            result = ThumbyGrowth.load_save_data()
            from rules import new_game_state
            expected = new_game_state()
            for key,value in expected.items():
                self.assertEqual(result[key],value)
            self.assertEqual(fake_thumby.saveData.setItem.call_count,0)
            self.assertEqual(fake_thumby.saveData.save.call_count,0)
            shown = ' '.join(self.texts())
            if kind == '없음': self.assertNotIn('LOAD ERR',shown)
            else: self.assertIn('LOAD ERR',shown)

    def test_case_8(self):
        memory = {}
        def put(key,value): memory[key] = deepcopy(value)
        def get(key,*args): return deepcopy(memory[key])
        fake_thumby.saveData.setItem.side_effect = put
        fake_thumby.saveData.hasItem.side_effect = lambda key: key in memory
        fake_thumby.saveData.getItem.side_effect = get
        original = state(HP=2,money=123,progress=5,owned=[False,True,False,True],
            equipped_weapon=1,equipped_armor=3,attack=6,defense=2)
        self.assertEqual(ThumbyGrowth.save_game(original),'SAVED')
        self.assertTrue(memory)
        fake_thumby.saveData.reset_mock()
        result = ThumbyGrowth.load_save_data()
        self.assertEqual(result,state(money=123,progress=5,owned=[False,True,False,True],equipped_weapon=1,equipped_armor=3,attack=6,defense=2))
        self.assertEqual(fake_thumby.saveData.save.call_count,0)
        self.assertEqual(fake_thumby.saveData.setItem.call_count,0)

    def test_case_9(self):
        # MicroPython 진입 경로 자체와 실기 실행은 별도 검토 대상입니다.
        # 프로필 지침에 따라 여기서는 CPython import 안전성만 검사합니다.
        importlib.reload(ThumbyGrowth)
        self.assertEqual(fake_thumby.saveData.mock_calls,[])
        self.assertEqual(fake_thumby.buttonA.justPressed.call_count,0)
        self.assertEqual(fake_thumby.display.update.call_count,0)

    def test_case_10(self):
        # 이 검사는 CPython fake 검증입니다. 생성기 연결, 실제 FPS·메모리·
        # 가독성·조작성·실기 저장 실패·전원중단 안전성은 미검증입니다.
        original = state(money=90,progress=3)
        snapshot = deepcopy(original)
        fake_thumby.saveData.setItem.side_effect = OSError('fake 쓰기 실패')
        result = ThumbyGrowth.save_game(original)
        self.assertEqual(result,'SAVE ERR')
        self.assertEqual(original,snapshot)
        self.assertEqual(fake_thumby.saveData.save.call_count,0)
