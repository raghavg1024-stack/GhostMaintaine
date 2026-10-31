import difflib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import repair_pr as repair


class RepairPublicationTests(unittest.TestCase):
    def report(self):
        before='python app.py test\n';after='python app.py init\npython app.py test\n'
        return {'repo':'https://github.com/owner/demo','revision':'a'*40,'status':'repaired',
            'original':{'ok':False},'negative_control':{'ok':False},'verification':{'ok':True,'non_vacuous':True},
            'goal':{'cmd':'python app.py test'},'patched_readme':after,
            'diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/README.md',tofile='b/README.md'))}

    def test_no_network_without_opt_in_or_verified_repair(self):
        with patch.object(repair,'api') as api:
            self.assertEqual(repair.publish(Path('.'),self.report())['status'],'disabled')
            for update in ({'status':'needs_human'},{'verification':{'ok':False}}, {'negative_control':{'ok':True}}, {'original':{'ok':True}}):
                self.assertEqual(repair.publish(Path('.'),{**self.report(),**update},True)['status'],'skipped')
            api.assert_not_called()

    def test_scope_and_diff_mismatch_block_publication(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'GHOST_GITHUB_TOKEN':'test-only'}),patch.object(repair,'api') as api:
            repo=Path(folder);(repo/'README.md').write_text('python app.py test\n',encoding='utf-8')
            report=self.report();report['diff']='different diff'
            with self.assertRaisesRegex(ValueError,'exactly match'):repair.publish(repo,report,True)
            report=self.report();report['patched_documents']={'../README.md':'unsafe'}
            with self.assertRaisesRegex(ValueError,'Markdown'):repair.publish(repo,report,True)
            api.assert_not_called()

    def test_publish_new_branch_and_pr_without_default_branch_update(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'GHOST_GITHUB_TOKEN':'test-only'}),patch.object(repair.subprocess,'check_output',return_value='a'*40),patch.object(repair,'api') as api:
            repo=Path(folder);(repo/'README.md').write_text('python app.py test\n',encoding='utf-8')
            api.side_effect=[{'permissions':{'push':True},'default_branch':'main'}, {'object':{'sha':'a'*40}},
                {'tree':{'sha':'base-tree'}},{'sha':'new-tree'},{'sha':'new-commit'},{}, {'html_url':'https://github.com/owner/demo/pull/1'}]
            result=repair.publish(repo,self.report(),True)
            self.assertEqual(result['status'],'pr_created')
            self.assertTrue(api.call_args_list[5].args[3]['ref'].startswith('refs/heads/ghostmaintainer/'))
            self.assertEqual(api.call_args_list[6].args[3]['base'],'main')
            self.assertNotIn('PATCH',[c.args[0] for c in api.call_args_list])

    def test_changed_default_branch_blocks_remote_mutations(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'GHOST_GITHUB_TOKEN':'test-only'}),patch.object(repair.subprocess,'check_output',return_value='a'*40),patch.object(repair,'api',side_effect=[{'permissions':{'push':True},'default_branch':'main'},{'object':{'sha':'b'*40}}]) as api:
            repo=Path(folder);(repo/'README.md').write_text('python app.py test\n',encoding='utf-8')
            self.assertEqual(repair.publish(repo,self.report(),True)['status'],'blocked')
            self.assertTrue(all(c.args[0]=='GET' for c in api.call_args_list))
