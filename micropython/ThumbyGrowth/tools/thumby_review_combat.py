"""전투 거리 표시와 전체 전투 검증. Ollama 호출 없음."""
from pathlib import Path
from datetime import datetime
import ast
import hashlib
import json
import os
import subprocess
import sys
BASE=Path('/Users/parkjihoon/workspace/thumby-rpg-first-20261008/ai/personal-game-ai')
RENDERER="def draw_game(state):\n    display = thumby.display\n    display.fill(0)\n    screen = state['screen_state']\n    status = state['save_status']\n    if screen == 'battle':\n        display.drawText('HP:'+str(state['HP']), 0, 0, 1)\n        money = state['money']\n        shown = str(money) if money < 1000 else str(min(999, money//1000))+'k'\n        display.drawText('$'+shown, 72-6*(len(shown)+1), 0, 1)\n        display.drawText('E:'+str(state['enemy_hp']), 0, 8, 1)\n        facing = '>' if state['direction'] == 'R' else '<'\n        display.drawText('P'+facing, 0, 18, 1)\n        gap = max(state['player_x'], state['enemy_x'])-min(state['player_x'], state['enemy_x'])-8\n        ahead = ((state['direction']=='R' and state['enemy_x']>state['player_x'])\n                 or (state['direction']=='L' and state['enemy_x']<state['player_x']))\n        hint = 'TURN' if not ahead else ('CLOSE' if gap<=2 else ('RANGE' if gap<=8 else 'FAR'))\n        display.drawText(hint, 36, 8, 1)\n        camera = max(0, min(72, state['player_x']-32))\n        positions = [state['player_x']]\n        if state['active_enemy']:\n            positions.append(state['enemy_x'])\n        for world_x in positions:\n            x = world_x-camera\n            left = max(0, x)\n            right = min(72, x+8)\n            if right > left:\n                display.drawFilledRectangle(left, 32, right-left, 8, 1)\n                if 0 <= x <= 64:\n                    marker = facing if world_x == state['player_x'] else 'X'\n                    flashing = (world_x == state['player_x'] and state['enemy_attack_cooldown'] >= 25\n                                and state['combat_frame'] % 2 == 0)\n                    display.drawText(marker, x+1, 32, 1 if flashing else 0)\n        if state['player_attack_cooldown'] >= 7:\n            attack_x = state['player_x']-camera+(8 if state['direction']=='R' else -6)\n            if 0 <= attack_x <= 66:\n                display.drawText('-', attack_x, 32, 1)\n    elif screen in ('shop_detail', 'equip_detail'):\n        item = state['menu_selection']\n        names = ('Blade', 'Sword', 'Vest', 'Armor')\n        prices = (40, 80, 40, 80)\n        display.drawText(names[item], 0, 0, 1)\n        display.drawText('P:'+str(prices[item]), 0, 8, 1)\n        money = str(state['money'])\n        display.drawText(money[:12], 0, 16, 1)\n        if len(money) > 12:\n            display.drawText(money[12:], 0, 24, 1)\n        owned = 'Y' if state['owned'][item] else 'N'\n        equipped = item in (state['equipped_weapon'], state['equipped_armor'])\n        display.drawText('O:'+owned+' E:'+('Y' if equipped else 'N'), 0, 32, 1)\n    elif screen == 'defeat':\n        display.drawText('DEFEAT', 0, 0, 1)\n        display.drawText('A:RETRY', 0, 20, 1)\n    else:\n        if screen == 'safe':\n            choices = ('NEXT', 'SHOP', 'EQUIP', 'SAVE')\n        elif screen == 'pause':\n            choices = ('RESUME', 'SAVE')\n        else:\n            choices = ('Blade', 'Sword', 'Vest', 'Armor')\n        display.drawText(status if status in ('SAVED','SAVE ERR') else screen.upper(), 0, 0, 1)\n        start = state['menu_scroll']\n        for row in range(3):\n            index = start+row\n            if index < len(choices):\n                selected = '>' if index == state['menu_selection'] else ' '\n                display.drawText(selected+choices[index], 0, 10+row*10, 1)\n    if status in ('SAVED', 'SAVE ERR') and screen in ('battle','shop_detail','equip_detail','defeat'):\n        display.drawText(status, 0, 0, 1)\n    display.update()"
QA="import unittest\nfrom test_rules import state, inputs\nfrom rules import update_state\n\nclass CombatPlaythrough(unittest.TestCase):\n    def contact(self, progress):\n        current = update_state(state(progress=progress, money=20*progress), inputs(A=True))\n        current['enemy_x'] = 24\n        hits = 0\n        for frame in range(1, 241):\n            old = current\n            current = update_state(current, inputs(A=(frame-1)%18 == 0))\n            if current['enemy_hp'] < old['enemy_hp']:\n                hits += 1\n            if current['screen_state'] != 'battle':\n                break\n        return current, hits\n\n    def test_first_enemy_can_be_defeated_at_contact(self):\n        current, hits = self.contact(0)\n        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress'], hits), ('safe', 10, 20, 1, 3))\n\n    def test_second_enemy_contact_loses_despite_hits(self):\n        current, hits = self.contact(1)\n        self.assertEqual((current['screen_state'], current['HP'], current['enemy_hp'], current['money'], hits), ('defeat', 0, 4, 20, 6))\n\n    def test_second_enemy_can_be_defeated_by_spacing(self):\n        current = update_state(state(progress=1, money=20), inputs(A=True))\n        for frame in range(1, 401):\n            gap = current['enemy_x']-current['player_x']-8\n            ready = current['player_attack_cooldown'] <= 1\n            if ready and gap <= 8:\n                keys = inputs(A=True, R=True)\n            elif gap < 5:\n                keys = inputs(L=True)\n            elif gap > 8 and current['player_x'] < 65:\n                keys = inputs(R=True)\n            else:\n                keys = inputs()\n            current = update_state(current, keys)\n            if current['screen_state'] != 'battle':\n                break\n        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress']), ('safe', 10, 50, 2))\n"
def sha(data):
    return hashlib.sha256(data).hexdigest()
def main():
    os.chdir(str(BASE))
    sys.path.insert(0,str(BASE))
    import edit_loop
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    if branch!='work/thumby-rpg-first-20261008':
        raise SystemExit('작업 브랜치가 달라 중단합니다.')
    game=root/'micropython/ThumbyGrowth'
    path=game/'ThumbyGrowth.py'
    if path.is_symlink():
        raise SystemExit('게임 경로가 심볼릭 링크여서 중단합니다.')
    original=path.read_bytes()
    if sha(original) not in {'b82a82648f975da05e076697d7f7e22895c66e7d08f923ac1db590c02f0bd39f','2d6dd5d87eeb9a896a09cf4416823daf16eb299a975cb04f9e928dde8d838616'}:
        raise SystemExit('검토한 화면 코드와 달라 덮어쓰지 않습니다.')
    rules=game/'rules.py'
    rules_data=rules.read_bytes()
    if rules.is_symlink() or sha(rules_data)!='565b08abb6fb5266f8695469b9eb1f3035b56cf3b661ecd8d8ba06c91836a333':
        raise SystemExit('규칙 코드가 검토한 버전과 달라 중단합니다.')
    fixed=[game/'test_rules.py',game/'test_ThumbyGrowth.py',game/'tools/qa/test_rules_review.py',game/'tools/qa/test_adapter_review.py']
    fixed_data={p:p.read_bytes() for p in fixed}
    for p in fixed:
        edit_loop.check_git_files(p,p)
    qa=game/'tools/qa/test_combat_playthrough.py'
    if qa.is_symlink() or (qa.exists() and (not qa.is_file() or qa.read_text(encoding='utf-8')!=QA)):
        raise SystemExit('같은 이름의 추가 검사가 이미 다르게 존재합니다.')
    source=original.decode('utf-8')
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='draw_game']
    if len(nodes)!=1:
        raise SystemExit('화면 함수 위치를 확인하지 못했습니다.')
    node=nodes[0];lines=source.splitlines(keepends=True)
    updated=''.join(lines[:node.lineno-1])+RENDERER+'\n'+''.join(lines[node.end_lineno:])
    compile(updated,str(path),'exec')
    old_funcs={n.name:ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
    new_funcs={n.name:ast.get_source_segment(updated,n) for n in ast.parse(updated).body if isinstance(n,ast.FunctionDef)}
    if set(old_funcs)!=set(new_funcs) or [n for n in old_funcs if old_funcs[n]!=new_funcs[n]]!=['draw_game']:
        raise SystemExit('화면 함수 외 수정이 있어 중단합니다.')
    lock=BASE/'.edit_loop.lock'
    with lock.open('x'):
        pass
    try:
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        folder=BASE/'outputs'/('combat_review_'+stamp)
        folder.mkdir()
        (folder/'before.py.txt').write_bytes(original)
        (folder/'after.py.txt').write_text(updated,encoding='utf-8')
        if path.read_bytes()!=original:
            raise SystemExit('작업 중 화면 코드가 변경됐습니다.')
        descriptor=os.open(str(path),os.O_RDWR|os.O_NOFOLLOW)
        with os.fdopen(descriptor,'r+b') as stream:
            if stream.read()!=original:
                raise SystemExit('작업 중 파일이 변경됐습니다.')
            stream.seek(0);stream.write(updated.encode('utf-8'));stream.truncate();stream.flush()
        if not qa.exists():
            with qa.open('x',encoding='utf-8') as stream:
                stream.write(QA)
        names=['test_rules','test_ThumbyGrowth','test_rules_review','test_combat_playthrough',
            'test_adapter_review.AdapterReview.test_end_to_end_purchase_equip_save_load',
            'test_adapter_review.AdapterReview.test_render_ownership_and_equipped_are_visible',
            'test_adapter_review.AdapterReview.test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep']
        runner='import sys,unittest;sys.path[:0]='+repr([str(game),str(qa.parent)])+';unittest.main(module=None,argv='+repr(['검증']+names+['-v'])+')'
        result=subprocess.run([sys.executable,'-B','-c',runner],cwd=str(game),capture_output=True,text=True,timeout=60)
        output=result.stdout+result.stderr
        (folder/'verification.txt').write_text(output,encoding='utf-8')
        print(output,flush=True)
        if rules.read_bytes()!=rules_data or any(p.read_bytes()!=data for p,data in fixed_data.items()):
            raise RuntimeError('검사 중 규칙 또는 고정 테스트가 변경됐습니다.')
        if path.read_bytes()!=updated.encode('utf-8'):
            raise RuntimeError('검사 중 화면 코드가 변경됐습니다.')
        report={'origin':'ChatGPT 전투 재현 및 화면 개선','changed':'draw_game만 변경, 전투 규칙과 고정 테스트 유지',
            'tests_passed':result.returncode==0,'tests_count':40,
            'reproduction':['첫 적 접촉 공격으로 승리','둘째 적 접촉 공격은 명중해도 패배','둘째 적 거리 유지로 승리'],
            'interpretation':'돈20 화면과 둘째 적 패배 재현이 일치하지만 사용자 실제 명중은 미확정',
            'unverified':['새 화면 에뮬레이터 사용자 조작','실기','상하 이동 및 A+B 시작 미구현'],
            'code_sha256':sha(path.read_bytes())}
        (folder/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('백업과 검증 기록:',folder,flush=True)
        if result.returncode:
            raise SystemExit('Mac 검사 실패. 수정 코드와 백업을 보존했습니다.')
        print('Mac40개 검사 통과. 게임 규칙·고정 테스트 변경과 commit·push·Ollama 호출 없음.',flush=True)
    finally:
        lock.unlink()
if __name__=='__main__':
    main()
