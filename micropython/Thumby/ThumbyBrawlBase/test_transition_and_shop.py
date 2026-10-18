"""Latched physical button edges and actionable shopping information."""
import unittest
from copy import deepcopy
from unittest.mock import patch
import test_ThumbyBrawlBase as f
import ThumbyBrawlBase as game
from rules import purchase_status,can_buy,item_counter,new_game_state


class LatchedButton:
    """Minimal consumable press latch; independent of firmware implementation."""
    def __init__(self):
        self.down=False;self.pending=False

    def set(self,down):
        if down and not self.down:self.pending=True
        self.down=down

    def pressed(self):return self.down

    def justPressed(self):
        result=self.pending;self.pending=False
        return result


class TransitionAndShopTests(unittest.TestCase):
    def setUp(self):
        f.TestAdapter.setUp(self);game.thumby=f.fake_thumby
        self.buttons={name:LatchedButton() for name in 'LRABUD'}
        for name,button in self.buttons.items():
            handle=patch.object(game.thumby,'button'+name,button)
            handle.start();self.addCleanup(handle.stop)

    def keys(self,**keys):
        for name,button in self.buttons.items():button.set(keys.get(name,False))

    def texts(self,state):
        game.thumby.display.reset_mock();game.draw_game(state)
        return [c.args[0] for c in game.thumby.display.drawText.call_args_list]

    def test_both_skip_buttons_are_consumed_before_country_choice_or_ending_save(self):
        for progress,kind,route in ((5,'event',[0]),(15,'ending',[0,1,2])):
            for release_before_sample in (False,True):
                self.keys();self.keys(A=True,B=True)
                if release_before_sample:self.keys()
                state=f.state(progress=progress,route=route)
                before=deepcopy(state)
                self.assertTrue(game.cutscene_frame(kind,0,state))
                result=game.step_frame(state)
                self.assertEqual(result['screen_state'],before['screen_state'])
                self.assertEqual(result['route'],route)
                self.assertFalse(result['save_requested'])
                self.assertEqual(result['save_status'],'')
        game.thumby.saveData.save.assert_not_called()

    def test_load_priority_consumes_new_game_edge_instead_of_selecting_country(self):
        self.keys(A=True,B=True)
        self.assertEqual(game.title_frame(),'load')
        state=game.step_frame(new_game_state())
        self.assertEqual((state['screen_state'],state['route'],state['menu_selection']),('country_select',[],0))
        game.thumby.saveData.save.assert_not_called()

    def test_new_game_consumes_down_edge_and_scene_consumes_direction_edges(self):
        self.keys(A=True,D=True)
        self.assertEqual(game.title_frame(),'new')
        state=game.step_frame(new_game_state())
        self.assertEqual(state['menu_selection'],0)
        self.keys();self.keys(A=True,D=True,U=True)
        self.assertTrue(game.cutscene_frame('opening',0,f.state()))
        state=game.step_frame(new_game_state())
        self.assertEqual((state['menu_selection'],state['route']),(0,[]))

    def test_each_title_action_and_skip_remain_available_after_release(self):
        for key,action in (('A','new'),('B','load'),('U','opening'),('D','ending')):
            self.keys();self.keys(**{key:True})
            self.assertEqual(game.title_frame(),action)
            self.assertIsNone(game.title_frame())
        for key in ('A','B'):
            self.keys();self.keys(**{key:True})
            self.assertTrue(game.cutscene_frame('opening',0,f.state()))
            self.assertFalse(game.cutscene_frame('opening',1,f.state()))

    def test_cash_stays_visible_with_largest_stats_and_money(self):
        for screen in ('shop','equip'):
            for money in (0,200,999,10000000):
                state=f.state(screen_state=screen,attack=11,defense=7,money=money)
                before=deepcopy(state)
                texts=self.texts(state)
                self.assertTrue(any(text.startswith('$') for text in texts))
                self.assertEqual(state,before)
                for call in game.thumby.display.drawText.call_args_list:
                    text,x,y,_=call.args
                    self.assertTrue(0<=x and x+6*len(text)<=72 and 0<=y and y+7<=40)

    def test_purchase_refusals_distinguish_stock_levels_owned_and_cash(self):
        state=f.state(money=100,owned=[True,False,False,False],potions=9,hp_growth=5)
        before=deepcopy(state)
        for item,status in ((0,'OWNED'),(5,'STOCK FULL'),(6,'MAX LEVEL'),(9,'A:BUY')):
            self.assertEqual(purchase_status(state,item),status)
            self.assertEqual(can_buy(state,item),status=='A:BUY')
        self.assertEqual(purchase_status(dict(state,money=0),9),'NO MONEY')
        self.assertEqual(state,before)

    def test_details_show_quantity_growth_and_learned_command(self):
        for item,fields,label,action in (
            (5,{'potions':9},'QTY9/9','STOCK FULL'),
            (6,{'hp_growth':5},'LV5/5','MAX LEVEL'),
            (7,{'atk_growth':2},'LV2/5','A:BUY'),
            (8,{'def_growth':3},'LV3/5','A:BUY'),
            (9,{'skill_owned':True},'UU+A READY','OWNED')):
            state=f.state(screen_state='shop_detail',menu_selection=item,money=200,**fields)
            texts=self.texts(state)
            self.assertIn(label,texts);self.assertIn(action,texts)
        texts=self.texts(f.state(screen_state='shop_detail',menu_selection=9))
        self.assertIn('BUY TO LEARN',texts);self.assertIn('NO MONEY',texts)

    def test_list_counters_and_heal_availability_follow_current_state(self):
        state=f.state(screen_state='shop',menu_selection=7,menu_scroll=5,
                      potions=3,hp_growth=2,atk_growth=1)
        self.texts(state)
        counters={(c.args[1],c.args[2]):c.args[0]
                  for c in game.thumby.display.drawText.call_args_list if c.args[1]==42}
        self.assertEqual(counters,{(42,10):'3',(42,20):'2',(42,30):'1'})
        for potions,hp,label in ((0,5,'NONE'),(1,10,'FULL'),(1,5,'HEAL')):
            self.assertIn(label,self.texts(f.state(screen_state='pause',potions=potions,HP=hp)))

    def test_detail_effect_and_cash_are_separated_and_identified(self):
        for screen in ('shop_detail','equip_detail'):
            for item in range(10 if screen=='shop_detail' else 5):
                for money in (0,5,999,1000,999999,10000000):
                    self.texts(f.state(screen_state=screen,menu_selection=item,money=money))
                    row=[c.args for c in game.thumby.display.drawText.call_args_list if c.args[2]==16]
                    self.assertEqual(len(row),2)
                    row.sort(key=lambda c:c[1])
                    effect,cash=row
                    self.assertTrue(cash[0].startswith('$'))
                    self.assertLessEqual(effect[1]+6*len(effect[0])+6,cash[1])
                    self.assertLessEqual(cash[1]+6*len(cash[0]),72)


if __name__=='__main__':unittest.main()
