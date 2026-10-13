"""구매·장착 화면 개선 및 버튼부터 저장까지 통합 검증. Ollama 호출 없음."""
from pathlib import Path
from datetime import datetime
import ast
import hashlib
import json
import os
import subprocess
import sys
BASE=Path(__file__).resolve().parents[4] / "ai" / "personal-game-ai"
RENDERER="def draw_game(state):\n    display = thumby.display\n    display.fill(0)\n    screen = state['screen_state']\n    status = state['save_status']\n    if screen == 'battle':\n        display.drawText('HP:'+str(state['HP']), 0, 0, 1)\n        money = state['money']\n        shown = str(money) if money < 1000 else str(min(999, money//1000))+'k'\n        display.drawText('$'+shown, 72-6*(len(shown)+1), 0, 1)\n        display.drawText('E:'+str(state['enemy_hp']), 0, 8, 1)\n        facing = '>' if state['direction'] == 'R' else '<'\n        display.drawText('P'+facing, 0, 18, 1)\n        gap = max(state['player_x'], state['enemy_x'])-min(state['player_x'], state['enemy_x'])-8\n        ahead = ((state['direction']=='R' and state['enemy_x']>state['player_x'])\n                 or (state['direction']=='L' and state['enemy_x']<state['player_x']))\n        hint = 'TURN' if not ahead else ('CLOSE' if gap<=2 else ('RANGE' if gap<=8 else 'FAR'))\n        display.drawText(hint, 36, 8, 1)\n        camera = max(0, min(72, state['player_x']-32))\n        positions = [state['player_x']]\n        if state['active_enemy']:\n            positions.append(state['enemy_x'])\n        for world_x in positions:\n            x = world_x-camera\n            left = max(0, x)\n            right = min(72, x+8)\n            if right > left:\n                display.drawFilledRectangle(left, 32, right-left, 8, 1)\n                if 0 <= x <= 64:\n                    marker = facing if world_x == state['player_x'] else 'X'\n                    flashing = (world_x == state['player_x'] and state['enemy_attack_cooldown'] >= 115\n                                and state['combat_frame'] % 2 == 0)\n                    display.drawText(marker, x+1, 32, 1 if flashing else 0)\n        if state['player_attack_cooldown'] >= 7:\n            attack_x = state['player_x']-camera+(8 if state['direction']=='R' else -6)\n            if 0 <= attack_x <= 66:\n                display.drawText('-', attack_x, 32, 1)\n    elif screen in ('shop_detail', 'equip_detail'):\n        item = state['menu_selection']\n        names = ('Blade', 'Sword', 'Vest', 'Armor')\n        prices = (40, 80, 40, 80)\n        display.drawText(names[item], 0, 0, 1)\n        display.drawText('P:'+str(prices[item]), 0, 8, 1)\n        effect = ('ATK+2','ATK+4','DEF+1','DEF+2')[item]\n        display.drawText(effect, 36, 8, 1)\n        money = str(state['money'])\n        display.drawText(money[:12], 0, 16, 1)\n        if len(money) > 12:\n            display.drawText(money[12:], 0, 24, 1)\n        owned = 'Y' if state['owned'][item] else 'N'\n        equipped = item in (state['equipped_weapon'], state['equipped_armor'])\n        if len(money) <= 12:\n            if screen == 'shop_detail':\n                action = 'OWNED' if state['owned'][item] else ('A:BUY' if state['money']>=prices[item] else 'NO MONEY')\n            else:\n                action = 'BUY FIRST' if not state['owned'][item] else ('A:REMOVE' if equipped else 'A:EQUIP')\n            display.drawText(action, 0, 24, 1)\n        display.drawText('O:'+owned+' E:'+('Y' if equipped else 'N'), 0, 32, 1)\n    elif screen == 'defeat':\n        display.drawText('DEFEAT', 0, 0, 1)\n        display.drawText('A:RETRY', 0, 20, 1)\n    else:\n        if screen == 'safe':\n            choices = ('NEXT', 'SHOP', 'EQUIP', 'SAVE')\n        elif screen == 'pause':\n            choices = ('RESUME', 'SAVE')\n        else:\n            choices = ('Blade', 'Sword', 'Vest', 'Armor')\n        header = screen.upper()\n        if screen in ('shop','equip'):\n            chosen = state['menu_selection']\n            if screen == 'shop':\n                header = 'BOUGHT' if state['owned'][chosen] else ('A:BUY' if state['money'] >= (40,80,40,80)[chosen] else 'NO MONEY')\n            else:\n                on = chosen in (state['equipped_weapon'],state['equipped_armor'])\n                header = 'BUY FIRST' if not state['owned'][chosen] else ('ON ATK'+str(state['attack']) if on and chosen<2 else ('ON DEF'+str(state['defense']) if on else 'A:EQUIP'))\n        if status in ('SAVED','SAVE ERR'):\n            header = status\n        display.drawText(header, 0, 0, 1)\n        cash = str(state['money']) if state['money']<1000 else str(min(999,state['money']//1000))+'k'\n        if len(header)+len(cash)+1 <= 12:\n            display.drawText('$'+cash, 72-6*(len(cash)+1), 0, 1)\n        start = state['menu_scroll']\n        for row in range(3):\n            index = start+row\n            if index < len(choices):\n                selected = '>' if index == state['menu_selection'] else ' '\n                label = selected+choices[index]\n                if screen in ('shop','equip') and state['owned'][index]:\n                    label += '+'\n                display.drawText(label, 0, 10+row*10, 1)\n                if screen == 'shop':\n                    display.drawText(str((40,80,40,80)[index]), 54, 10+row*10, 1)\n                elif screen == 'equip':\n                    on = index in (state['equipped_weapon'],state['equipped_armor'])\n                    display.drawText('ON' if on else ('OK' if state['owned'][index] else '--'), 54, 10+row*10, 1)\n    if status in ('SAVED', 'SAVE ERR') and screen in ('battle','shop_detail','equip_detail','defeat'):\n        display.drawText(status, 0, 0, 1)\n    display.update()"
QA="import unittest\nimport json\nimport test_ThumbyGrowth as fixtures\nimport ThumbyGrowth\n\nclass ShopEquipmentUI(unittest.TestCase):\n    def setUp(self):\n        fixtures.TestAdapter().setUp()\n        ThumbyGrowth.thumby = fixtures.fake_thumby\n\n    def frame(self, current, **keys):\n        device = fixtures.fake_thumby\n        for name in ('L','R','A','B','U','D'):\n            button = getattr(device,'button'+name)\n            button.pressed.return_value = bool(keys.get(name,False))\n            button.justPressed.return_value = bool(keys.get(name,False))\n        device.display.reset_mock()\n        return ThumbyGrowth.step_frame(current)\n\n    def texts(self):\n        return ' '.join(str(c.args[0]) for c in fixtures.fake_thumby.display.drawText.call_args_list)\n\n    def buy_and_equip(self):\n        current = fixtures.state(money=50)\n        current = self.frame(current,D=True)\n        current = self.frame(current,A=True)\n        self.assertEqual(current['screen_state'],'shop')\n        self.assertIn('$50',self.texts())\n        current = self.frame(current,A=True)\n        self.assertEqual((current['money'],current['owned'],current['equipped_weapon']), (10,[True,False,False,False],None))\n        self.assertIn('BOUGHT',self.texts())\n        self.assertIn('$10',self.texts())\n        current = self.frame(current,B=True)\n        current = self.frame(current,D=True)\n        current = self.frame(current,D=True)\n        current = self.frame(current,A=True)\n        self.assertEqual(current['screen_state'],'equip')\n        current = self.frame(current,A=True)\n        self.assertEqual((current['equipped_weapon'],current['attack']), (0,4))\n        self.assertIn('ON',self.texts())\n        self.assertIn('ON ATK4',self.texts())\n        return current\n\n    def test_menu_buttons_purchase_and_equipment(self):\n        current = self.buy_and_equip()\n        self.assertEqual((current['money'],current['attack']), (10,4))\n\n    def test_insufficient_money_is_visible_and_does_not_charge(self):\n        original = fixtures.state(screen_state='shop',money=20)\n        current = self.frame(original,A=True)\n        self.assertEqual((current['money'],current['owned']), (20,[False]*4))\n        self.assertIn('NO MONEY',self.texts())\n        self.assertIn('$20',self.texts())\n        current = self.frame(current,R=True)\n        self.assertEqual(current['screen_state'],'shop_detail')\n        self.assertIn('NO MONEY',self.texts())\n\n    def test_unowned_equipment_tells_player_to_buy(self):\n        current = self.frame(fixtures.state(screen_state='equip'),A=True)\n        self.assertIsNone(current['equipped_weapon'])\n        self.assertIn('BUY FIRST',self.texts())\n        current = self.frame(current,R=True)\n        self.assertIn('BUY FIRST',self.texts())\n\n    def test_duplicate_purchase_is_visible_and_free(self):\n        current = self.frame(fixtures.state(screen_state='shop',money=50,owned=[True,False,False,False]),A=True)\n        self.assertEqual(current['money'],50)\n        self.assertIn('BOUGHT',self.texts())\n        self.assertIn('Blade+',self.texts())\n\n    def test_equipment_toggle_is_visible_and_recalculates_stats(self):\n        current = self.buy_and_equip()\n        current = self.frame(current)\n        current = self.frame(current,A=True)\n        self.assertEqual((current['equipped_weapon'],current['attack']), (None,2))\n        self.assertIn('A:EQUIP',self.texts())\n        self.assertNotIn('ON ATK',self.texts())\n\n    def test_detail_shows_price_effect_and_available_action(self):\n        for item, price, effect in ((0,40,'ATK+2'),(1,80,'ATK+4'),(2,40,'DEF+1'),(3,80,'DEF+2')):\n            fixtures.fake_thumby.display.reset_mock()\n            ThumbyGrowth.draw_game(fixtures.state(screen_state='shop_detail',menu_selection=item,money=80))\n            shown=self.texts()\n            self.assertIn('P:'+str(price),shown)\n            self.assertIn(effect,shown)\n            self.assertIn('A:BUY',shown)\n\n    def test_menu_purchase_equipment_save_and_reload(self):\n        memory={}\n        device=fixtures.fake_thumby\n        device.saveData.setItem.side_effect=lambda key,value:memory.__setitem__(key,value)\n        device.saveData.hasItem.side_effect=lambda key:key in memory\n        device.saveData.getItem.side_effect=lambda key:memory[key]\n        current=self.buy_and_equip()\n        current=self.frame(current,B=True)\n        for _ in range(3):current=self.frame(current,D=True)\n        current=self.frame(current,A=True)\n        self.assertEqual(current['save_status'],'SAVED')\n        self.assertIn('SAVED',self.texts())\n        self.assertEqual(device.saveData.save.call_count,1)\n        restored=ThumbyGrowth.load_save_data()\n        self.assertEqual((restored['money'],restored['equipped_weapon'],restored['attack']), (10,0,4))\n        self.assertEqual(json.loads(memory['state'])['owned'],[True,False,False,False])\n"
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    os.chdir(str(BASE));sys.path.insert(0,str(BASE))
    def git(*args):return subprocess.check_output(['git']+list(args),text=True).strip()
    if git('branch','--show-current')!=json.loads((BASE / "target.json").read_text(encoding="utf-8"))["expected_branch"]:
        raise SystemExit('작업 브랜치가 달라 중단합니다.')
    root=Path(git('rev-parse','--show-toplevel'))
    game=root/'micropython/Thumby/ThumbyGrowth'
    path=game/'ThumbyGrowth.py'
    if path.is_symlink():raise SystemExit('화면 코드가 심볼릭 링크입니다.')
    original=path.read_bytes()
    if sha(original) not in {'976f8929743d7b3be268eff116c05f36a19c6bd78e883cf1ceaa1529e875147f','ef3934050b141effacf9688af7e81cc169e63852dd5e078800d1d92d1a02285a'}:
        raise SystemExit('검토한 화면 버전과 달라 덮어쓰지 않습니다.')
    rules=game/'rules.py';test=game/'test_rules.py'
    pair=(sha(rules.read_bytes()),sha(test.read_bytes()))
    pairs={('f37f8ace8f698adc036f8f8eb042b7d81c48c23a5f5db26dc74604a535c6c045','06f47ebe7b660509a11c693792c545d9612381bc69d02fe2c115da2b9f1346e6'),
        ('16da55b7761d58ddce7bd5a5f7645857d1abdb91da3e42190ab5ffc01cbd07d6','20f6f77586fb9debf4a79bc6750f728ff4a1ff6c95db4871b852f7e962f6ec53')}
    if pair not in pairs:raise SystemExit('규칙과 고정 테스트가 검토한 버전과 다릅니다.')
    protected_paths=[rules,test,game/'test_ThumbyGrowth.py',game/'tools/qa/test_rules_review.py',game/'tools/qa/test_adapter_review.py',game/'tools/qa/test_combat_playthrough.py',root/'docs/personal-game-ai/THUMBY_GROWTH_FIRST.md']
    protected={p:p.read_bytes() for p in protected_paths}
    for p in protected:
        if p.is_symlink():raise SystemExit('보존 경로에 심볼릭 링크가 있습니다.')
    qa=game/'tools/qa/test_shop_equipment_ui.py'
    if qa.is_symlink() or (qa.exists() and (not qa.is_file() or qa.read_text(encoding='utf-8')!=QA)):
        raise SystemExit('동일한 추가 검사 파일이 다르게 존재합니다.')
    source=original.decode('utf-8');tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='draw_game')
    lines=source.splitlines(keepends=True)
    replacement=RENDERER
    if pair[0]=='f37f8ace8f698adc036f8f8eb042b7d81c48c23a5f5db26dc74604a535c6c045':
        replacement=replacement.replace("state['enemy_attack_cooldown'] >= 115","state['enemy_attack_cooldown'] >= 55")
    updated=''.join(lines[:node.lineno-1])+replacement+'\n'+''.join(lines[node.end_lineno:])
    compile(updated,str(path),'exec')
    old={n.name:ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
    new={n.name:ast.get_source_segment(updated,n) for n in ast.parse(updated).body if isinstance(n,ast.FunctionDef)}
    if set(old)!=set(new) or [k for k in old if old[k]!=new[k]]!=['draw_game']:
        raise SystemExit('그리기 함수 외 변경이 있어 중단합니다.')
    lock=BASE/'.edit_loop.lock'
    with lock.open('x'):pass
    try:
        folder=BASE/'outputs'/('shop_equipment_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        folder.mkdir()
        (folder/'before.py.txt').write_bytes(original)
        (folder/'after.py.txt').write_text(updated,encoding='utf-8')
        descriptor=os.open(str(path),os.O_RDWR|os.O_NOFOLLOW)
        with os.fdopen(descriptor,'r+b') as stream:
            if stream.read()!=original:raise RuntimeError('작업 중 코드가 변경됐습니다.')
            stream.seek(0);stream.write(updated.encode('utf-8'));stream.truncate();stream.flush()
        if not qa.exists():
            with qa.open('x',encoding='utf-8') as stream:stream.write(QA)
        names=['test_rules','test_ThumbyGrowth','test_rules_review','test_combat_playthrough','test_shop_equipment_ui',
            'test_adapter_review.AdapterReview.test_end_to_end_purchase_equip_save_load',
            'test_adapter_review.AdapterReview.test_render_ownership_and_equipped_are_visible',
            'test_adapter_review.AdapterReview.test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep']
        runner="import sys,unittest,json;sys.path[:0]="+repr([str(game),str(qa.parent)])+";suite=unittest.defaultTestLoader.loadTestsFromNames("+repr(names)+");result=unittest.TextTestRunner(verbosity=2).run(suite);print(json.dumps({'tests_run':result.testsRun,'passed':result.wasSuccessful()}));sys.exit(0 if result.wasSuccessful() else 1)"
        result=subprocess.run([sys.executable,'-B','-c',runner],cwd=str(game),capture_output=True,text=True,timeout=60)
        output=result.stdout+result.stderr
        (folder/'verification.txt').write_text(output,encoding='utf-8');print(output,flush=True)
        for p,data in protected.items():
            if p.is_symlink() or p.read_bytes()!=data:raise RuntimeError('보존 대상이 변경됐습니다.')
        if path.read_bytes()!=updated.encode('utf-8'):raise RuntimeError('검사 중 화면 코드가 변경됐습니다.')
        summary=json.loads(result.stdout.strip().splitlines()[-1])
        record={'origin':'ChatGPT 구매·장착 화면 개선','source_ui_sha256':sha(original),'code_sha256':sha(path.read_bytes()),
            'rules_sha256':pair[0],'verification':summary,'new_tests':7,
            'changed':'draw_game만 수정. 구매·장착·전투·저장 규칙과 기존 검사 유지',
            'features':['소지금·가격·효과·소유·장착 표시','돈부족·미소유 장비 안내','구매 후 BOUGHT, 장착 후 ON 표시'],
            'unverified':['새 화면 에뮬레이터 사용자 구매·장착','실기 저장 복원','자동 경험 검색·재사용 미구현']}
        (folder/'review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('백업·검증 기록:',folder,flush=True)
        if result.returncode:raise SystemExit('Mac 검사 실패. 코드와 백업을 보존했습니다.')
        print('구매·장착 화면 적용 및 Mac 검사 통과. commit·push·Ollama 호출 없음.',flush=True)
    finally:lock.unlink()
if __name__=='__main__':main()
