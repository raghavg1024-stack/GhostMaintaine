import json
import unittest
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import assistant as a


class AssistantTests(unittest.TestCase):
    def test_setup_after_line_180_and_config_survive_large_readme(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'README.md').write_text(('Project history and release news.\n'*700)+'\n## Contributor setup\npython -m pip install -e .\npython -m pytest\n',encoding='utf-8')
            (repo/'pyproject.toml').write_text('[project]\nname="sample"\n',encoding='utf-8')
            files=a.context(repo,profile='low')
        self.assertIn('python -m pip install -e .',files['README.md'])
        self.assertIn('pyproject.toml',files)
        self.assertLessEqual(sum(map(len,files.values())),6000)
        a.citations(['README.md:703'],files)
        with self.assertRaises(ValueError):
            a.citations(['README.md:400'],files)
        steps=a.validate_plan({'steps':[{'cmd':'python -m pip install -e .','citations':['README.md:703']}]},files)
        self.assertEqual(steps[0]['source'],'README.md:703')

    def test_initial_plan_does_not_receive_full_large_document(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'README.md').write_text('history\n'*5000+'\nSetup: python -m pytest\n',encoding='utf-8')
            (repo/'ghostmaintainer.json').write_text('{"cmd":"python -m pytest"}',encoding='utf-8')
            options=SimpleNamespace(backend='docker',resource_profile='low',labeller='small',net=False)
            with patch.object(a,'plan',side_effect=ValueError('stop before execution')) as plan:
                report=a.run(repo,options)
            supplied=plan.call_args.args[0]
        self.assertLessEqual(sum(map(len,supplied.values())),6000)
        self.assertEqual(report['context']['planning_characters'],sum(map(len,supplied.values())))

    def test_failure_terms_retrieve_late_code_with_original_line_numbers(self):
        text='irrelevant details\n'*300+'raise RuntimeError("MISSING_CONFIG: run initialize")\n'
        selected=a.excerpt(text,400,query='MISSING_CONFIG')
        self.assertIn('MISSING_CONFIG',selected)
        self.assertIn('301: raise RuntimeError',a.numbered({'app.py':selected})['app.py'])

    def test_low_context_keeps_readme_and_respects_character_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'README.md').write_text('x'*20000,encoding='utf-8')
            files=a.context(repo,profile='low')
        self.assertIn('README.md',files)
        self.assertLessEqual(sum(map(len,files.values())),a.AI_PROFILES['low']['max_chars'])
        self.assertEqual(len(files['README.md']),a.AI_PROFILES['low']['max_chars'])

    def test_remote_safe_context_excludes_source_and_environment_files(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'README.md').write_text('Run tests with pytest.',encoding='utf-8')
            (repo/'pyproject.toml').write_text('[tool.pytest]\n',encoding='utf-8')
            (repo/'app.py').write_text('secret = "never send"',encoding='utf-8')
            (repo/'.env').write_text('PASSWORD=never-send',encoding='utf-8')
            files=a.context(repo,profile='low',remote_safe=True)
        self.assertIn('README.md',files)
        self.assertIn('pyproject.toml',files)
        self.assertNotIn('app.py',files)
        self.assertNotIn('.env',files)

    def test_low_model_request_uses_small_context_budget(self):
        response=BytesIO(b'{"response":"{\\"ok\\": true}"}')
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'.cache').mkdir()
            with patch.object(a.gm,'ROOT',Path(folder)),patch('urllib.request.urlopen',return_value=response) as fetch:
                result,meta=a.ask('test-profile-context','tiny prompt',{},profile='low')
        payload=json.loads(fetch.call_args.args[0].data)
        self.assertEqual(payload['options']['num_ctx'],4096)
        self.assertEqual(payload['options']['num_predict'],800)
        self.assertEqual(meta['resource_profile'],'low')
        self.assertEqual(meta['context_tokens'],4096)

    def test_remote_failure_evidence_is_trimmed_and_redacts_common_secrets(self):
        answer={'diagnosis':'Missing credential','category':'needs_credentials','confidence':'low','evidence':[],'questions':[],'edits':[]}
        failure={'status':'failed','reason':'failed','events':[{'cmd':'run','exit_code':1,'output':'x'*900+' token=supersecret'}]}
        with patch.object(a,'ask',return_value=(answer,{})) as model:
            a.propose({'README.md':'Install and test.'},{'README.md':'Install and test.'},failure,{'cmd':'pytest'},'small',profile='low',remote=True)
        sent=model.call_args.args[2]['failure']['events'][0]['output']
        self.assertLessEqual(len(sent),800)
        self.assertNotIn('supersecret',sent)
        self.assertIn('[REDACTED]',sent)

    def test_invalid_repair_returns_unverified_report(self):
        failure={'ok':False,'status':'failed','events':[{'cmd':'python app.py test','exit_code':1,'output':'missing config','goal':False}]}
        options=SimpleNamespace(backend='docker',labeller='test-model',net=False,image='python:3.12-slim')
        with patch.object(a,'plan',return_value=([{'cmd':'python app.py test'}],{'summary':'test'}, {'cached':False})),patch.object(a.gm,'run',return_value=failure),patch.object(a,'propose',side_effect=ValueError('bad patch')):
            report=a.run(a.gm.ROOT/'fixtures'/'haunted_env',options)
        self.assertEqual(report['status'],'needs_human')
        self.assertFalse(report['assistant']['proposal_verified'])
        self.assertNotIn('diff',report)
        self.assertIn('bad patch',report['assistant']['validation_error'])

    def test_plan_corrects_invalid_citation_once(self):
        invalid={'steps':[{'cmd':'python check.py','citations':['missing.md:1']}]}
        valid={'steps':[{'cmd':'python check.py','citations':['README.md:1']}]}
        with patch.object(a,'ask',side_effect=[(invalid,{}),(valid,{'cached':False})]) as ask:
            steps,_,_=a.plan({'README.md':'python check.py'},'test-model')
        self.assertEqual(steps[0]['cmd'],'python check.py')
        self.assertEqual(ask.call_count,2)
        self.assertIn('Previous response was rejected',ask.call_args.args[1])

    def test_invalid_initial_plan_returns_report_without_execution(self):
        options=SimpleNamespace(backend='docker',labeller='test-model',net=False)
        with patch.object(a,'plan',side_effect=ValueError('bad citation')),patch.object(a.gm,'run') as execute:
            report=a.run(a.gm.ROOT/'fixtures'/'haunted_env',options)
        execute.assert_not_called()
        self.assertEqual(report['status'],'inconclusive')
        self.assertEqual(report['original']['status'],'invalid_plan')
        self.assertNotIn('diff',report)
        with tempfile.TemporaryDirectory() as folder:
            a.gm.save_report(report,Path(folder))
            self.assertTrue((Path(folder)/'replay.html').exists())

    def test_blocked_runner_does_not_request_a_documentation_repair(self):
        options=SimpleNamespace(backend='docker',labeller='test-model',net=False)
        failure={'ok':False,'status':'environment_blocked','events':[], 'reason':'pytest unavailable'}
        with patch.object(a,'plan',return_value=([],{}, {'cached':False})),patch.object(a.gm,'run',return_value=failure),patch.object(a,'propose') as propose:
            report=a.run(a.gm.ROOT/'fixtures'/'haunted_env',options)
        propose.assert_not_called()
        self.assertEqual(report['status'],'inconclusive')

    def test_invalid_verification_plan_cannot_escape_or_publish_patch(self):
        options=SimpleNamespace(backend='docker',labeller='test-model',net=False)
        failure={'ok':False,'status':'failed','events':[{'cmd':'python app.py test','exit_code':1,'output':'missing config'}]}
        diagnosis={'category':'documentation_gap','edits':[]}
        with patch.object(a,'plan',side_effect=[([],{}, {'cached':False}),ValueError('bad verification citation')]),patch.object(a.gm,'run',return_value=failure),patch.object(a,'propose',return_value=({'README.md':'changed'},diagnosis,{})):
            report=a.run(a.gm.ROOT/'fixtures'/'haunted_env',options)
        self.assertEqual(report['status'],'inconclusive')
        self.assertFalse(report['assistant']['proposal_verified'])
        self.assertNotIn('diff',report)
        self.assertIn('bad verification citation',report['assistant']['validation_error'])

    def test_guessed_install_is_not_supported_by_an_unrelated_valid_citation(self):
        answer={'steps':[{'cmd':'pip install click','citations':['README.md:1']}]}
        with patch.object(a,'ask',return_value=(answer,{})),self.assertRaisesRegex(ValueError,'Installation command is not present'):
            a.plan({'README.md':'import click'},'test-model')

    def test_citation_ranges(self):
        a.citations(['README.md:1-2'],{'README.md':'one\ntwo'})
        with self.assertRaises(ValueError):
            a.citations(['README.md:1-3'],{'README.md':'one\ntwo'})

    def test_indentation_only_context_matching(self):
        docs={'README.md':'Setup:\n\n   ```sh\n   python test.py\n   ```\n'}
        answer={'category':'documentation_gap','edits':[{'file':'README.md','old':'    ```sh\n    python test.py\n    ```','new':'```sh\npython init.py\npython test.py\n```','citations':['Makefile:1']}]}
        with patch.object(a,'ask',return_value=(answer,{})):
            patched,_,_=a.propose({**docs,'Makefile':'init: python init.py'},docs,{},{},'test-model')
        self.assertIn('python init.py',patched['README.md'])

    def test_prose_interpretation_has_real_receipts(self):
        files={'README.md':'Run the check with `python check.py`.'}
        answer={'summary':'Run the documented check','steps':[{'cmd':'python check.py','citations':['README.md:1'],'reason':'inline instruction'}],'questions':[]}
        with patch.object(a,'ask',return_value=(answer,{'cached':False})):
            steps,_,_=a.plan(files,'test-model')
        self.assertEqual(steps[0]['cmd'],'python check.py')

    def test_bad_citation_and_unsafe_command_rejected(self):
        for command,ref in [('python check.py','README.md:99'),('sudo apt install x','README.md:1')]:
            answer={'steps':[{'cmd':command,'citations':[ref]}]}
            with patch.object(a,'ask',return_value=(answer,{})),self.assertRaises(ValueError):
                a.plan({'README.md':'test'},'test-model')

    def test_only_exact_documentation_edits_allowed(self):
        files={'README.md':'Run tests.','Makefile':'test: python check.py'}
        for filename,old in [('app.py','Run tests.'),('README.md','not present')]:
            answer={'category':'documentation_gap','edits':[{'file':filename,'old':old,'new':'changed','citations':['Makefile:1']}]}
            with patch.object(a,'ask',return_value=(answer,{})),self.assertRaises(ValueError):
                a.propose(files,{'README.md':'Run tests.'},{},{},'test-model')

    def test_patch_preserves_unrelated_documentation(self):
        docs={'README.md':'Title\nRun tests.\nPreserve this section.\n'}
        answer={'category':'documentation_gap','edits':[{'file':'README.md','old':'Run tests.','new':'First initialize. Then run tests.','citations':['Makefile:1']}]}
        with patch.object(a,'ask',return_value=(answer,{})):
            result,_,_=a.propose({**docs,'Makefile':'init: python init.py'},docs,{},{},'test-model')
        self.assertIn('Preserve this section.',result['README.md'])
