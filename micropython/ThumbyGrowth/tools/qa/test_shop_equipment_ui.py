import unittest
import json
import test_ThumbyGrowth as fixtures
import ThumbyGrowth

class ShopEquipmentUI(unittest.TestCase):
    def setUp(self):
        fixtures.TestAdapter().setUp()
        ThumbyGrowth.thumby = fixtures.fake_thumby

    def frame(self, current, **keys):
        device = fixtures.fake_thumby
        for name in ('L','R','A','B','U','D'):
            button = getattr(device,'button'+name)
            button.pressed.return_value = bool(keys.get(name,False))
            button.justPressed.return_value = bool(keys.get(name,False))
        device.display.reset_mock()
        return ThumbyGrowth.step_frame(current)

    def texts(self):
        return ' '.join(str(c.args[0]) for c in fixtures.fake_thumby.display.drawText.call_args_list)

    def buy_and_equip(self):
        current = fixtures.state(money=50)
        current = self.frame(current,D=True)
        current = self.frame(current,A=True)
        self.assertEqual(current['screen_state'],'shop')
        self.assertIn('$50',self.texts())
        current = self.frame(current,A=True)
        self.assertEqual((current['money'],current['owned'],current['equipped_weapon']), (10,[True,False,False,False],None))
        self.assertIn('BOUGHT',self.texts())
        self.assertIn('$10',self.texts())
        current = self.frame(current,B=True)
        current = self.frame(current,D=True)
        current = self.frame(current,D=True)
        current = self.frame(current,A=True)
        self.assertEqual(current['screen_state'],'equip')
        current = self.frame(current,A=True)
        self.assertEqual((current['equipped_weapon'],current['attack']), (0,4))
        self.assertIn('ON',self.texts())
        self.assertIn('ON ATK4',self.texts())
        return current

    def test_menu_buttons_purchase_and_equipment(self):
        current = self.buy_and_equip()
        self.assertEqual((current['money'],current['attack']), (10,4))

    def test_insufficient_money_is_visible_and_does_not_charge(self):
        original = fixtures.state(screen_state='shop',money=20)
        current = self.frame(original,A=True)
        self.assertEqual((current['money'],current['owned']), (20,[False]*4))
        self.assertIn('NO MONEY',self.texts())
        self.assertIn('$20',self.texts())
        current = self.frame(current,R=True)
        self.assertEqual(current['screen_state'],'shop_detail')
        self.assertIn('NO MONEY',self.texts())

    def test_unowned_equipment_tells_player_to_buy(self):
        current = self.frame(fixtures.state(screen_state='equip'),A=True)
        self.assertIsNone(current['equipped_weapon'])
        self.assertIn('BUY FIRST',self.texts())
        current = self.frame(current,R=True)
        self.assertIn('BUY FIRST',self.texts())

    def test_duplicate_purchase_is_visible_and_free(self):
        current = self.frame(fixtures.state(screen_state='shop',money=50,owned=[True,False,False,False]),A=True)
        self.assertEqual(current['money'],50)
        self.assertIn('BOUGHT',self.texts())
        self.assertIn('Blade+',self.texts())

    def test_equipment_toggle_is_visible_and_recalculates_stats(self):
        current = self.buy_and_equip()
        current = self.frame(current)
        current = self.frame(current,A=True)
        self.assertEqual((current['equipped_weapon'],current['attack']), (None,2))
        self.assertIn('A:EQUIP',self.texts())
        self.assertNotIn('ON ATK',self.texts())

    def test_detail_shows_price_effect_and_available_action(self):
        for item, price, effect in ((0,40,'ATK+2'),(1,80,'ATK+4'),(2,40,'DEF+1'),(3,80,'DEF+2')):
            fixtures.fake_thumby.display.reset_mock()
            ThumbyGrowth.draw_game(fixtures.state(screen_state='shop_detail',menu_selection=item,money=80))
            shown=self.texts()
            self.assertIn('P:'+str(price),shown)
            self.assertIn(effect,shown)
            self.assertIn('A:BUY',shown)

    def test_menu_purchase_equipment_save_and_reload(self):
        memory={}
        device=fixtures.fake_thumby
        device.saveData.setItem.side_effect=lambda key,value:memory.__setitem__(key,value)
        device.saveData.hasItem.side_effect=lambda key:key in memory
        device.saveData.getItem.side_effect=lambda key:memory[key]
        current=self.buy_and_equip()
        current=self.frame(current,B=True)
        for _ in range(3):current=self.frame(current,D=True)
        current=self.frame(current,A=True)
        self.assertEqual(current['save_status'],'SAVED')
        self.assertIn('SAVED',self.texts())
        self.assertEqual(device.saveData.save.call_count,1)
        restored=ThumbyGrowth.load_save_data()
        self.assertEqual((restored['money'],restored['equipped_weapon'],restored['attack']), (10,0,4))
        self.assertEqual(json.loads(memory['state'])['owned'],[True,False,False,False])
