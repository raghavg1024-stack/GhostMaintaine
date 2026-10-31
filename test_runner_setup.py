import json
import os
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ghostmaintainer as gm
from runner_setup import AI_PROFILES,dependency_plan,default_goal,health,ollama_config


class SetupTests(unittest.TestCase):
    def test_resource_profiles_are_bounded_and_have_expected_defaults(self):
        self.assertEqual(AI_PROFILES['low']['model'],'qwen3:1.7b')
        self.assertEqual(AI_PROFILES['low']['num_ctx'],4096)
        self.assertEqual(AI_PROFILES['low']['max_chars'],6000)
        self.assertEqual(AI_PROFILES['balanced']['num_ctx'],8192)
        self.assertEqual(AI_PROFILES['rules']['num_ctx'],0)

    def test_remote_ollama_requires_https_and_rejects_credentials_in_url(self):
        with patch.dict(os.environ,{'GHOST_OLLAMA_URL':'https://ollama.example:11434/base'}):
            self.assertEqual(ollama_config(),('https://ollama.example:11434/base',True,'https://ollama.example:11434'))
        for value in ('http://ollama.example:11434','https://user:pass@ollama.example','https://ollama.example?token=x'):
            with patch.dict(os.environ,{'GHOST_OLLAMA_URL':value}),self.subTest(value=value),self.assertRaises(ValueError):
                ollama_config()

    def test_remote_health_does_not_contact_endpoint_before_consent(self):
        with patch.dict(os.environ,{'GHOST_OLLAMA_URL':'https://ollama.example:11434'}),patch('runner_setup.find_docker',return_value=None),patch('urllib.request.urlopen') as fetch:
            result=health('qwen3:1.7b')
        fetch.assert_not_called()
        self.assertTrue(result['remote_configured'])
        self.assertTrue(result['remote_consent_required'])
        self.assertFalse(result['model_installed'])

    def test_remote_health_uses_authorization_only_after_consent(self):
        response=BytesIO(b'{"models":[{"name":"qwen3:1.7b"}]}')
        with patch.dict(os.environ,{'GHOST_OLLAMA_URL':'https://ollama.example:11434','GHOST_OLLAMA_API_KEY':'test-key'}),patch('runner_setup.find_docker',return_value=None),patch('urllib.request.urlopen',return_value=response) as fetch:
            result=health('qwen3:1.7b',remote_consent=True)
        request=fetch.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'),'Bearer test-key')
        self.assertTrue(result['model_installed'])

    def test_declared_dependencies_and_nested_groups_have_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            (repo/'pyproject.toml').write_text('[build-system]\nrequires=["flit_core<4"]\n[dependency-groups]\nbase=["pytest>=8"]\ntests=[{include-group="base"},"freezegun"]\n',encoding='utf-8')
            steps=dependency_plan(repo)
            self.assertIn("'flit_core<4'",steps[0]['cmd'])
            self.assertIn("'pytest>=8'",steps[0]['cmd'])
            self.assertIn('freezegun',steps[0]['cmd'])
            self.assertTrue(all(step['source'].startswith('pyproject.toml:') for step in steps))
            self.assertIn('--no-build-isolation -e .',steps[-1]['cmd'])

    def test_cycle_and_package_option_injection_are_rejected(self):
        for contents in ('[dependency-groups]\ntests=[{include-group="tests"}]','[dependency-groups]\ntests=["--index-url=evil"]'):
            with self.subTest(contents=contents), tempfile.TemporaryDirectory() as folder:
                repo=Path(folder);(repo/'pyproject.toml').write_text(contents,encoding='utf-8')
                with self.assertRaises(ValueError): dependency_plan(repo)

    def test_project_goal_is_not_overridden_by_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder);(repo/'pyproject.toml').write_text('[tool.pytest.ini_options]\n',encoding='utf-8')
            self.assertEqual(default_goal(repo),'python -m pytest -q')
            (repo/'ghostmaintainer.json').write_text(json.dumps({'cmd':'python custom_check.py'}),encoding='utf-8')
            self.assertEqual(default_goal(repo),'python custom_check.py')

    def test_preparation_cannot_enable_network_implicitly(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(gm.shutil,'which',return_value='docker'),patch.object(gm.subprocess,'run') as execute:
            with self.assertRaisesRegex(ValueError,'explicit network permission'):
                gm.run(Path(folder),[],{'cmd':'python -m pytest'},preparation=[{'cmd':'python -m pip install pytest','source':'pyproject.toml:1'}])
            execute.assert_not_called()

    @unittest.skipUnless(os.environ.get('GHOST_TEST_BACKEND')=='docker','Docker integration')
    def test_preparation_events_and_failures_are_separate_from_docs(self):
        with tempfile.TemporaryDirectory() as folder:
            result=gm.run(Path(folder),[],{'cmd':'python -c "print(123)"'},network=True,preparation=[{'cmd':'python -c "raise SystemExit(3)"','source':'pyproject.toml:1'}])
        self.assertEqual(result['status'],'environment_blocked')
        self.assertEqual(result['events'][0]['stage'],'preparation')
        self.assertFalse(result['events'][0]['goal'])
        self.assertEqual(result['events'][0]['source'],'pyproject.toml:1')

if __name__=='__main__': unittest.main()
