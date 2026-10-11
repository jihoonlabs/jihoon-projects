import unittest
from copy import deepcopy
from rules import update_state, calculate_damage, get_item_price, get_item_type, is_valid_save_data, encode_save_data, decode_save_data


def state(**changes):
    value = dict(HP=10, maxHP=10, money=0, attack=2, defense=0, progress=0,
        owned=[False]*4, equipped_weapon=None, equipped_armor=None,
        player_x=16, enemy_x=112, screen_state='safe', menu_selection=0,
        menu_scroll=0, direction='R', player_attack_cooldown=0,
        enemy_attack_cooldown=0, active_enemy=False, enemy_hp=0,
        enemy_attack=0, enemy_defense=0, combat_frame=0,
        save_requested=False, save_status='', menu_r_held=False)
    value.update(changes)
    return value


def inputs(**changes):
    value = dict.fromkeys(('L','R','A','B','U','D'), False)
    value.update(changes)
    return value


def battle(**changes):
    value = state(screen_state='battle', active_enemy=True, enemy_hp=6,
                  enemy_attack=2)
    value.update(changes)
    return value


class TestRules(unittest.TestCase):
    def advance(self, original, **buttons):
        keys = inputs(**buttons)
        before, keys_before = deepcopy(original), deepcopy(keys)
        result = update_state(original, keys)
        self.assertEqual(original, before)
        self.assertEqual(keys, keys_before)
        self.assertIsNot(result, original)
        self.assertIsNot(result['owned'], original['owned'])
        return result

    def test_case_1(self):
        for progress, stats in ((0,(6,2,0)), (1,(10,3,1))):
            result = self.advance(state(progress=progress, HP=3,
                player_x=55, direction='L', combat_frame=9,
                player_attack_cooldown=7), A=True)
            self.assertEqual(result['screen_state'], 'battle')
            self.assertTrue(result['active_enemy'])
            self.assertEqual(tuple(result[k] for k in ('enemy_hp','enemy_attack','enemy_defense')), stats)
            self.assertEqual(tuple(result[k] for k in ('HP','player_x','enemy_x','combat_frame','player_attack_cooldown','enemy_attack_cooldown')), (10,16,112,0,0,0))
            self.assertEqual(result['direction'], 'R')

    def test_case_2(self):
        data = dict(version=1, money=0, progress=0, owned=[False]*4,
                    equipped_weapon=None, equipped_armor=None)
        original = deepcopy(data)
        result = decode_save_data(data)
        self.assertEqual(result, state())
        self.assertEqual(data, original)
        self.assertIsNot(result['owned'], data['owned'])

    def test_case_3(self):
        for screen in ('shop','shop_detail'):
            result = self.advance(state(screen_state=screen, money=40), A=True)
            self.assertEqual(result['money'], 0)
            self.assertEqual(result['owned'], [True,False,False,False])
            self.assertIsNone(result['equipped_weapon'])
            self.assertEqual(result['attack'], 2)
        result = self.advance(state(money=40, menu_selection=1), A=True)
        self.assertEqual(result['screen_state'], 'shop')
        self.assertEqual(result['money'], 40)
        self.assertEqual(result['owned'], [False]*4)
        self.assertEqual([get_item_price(i) for i in range(4)], [40,80,40,80])
        self.assertEqual([get_item_type(i) for i in range(4)], ['weapon','weapon','armor','armor'])

    def test_case_4(self):
        for owned, money in (([False]*4,39), ([True,False,False,False],100)):
            for screen in ('shop','shop_detail'):
                original = state(screen_state=screen, owned=owned[:], money=money)
                result = self.advance(original, A=True, R=True)
                for key in ('HP','money','owned','equipped_weapon','equipped_armor','attack','defense','player_x','enemy_x','enemy_hp','progress','combat_frame','player_attack_cooldown','enemy_attack_cooldown'):
                    self.assertEqual(result[key], original[key])
                self.assertTrue(result['menu_r_held'])

    def test_case_5(self):
        result = state(screen_state='equip', owned=[True]*4,
            equipped_armor=3, defense=2)
        for selected, weapon, attack in ((0,0,4),(1,1,6),(1,None,2)):
            result['menu_selection'] = selected
            result = self.advance(result, A=True)
            self.assertEqual(result['equipped_weapon'], weapon)
            self.assertEqual(result['attack'], attack)
            self.assertEqual((result['equipped_armor'],result['defense']), (3,2))

    def test_case_6(self):
        original = state(screen_state='equip', menu_selection=0)
        self.assertEqual(self.advance(original,A=True), original)
        result = state(screen_state='equip_detail', owned=[True]*4,
                       equipped_weapon=1, attack=6)
        for selected, armor, defense in ((2,2,1),(3,3,2),(3,None,0)):
            result['menu_selection'] = selected
            result = self.advance(result,A=True)
            self.assertEqual((result['equipped_armor'],result['defense']), (armor,defense))
            self.assertEqual((result['equipped_weapon'],result['attack']), (1,6))

    def test_case_7(self):
        first = self.advance(battle(),R=True)
        second = self.advance(first)
        self.assertEqual((first['player_x'],first['enemy_x'],first['combat_frame']), (17,112,1))
        self.assertEqual((second['player_x'],second['enemy_x'],second['combat_frame']), (17,111,2))

    def test_case_8(self):
        for original, buttons, expected in (
            (battle(),dict(L=True,R=True),(16,'R')),
            (battle(player_x=0),dict(L=True),(0,'R')),
            (battle(player_x=136,enemy_x=0),dict(R=True),(136,'R')),
            (battle(enemy_x=24),dict(R=True),(16,'R')),
            (battle(player_x=24,enemy_x=16),dict(L=True),(24,'R'))):
            result = self.advance(original,**buttons)
            self.assertEqual((result['player_x'],result['direction']),expected)

    def test_case_9(self):
        for changes, keys, hp, wait in (
            ({'enemy_x':32},dict(A=True),4,15),
            ({'enemy_x':32,'direction':'L'},dict(A=True),6,15),
            ({'enemy_x':33},dict(A=True),6,15),
            ({'enemy_x':32,'player_attack_cooldown':2},dict(A=True),6,1),
            ({'enemy_x':32},dict(),6,0),
            ({'enemy_x':32,'player_attack_cooldown':1},dict(A=True),4,15)):
            result = self.advance(battle(**changes),**keys)
            self.assertEqual(result['enemy_hp'],hp)
            self.assertEqual(result['player_attack_cooldown'],wait)
        result = self.advance(battle(player_x=32,enemy_x=16,direction='L'),A=True)
        self.assertEqual(result['enemy_hp'],4)

    def test_case_10(self):
        result = self.advance(battle(enemy_x=26),A=True)
        self.assertEqual((result['HP'],result['enemy_hp']), (8,4))
        self.assertEqual((result['player_attack_cooldown'],result['enemy_attack_cooldown']), (15,30))
        later = self.advance(result)
        self.assertEqual((later['player_attack_cooldown'],later['enemy_attack_cooldown']), (14,29))
        distant = self.advance(battle(enemy_x=27))
        self.assertEqual((distant['HP'],distant['enemy_attack_cooldown']), (10,0))
        killed = self.advance(battle(enemy_x=24,enemy_hp=2,HP=1),A=True)
        self.assertEqual((killed['HP'],killed['screen_state']), (10,'safe'))
        defeated = self.advance(battle(enemy_x=24,HP=1))
        self.assertEqual((defeated['HP'],defeated['screen_state']), (0,'defeat'))

    def test_case_11(self):
        for attack, expected in ((2,1),(4,3),(0,1)):
            a,d = {'attack':attack}, {'defense':1}
            result = calculate_damage(a,d)
            self.assertEqual(result,expected)
            self.assertIs(type(result),int)
            self.assertEqual((a,d),({'attack':attack},{'defense':1}))
        result = self.advance(battle(enemy_x=32,enemy_defense=1,attack=4,
            owned=[True,False,False,False],equipped_weapon=0),A=True)
        self.assertEqual(result['enemy_hp'],3)

    def test_case_12(self):
        for progress, reward in ((0,20),(1,30)):
            result = self.advance(battle(enemy_x=24,enemy_hp=1,progress=progress,HP=2),A=True)
            self.assertEqual((result['money'],result['progress'],result['HP']), (reward,progress+1,10))
            self.assertEqual(result['screen_state'],'safe')
            self.assertFalse(result['active_enemy'])
            self.assertEqual(tuple(result[k] for k in ('enemy_hp','enemy_attack','enemy_defense')),(0,0,0))
            for _ in range(3):
                result = self.advance(result)
            self.assertEqual((result['money'],result['progress']),(reward,progress+1))
            self.assertFalse(result['active_enemy'])
            result = self.advance(result,A=True)
            expected = (10,3,1) if progress == 0 else (6,2,0)
            self.assertEqual(tuple(result[k] for k in ('enemy_hp','enemy_attack','enemy_defense')),expected)

    def test_case_13(self):
        fields = ('player_x','enemy_x','enemy_hp','combat_frame','player_attack_cooldown','enemy_attack_cooldown')
        for screen in ('pause','shop','equip','shop_detail','equip_detail','defeat'):
            original = battle(screen_state=screen,combat_frame=7,player_attack_cooldown=9,enemy_attack_cooldown=11)
            result = self.advance(original)
            self.assertEqual(tuple(result[k] for k in fields),tuple(original[k] for k in fields))
        original = battle(combat_frame=7,player_attack_cooldown=9)
        paused = self.advance(original,B=True,A=True,R=True)
        self.assertEqual(paused['screen_state'],'pause')
        self.assertEqual(tuple(paused[k] for k in fields),tuple(original[k] for k in fields))
        resumed = self.advance(paused,B=True,A=True)
        self.assertEqual(resumed['screen_state'],'battle')
        self.assertEqual(tuple(resumed[k] for k in fields),tuple(original[k] for k in fields))
        for screen in ('safe','shop','equip'):
            result = state(screen_state=screen)
            result = self.advance(result,U=True)
            self.assertEqual(result['menu_selection'],0)
            result = self.advance(result,U=True,D=True)
            self.assertEqual(result['menu_selection'],0)
            for _ in range(5): result = self.advance(result,D=True)
            self.assertEqual((result['menu_selection'],result['menu_scroll']),(3,1))
        for screen in ('shop','equip'):
            original = state(screen_state=screen,menu_selection=3,menu_scroll=1)
            detail = self.advance(original,R=True)
            self.assertEqual((detail['screen_state'],detail['menu_selection'],detail['menu_scroll']),(screen+'_detail',3,1))
            back = self.advance(detail,B=True,A=True,R=True)
            self.assertEqual((back['screen_state'],back['menu_selection'],back['menu_scroll']),(screen,3,1))
            held = self.advance(back,R=True)
            self.assertEqual(held['screen_state'],screen)
            released = self.advance(held)
            self.assertEqual(self.advance(released,R=True)['screen_state'],screen+'_detail')
        for screen,selected in (('safe',3),('pause',1)):
            result = self.advance(state(screen_state=screen,menu_selection=selected),A=True)
            self.assertTrue(result['save_requested'])
            self.assertEqual(result['screen_state'],screen)
            self.assertFalse(self.advance(result)['save_requested'])

    def test_case_14(self):
        original = battle(screen_state='defeat',HP=0,money=90,progress=1,
            owned=[True,False,True,False],equipped_weapon=0,equipped_armor=2,
            attack=4,defense=1,player_x=70,enemy_x=80,direction='L',combat_frame=9,
            player_attack_cooldown=5,enemy_attack_cooldown=6)
        result = self.advance(original,A=True)
        self.assertEqual(tuple(result[k] for k in ('money','progress','owned','equipped_weapon','equipped_armor')),
                         tuple(original[k] for k in ('money','progress','owned','equipped_weapon','equipped_armor')))
        self.assertEqual((result['attack'],result['defense'],result['HP']),(4,1,10))
        self.assertEqual((result['player_x'],result['enemy_x'],result['direction']),(16,112,'R'))
        self.assertEqual((result['combat_frame'],result['player_attack_cooldown'],result['enemy_attack_cooldown']),(0,0,0))
        self.assertEqual((result['screen_state'],result['active_enemy'],result['enemy_hp'],result['enemy_attack'],result['enemy_defense']),('battle',True,10,3,1))

    def test_case_15(self):
        original = state(HP=2,money=100,progress=5,owned=[False,True,False,True],
            equipped_weapon=1,equipped_armor=3,attack=6,defense=2)
        before = deepcopy(original)
        data = encode_save_data(original)
        expected = dict(version=1,money=100,progress=5,owned=[False,True,False,True],equipped_weapon=1,equipped_armor=3)
        self.assertEqual(data,expected)
        self.assertEqual(original,before)
        self.assertIsNot(data['owned'],original['owned'])
        self.assertTrue(is_valid_save_data(data))
        result = decode_save_data(data)
        self.assertEqual(result,state(money=100,progress=5,owned=[False,True,False,True],equipped_weapon=1,equipped_armor=3,attack=6,defense=2))
        self.assertIsNot(result['owned'],data['owned'])
        invalid = [None,[],{},dict(data,extra=1)]
        for key in data:
            copy = deepcopy(data); del copy[key]; invalid.append(copy)
        for key,values in (('version',(True,2,1.0)),('money',(True,-1,1.0)),('progress',(False,-1,'5')),
                           ('owned',([0,1,0,1],[True]*3,tuple([True]*4))),
                           ('equipped_weapon',(True,2,-1,0)),('equipped_armor',(True,1,4,2))):
            for value in values: invalid.append(dict(data,**{key:value}))
        for value in invalid:
            snapshot = deepcopy(value)
            self.assertIs(is_valid_save_data(value),False)
            self.assertIsNone(decode_save_data(value))
            self.assertEqual(value,snapshot)

    def test_case_16(self):
        original = state(screen_state='shop',money=80)
        result = self.advance(original,A=True)
        result['owned'][0] = False
        self.assertEqual(original['owned'],[False]*4)
        self.assertEqual(original['money'],80)
