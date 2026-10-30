import unittest
from types import SimpleNamespace
from unittest.mock import patch
import assistant as a


class AssistantTests(unittest.TestCase):
    def test_invalid_repair_returns_unverified_report(self):
        failure={'ok':False,'status':'failed','events':[{'cmd':'python app.py test','exit_code':1,'output':'missing config','goal':False}]}
        options=SimpleNamespace(backend='docker',labeller='test-model',net=False,image='python:3.12-slim')
        with patch.object(a,'plan',return_value=([{'cmd':'python app.py test'}],{'summary':'test'}, {'cached':False})),patch.object(a.gm,'run',return_value=failure),patch.object(a,'propose',side_effect=ValueError('bad patch')):
            report=a.run(a.gm.ROOT/'fixtures'/'haunted_env',options)
        self.assertEqual(report['status'],'needs_human')
        self.assertFalse(report['assistant']['proposal_verified'])
        self.assertNotIn('diff',report)
        self.assertIn('bad patch',report['assistant']['validation_error'])

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
