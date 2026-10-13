"""마지막 타격 여유 및 처치 경계 검증 및 Mac 검증. Ollama 호출 없음."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import subprocess
import sys
BASE=Path(__file__).resolve().parents[4] / "ai" / "personal-game-ai"
QA="import unittest\nfrom test_rules import state, inputs\nfrom rules import update_state\n\nclass CombatPlaythrough(unittest.TestCase):\n    def contact(self, progress):\n        current = update_state(state(progress=progress, money=20*progress), inputs(A=True))\n        current['enemy_x'] = 24\n        hits = 0\n        for frame in range(1, 241):\n            old = current\n            current = update_state(current, inputs(A=(frame-1)%18 == 0))\n            if current['enemy_hp'] < old['enemy_hp']:\n                hits += 1\n            if current['screen_state'] != 'battle':\n                break\n        return current, hits\n\n    def test_first_enemy_can_be_defeated_at_contact(self):\n        current, hits = self.contact(0)\n        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress'], hits), ('safe', 10, 20, 1, 3))\n\n    def test_second_enemy_contact_wins_with_repeated_hits(self):\n        current, hits = self.contact(1)\n        self.assertEqual((current['screen_state'], current['HP'], current['enemy_hp'], current['money'], hits), ('safe', 10, 0, 50, 10))\n\n    def test_second_enemy_can_be_defeated_by_spacing(self):\n        current = update_state(state(progress=1, money=20), inputs(A=True))\n        for frame in range(1, 401):\n            gap = current['enemy_x']-current['player_x']-8\n            ready = current['player_attack_cooldown'] <= 1\n            if ready and gap <= 8:\n                keys = inputs(A=True, R=True)\n            elif gap < 5:\n                keys = inputs(L=True)\n            elif gap > 8 and current['player_x'] < 65:\n                keys = inputs(R=True)\n            else:\n                keys = inputs()\n            current = update_state(current, keys)\n            if current['screen_state'] != 'battle':\n                break\n        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress']), ('safe', 10, 50, 2))\n\n    def test_enemy_attacks_again_only_after_120_battle_frames(self):\n        current = update_state(state(progress=1), inputs(A=True))\n        current['enemy_x'] = 24\n        current = update_state(current, inputs())\n        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (7, 120))\n        for _ in range(119):\n            current = update_state(current, inputs())\n        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (7, 1))\n        current = update_state(current, inputs())\n        self.assertEqual((current['HP'], current['enemy_attack_cooldown']), (4, 120))\n\n    def test_waiting_without_attacking_still_causes_defeat(self):\n        current = update_state(state(progress=1), inputs(A=True))\n        current['enemy_x'] = 24\n        for _ in range(361):\n            current = update_state(current, inputs())\n            if current['screen_state'] == 'defeat':\n                break\n        self.assertEqual((current['screen_state'], current['HP'], current['enemy_hp']), ('defeat', 0, 10))\n\n    def test_one_hp_enemy_dies_before_fatal_counterattack(self):\n        current = state(screen_state='battle', active_enemy=True, HP=1,\n            progress=1, money=20, player_x=16, enemy_x=24,\n            enemy_hp=1, enemy_attack=3, enemy_defense=1,\n            player_attack_cooldown=1, enemy_attack_cooldown=0)\n        result = update_state(current, inputs(A=True))\n        self.assertEqual((result['screen_state'], result['HP'], result['enemy_hp'],\n            result['money'], result['progress'], result['active_enemy']), ('safe',10,0,50,2,False))\n\n    def test_one_hp_kill_does_not_reward_twice(self):\n        current = state(screen_state='battle', active_enemy=True, progress=1,\n            money=20, player_x=16, enemy_x=24, enemy_hp=1,\n            enemy_attack=3, enemy_defense=1)\n        result = update_state(current, inputs(A=True))\n        later = update_state(result, inputs())\n        self.assertEqual((later['money'],later['progress']), (50,2))\n\n    def test_last_hit_waits_for_player_cooldown(self):\n        current = state(screen_state='battle', active_enemy=True,\n            player_x=16, enemy_x=27, enemy_hp=1, enemy_attack=3,\n            enemy_defense=1, player_attack_cooldown=2)\n        first = update_state(current, inputs(A=True))\n        self.assertEqual((first['enemy_hp'],first['player_attack_cooldown']), (1,1))\n        second = update_state(first, inputs(A=True))\n        self.assertEqual((second['screen_state'],second['enemy_hp']), ('safe',0))\n\n    def test_second_enemy_can_be_defeated_with_1_2_second_taps(self):\n        current = update_state(state(progress=1,money=20), inputs(A=True))\n        current['enemy_x'] = 24\n        minimum_hp = 10\n        for frame in range(1, 401):\n            current = update_state(current, inputs(A=(frame-1)%36==0))\n            minimum_hp = min(minimum_hp,current['HP'])\n            if current['screen_state']!='battle':\n                break\n        self.assertEqual((current['screen_state'], current['HP'], current['money'], current['progress']), ('safe',10,50,2))\n        self.assertGreaterEqual(minimum_hp,1)\n"
def sha(data):
    return hashlib.sha256(data).hexdigest()
def main():
    os.chdir(str(BASE));sys.path.insert(0,str(BASE))
    import edit_loop
    def git(*args):
        return subprocess.check_output(['git']+list(args),text=True).strip()
    if git('branch','--show-current')!=json.loads((BASE / "target.json").read_text(encoding="utf-8"))["expected_branch"]:
        raise SystemExit('작업 브랜치가 달라 중단합니다.')
    root=Path(git('rev-parse','--show-toplevel'))
    game=root/'micropython/Thumby/ThumbyGrowth'
    design=BASE/'outputs/design_20261011_232344_146552/design.json'
    approval=design.with_name('approval.json')
    originals={design:design.read_bytes(),approval:approval.read_bytes()}
    if sha(originals[design])!='bd989e114e8f469dd092ae97417bb4bee8005dfe95d5c3ff3523f932767774e2':
        raise SystemExit('원래 승인 설계가 달라 중단합니다.')
    work=root/'docs/personal-game-ai/THUMBY_GROWTH_FIRST.md'
    work_data=work.read_bytes()
    previous_path=BASE/'outputs/balance_review_20261012_213223_624651/contract_revision.json'
    previous_data=previous_path.read_bytes()
    previous=json.loads(previous_data)
    if previous['change']['enemy_attack_cooldown']['after']!=60:
        raise SystemExit('이전 조정 계약이 달라 중단합니다.')
    originals[previous_path]=previous_data
    changes={
        game/'rules.py':('f37f8ace8f698adc036f8f8eb042b7d81c48c23a5f5db26dc74604a535c6c045',None),
        game/'ThumbyGrowth.py':('976f8929743d7b3be268eff116c05f36a19c6bd78e883cf1ceaa1529e875147f',None),
        game/'test_rules.py':('06f47ebe7b660509a11c693792c545d9612381bc69d02fe2c115da2b9f1346e6',None),
        game/'tools/qa/test_combat_playthrough.py':('3c32d36b658423cda25814b87a519fb83deeb856eae0fae32b73cc19b0c6812d',QA),
    }
    targets={};before={}
    for p,(digest,replacement) in changes.items():
        if p.is_symlink():raise SystemExit('수정 경로가 심볼릭 링크입니다.')
        data=p.read_bytes()
        if sha(data)!=digest:raise SystemExit('검토한 파일과 달라 덮어쓰지 않습니다: '+p.name)
        before[p]=data;source=data.decode('utf-8')
        if p.name=='rules.py':
            old="new_state['enemy_attack_cooldown'] = 60"
            if source.count(old)!=1:raise SystemExit('적 대기 수정 위치가 다릅니다.')
            replacement=source.replace(old,"new_state['enemy_attack_cooldown'] = 120",1)
        elif p.name=='test_rules.py':
            if source.count('(15,60)')!=1 or source.count('(14,59)')!=1:
                raise SystemExit('고정 테스트 기대값 위치가 다릅니다.')
            replacement=source.replace('(15,60)','(15,120)',1).replace('(14,59)','(14,119)',1)
        elif p.name=='ThumbyGrowth.py':
            old="state['enemy_attack_cooldown'] >= 25"
            if source.count(old)!=1:raise SystemExit('피격 표시 위치가 다릅니다.')
            replacement=source.replace(old,"state['enemy_attack_cooldown'] >= 115",1)
        compile(replacement,str(p),'exec')
        targets[p]=replacement.encode('utf-8')
    # 전 단계에서 만든 변경은 위 SHA 검사로 확인하고 보존한다.
    fixed=[game/'test_ThumbyGrowth.py',game/'tools/qa/test_rules_review.py',game/'tools/qa/test_adapter_review.py']
    protected={p:p.read_bytes() for p in fixed}
    for p in fixed:
        edit_loop.check_git_files(p,p)
    lock=BASE/'.edit_loop.lock'
    with lock.open('x'):pass
    try:
        folder=BASE/'outputs'/('combat_grace_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        folder.mkdir()
        for p,data in before.items():
            (folder/(p.name+'.before.txt')).write_bytes(data)
            (folder/(p.name+'.after.txt')).write_bytes(targets[p])
        for p,data in originals.items():
            (folder/('original_'+p.name)).write_bytes(data)
        envelope=json.loads(originals[design])
        envelope['design']=json.loads(json.dumps(previous['revised_design']))
        envelope['request']['requirements']=dict(previous['revised_requirements'])
        fn=next(f for item in envelope['design']['files'] if item['id']=='001' for f in item['functions'] if f['name']=='update_state')
        fn['behavior']=fn['behavior'].replace('공격·대기60','공격·대기120')
        for item in envelope['design']['files']:
            for check in item['checks']:
                if isinstance(check.get('expected'),str):
                    check['expected']=check['expected'].replace('적 대기60','적 대기120')
        requirements=dict(envelope['request']['requirements'])
        requirements['R3']=requirements['R3'].replace('대기60전투프레임','대기120전투프레임')
        contract={'origin':'사용자 요청에 따른 마지막 타격 여유 조정','previous_contract':str(previous_path.relative_to(BASE)),'previous_contract_sha256':sha(previous_data),'source_design_sha256':sha(originals[design]),
            'change':{'enemy_attack_cooldown':{'before':60,'after':120}},
            'revised_design':envelope['design'],'revised_requirements':requirements,
            'fixed_test_change':'test_case_10의60/59를120/119로 변경. 다른 고정 assertion 유지',
            'workflow_connection':'standalone 조정 기록. 기존 승인 파일과 자동 workflow는 변경하지 않음'}
        (folder/'contract_revision.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for p,data in targets.items():
            descriptor=os.open(str(p),os.O_RDWR|os.O_NOFOLLOW)
            with os.fdopen(descriptor,'r+b') as stream:
                if stream.read()!=before[p]:raise RuntimeError('작업 중 파일이 변경됐습니다.')
                stream.seek(0);stream.write(data);stream.truncate();stream.flush()
        names=['test_rules','test_ThumbyGrowth','test_rules_review','test_combat_playthrough',
            'test_adapter_review.AdapterReview.test_end_to_end_purchase_equip_save_load',
            'test_adapter_review.AdapterReview.test_render_ownership_and_equipped_are_visible',
            'test_adapter_review.AdapterReview.test_offscreen_enemy_is_clipped_and_load_has_no_host_sleep']
        runner='import sys,unittest;sys.path[:0]='+repr([str(game),str(game/'tools/qa')])+';unittest.main(module=None,argv='+repr(['검증']+names+['-v'])+')'
        result=subprocess.run([sys.executable,'-B','-c',runner],cwd=str(game),capture_output=True,text=True,timeout=60)
        log=result.stdout+result.stderr
        (folder/'verification.txt').write_text(log,encoding='utf-8');print(log,flush=True)
        for p,data in {**protected,**originals,work:work_data}.items():
            if p.is_symlink() or p.read_bytes()!=data:raise RuntimeError('보존 대상이 변경됐습니다.')
        for p,data in targets.items():
            if p.is_symlink() or p.read_bytes()!=data:raise RuntimeError('검사 중 수정 파일이 변경됐습니다.')
        (folder/'result.json').write_text(json.dumps({'passed':result.returncode==0,'tests_count':46,
            'code_sha256':sha((game/'rules.py').read_bytes()),'head':git('rev-parse','HEAD'),
            'work_sha256':sha(work_data),'unverified':['새 수치의 에뮬레이터 플레이','실기','자동 경험 검색·재사용 미구현']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('백업·조정 계약·검증 기록:',folder,flush=True)
        if result.returncode:raise SystemExit('검사 실패. 파일과 백업을 보존했습니다.')
        print('Mac46개 검사 통과. 적 공격 간격60→120프레임과 짧은 피격 표시 적용. commit·push·Ollama 호출 없음.',flush=True)
        print(git('status','--short'))
    finally:lock.unlink()
if __name__=='__main__':main()
