import json
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import ghostmaintainer as gm


class PipelineTests(unittest.TestCase):
    def test_default_cli_evaluation_uses_rules_without_ollama(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(gm.sys,'argv',
            ['ghostmaintainer.py','eval',str(gm.ROOT/'fixtures'/'healthy'),'--backend','fixture','--out',folder]), \
            patch('urllib.request.urlopen',side_effect=AssertionError('Default evaluation must not contact Ollama')),redirect_stdout(StringIO()):
            self.assertEqual(gm.main(),0)
            result=json.loads((Path(folder)/'evaluation.json').read_text(encoding='utf-8'))
            self.assertEqual(result[0]['labeller'],'rules')

    def test_fixture_hash_uses_portable_filename_order(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            (repo / 'Z.md').write_bytes(b'upper')
            (repo / 'a.py').write_bytes(b'lower')
            expected = hashlib.sha256(b'Z.mduppera.pylower').hexdigest()
            self.assertEqual(gm.fixture_digest(repo), expected)

    def setUp(self):
        self.options = SimpleNamespace(backend=os.environ.get('GHOST_TEST_BACKEND', 'fixture'), net=False, labeller='rules')

    def test_repair_controls_and_minimality(self):
        for name in ('haunted_env', 'haunted_init', 'haunted_order', 'haunted_noise'):
            with self.subTest(name=name):
                report = gm.drill(gm.ROOT / 'fixtures' / name, self.options)
                self.assertEqual(report['status'], 'repaired')
                self.assertFalse(report['negative_control']['ok'])
                self.assertTrue(report['verification']['ok'])
                self.assertTrue(report['verification']['non_vacuous'])
                self.assertNotIn('deploy', report['diff'])
                self.assertNotIn('lint', report['diff'])
                self.assertTrue(all(p['source'].startswith('.github/') for p in report['patches']))

    def test_healthy_and_missing_secret(self):
        for name in ('healthy', 'healthy_minimal', 'healthy_noise'):
            report = gm.drill(gm.ROOT / 'fixtures' / name, self.options)
            self.assertEqual(report['status'], 'healthy')
            self.assertEqual(report['patches'], [])
        report = gm.drill(gm.ROOT / 'fixtures' / 'haunted_secret', self.options)
        self.assertEqual(report['status'], 'needs_human')
        self.assertNotIn('diff', report)

    def test_fixed_goal_catches_empty_extraction(self):
        report = gm.drill(gm.ROOT / 'fixtures' / 'haunted_env', self.options, '# No setup commands\n')
        self.assertFalse(report['original']['ok'])

    def test_marker_required(self):
        repo = gm.ROOT / 'fixtures' / 'healthy'
        result = gm.run(repo, gm.extract(gm.read(repo / 'README.md')),
                        {'cmd': 'python app.py lint', 'marker': 'NOT_PRESENT'}, 'fixture')
        self.assertFalse(result['ok'])

    def test_unknown_repo_cannot_use_host(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                gm.check_fixture(Path(directory))

    def test_static_baseline_misses_order_and_flags_noise(self):
        self.assertEqual(gm.baseline(gm.ROOT / 'fixtures' / 'haunted_order'), [])
        commands = [s['cmd'] for s in gm.baseline(gm.ROOT / 'fixtures' / 'healthy_noise')]
        self.assertIn('python app.py deploy', commands)

    def test_report_is_self_contained(self):
        report = gm.drill(gm.ROOT / 'fixtures' / 'haunted_env', self.options)
        with tempfile.TemporaryDirectory() as directory:
            gm.save_report(report, Path(directory))
            self.assertTrue((Path(directory) / 'README.patch').exists())
            self.assertEqual(json.loads(gm.read(Path(directory) / 'report.json'))['status'], 'repaired')

    def test_presentation_evidence_is_visible_and_escaped(self):
        report=gm.drill(gm.ROOT/'fixtures'/'haunted_env',self.options)
        report['assistant']={'diagnosis':{'diagnosis':'Missing initialization <script>bad</script>',
            'category':'documentation_gap','confidence':'high','evidence':['app.py:3'],
            'questions':['Which initialization mode?']},'calls':[{'model':'qwen','cached':False,'duration_s':1.2}]}
        page=gm.readable_report_html(report)
        for text in ('Repeated original instructions','Patched instructions in a fresh environment','Which initialization mode?',
                     'documentation_gap','app.py:3','fresh response','python app.py init','Documentation diff'):
            self.assertIn(text,page)
        self.assertNotIn('<script>bad</script>',page)
        self.assertNotIn('this run did not reach one',page)
        self.assertIn('Fresh verification: passed',gm.readable_report_markdown(report))

    def test_inconclusive_report_keeps_status_and_absent_stages_honest(self):
        report={'status':'inconclusive','repo':'demo','goal':{'cmd':'python -m pytest'},
                'original':{'ok':False,'status':'invalid_plan','events':[]},'reason':'Model plan rejected'}
        page=gm.readable_report_html(report)
        self.assertIn('INCONCLUSIVE',page)
        self.assertIn('Repeated original instructions · Not run',page)
        self.assertNotIn('>NOT TESTED<',page)

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND') == 'docker', 'Docker integration check')
    def test_docker_preserves_shell_state_and_captures_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / 'source'
            repo.mkdir()
            result = gm.run(repo, [{'cmd': 'export GHOST_STATE=retained'},
                                   {'cmd': 'mkdir child && cd child'},
                                   {'cmd': 'echo diagnostic >&2'}],
                            {'cmd': 'test "$GHOST_STATE" = retained && test "$PWD" = /workspace/child && echo STATE_OK', 'marker': 'STATE_OK'}, 'docker')
            self.assertTrue(result['ok'])
            self.assertIn('diagnostic', result['events'][2]['output'])

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND') == 'docker', 'Docker integration check')
    def test_missing_executable_is_environment_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / 'source'
            repo.mkdir()
            result = gm.run(repo, [{'cmd': 'ghost_nonexistent_executable'}],
                            {'cmd': 'echo OK', 'marker': 'OK'}, 'docker')
            self.assertEqual(result['status'], 'environment_blocked')
            self.assertFalse(result['ok'])

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND') == 'docker', 'Docker integration check')
    def test_missing_pytest_is_environment_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            result=gm.run(Path(directory),[],{'cmd':'python -m pytest -q'},'docker')
        self.assertEqual(result['status'],'environment_blocked')
        self.assertIn('No module named pytest',result['events'][-1]['output'])
        self.assertIn('not proof of a repository defect',result['reason'])

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND') == 'docker', 'Docker integration check')
    def test_network_disabled_dependency_error_is_environment_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            result=gm.run(Path(directory),[],{'cmd':"python -c \"import sys; print('Temporary failure in name resolution'); sys.exit(1)\""},'docker',False)
        self.assertEqual(result['status'],'environment_blocked')
        self.assertIn('networking is disabled',result['reason'])

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND') == 'docker', 'Docker Unicode check')
    def test_unicode_container_output(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / 'source'
            repo.mkdir()
            result = gm.run(repo, [], {'cmd': 'python -c "print(chr(0x1f47b))"', 'marker': '\U0001f47b'}, 'docker')
            self.assertTrue(result['ok'])


if __name__ == '__main__':
    unittest.main()
