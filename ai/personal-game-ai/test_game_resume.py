"""Bounded resume, regression retry, rollback and publication failure contracts."""
import json
import subprocess
import unittest
from unittest.mock import patch
import test_game_chat as fixture
import game_resume
import edit_loop


TESTS='import unittest\nfrom rules import step\nclass Acceptance(unittest.TestCase):\n    def test_goal(self):\n        self.assertEqual(step(),2)\n'


class ResumeTests(unittest.TestCase):
    git=fixture.GameChatTests.git

    def setUp(self):
        fixture.GameChatTests.setUp(self)
        (self.game/'scene_art.py').write_text('SCENE_BITMAPS=()\n')
        self.git('add','.')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid',
                 '-c','commit.gpgsign=false','commit','-qm','scene fixture')
        self.private=patch.object(game_resume,'internal_rules',return_value='Keep agreed scope; no jump.')
        self.private.start();self.addCleanup(self.private.stop)
        self.plan=json.dumps({'goal':'Return 2 from step','files':['rules.py'],'acceptance':'step()==2'})

    def candidate(self,code='def step():\n    return 2\n',files=None):
        return json.dumps({'files':files or {'rules.py':code},'tests':TESTS})

    def test_continue_runs_work_plan_edit_all_tests_and_updates_work(self):
        self.model.side_effect=[self.plan,self.candidate()]
        result=self.chat.turn('이어서 해')
        self.assertEqual(result['status'],'tests_passed')
        self.assertEqual(self.target.read_text(),'def step():\n    return 2\n')
        self.assertEqual(self.runner.call_count,2)
        self.assertTrue(all(c.args[1]=='discover' for c in self.runner.call_args_list))
        self.assertIn('Return 2 from step',self.document.read_text())
        self.assertEqual(len(list(self.game.glob('test_resume_*.py'))),1)
        self.assertIn('Make Thumby game.',self.model.call_args_list[0].args[0])
        self.assertFalse((self.base/'.game_chat.lock').exists())

    def test_failed_candidate_retries_with_real_feedback_then_passes(self):
        self.model.side_effect=[self.plan,self.candidate('def step():\n    return 0\n'),self.candidate()]
        self.runner.side_effect=[(True,'baseline'),(False,'AssertionError: 0 != 2'),(True,'passed')]
        result=self.chat.turn('/continue')
        self.assertEqual(result['attempts'],2)
        self.assertIn('AssertionError: 0 != 2',self.model.call_args.args[0])

    def test_attempt_limit_restores_all_files_removes_own_test_and_keeps_work(self):
        self.model.side_effect=[self.plan]+[self.candidate()]*3
        self.runner.side_effect=[(True,'baseline')]+[(False,'fail')]*3
        result=self.chat.turn('/continue')
        self.assertEqual(result['status'],'failed')
        self.assertEqual(self.target.read_text(),self.original)
        self.assertEqual(self.document.read_text(),'Make Thumby game.\n')
        self.assertEqual(list(self.game.glob('test_resume_*.py')),[])
        self.assertTrue((self.chat.folder/'resume_journal.json').exists())

    def test_two_file_transaction_restores_on_failure(self):
        plan=json.dumps({'goal':'Two files','files':['rules.py','scene_art.py'],'acceptance':'both changed'})
        candidate=self.candidate(files={'rules.py':'def step():\n    return 2\n','scene_art.py':'SCENE_BITMAPS=(1,)\n'})
        self.model.side_effect=[plan]+[candidate]*3
        self.runner.side_effect=[(True,'baseline')]+[(False,'fail')]*3
        self.chat.turn('/continue')
        self.assertEqual((self.game/'scene_art.py').read_text(),'SCENE_BITMAPS=()\n')
        self.assertEqual(self.target.read_text(),self.original)

    def test_external_editor_is_preserved_and_other_candidate_is_restored(self):
        self.model.side_effect=[self.plan,self.candidate()]
        calls=0
        def checker(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:self.target.write_text('# external editor\n')
            return True,'passed'
        self.runner.side_effect=checker
        with self.assertRaisesRegex(RuntimeError,'외부 변경'):self.chat.turn('/continue')
        self.assertEqual(self.target.read_text(),'# external editor\n')
        self.assertEqual(self.document.read_text(),'Make Thumby game.\n')

    def test_test_contract_external_change_is_never_restored(self):
        self.model.side_effect=[self.plan,self.candidate()]
        calls=0
        def checker(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:self.fixed.write_text('# external tests\n')
            return True,'passed'
        self.runner.side_effect=checker
        with self.assertRaisesRegex(RuntimeError,'외부 변경'):self.chat.turn('/continue')
        self.assertEqual(self.fixed.read_text(),'# external tests\n')
        self.assertEqual(self.target.read_text(),self.original)

    def test_dirty_file_and_missing_rules_block_before_model(self):
        self.target.write_text('# dirty\n')
        with self.assertRaisesRegex(RuntimeError,'기존 변경'):self.chat.turn('/continue')
        self.model.assert_not_called()
        self.target.write_text(self.original)
        with patch.object(game_resume,'internal_rules',side_effect=RuntimeError('missing rules')):
            with self.assertRaisesRegex(RuntimeError,'missing rules'):self.chat.turn('/continue')
        self.model.assert_not_called()

    def test_baseline_failure_never_generates_candidate(self):
        self.model.side_effect=[self.plan]
        self.runner.return_value=False,'baseline failed'
        self.assertEqual(self.chat.turn('/continue')['status'],'blocked')
        self.assertEqual(self.model.call_count,1)
        self.assertEqual(self.target.read_text(),self.original)

    def test_time_limit_stops_before_model(self):
        with patch.object(game_resume,'MAX_SECONDS',-1):
            with self.assertRaisesRegex(RuntimeError,'시간 상한'):self.chat.turn('/continue')
        self.model.assert_not_called()

    def test_unsafe_plan_or_candidate_paths_and_empty_checks_are_rejected(self):
        for files in (['../AGENTS.md'],['test_floor_movement.py'],['rules.py','rules.py']):
            with self.assertRaises(ValueError):
                game_resume.validate_plan({'goal':'g','acceptance':'a','files':files})
        with self.assertRaises(ValueError):
            game_resume.validate_candidate({'files':{'rules.py':self.original},'tests':'# no checks'},
                                           {'files':['rules.py']})

    def test_publication_error_preserves_verified_code_and_work(self):
        config=json.loads(self.config.read_text());config['resume_publish']=True
        self.config.write_text(json.dumps(config));self.git('add','.')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','publish config')
        self.model.side_effect=[self.plan,self.candidate()]
        # No author setup in the temporary repo: commit fails, checked changes survive.
        real=subprocess.run
        def run(command,**kwargs):
            if command[:2]==['git','commit']:
                raise subprocess.CalledProcessError(1,command)
            return real(command,**kwargs)
        with patch.object(game_resume.subprocess,'run',side_effect=run):
            with self.assertRaises(subprocess.CalledProcessError):self.chat.turn('/continue')
        self.assertIn('Return 2 from step',self.document.read_text())
        self.assertEqual(self.target.read_text(),'def step():\n    return 2\n')

    def test_successful_publication_commits_only_owned_files_and_pushes_expected_branch(self):
        config=json.loads(self.config.read_text());config['resume_publish']=True
        self.config.write_text(json.dumps(config));self.git('add','.')
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','publish config')
        self.git('config','user.name','Test');self.git('config','user.email','test@example.invalid')
        self.git('remote','add','origin','https://github.com/jihoonlabs/jihoon-projects.git')
        unrelated=self.root/'unrelated.txt';unrelated.write_text('keep local')
        self.model.side_effect=[self.plan,self.candidate()]
        real=subprocess.run;pushes=[]
        def run(command,**kwargs):
            if command[:2]==['git','push']:
                pushes.append(command)
                return subprocess.CompletedProcess(command,0,'','')
            return real(command,**kwargs)
        with patch.object(game_resume.subprocess,'run',side_effect=run):
            result=self.chat.turn('/continue')
        self.assertTrue(result['pushed'])
        self.assertEqual(result['commit'],self.git('rev-parse','HEAD').stdout.strip())
        self.assertEqual(pushes,[['git','push','origin','HEAD:refs/heads/test-epic']])
        changed=self.git('show','--pretty=format:','--name-only','HEAD').stdout
        self.assertNotIn('unrelated.txt',changed)
        self.assertEqual(unrelated.read_text(),'keep local')

    def test_resume_question_answer_preserves_original_request(self):
        self.model.side_effect=[json.dumps({'question':'범위 확인?'}),self.plan,self.candidate()]
        self.assertEqual(self.chat.turn('이어서 해')['status'],'waiting_for_user')
        self.assertEqual(self.chat.turn('기존 합의 범위로 해')['status'],'tests_passed')
        prompt=self.model.call_args_list[1].args[0]
        self.assertIn('이어서 해',prompt)
        self.assertIn('기존 합의 범위로 해',prompt)


if __name__=='__main__':unittest.main()
