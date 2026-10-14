"""One bounded WORK-driven task; candidate code runs only in isolated Docker."""
import ast
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

import generation_profile
import edit_loop
import ask_ai
from read_context import git_output

MAX_ATTEMPTS = 3
MAX_SECONDS = 1200
ALLOWED = ('rules.py','ThumbyGrowth.py','scene_art.py')
MARKER = '\n## 로컬 작업 결과\n'


def internal_rules(root):
    value = os.environ.get('GAME_AI_INTERNAL_RULES')
    candidates = [Path(value).expanduser()] if value else [
        root.parent/'jihoon-ai-internal'/'AGENTS_INTERNAL.md']
    for path in candidates:
        if path.is_file() and not path.is_symlink():
            private = Path(git_output(path.parent,'rev-parse','--show-toplevel'))
            remote = git_output(private,'remote','get-url','origin')
            if remote.rstrip('/').removesuffix('.git') not in (
                    'https://github.com/jihoonlabs/jihoon-ai-internal',
                    'git@github.com:jihoonlabs/jihoon-ai-internal'):
                raise RuntimeError('내부 규칙 저장소의 origin을 확인하세요.')
            subprocess.run(['git','fetch','origin','main'],cwd=private,check=True,
                           capture_output=True,text=True,timeout=60)
            relative = path.resolve().relative_to(private.resolve()).as_posix()
            content = git_output(private,'show','origin/main:'+relative)
            if len(content)>20000:
                raise ValueError('내부 규칙 문맥이 너무 큽니다.')
            return content
    raise RuntimeError('최신 내부 규칙 checkout을 찾지 못했습니다. '
                       'GAME_AI_INTERNAL_RULES에 AGENTS_INTERNAL.md 실제 경로를 지정하세요.')


def decode(raw):
    if not isinstance(raw,str) or len(raw)>200000:
        raise ValueError('모델 JSON 응답 길이를 확인하세요.')
    value = json.loads(raw)
    if not isinstance(value,dict):
        raise ValueError('JSON 객체가 필요합니다.')
    return value


def validate_plan(value):
    if set(value)=={'question'} and isinstance(value['question'],str) and 0<len(value['question'])<=2000:
        return value
    if set(value)!={'goal','files','acceptance'}:
        raise ValueError('계획은 goal/files/acceptance만 사용합니다.')
    for field in ('goal','acceptance'):
        if not isinstance(value[field],str) or not 0<len(value[field])<=2000:
            raise ValueError('작업 목표와 완료 조건이 필요합니다.')
    files = value['files']
    if not isinstance(files,list) or not 1<=len(files)<=3 or any(
            not isinstance(name,str) or name not in ALLOWED for name in files) or len(set(files))!=len(files):
        raise ValueError('현재 게임의 허용된 파일만 선택하세요.')
    return value


def validate_candidate(value,plan):
    if set(value)!={'files','tests'} or not isinstance(value['files'],dict) or set(value['files'])!=set(plan['files']):
        raise ValueError('계획에 선택된 전체 파일과 tests만 반환하세요.')
    encoded = {}
    for name,code in value['files'].items():
        if not isinstance(code,str) or not code.strip() or len(code)>100000:
            raise ValueError('빈 파일 또는 너무 큰 후보입니다.')
        compile(code,name,'exec')
        generation_profile.validate_code('game',code,name)
        encoded[name]=(code.rstrip()+'\n').encode()
    tests = value['tests']
    if not isinstance(tests,str) or not 0<len(tests)<=20000:
        raise ValueError('작업 전용 회귀 검사가 필요합니다.')
    tree=ast.parse(tests)
    cases=[n for n in tree.body if isinstance(n,ast.ClassDef) and any(
        (isinstance(base,ast.Attribute) and isinstance(base.value,ast.Name)
         and base.value.id=='unittest' and base.attr=='TestCase')
        or (isinstance(base,ast.Name) and base.id=='TestCase') for base in n.bases)]
    methods=[n for case in cases for n in case.body
             if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if not methods or not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='self'
               and n.func.attr.startswith('assert') for method in methods for n in ast.walk(method)):
        raise ValueError('TestCase의 test_ 메서드 안에 실제 assertion이 필요합니다.')
    return encoded,(tests.rstrip()+'\n').encode()


def run(chat,directory,root,context,request,notify=print):
    started=time.monotonic()
    config=json.loads(chat.config_path.read_text())
    work=root/config['branch_document']
    if work.is_symlink():
        raise ValueError('WORK 심볼릭 링크는 지원하지 않습니다.')
    rules=internal_rules(root)
    original_work=work.read_bytes()
    expected_work=original_work
    head=git_output(root,'rev-parse','HEAD')
    paths=[directory/name for name in ALLOWED]
    fixed=list(directory.glob('test_*.py'))
    for path in paths+[work]+fixed:
        if path.is_symlink() or not path.is_file():
            raise ValueError('실제 일반 파일이 필요합니다: '+path.name)
        relative=path.relative_to(root).as_posix()
        git_output(root,'ls-files','--error-unmatch','--',relative)
        if git_output(root,'status','--porcelain=v1','--',relative):
            raise RuntimeError('기존 변경을 보존하고 중단합니다: '+relative)
    if git_output(root,'diff','--cached','--name-only'):
        raise RuntimeError('기존 staged 변경을 먼저 확인하세요. 자동 commit에 섞지 않습니다.')
    originals={p:p.read_bytes() for p in paths}
    fixed_bytes={p:p.read_bytes() for p in fixed}
    expected=dict(originals)
    task_test=directory/('test_resume_'+uuid.uuid4().hex[:12]+'.py')
    task_bytes=None
    published=False

    def check():
        edit_loop.check_directory(directory)
        if git_output(root,'rev-parse','HEAD')!=head or git_output(root,'branch','--show-current')!=config['expected_branch']:
            raise RuntimeError('작업 중 Git 기준이 변경됐습니다.')
        if work.is_symlink() or work.read_bytes()!=expected_work:
            raise RuntimeError('작업 중 WORK가 변경됐습니다.')
        for path,data in {**expected,**fixed_bytes}.items():
            if path.is_symlink() or not path.is_file() or path.read_bytes()!=data:
                raise RuntimeError('외부 변경을 발견했습니다: '+path.name)
        if set(directory.glob('test_*.py'))!=set(fixed)|({task_test} if task_bytes is not None else set()):
            raise RuntimeError('검사 파일 구성이 변경됐습니다.')
        if task_bytes is not None and (task_test.is_symlink() or task_test.read_bytes()!=task_bytes):
            raise RuntimeError('작업 전용 검사에 외부 변경이 있습니다.')
        if time.monotonic()-started>=MAX_SECONDS:
            raise RuntimeError('작업 시간 상한에 도달했습니다.')

    def call(prompt):
        check()
        if chat.model is ask_ai.ask_model:
            raw=chat.model(prompt,timeout=max(1,min(600,MAX_SECONDS-(time.monotonic()-started))))
        else:
            raw=chat.model(prompt)
        chat.record({'resume_response':raw})
        check()
        return decode(raw)

    try:
        notify('WORK에서 다음 작업 하나를 선택합니다.')
        # Private rules stay in memory; never copy them into public WORK or logs.
        work_text=original_work.decode()
        prompt=('내부 실행 규칙:\n'+rules+'\n현재 WORK:\n'+work_text+
                '\n사용자 지시:\n'+request+'\n현재 파일/함수 목록:\n'+
                json.dumps({p.name:[n.name for n in ast.parse(data.decode()).body
                                      if isinstance(n,ast.FunctionDef)] for p,data in originals.items()},ensure_ascii=False)+
                '\n합의된 미완료 작업 하나만 선택하세요. 로컬 작업 결과와 실제 코드에 이미 구현된 작업을 반복하지 마세요. 새 사양을 발명하지 마세요. '
                '조회에서 끝내지 말고 실제 구현 계획을 선택하세요. 중대한 결정이 필요하면 {"question":"질문"}. '
                '그 외 Markdown 없이 {"goal":"목표","files":["rules.py"],"acceptance":"관찰 가능한 완료 조건"}. '
                '허용 파일: '+json.dumps(ALLOWED))
        plan=validate_plan(call(prompt))
        if 'question' in plan:
            return {'status':'waiting_for_user','question':plan['question']}
        chat.record({'resume_plan':plan})
        notify('작업: '+plan['goal'])
        chat.docker_check()
        check()
        passed,feedback=edit_loop.run_test(chat.folder/'resume_baseline.txt','discover',work_dir=directory)
        check()
        if not passed:
            return {'status':'blocked','message':'수정 전 전체 게임 검사가 실패했습니다.','feedback':feedback}
        feedback=''
        for attempt in range(1,MAX_ATTEMPTS+1):
            notify('구현·전체 검사 '+str(attempt)+'/'+str(MAX_ATTEMPTS))
            source='\n'.join('--- '+name+' ---\n'+expected[directory/name].decode() for name in ALLOWED)
            candidate_prompt=('내부 실행 규칙:\n'+rules+'\n현재 WORK:\n'+work_text+
                '\n선택한 단일 작업:\n'+json.dumps(plan,ensure_ascii=False)+'\n현재 코드:\n'+source+
                '\n일반 Thumby API 계약:\n'+generation_profile.design_prompt('game')+
                '\n실패 피드백:\n'+feedback[-6000:]+
                '\n전체 교체 코드와 이 작업의 완료 조건을 검증하는 unittest를 반환하세요. '
                '기존 검사는 변경하지 않습니다. 새 검사는 CPython fake thumby를 사용합니다. '
                '새 기능과 기존 계약 보존을 실제 assertion으로 검사하세요. '
                '임의 셸/외부 API/새 의존성을 추가하지 마세요. '
                'Markdown 없이 {"files":{"파일.py":"전체 코드"},"tests":"unittest 코드"}.')
            try:
                changed,new_tests=validate_candidate(call(candidate_prompt),plan)
            except (ValueError,SyntaxError) as error:
                feedback=str(error)
                continue
            if all(changed[name]==originals[directory/name] for name in changed):
                feedback='원본과 동일합니다. 작업을 구현한 변경이 필요합니다.'
                continue
            check()
            journal={'originals':{p.name:data.decode() for p,data in originals.items()},
                     'candidates':{name:(changed[name].decode() if name in changed else expected[directory/name].decode()) for name in ALLOWED},
                     'test_file':task_test.name,'test_code':new_tests.decode(),'head':head}
            (chat.folder/'resume_journal.json').write_text(json.dumps(journal,ensure_ascii=False))
            for name,data in changed.items():
                (directory/name).write_bytes(data)
                expected[directory/name]=data
            if task_bytes is None:
                with task_test.open('xb') as stream:
                    stream.write(new_tests)
            else:
                task_test.write_bytes(new_tests)
            task_bytes=new_tests
            passed,feedback=edit_loop.run_test(chat.folder/('resume_test_'+str(attempt)+'.txt'),'discover',work_dir=directory)
            check()
            if passed:
                selected=[directory/name for name in plan['files'] if expected[directory/name]!=originals[directory/name]]
                result={'status':'tests_passed','goal':plan['goal'],'attempts':attempt,
                        'files':[p.name for p in selected],'test_module':'discover',
                        'message':'작업 전용 검사와 전체 게임 검사 통과. 실제 기기·그림 품질은 미검증입니다.'}
                entry=MARKER+'- 작업: '+plan['goal'].replace('\n',' ')+'\n- 검증: 작업 전용 unittest + 전체 게임 검사 통과. 실기/시각 품질은 미검증.\n- 다음: 현재 미완료 목록과 실제 코드를 대조해 다음 단일 작업을 선택한다.\n'
                work.write_text(work_text.split(MARKER)[0]+entry)
                expected_work=work.read_bytes()
                check()
                published=True  # Verified changes and WORK survive publication failures.
                if config.get('resume_publish') is True:
                    notify('검증된 변경을 커밋·푸시합니다.')
                    files=[p.relative_to(root).as_posix() for p in selected+[task_test,work]]
                    # Commit only owned paths; unrelated staged changes cannot be included.
                    subprocess.run(['git','add','--',*files],cwd=root,check=True,capture_output=True,timeout=10)
                    subprocess.run(['git','commit','--only','-m','Complete bounded Thumby task: '+plan['goal'][:120],'--',*files],
                                   cwd=root,check=True,capture_output=True,text=True,timeout=30)
                    result['commit']=git_output(root,'rev-parse','HEAD')
                    remote=git_output(root,'remote','get-url','origin')
                    if remote.rstrip('/').removesuffix('.git') not in (
                            'https://github.com/jihoonlabs/jihoon-projects',
                            'git@github.com:jihoonlabs/jihoon-projects'):
                        raise RuntimeError('commit은 보존했습니다. 공개 저장소 origin을 확인하세요.')
                    subprocess.run(['git','push','origin','HEAD:refs/heads/'+config['expected_branch']],
                                   cwd=root,check=True,capture_output=True,text=True,timeout=60)
                    result['pushed']=True
                return result
        return {'status':'failed','message':'재시도 상한에 도달했습니다. 이번 후보를 복원합니다.','feedback':feedback}
    finally:
        if not published:
            # Restore our own bytes only; preserve any concurrent editor's work.
            for path,data in originals.items():
                if not path.is_symlink() and path.is_file() and path.read_bytes()==expected[path]:
                    path.write_bytes(data)
            if task_bytes is not None and not task_test.is_symlink() and task_test.is_file() and task_test.read_bytes()==task_bytes:
                task_test.unlink()
            if not work.is_symlink() and work.is_file() and work.read_bytes()==expected_work:
                work.write_bytes(original_work)
