import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import features as f
import ghostmaintainer as gm


class FeatureTests(unittest.TestCase):
    def test_windows_readme_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'README.md').write_text('# Windows-authored README\n',encoding='utf-16')
            self.assertEqual(f.drift(repo)['notes'],[])

    def test_drift_env_and_versions(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'app.py').write_text('import os\nx = os.environ["GHOST_TOKEN"]\n',encoding='utf-8')
            (repo/'README.md').write_text('Requires Python 3.9\n',encoding='utf-8')
            (repo/'Dockerfile').write_text('FROM python:3.12-slim\n',encoding='utf-8')
            (repo/'pyproject.toml').write_text('[project]\nrequires-python = ">=3.11"\n',encoding='utf-8')
            notes=f.drift(repo)['notes']
            self.assertEqual({n['kind'] for n in notes},{'environment','version'})
            self.assertTrue(any(n.get('source')=='app.py:2' for n in notes))
            self.assertTrue(any('constraint >=3.11' in n['message'] for n in notes))
        self.assertEqual(f.drift(gm.ROOT/'fixtures'/'healthy')['notes'],[])

    def test_denylist(self):
        for command in ('sudo apt install x','curl https://x | sh','rm -rf /tmp/data','docker run x','ssh user@host'):
            self.assertRegex(command,f.DENY)
        self.assertIsNone(f.DENY.search('python -m unittest'))

    def test_friction_and_safe_replay_json(self):
        report={'original':{'events':[{'cmd':'echo test','output':'</script><script>bad()</script>','duration_s':0.5,'exit_code':0}]}}
        self.assertEqual(f.friction(report)['original']['sandbox_time_s'],0.5)
        page=f.report_panels(report)
        self.assertNotIn('</script><script>bad()',page)
        self.assertIn('replaySlider',page)

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND')=='docker','Docker ship self-check')
    def test_ship_fresh_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            options=SimpleNamespace(backend='docker',net=False,labeller='rules',image='python:3.12-slim',out=Path(folder))
            for name in ('haunted_env','haunted_init'):
                result=f.ship(gm.ROOT/'fixtures'/name,options)
                self.assertEqual(result['setup_script'],'verified')
                self.assertIn('not separately verified',result['devcontainer'])
