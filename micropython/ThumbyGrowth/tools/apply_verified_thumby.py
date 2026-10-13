"""검증된 Thumby 코드 적용 및 Mac CPython 재검증. Ollama 호출 없음."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PAYLOAD = {'rules.py': "def update_state(state, inputs):\n    new_state = dict(state)\n    new_state['owned'] = list(state['owned'])\n    screen = state['screen_state']\n    r_new = inputs['R'] and not state['menu_r_held']\n    new_state['menu_r_held'] = inputs['R']\n    new_state['save_requested'] = False\n\n    # 복귀 입력은 전환한 화면에서 다시 처리하지 않는다.\n    if inputs['B']:\n        if screen == 'battle':\n            new_state['screen_state'] = 'pause'\n        elif screen == 'pause':\n            new_state['screen_state'] = 'battle'\n        elif screen in ('shop', 'equip'):\n            new_state['screen_state'] = 'safe'\n        elif screen in ('shop_detail', 'equip_detail'):\n            new_state['screen_state'] = screen[:-7]\n            return new_state\n        else:\n            return new_state\n        new_state['menu_selection'] = 0\n        new_state['menu_scroll'] = 0\n        return new_state\n\n    if screen in ('safe', 'pause', 'shop', 'equip'):\n        limit = 1 if screen == 'pause' else 3\n        selected = state['menu_selection']\n        if inputs['U'] and not inputs['D']:\n            selected = max(0, selected - 1)\n        elif inputs['D'] and not inputs['U']:\n            selected = min(limit, selected + 1)\n        scroll = state['menu_scroll']\n        if selected < scroll:\n            scroll = selected\n        elif selected >= scroll + 3:\n            scroll = selected - 2\n        new_state['menu_selection'] = selected\n        new_state['menu_scroll'] = max(0, min(max(0, limit - 2), scroll))\n        if screen in ('shop', 'equip') and r_new:\n            new_state['screen_state'] = screen + '_detail'\n            return new_state\n\n    # NEXT와 재도전은 초기화만 수행하고 전투는 다음 호출부터 진행한다.\n    if inputs['A'] and ((screen == 'safe' and new_state['menu_selection'] == 0)\n                        or screen == 'defeat'):\n        new_state['HP'] = new_state['maxHP']\n        new_state['player_x'] = 16\n        new_state['enemy_x'] = 112\n        new_state['direction'] = 'R'\n        new_state['combat_frame'] = 0\n        new_state['player_attack_cooldown'] = 0\n        new_state['enemy_attack_cooldown'] = 0\n        new_state['active_enemy'] = True\n        odd = new_state['progress'] % 2\n        new_state['enemy_hp'] = 10 if odd else 6\n        new_state['enemy_attack'] = 3 if odd else 2\n        new_state['enemy_defense'] = 1 if odd else 0\n        weapon = new_state['equipped_weapon']\n        armor = new_state['equipped_armor']\n        new_state['attack'] = 2 + (0 if weapon is None else (2 if weapon == 0 else 4))\n        new_state['defense'] = 0 if armor is None else (1 if armor == 2 else 2)\n        new_state['screen_state'] = 'battle'\n        new_state['menu_selection'] = 0\n        new_state['menu_scroll'] = 0\n        return new_state\n\n    if screen == 'safe':\n        if inputs['A']:\n            selected = new_state['menu_selection']\n            if selected in (1, 2):\n                new_state['screen_state'] = 'shop' if selected == 1 else 'equip'\n                new_state['menu_selection'] = 0\n                new_state['menu_scroll'] = 0\n            elif selected == 3:\n                new_state['save_requested'] = True\n        return new_state\n    if screen == 'pause':\n        if inputs['A']:\n            if new_state['menu_selection'] == 0:\n                new_state['screen_state'] = 'battle'\n                new_state['menu_selection'] = 0\n                new_state['menu_scroll'] = 0\n            else:\n                new_state['save_requested'] = True\n        return new_state\n    if screen == 'defeat':\n        return new_state\n\n    if screen in ('shop', 'shop_detail', 'equip', 'equip_detail'):\n        if inputs['A']:\n            item_id = new_state['menu_selection']\n            if screen in ('shop', 'shop_detail'):\n                price = get_item_price(item_id)\n                if not new_state['owned'][item_id] and new_state['money'] >= price:\n                    new_state['money'] -= price\n                    new_state['owned'][item_id] = True\n            elif new_state['owned'][item_id]:\n                if item_id < 2:\n                    new_state['equipped_weapon'] = None if new_state['equipped_weapon'] == item_id else item_id\n                else:\n                    new_state['equipped_armor'] = None if new_state['equipped_armor'] == item_id else item_id\n                weapon = new_state['equipped_weapon']\n                armor = new_state['equipped_armor']\n                new_state['attack'] = 2 + (0 if weapon is None else (2 if weapon == 0 else 4))\n                new_state['defense'] = 0 if armor is None else (1 if armor == 2 else 2)\n        return new_state\n    if screen != 'battle':\n        return new_state\n\n    new_state['combat_frame'] += 1\n    new_state['player_attack_cooldown'] = max(0, state['player_attack_cooldown'] - 1)\n    new_state['enemy_attack_cooldown'] = max(0, state['enemy_attack_cooldown'] - 1)\n    player = state['player_x']\n    enemy = state['enemy_x']\n    moved = player\n    if inputs['L'] and not inputs['R']:\n        moved = max(0, player - 1)\n        if new_state['active_enemy'] and enemy < player:\n            moved = max(moved, enemy + 8)\n    elif inputs['R'] and not inputs['L']:\n        moved = min(136, player + 1)\n        if new_state['active_enemy'] and enemy > player:\n            moved = min(moved, enemy - 8)\n    if moved != player:\n        new_state['direction'] = 'R' if moved > player else 'L'\n    new_state['player_x'] = moved\n    if new_state['active_enemy'] and new_state['combat_frame'] % 2 == 0:\n        if enemy > moved:\n            enemy = max(moved + 8, enemy - 1)\n        else:\n            enemy = min(moved - 8, enemy + 1)\n        new_state['enemy_x'] = enemy\n\n    if inputs['A'] and new_state['player_attack_cooldown'] == 0:\n        new_state['player_attack_cooldown'] = 15\n        gap = enemy - (moved + 8) if new_state['direction'] == 'R' else moved - (enemy + 8)\n        if new_state['active_enemy'] and 0 <= gap <= 8:\n            damage = calculate_damage(new_state, {'defense': new_state['enemy_defense']})\n            new_state['enemy_hp'] = max(0, new_state['enemy_hp'] - damage)\n            if new_state['enemy_hp'] == 0:\n                new_state['money'] += 30 if new_state['progress'] % 2 else 20\n                new_state['progress'] += 1\n                new_state['HP'] = new_state['maxHP']\n                new_state['active_enemy'] = False\n                new_state['enemy_hp'] = 0\n                new_state['enemy_attack'] = 0\n                new_state['enemy_defense'] = 0\n                new_state['screen_state'] = 'safe'\n                new_state['menu_selection'] = 0\n                new_state['menu_scroll'] = 0\n                return new_state\n\n    gap = max(moved, enemy) - (min(moved, enemy) + 8)\n    if new_state['active_enemy'] and 0 <= gap <= 2 and new_state['enemy_attack_cooldown'] == 0:\n        damage = calculate_damage({'attack': new_state['enemy_attack']}, new_state)\n        new_state['HP'] = max(0, new_state['HP'] - damage)\n        new_state['enemy_attack_cooldown'] = 30\n    if new_state['HP'] == 0:\n        new_state['screen_state'] = 'defeat'\n        new_state['menu_selection'] = 0\n        new_state['menu_scroll'] = 0\n    return new_state\n\ndef calculate_damage(attacker_stats, defender_stats):\n    return max(1, attacker_stats['attack'] - defender_stats['defense'])\n\ndef get_item_price(item_id):\n    prices = [40, 80, 40, 80]\n    return prices[item_id]\n\ndef get_item_type(item_id):\n    types = ['weapon', 'weapon', 'armor', 'armor']\n    return types[item_id]\n\ndef is_valid_save_data(data):\n    if not isinstance(data, dict):\n        return False\n    \n    required_keys = {'version', 'money', 'progress', 'owned', 'equipped_weapon', 'equipped_armor'}\n    if set(data.keys()) != required_keys:\n        return False\n    \n    if data['version'] != 1 or type(data['version']) is not int:\n        return False\n    \n    if type(data['money']) is not int or data['money'] < 0:\n        return False\n    \n    if type(data['progress']) is not int or data['progress'] < 0:\n        return False\n    \n    if not isinstance(data['owned'], list) or len(data['owned']) != 4:\n        return False\n    for item in data['owned']:\n        if not isinstance(item, bool):\n            return False\n    \n    if data['equipped_weapon'] is not None and (type(data['equipped_weapon']) is not int or data['equipped_weapon'] not in (0, 1)):\n        return False\n    \n    if data['equipped_armor'] is not None and (type(data['equipped_armor']) is not int or data['equipped_armor'] not in (2, 3)):\n        return False\n    \n    # 장착된 아이템은 반드시 소유해야 함\n    if data['equipped_weapon'] is not None and not data['owned'][data['equipped_weapon']]:\n        return False\n    \n    if data['equipped_armor'] is not None and not data['owned'][data['equipped_armor']]:\n        return False\n    \n    return True\n\ndef encode_save_data(state):\n    return {\n        'version': 1,\n        'money': state['money'],\n        'progress': state['progress'],\n        'owned': list(state['owned']),\n        'equipped_weapon': state['equipped_weapon'],\n        'equipped_armor': state['equipped_armor']\n    }\n\ndef decode_save_data(data):\n    if not is_valid_save_data(data):\n        return None\n    \n    new_state = dict(\n        HP=10,\n        maxHP=10,\n        money=data['money'],\n        attack=2,\n        defense=0,\n        progress=data['progress'],\n        owned=list(data['owned']),\n        equipped_weapon=data['equipped_weapon'],\n        equipped_armor=data['equipped_armor'],\n        player_x=16,\n        enemy_x=112,\n        screen_state='safe',\n        menu_selection=0,\n        menu_scroll=0,\n        direction='R',\n        player_attack_cooldown=0,\n        enemy_attack_cooldown=0,\n        active_enemy=False,\n        enemy_hp=0,\n        enemy_attack=0,\n        enemy_defense=0,\n        combat_frame=0,\n        save_requested=False,\n        save_status='',\n        menu_r_held=False\n    )\n    \n    # 장비 스탯 재계산\n    if new_state['equipped_weapon'] is not None:\n        new_state['attack'] += 2 if new_state['equipped_weapon'] == 0 else 4\n    \n    if new_state['equipped_armor'] is not None:\n        new_state['defense'] += 1 if new_state['equipped_armor'] == 2 else 2\n    \n    return new_state\n", 'ThumbyGrowth.py': "import sys\nimport time\ntry:\n    import ujson as json\nexcept ImportError:\n    import json\nimport thumby\nfrom rules import update_state, encode_save_data, decode_save_data\n\n\ndef main_loop():\n    thumby.display.setFPS(30)\n    state = load_save_data()\n    while True:\n        state = step_frame(state)\n\n\ndef step_frame(state):\n    inputs = handle_inputs()\n    new_state = update_state(state, inputs)\n    if new_state['save_requested']:\n        new_state['save_status'] = save_game(new_state)\n        new_state['save_requested'] = False\n    elif new_state['screen_state'] != state['screen_state']:\n        new_state['save_status'] = ''\n    else:\n        new_state['save_status'] = state['save_status']\n    draw_game(new_state)\n    return new_state\n\n\ndef draw_game(state):\n    display = thumby.display\n    display.fill(0)\n    screen = state['screen_state']\n    status = state['save_status']\n    if screen == 'battle':\n        display.drawText('HP:'+str(state['HP']), 0, 0, 1)\n        money = state['money']\n        shown = str(money) if money < 1000 else str(min(999, money//1000))+'k'\n        display.drawText('$'+shown, 72-6*(len(shown)+1), 0, 1)\n        camera = max(0, min(72, state['player_x']-32))\n        positions = [state['player_x']]\n        if state['active_enemy']:\n            positions.append(state['enemy_x'])\n        for world_x in positions:\n            x = world_x-camera\n            left = max(0, x)\n            right = min(72, x+8)\n            if right > left:\n                display.drawFilledRectangle(left, 32, right-left, 8, 1)\n    elif screen in ('shop_detail', 'equip_detail'):\n        item = state['menu_selection']\n        names = ('Blade', 'Sword', 'Vest', 'Armor')\n        prices = (40, 80, 40, 80)\n        display.drawText(names[item], 0, 0, 1)\n        display.drawText('P:'+str(prices[item]), 0, 8, 1)\n        money = str(state['money'])\n        display.drawText(money[:12], 0, 16, 1)\n        if len(money) > 12:\n            display.drawText(money[12:], 0, 24, 1)\n        owned = 'Y' if state['owned'][item] else 'N'\n        equipped = item in (state['equipped_weapon'], state['equipped_armor'])\n        display.drawText('O:'+owned+' E:'+('Y' if equipped else 'N'), 0, 32, 1)\n    elif screen == 'defeat':\n        display.drawText('DEFEAT', 0, 0, 1)\n        display.drawText('A:RETRY', 0, 20, 1)\n    else:\n        if screen == 'safe':\n            choices = ('NEXT', 'SHOP', 'EQUIP', 'SAVE')\n        elif screen == 'pause':\n            choices = ('RESUME', 'SAVE')\n        else:\n            choices = ('Blade', 'Sword', 'Vest', 'Armor')\n        display.drawText(status if status in ('SAVED','SAVE ERR') else screen.upper(), 0, 0, 1)\n        start = state['menu_scroll']\n        for row in range(3):\n            index = start+row\n            if index < len(choices):\n                selected = '>' if index == state['menu_selection'] else ' '\n                display.drawText(selected+choices[index], 0, 10+row*10, 1)\n    if status in ('SAVED', 'SAVE ERR') and screen in ('battle','shop_detail','equip_detail','defeat'):\n        display.drawText(status, 0, 0, 1)\n    display.update()\n\n\ndef handle_inputs():\n    return {\n        'L': bool(thumby.buttonL.pressed()),\n        'R': bool(thumby.buttonR.pressed()),\n        'A': bool(thumby.buttonA.justPressed()),\n        'B': bool(thumby.buttonB.justPressed()),\n        'U': bool(thumby.buttonU.justPressed()),\n        'D': bool(thumby.buttonD.justPressed()),\n    }\n\n\ndef load_save_data():\n    initial = {\n        'version': 1, 'money': 0, 'progress': 0, 'owned': [False]*4,\n        'equipped_weapon': None, 'equipped_armor': None,\n    }\n    try:\n        thumby.saveData.setName('ThumbyGrowth')\n        if not thumby.saveData.hasItem('state'):\n            return decode_save_data(initial)\n        raw = thumby.saveData.getItem('state')\n        restored = decode_save_data(json.loads(raw))\n        if restored is not None:\n            return restored\n    except Exception:\n        pass\n    thumby.display.fill(0)\n    thumby.display.drawText('LOAD ERR', 0, 0, 1)\n    thumby.display.update()\n    if sys.implementation.name == 'micropython':\n        time.sleep(1)\n    return decode_save_data(initial)\n\n\ndef save_game(state):\n    try:\n        data = json.dumps(encode_save_data(state))\n        thumby.saveData.setName('ThumbyGrowth')\n        thumby.saveData.setItem('state', data)\n        thumby.saveData.save()\n        return 'SAVED'\n    except Exception:\n        return 'SAVE ERR'\n\n\nif sys.implementation.name == 'micropython':\n    main_loop()\n", 'test_rules_review.py': "import unittest\nfrom copy import deepcopy\nfrom itertools import product\nfrom rules import update_state\nfrom test_rules import state, inputs, battle\n\nclass ReviewBoundaries(unittest.TestCase):\n    def test_r_does_not_confirm_safe_or_pause(self):\n        for screen,selection in product(('safe','pause'),(0,1)):\n            result=update_state(state(screen_state=screen,menu_selection=selection),inputs(R=True))\n            self.assertEqual(result['screen_state'],screen)\n            self.assertFalse(result['save_requested'])\n\n    def test_save_is_a_pulse_on_every_screen(self):\n        for screen in ('safe','battle','pause','shop','equip','shop_detail','equip_detail','defeat'):\n            result=update_state(state(screen_state=screen,save_requested=True),inputs(B=True))\n            self.assertFalse(result['save_requested'])\n            self.assertFalse(result['menu_r_held'])\n\n    def test_detail_preserves_selection_without_owned(self):\n        for screen in ('shop','equip'):\n            original=state(screen_state=screen,menu_selection=3,menu_scroll=1)\n            result=update_state(original,inputs(R=True))\n            self.assertEqual(result['screen_state'],screen+'_detail')\n            self.assertEqual((result['menu_selection'],result['menu_scroll']),(3,1))\n            detailed=update_state(result,inputs(U=True,D=True,L=True,R=True))\n            self.assertEqual(detailed,result)\n\n    def test_retry_recalculates_equipment(self):\n        result=update_state(state(screen_state='defeat',HP=0,attack=99,defense=99,\n            owned=[False,True,False,True],equipped_weapon=1,equipped_armor=3,progress=1),inputs(A=True))\n        self.assertEqual((result['attack'],result['defense'],result['HP'],result['combat_frame']),(6,2,10,0))\n\n    def test_pause_limits_and_resume_time(self):\n        original=battle(screen_state='pause',combat_frame=5,player_attack_cooldown=7,enemy_attack_cooldown=8)\n        held=update_state(original,inputs(U=True,D=True))\n        self.assertEqual(held,original)\n        resumed=update_state(original,inputs(A=True))\n        self.assertEqual(resumed['screen_state'],'battle')\n        self.assertEqual((resumed['combat_frame'],resumed['player_attack_cooldown'],resumed['enemy_attack_cooldown']),(5,7,8))\n        end=update_state(state(screen_state='pause',menu_selection=1),inputs(D=True))\n        self.assertEqual((end['menu_selection'],end['menu_scroll']),(1,0))\n\n    def test_b_priority_prevents_purchase(self):\n        original=state(screen_state='shop_detail',money=80,menu_selection=1)\n        result=update_state(original,inputs(A=True,B=True,R=True))\n        self.assertEqual((result['screen_state'],result['money'],result['owned']),('shop',80,[False]*4))\n        self.assertTrue(result['menu_r_held'])\n\n    def test_even_enemy_motion_changes_attack_range_before_hit(self):\n        original=battle(enemy_x=33,combat_frame=1)\n        result=update_state(original,inputs(A=True))\n        self.assertEqual((result['enemy_x'],result['enemy_hp'],result['combat_frame']),(32,4,2))\n        result=update_state(battle(player_x=33,enemy_x=16,combat_frame=1,direction='L'),inputs(A=True))\n        self.assertEqual((result['enemy_x'],result['enemy_hp']),(17,4))\n\n    def test_valid_battle_positions_never_overlap_or_mutate(self):\n        positions=(0,8,16,64,128,136)\n        for player,enemy in product(positions,positions):\n            if abs(player-enemy)<8: continue\n            for frame in (0,1):\n                for l,r,a,b in product((False,True),repeat=4):\n                    original=battle(player_x=player,enemy_x=enemy,combat_frame=frame,enemy_hp=10)\n                    before=deepcopy(original)\n                    result=update_state(original,inputs(L=l,R=r,A=a,B=b))\n                    self.assertEqual(original,before)\n                    self.assertIsNot(result['owned'],original['owned'])\n                    self.assertTrue(0<=result['player_x']<=136)\n                    self.assertTrue(0<=result['enemy_x']<=136)\n                    self.assertGreaterEqual(abs(result['player_x']-result['enemy_x']),8)\n", 'test_adapter_review.py': "import unittest\nfrom copy import deepcopy\nfrom unittest.mock import patch\nimport test_ThumbyGrowth as fixtures\nimport ThumbyGrowth\n\nclass AdapterReview(fixtures.TestAdapter):\n    # 상속된 고정 테스트를 다시 세지 않도록 별도 suite에서 이 메서드만 선택한다.\n    def test_end_to_end_purchase_equip_save_load(self):\n        memory={}\n        device=fixtures.fake_thumby\n        device.saveData.setItem.side_effect=lambda key,value: memory.__setitem__(key,deepcopy(value))\n        device.saveData.hasItem.side_effect=lambda key:key in memory\n        device.saveData.getItem.side_effect=lambda key:deepcopy(memory[key])\n        state=fixtures.state(money=40)\n        for keys in (fixtures.inputs(D=True),fixtures.inputs(A=True),fixtures.inputs(A=True),\n                     fixtures.inputs(B=True),fixtures.inputs(D=True),fixtures.inputs(D=True),\n                     fixtures.inputs(A=True),fixtures.inputs(A=True),fixtures.inputs(B=True),\n                     fixtures.inputs(D=True),fixtures.inputs(D=True),fixtures.inputs(D=True),\n                     fixtures.inputs(A=True)):\n            with patch.object(ThumbyGrowth,'handle_inputs',return_value=keys):\n                state=ThumbyGrowth.step_frame(state)\n        self.assertEqual((state['money'],state['attack'],state['equipped_weapon'],state['save_status']),(0,4,0,'SAVED'))\n        self.assertEqual(device.saveData.save.call_count,1)\n        restored=ThumbyGrowth.load_save_data()\n        self.assertEqual((restored['money'],restored['attack'],restored['equipped_weapon'],restored['HP']),(0,4,0,10))\n\n    def test_render_ownership_and_equipped_are_visible(self):\n        device=fixtures.fake_thumby\n        renders=[]\n        for owned,equipped in ((False,None),(True,None),(True,0)):\n            device.display.reset_mock()\n            ThumbyGrowth.draw_game(fixtures.state(screen_state='equip_detail',owned=[owned,False,False,False],equipped_weapon=equipped))\n            renders.append(tuple(self.texts()))\n        self.assertNotEqual(renders[0],renders[1])\n        self.assertNotEqual(renders[1],renders[2])\n\n    def test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep(self):\n        device=fixtures.fake_thumby\n        ThumbyGrowth.draw_game(fixtures.state(screen_state='battle',active_enemy=True,player_x=16,enemy_x=112))\n        calls=device.display.drawFilledRectangle.call_args_list\n        self.assertEqual(len(calls),1)\n        self.assertEqual(calls[0].args[:4],(16,32,8,8))\n        device.saveData.hasItem.return_value=True\n        device.saveData.getItem.side_effect=OSError('읽기 오류')\n        with patch.object(ThumbyGrowth.time,'sleep') as sleep:\n            result=ThumbyGrowth.load_save_data()\n        self.assertEqual(result['screen_state'],'safe')\n        self.assertEqual(sleep.call_count,0)\n\nif __name__=='__main__':\n    suite=unittest.TestSuite(AdapterReview(name) for name in (\n        'test_end_to_end_purchase_equip_save_load',\n        'test_render_ownership_and_equipped_are_visible',\n        'test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep'))\n    runner=unittest.TextTestRunner(verbosity=2)\n    raise SystemExit(not runner.run(suite).wasSuccessful())\n"}

BASE = Path('/Users/parkjihoon/workspace/thumby-rpg-first-20261008/ai/personal-game-ai')
OLD_TESTS_SHA = '23ea8a184a374aa7f1cc62300e0025124c828ea66b79b0af7061d1825a11c8d6'
NEW_TESTS_SHA = 'cdb15101d9a25c4bed8c8ffc0036dd6deb5966cbeaeb4fcc02222ee8a0fc1629'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    if path.is_symlink():
        raise RuntimeError('심볼릭 링크에 쓰지 않습니다: '+str(path))
    if path.exists():
        if not path.is_file() or path.read_bytes() != data:
            raise RuntimeError('같은 이름의 다른 파일을 덮어쓰지 않습니다: '+str(path))
        return
    with path.open('xb') as stream:
        stream.write(data)


def main():
    if not BASE.is_dir():
        raise SystemExit('작업 폴더가 없어 중단합니다.')
    os.chdir(str(BASE))
    sys.path.insert(0,str(BASE))
    import create_loop
    import design_plan
    import edit_loop
    import generation_profile
    import implementation_link
    import test_plan

    def git(*args):
        return subprocess.check_output(['git']+list(args),text=True).strip()
    if git('branch','--show-current') != 'work/thumby-rpg-first-20261008':
        raise SystemExit('작업 브랜치가 달라 중단합니다.')
    if git('diff','--cached','--name-only'):
        raise SystemExit('이미 스테이징한 파일이 있어 중단합니다.')
    old_manifest = BASE/'outputs/test_plan_20261012_083518_807142/tests.json'
    envelope,original_tests,snapshot = implementation_link.read_confirmed(old_manifest,OLD_TESTS_SHA)
    if sha((BASE/'outputs/design_20261011_232344_146552/design.json').read_bytes()) != 'bd989e114e8f469dd092ae97417bb4bee8005dfe95d5c3ff3523f932767774e2':
        raise SystemExit('승인 설계가 달라 중단합니다.')
    root = Path(git('rev-parse','--show-toplevel'))
    directory = design_plan.directory_for('game')
    if directory.resolve() != (root/'micropython/ThumbyGrowth').resolve():
        raise SystemExit('게임 대상 경로가 달라 중단합니다.')
    source = BASE/'outputs/create_20261012_094540_590078/merged_1.py'
    if source.is_symlink() or sha(source.read_bytes()) != 'bd840fb348571ec7c758aae7a017db62f41374429c22be404b8a0487bf4b2168':
        raise SystemExit('검토한 Mac 원본 코드가 달라 중단합니다.')
    original_functions = {n.name:ast.get_source_segment(source.read_text(encoding='utf-8'),n) for n in ast.parse(source.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
    fixed_functions = {n.name:ast.get_source_segment(PAYLOAD['rules.py'],n) for n in ast.parse(PAYLOAD['rules.py']).body if isinstance(n,ast.FunctionDef)}
    if set(original_functions) != set(fixed_functions) or [name for name in original_functions if original_functions[name]!=fixed_functions[name]] != ['update_state']:
        raise SystemExit('규칙 수정 범위가 update_state 하나가 아니어서 중단합니다.')
    for item in original_tests['files']:
        path=directory/item['filename']
        if path.is_symlink() or path.read_bytes()!=item['code'].encode('utf-8'):
            raise SystemExit('현재 고정 테스트가 검토한 버전과 달라 중단합니다.')
        edit_loop.check_git_files(path,path)

    for name in ('rules.py','ThumbyGrowth.py'):
        compile(PAYLOAD[name],name,'exec')
        generation_profile.validate_code('game',PAYLOAD[name],name)
        create_loop.prepare_create('game/'+name,'승인 계약에 맞춰 검토자가 작성하고 CPython으로 검증한 코드 적용.','test_'+Path(name).stem)
    qa=directory/'tools/qa'
    if qa.is_symlink() or (qa.exists() and not qa.is_dir()):
        raise SystemExit('추가 검사 폴더가 달라 중단합니다.')
    for name in ('test_rules_review.py','test_adapter_review.py'):
        p=qa/name
        if p.is_symlink() or (p.exists() and (not p.is_file() or p.read_text(encoding='utf-8')!=PAYLOAD[name])):
            raise SystemExit('추가 검사 파일이 이미 다르게 존재해 중단합니다.')

    # 고정 테스트의 검증 조건은 그대로 두고 일관된 초기 스크롤만 수정한다.
    corrected=json.loads(json.dumps(original_tests,ensure_ascii=False))
    adapter_test=next(item for item in corrected['files'] if item['id']=='002')
    before="original = state(money=55,screen_state='safe',menu_selection=3)"
    after="original = state(money=55,screen_state='safe',menu_selection=3,menu_scroll=1)"
    if adapter_test['code'].count(before)!=1:
        raise SystemExit('테스트 초기 조건 수정 위치를 확인하지 못했습니다.')
    old_code=adapter_test['code'].encode('utf-8')
    adapter_test['code']=adapter_test['code'].replace(before,after,1)
    new_code=adapter_test['code'].encode('utf-8')
    test_plan.validate_candidate(corrected,envelope['design'])
    print('저장 실패 테스트의 초기 스크롤만 0→1로 수정합니다. 모든 assertion은 유지합니다.',flush=True)
    new_manifest=test_plan.generate_tests(BASE/'outputs/design_20261011_232344_146552/design.json',model=lambda prompt:json.dumps(corrected,ensure_ascii=False))
    if sha(new_manifest.read_bytes())!=NEW_TESTS_SHA:
        raise SystemExit('새 테스트 후보 SHA가 예상과 달라 적용 전에 중단합니다.')
    test_plan.confirm_tests(new_manifest,NEW_TESTS_SHA)
    lock=edit_loop.BASE_DIR/'.edit_loop.lock'
    with lock.open('x'):
        pass
    test_path=directory/adapter_test['filename']
    try:
        implementation_link.read_confirmed(old_manifest,OLD_TESTS_SHA)
        descriptor=os.open(str(test_path),os.O_RDWR|os.O_NOFOLLOW)
        with os.fdopen(descriptor,'r+b') as stream:
            if stream.read()!=old_code:
                raise RuntimeError('고정 테스트가 외부에서 변경돼 중단합니다.')
            stream.seek(0);stream.write(new_code);stream.truncate();stream.flush()
    finally:
        lock.unlink()
    relative=test_path.relative_to(root).as_posix()
    subprocess.run(['git','-C',str(root),'diff','--check','--',relative],check=True)
    subprocess.run(['git','-C',str(root),'add','--',relative],check=True)
    subprocess.run(['git','-C',str(root),'commit','--only','-m','ThumbyGrowth 저장 실패 테스트 초기 스크롤 수정','--',relative],check=True)
    print('테스트 수정 커밋:',git('rev-parse','HEAD'),flush=True)
    print('새 테스트 확정 기록:',new_manifest,flush=True)
    implementation_link.read_confirmed(new_manifest,NEW_TESTS_SHA)
    qa.mkdir(parents=True,exist_ok=True)
    for name in ('test_rules_review.py','test_adapter_review.py'):
        write_new(qa/name,PAYLOAD[name].encode('utf-8'))

    context=edit_loop.read_context()
    record_paths=(new_manifest,new_manifest.with_name('confirmation.json'),BASE/'outputs/design_20261011_232344_146552/design.json',BASE/'outputs/design_20261011_232344_146552/approval.json')
    records={p:p.read_bytes() for p in record_paths}
    result_history=[]
    dependency=None
    def check():
        for p,data in records.items():
            if p.is_symlink() or p.read_bytes()!=data:
                raise RuntimeError('승인 기록이 변경됐습니다.')
        if edit_loop.read_context()!=context:
            raise RuntimeError('작업 문맥이 변경됐습니다.')
        for item in corrected['files']:
            p=directory/item['filename']
            if p.is_symlink() or p.read_bytes()!=item['code'].encode('utf-8'):
                raise RuntimeError('고정 테스트가 변경됐습니다.')
            edit_loop.check_git_files(p,p)
        if dependency is not None and (directory/'rules.py').read_bytes()!=dependency:
            raise RuntimeError('검증한 선행 코드가 변경됐습니다.')
    attempts=edit_loop.MAX_ATTEMPTS
    try:
        edit_loop.MAX_ATTEMPTS=1
        for name in ('rules.py','ThumbyGrowth.py'):
            check()
            code=PAYLOAD[name]
            def reviewed_model(prompt,code=code):
                check()
                return json.dumps({'action':'create','code':code},ensure_ascii=False)
            print('\n검증 코드 적용:',name,'Ollama 호출 없음',flush=True)
            result=create_loop.run_create('game/'+name,'승인된 설계에 맞춰 ChatGPT가 검토·수정하고 CPython으로 검증한 코드 적용.','test_'+Path(name).stem,model=reviewed_model)
            result_history.append(result)
            print('결과:',json.dumps(result,ensure_ascii=False),flush=True)
            if result.get('status')!='tests_passed':
                raise SystemExit('Mac 고정 테스트가 실패하여 다음 적용을 중단합니다.')
            if name=='rules.py': dependency=(directory/'rules.py').read_bytes()
    finally:
        edit_loop.MAX_ATTEMPTS=attempts
    check()
    test_names=['test_rules','test_ThumbyGrowth','test_rules_review',
        'test_adapter_review.AdapterReview.test_end_to_end_purchase_equip_save_load',
        'test_adapter_review.AdapterReview.test_render_ownership_and_equipped_are_visible',
        'test_adapter_review.AdapterReview.test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep']
    runner='import sys,unittest; sys.path[:0]='+repr([str(directory),str(qa)])+'; unittest.main(module=None,argv='+repr(['검증']+test_names+['-v'])+')'
    result=subprocess.run([sys.executable,'-B','-c',runner],cwd=str(directory),capture_output=True,text=True,timeout=60)
    log=new_manifest.parent/'mac_verification.txt'
    write_new(log,(result.stdout+'\n'+result.stderr).encode('utf-8'))
    print(result.stdout+result.stderr,flush=True)
    if result.returncode:
        raise SystemExit('추가 통합 검증이 실패했습니다. 코드와 기록을 보존합니다.')
    for name in ('rules.py','ThumbyGrowth.py'):
        if (directory/name).read_bytes()!=PAYLOAD[name].encode('utf-8'):
            raise RuntimeError('Mac 검증 중 게임 코드가 변경됐습니다.')
    check()
    with (new_manifest.parent/'code_review.json').open('x',encoding='utf-8') as stream:
        json.dump({'origin':'Mac Ollama 원본의 update_state를 ChatGPT가 수정, 기기 어댑터는 ChatGPT가 직접 작성',
            'original_source_sha256':'bd840fb348571ec7c758aae7a017db62f41374429c22be404b8a0487bf4b2168',
            'tests_sha256':NEW_TESTS_SHA,'host_tests':'CPython 고정26개+추가11개 통과',
            'mac_tests':'같은37개 통과','create_results':result_history,
            'code_sha256':{name:sha((directory/name).read_bytes()) for name in ('rules.py','ThumbyGrowth.py')},
            'unverified':['실기 FPS·메모리·가독성·조작성·저장 실패·전원중단 안전성','매우 긴 돈의 상세 화면 표시'],
            'experience_reuse':'실패·수정·검증 기록은 보존했지만 자동 검색·재사용은 미구현'},stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print('\nMac에서37개 검사 통과. 다음은 코드 최종 검토와 실기 확인입니다.',flush=True)
    print('게임 코드 commit·push·main 머지는 하지 않았습니다.',flush=True)
    print('검증 기록:',log,flush=True)
    print(git('status','--short'),flush=True)

if __name__=='__main__':
    main()
