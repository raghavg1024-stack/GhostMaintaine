import unittest
from app import repository_url
from unittest.mock import patch


class URLTests(unittest.TestCase):
    def test_public_repo(self):
        self.assertEqual(repository_url('https://github.com/owner/repository'), 'https://github.com/owner/repository.git')
        self.assertEqual(repository_url('https://github.com/owner/repository.git/'), 'https://github.com/owner/repository.git')

    def test_reject_local_and_nonrepository_urls(self):
        for url in ('file:///etc/passwd', 'http://127.0.0.1/repo', 'https://github.com.evil.test/a/b',
                    'https://name:password@github.com/a/b', 'https://github.com/a/b/tree/main',
                    'https://github.com/a/..', 'https://github.com/a/b?token=secret'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                repository_url(url)


class APIPermissionTests(unittest.TestCase):
    def test_prepare_and_network_flags_are_checked_at_http_boundary(self):
        import app
        for extra in ({'prepare':True,'network':False},{'prepare':'true','network':True},{'no_cache':'false'},{'auto_pr':'true'},{'auto_pr':True,'mode':'drift'}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                app.validate_request_flags(extra)

    def test_resource_profile_and_remote_consent_are_validated(self):
        import app
        with self.assertRaisesRegex(ValueError,'resource mode'):
            app.validate_request_flags({'resource_profile':'unbounded'})
        with patch('app.ollama_config',return_value=('https://ollama.example',True,'https://ollama.example')):
            with self.assertRaisesRegex(ValueError,'Explicit consent'):
                app.validate_request_flags({'mode':'assist','resource_profile':'low','remote_ai':False})
            app.validate_request_flags({'mode':'assist','resource_profile':'low','remote_ai':True})

    def test_remote_health_consent_needs_the_current_session_token(self):
        import app
        with self.assertRaisesRegex(ValueError,'session token'):
            app.validate_remote_health_consent(True,'not-the-session-token')
        app.validate_remote_health_consent(True,app.TOKEN)
        app.validate_remote_health_consent(False,None)
