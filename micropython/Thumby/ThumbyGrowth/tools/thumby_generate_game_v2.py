"""승인 설계와 고정 테스트로 Mac Ollama 게임 구현을 생성합니다."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[4] / "ai" / "personal-game-ai"
DESIGN_SHA = 'bd989e114e8f469dd092ae97417bb4bee8005dfe95d5c3ff3523f932767774e2'
TESTS_SHA = '23ea8a184a374aa7f1cc62300e0025124c828ea66b79b0af7061d1825a11c8d6'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exclusive(path, text):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(text)


def main():
    if not BASE.is_dir():
        raise SystemExit('작업 폴더가 없어 중단합니다.')
    os.chdir(str(BASE))
    sys.path.insert(0,str(BASE))
    import ask_ai
    import create_loop
    import edit_loop
    import generation_profile
    import implementation_link

    branch = subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    if branch != json.loads((BASE / "target.json").read_text(encoding="utf-8"))["expected_branch"]:
        raise SystemExit('작업 브랜치가 달라 중단합니다.')
    if ask_ai.payload.get('model') != 'qwen3-coder:30b':
        raise SystemExit('요청 모델이 달라 중단합니다.')
    options = ask_ai.model_options()
    if options['num_ctx'] != 32768 or options['num_predict'] != 16384:
        raise SystemExit('문맥32768/출력16384 설정이 필요합니다.')

    manifest = BASE/'outputs/test_plan_20261012_083518_807142/tests.json'
    envelope,candidate,snapshot = implementation_link.read_confirmed(manifest,TESTS_SHA)
    if digest((BASE/'outputs/design_20261011_232344_146552/design.json').read_bytes()) != DESIGN_SHA:
        raise SystemExit('승인 설계가 달라 중단합니다.')
    generation_profile.validate_tests('game',candidate,envelope['design'])
    directory,_ = edit_loop.game_location()
    expected_directory = BASE.parent.parent/'micropython/Thumby/ThumbyGrowth'
    if directory.resolve() != expected_directory.resolve():
        raise SystemExit('게임 생성 대상이 달라 중단합니다.')
    fixed = {item['id']:item for item in candidate['files']}
    sources = envelope['design']['files']
    if [(item['id'],item['filename'],item['depends_on']) for item in sources] != [
        ('001','rules.py',[]),('002','ThumbyGrowth.py',['001'])]:
        raise SystemExit('승인 파일 순서나 의존성이 달라 중단합니다.')

    requests = {}
    for item in sources:
        request = (
            '승인 설계 SHA256='+DESIGN_SHA+'의 '+item['filename']+'만 구현하세요.\n'
            '전체 승인 계약과 고정 테스트는 이번 모델 요청 뒤에 직접 첨부됩니다.\n'
            '최상위 함수는 다음 이름만 정의하세요: '
            + ', '.join(function['name'] for function in item['functions'])
            + '\n다른 파일의 함수는 복제하지 마세요. rules는 기기 I/O와 어댑터 import 금지.\n'
            'MicroPython과 CPython3.9에서 사용할 수 있는 코드를 작성하세요.\n'
            '주석·설명·진단 메시지는 한국어이며 중국어 문자열은 금지입니다.\n'
            '승인된 영문 함수명·키·화면·표시 문자열은 유지하세요.\n'
            + generation_profile.implementation_prompt('game',item['filename'])
        )
        requests[item['id']] = request
        create_loop.prepare_create('game/'+item['filename'],request,Path(fixed[item['id']]['filename']).stem)
    for item in candidate['files']:
        path = directory/item['filename']
        if path.read_bytes() != item['code'].encode('utf-8'):
            raise SystemExit('설치 테스트가 확정 후보와 달라 중단합니다.')
        edit_loop.check_git_files(path,path)

    approved_context = edit_loop.read_context()
    dependency_artifacts = {}
    design_file = BASE/'outputs/design_20261011_232344_146552/design.json'
    protected = {
        path: path.read_bytes()
        for path in (
            manifest,
            manifest.with_name('confirmation.json'),
            design_file,
            design_file.with_name('approval.json'),
        )
    }
    seed_file = BASE/'outputs/create_20261012_090923_737940/candidate_1.py'
    if seed_file.is_symlink() or not seed_file.is_file():
        raise SystemExit('저장된 1차 생성 코드를 찾지 못했습니다.')
    seed_code = seed_file.read_text(encoding='utf-8')
    compile(seed_code,str(seed_file),'exec')

    def check_inputs():
        for path,content in protected.items():
            if path.is_symlink() or path.read_bytes() != content:
                raise RuntimeError('승인 계약이나 고정 테스트 기록이 변경됐습니다.')
        if edit_loop.read_context() != approved_context:
            raise RuntimeError('작업 문맥이 변경됐습니다.')
        for identifier,content in dependency_artifacts.items():
            source = next(item for item in sources if item['id']==identifier)
            path = directory/source['filename']
            if path.is_symlink() or path.read_bytes() != content:
                raise RuntimeError('통과한 선행 코드가 변경됐습니다.')
        for test in candidate['files']:
            path = directory/test['filename']
            if path.is_symlink() or path.read_bytes() != test['code'].encode('utf-8'):
                raise RuntimeError('고정 테스트가 변경됐습니다.')
            edit_loop.check_git_files(path,path)

    print('실제 Mac Ollama 게임 생성을 시작합니다.',flush=True)
    print('모델: qwen3-coder:30b',flush=True)
    print('적용 옵션:',options,flush=True)
    for item in sources:
        check_inputs()
        identifier = item['id']
        before_folders = set((BASE/'outputs').glob('create_*'))
        calls = 0

        def model(prompt):
            nonlocal calls
            calls += 1
            check_inputs()
            fresh = [path for path in (BASE/'outputs').glob('create_*') if path not in before_folders and path.is_dir()]
            if len(fresh) != 1:
                raise RuntimeError('이번 생성 기록 폴더를 구분하지 못했습니다.')
            folder = fresh[0]
            full_prompt = prompt + (
                '\n\n# 변경할 수 없는 전체 승인 설계와 공유 계약\n'
                + json.dumps({'requirements':envelope['request']['requirements'],'design':envelope['design']},ensure_ascii=False)
                + '\n\n# 이번 target의 고정 테스트 원문\n' + fixed[identifier]['code']
            )
            for dependency in item['depends_on']:
                dependency_item = next(source for source in sources if source['id']==dependency)
                full_prompt += '\n\n# 테스트를 통과한 선행 파일: '+dependency_item['filename']+'\n'+dependency_artifacts[dependency].decode('utf-8')
            full_prompt += (
                '\n\n이번 target은 '+item['filename']+'입니다. 다른 파일은 구현하지 마세요. '
                '테스트와 승인 설계는 변경하지 마세요. '
                '실기 미검증 항목을 구현 완료나 실기 검증 통과라고 주장하지 마세요. '
                '응답은 {"action":"create","code":"전체 코드"} JSON 하나입니다.'
            )
            exclusive(folder/('full_prompt_%d.txt'%calls),full_prompt)
            print('실제 요청 길이:',len(full_prompt),'자',flush=True)
            print('이번 생성 기록:',folder,flush=True)
            if identifier == '001' and calls == 1:
                print('저장된 1차 코드를 재사용하여 실패 내용을 다시 확인합니다. Ollama 호출 없음.',flush=True)
                return json.dumps({'action':'create','code':seed_code},ensure_ascii=False)
            full_prompt += (
                '\n추가 수정 지침: update_state는 새 dict뿐 아니라 owned도 새 list로 복사하세요. '
                '구매로 입력 state의 owned를 변경하면 안 됩니다. '
                '저장 정수 검사는 bool을 거부하도록 type(value) is int로 검사하세요. '
                'version·money·progress·장착ID 모두 승인된 정확한 타입 계약을 지키세요. '
                '이전 테스트 실패를 수정하고 나머지 승인 동작도 유지하세요.'
            )
            exclusive(folder/('actual_prompt_%d.txt'%calls),full_prompt)
            try:
                answer = ask_ai.ask_model(full_prompt)
            except ask_ai.ModelLengthError as error:
                exclusive(folder/('length_result_%d.json'%calls),json.dumps(error.result,ensure_ascii=False,indent=2)+'\n')
                print('중단 응답과 토큰 기록 보존:',folder,flush=True)
                print('입력 토큰:',error.result.get('prompt_eval_count'),flush=True)
                print('출력 토큰:',error.result.get('eval_count'),flush=True)
                raise
            check_inputs()
            return answer

        print('\n생성 대상:',item['filename'],flush=True)
        result = create_loop.run_create('game/'+item['filename'],requests[identifier],Path(fixed[identifier]['filename']).stem,model=model)
        print('생성 결과:',json.dumps(result,ensure_ascii=False),flush=True)
        if result.get('status') != 'tests_passed':
            raise SystemExit('이 파일의 고정 테스트가 통과하지 않아 다음 파일 생성을 중단합니다.')
        check_inputs()
        path = directory/item['filename']
        code = path.read_text(encoding='utf-8')
        definitions = [node.name for node in ast.parse(code).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
        expected_names = [function['name'] for function in item['functions']]
        if sorted(definitions) != sorted(expected_names):
            raise SystemExit('최상위 함수 구성이 승인 설계와 다릅니다. 생성 파일을 보존하고 중단합니다.')
        dependency_artifacts[identifier] = path.read_bytes()
        print('통과 파일:',path,flush=True)
        print('파일 SHA256:',digest(path.read_bytes()),flush=True)

    print('\n두 파일의 개별 고정 테스트가 통과했습니다.',flush=True)
    print('통합 회귀·코드 검토·MicroPython 진입·실기 검증은 아직입니다.',flush=True)
    print('게임 코드 commit·push는 하지 않았습니다.',flush=True)
    print(subprocess.check_output(['git','status','--short'],text=True))

if __name__ == '__main__':
    main()
