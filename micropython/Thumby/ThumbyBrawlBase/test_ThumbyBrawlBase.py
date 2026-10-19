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
fake_thumby.display = Mock(spec=['fill','drawFilledRectangle','drawText','update','setFPS','blit'])
fake_thumby.audio = Mock(spec=['play','stop'])
fake_thumby.saveData = Mock(spec=['setName','setItem','getItem','hasItem','save'])
fake_thumby.saveData.hasItem.return_value = False
fake_thumby.saveData.getItem.side_effect = KeyError('保存データなし')
sys.modules['thumby'] = fake_thumby
import ThumbyBrawlBase


def state(**changes):
    value = dict(HP=10,maxHP=10,money=0,attack=2,defense=0,progress=0,
        owned=[False]*4,equipped_weapon=None,equipped_armor=None,
        player_x=16,enemy_x=112,player_y=28,enemy_y=28,screen_state='safe',menu_selection=0,
        menu_scroll=0,direction='R',player_attack_cooldown=0,
        enemy_attack_cooldown=0,active_enemy=False,enemy_hp=0,
        enemy_attack=0,enemy_defense=0,combat_frame=0,
        save_requested=False,save_status='',menu_r_held=False)
    value.update(dict(gun_owned=False,skill_owned=False,potions=0,hp_growth=0,atk_growth=0,def_growth=0,command_timer=0,command_ready=0))
    value.update(changes)
    from rules import legacy_route
    value.setdefault('route', legacy_route(value['progress']))
    value.setdefault('attack_kind', 'punch')
    for field in ('enemy_windup','enemy_stun','enemy_hit_flash','player_hit_flash'):
        value.setdefault(field,0)
    if value['progress'] in (5,10) and 'screen_state' not in changes:
        value['screen_state']='country_select'
    return value


def inputs(**changes):
    value = dict.fromkeys(('L','R','A','B','U','D','L_tap','R_tap','U_tap','D_tap',
                           'U_held','D_held','A_held','B_held'),False)
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
        fake_thumby.saveData.getItem.side_effect = KeyError('保存データなし')

    def texts(self):
        return [str(call.args[0]) for call in fake_thumby.display.drawText.call_args_list]

    def test_case_1(self):
        # Directional movement is edge-triggered, even while a key stays held.
        for key in ('L','R','U','D'):
            button=getattr(fake_thumby,'button'+key)
            button.pressed.return_value=True
            button.justPressed.return_value=False
        self.assertEqual(ThumbyBrawlBase.handle_inputs(),inputs())
        for key in ('L','R','U','D'):
            button=getattr(fake_thumby,'button'+key)
            button.justPressed.return_value=True
        result=ThumbyBrawlBase.handle_inputs()
        for key in ('L','R','U','D'):
            self.assertTrue(result[key])
            self.assertTrue(result[key+'_tap'])
        self.assertTrue(result['U_held'] and result['D_held'])
        self.assertTrue(all(type(value) is bool for value in result.values()))
        for key in ('L','R','U','D'):
            getattr(fake_thumby,'button'+key).justPressed.return_value=False
        self.assertEqual(ThumbyBrawlBase.handle_inputs(),inputs())

        # Attack buttons still expose both press edges and held state.
        for key in ('A','B'):
            button=getattr(fake_thumby,'button'+key)
            button.pressed.return_value=True
            button.justPressed.return_value=False
        self.assertEqual(ThumbyBrawlBase.handle_inputs(),inputs(A_held=True,B_held=True))
        for key in ('A','B'):
            getattr(fake_thumby,'button'+key).justPressed.return_value=True
        self.assertEqual(ThumbyBrawlBase.handle_inputs(),inputs(A=True,B=True,A_held=True,B_held=True))
        for key in ('L','R','U','D','A','B'):
            button=getattr(fake_thumby,'button'+key)
            button.pressed.return_value=False
            button.justPressed.return_value=False
        self.assertEqual(ThumbyBrawlBase.handle_inputs(),inputs())
        self.assertEqual(fake_thumby.saveData.mock_calls,[])

    def test_case_2(self):
        original = state(screen_state='battle',player_x=100,enemy_x=116,
            active_enemy=True,enemy_hp=6,enemy_attack=2)
        snapshot = deepcopy(original)
        ThumbyBrawlBase.draw_game(original)
        self.assertEqual(original,snapshot)
        rectangles = fake_thumby.display.drawFilledRectangle.call_args_list
        self.assertTrue(any(c.args[0] <= 35 < c.args[0]+c.args[2]
                            and c.args[1] == 32 and c.args[4] == 1
                            for c in rectangles))
        self.assertTrue(any(0 <= c.args[2] <= 8 and 0 <= c.args[3] <= 8 for c in rectangles))
        self.assertTrue(any(0 <= c.args[2] <= 7 for c in fake_thumby.display.drawText.call_args_list))
        self.assertGreater(fake_thumby.display.update.call_count,0)
        for screen in ('shop','equip'):
            seen = set()
            for selected,scroll in ((0,0),(3,1)):
                fake_thumby.display.reset_mock()
                current = state(screen_state=screen,menu_selection=selected,menu_scroll=scroll)
                ThumbyBrawlBase.draw_game(current)
                seen.update(self.texts())
                rows = {c.args[2] for c in fake_thumby.display.drawText.call_args_list}
                self.assertTrue({0,10,20,30}.issubset(rows))
                self.assertEqual((current['menu_selection'],current['menu_scroll']),(selected,scroll))
            rendered = ' '.join(seen)
            for name in ('BLADE','SWORD','VEST','ARMOR'): self.assertIn(name,rendered)
            self.assertGreaterEqual(fake_thumby.display.drawFilledRectangle.call_count,20)
        for screen in ('shop_detail','equip_detail'):
            for selected,name,price in ((0,'BLADE',40),(1,'SWORD',80),(2,'VEST',40),(3,'ARMOR',80)):
                fake_thumby.display.reset_mock()
                current = state(screen_state=screen,menu_selection=selected,
                    menu_scroll=1,money=123456,owned=[True]*4,
                    equipped_weapon=1,equipped_armor=3,attack=6,defense=2)
                before = deepcopy(current)
                ThumbyBrawlBase.draw_game(current)
                rendered = ' '.join(self.texts())
                self.assertIn(name,rendered)
                self.assertIn(str(price),rendered)
                self.assertIn('$123k',rendered)
                self.assertTrue(all(text.isascii() for text in self.texts()))
                self.assertEqual(current,before)
        for status in ('SAVED','SAVE ERR'):
            fake_thumby.display.reset_mock()
            ThumbyBrawlBase.draw_game(state(save_status=status))
            self.assertIn(status,' '.join(self.texts()))
        self.assertEqual(fake_thumby.saveData.mock_calls,[])

    def test_case_3(self):
        paths = list(sys.path)
        importlib.reload(ThumbyBrawlBase)
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
        def read(): order.append('入力'); return keys
        def rule(s,i):
            self.assertEqual((s,i),(original,keys)); order.append('ルール'); return deepcopy(returned)
        def draw(s): self.assertEqual(s,returned); order.append('描画')
        with patch.object(ThumbyBrawlBase,'handle_inputs',side_effect=read), \
             patch.object(ThumbyBrawlBase,'update_state',side_effect=rule), \
             patch.object(ThumbyBrawlBase,'draw_game',side_effect=draw), \
             patch.object(ThumbyBrawlBase,'save_game') as save:
            result = ThumbyBrawlBase.step_frame(original)
        self.assertEqual(order,['入力','ルール','描画'])
        self.assertEqual(result,returned)
        self.assertEqual(save.call_count,0)
        self.assertEqual(original,snapshot)
        for before_screen,after_screen,expected in (('safe','safe','SAVED'),('safe','shop','')):
            original = state(screen_state=before_screen,save_status='SAVED')
            returned = state(screen_state=after_screen,save_status='SAVED')
            with patch.object(ThumbyBrawlBase,'handle_inputs',return_value=inputs()), \
                 patch.object(ThumbyBrawlBase,'update_state',return_value=returned), \
                 patch.object(ThumbyBrawlBase,'draw_game'), \
                 patch.object(ThumbyBrawlBase,'save_game') as save:
                result = ThumbyBrawlBase.step_frame(original)
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
            with patch.object(ThumbyBrawlBase,'handle_inputs',return_value=inputs(A=True)), \
                 patch.object(ThumbyBrawlBase,'draw_game') as draw, \
                 patch.object(ThumbyBrawlBase,'save_game',side_effect=saved) as save:
                result = ThumbyBrawlBase.step_frame(original)
                self.assertEqual(save.call_count,1)
                self.assertTrue(captured[0]['save_requested'])
                self.assertEqual(result['save_status'],'SAVED')
                self.assertFalse(result['save_requested'])
                self.assertEqual(draw.call_args.args[0],result)
                self.assertEqual(original,before)
                with patch.object(ThumbyBrawlBase,'handle_inputs',return_value=inputs()):
                    later = ThumbyBrawlBase.step_frame(result)
                self.assertEqual(save.call_count,1)
                self.assertEqual(later['save_status'],'SAVED')
        original = state(money=55)
        before = deepcopy(original)
        self.assertEqual(ThumbyBrawlBase.save_game(original),'SAVED')
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
        fake_thumby.saveData.save.side_effect = OSError('保存失敗')
        with patch.object(ThumbyBrawlBase,'handle_inputs',return_value=inputs(A=True)), \
             patch.object(ThumbyBrawlBase,'draw_game'):
            result = ThumbyBrawlBase.step_frame(original)
        self.assertEqual(result['save_status'],'SAVE ERR')
        self.assertFalse(result['save_requested'])
        for key in before:
            if key not in ('save_status','save_requested'):
                self.assertEqual(result[key],before[key])
        self.assertEqual(original,before)
        self.assertEqual(fake_thumby.saveData.save.call_count,1)
        with patch.object(ThumbyBrawlBase,'encode_save_data',side_effect=ValueError('エンコード失敗')):
            self.assertEqual(ThumbyBrawlBase.save_game(original),'SAVE ERR')
        self.assertEqual(original,before)
        self.assertEqual(fake_thumby.saveData.save.call_count,1)

    def test_case_7(self):
        for kind in ('なし','読み込み失敗','破損'):
            fake_thumby.saveData.reset_mock(return_value=True,side_effect=True)
            fake_thumby.display.reset_mock()
            fake_thumby.saveData.hasItem.return_value = kind != 'なし'
            fake_thumby.saveData.getItem.side_effect = OSError('読み込み失敗') if kind == '読み込み失敗' else None
            fake_thumby.saveData.getItem.return_value = '破損データ'
            result = ThumbyBrawlBase.load_save_data()
            import campaign
            expected = campaign.new_game_state()
            for key,value in expected.items():
                self.assertEqual(result[key],value)
            self.assertEqual(fake_thumby.saveData.setItem.call_count,0)
            self.assertEqual(fake_thumby.saveData.save.call_count,0)
            shown = ' '.join(self.texts())
            if kind == 'なし': self.assertNotIn('LOAD ERR',shown)
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
        self.assertEqual(ThumbyBrawlBase.save_game(original),'SAVED')
        self.assertTrue(memory)
        fake_thumby.saveData.reset_mock()
        result = ThumbyBrawlBase.load_save_data()
        import campaign
        self.assertEqual(result['campaign_mode'],True)
        self.assertEqual((result['money'],result['progress'],result['owned'],
                          result['equipped_weapon'],result['equipped_armor'],
                          result['attack'],result['defense'],result['HP']),
                         (123,5,[False,True,False,True],1,3,6,2,10))
        self.assertEqual(fake_thumby.saveData.save.call_count,0)
        self.assertEqual(fake_thumby.saveData.setItem.call_count,0)

    def test_case_9(self):
        # MicroPythonの起動経路と実機での動作は、別途確認が必要です。
        # ここではCPythonから安全にimportできることだけを確認します。
        importlib.reload(ThumbyBrawlBase)
        self.assertEqual(fake_thumby.saveData.mock_calls,[])
        self.assertEqual(fake_thumby.buttonA.justPressed.call_count,0)
        self.assertEqual(fake_thumby.display.update.call_count,0)

    def test_case_10(self):
        # この検証はCPython上のテスト用デバイスによるものです。生成機能との接続、実際のFPS・メモリ・
# 視認性・操作性・実機での保存失敗・電源断に対する安全性は未確認です。
        original = state(money=90,progress=3)
        snapshot = deepcopy(original)
        fake_thumby.saveData.setItem.side_effect = OSError('テスト書き込み失敗')
        result = ThumbyBrawlBase.save_game(original)
        self.assertEqual(result,'SAVE ERR')
        self.assertEqual(original,snapshot)
        self.assertEqual(fake_thumby.saveData.save.call_count,0)
