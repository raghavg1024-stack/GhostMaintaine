import unittest
from app import repository_url


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
