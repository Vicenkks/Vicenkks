import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import profile_stats as stats


class CommitTests(unittest.TestCase):
    def test_all_branches_pagination_forks_and_extra_email(self):
        calls = []
        def fake(path):
            url = urlsplit(path)
            q = parse_qs(url.query)
            calls.append((url.path, q))
            if url.path.endswith('/branches'):
                return [{'commit': {'sha': 'main-tip'}}, {'commit': {'sha': 'feature-tip'}}]
            if q['author'] == ['old@example.test']:
                return [{'sha': 'old-email-commit'}]
            if q['sha'] == ['feature-tip']:
                return [{'sha': '0'}, {'sha': 'feature-only'}]
            if q['page'] == ['1']:
                return [{'sha': str(i)} for i in range(100)]
            return [{'sha': 'page-two'}]
        with patch.object(stats, 'api', side_effect=fake), patch.dict(os.environ, {'COMMIT_EMAILS': 'old@example.test'}):
            self.assertEqual(stats.count_commits([{'full_name': 'Vicenkks/repo'}, {'full_name': 'team/fork'}]), 103)
        self.assertTrue(any(q.get('page') == ['2'] for _, q in calls))
        self.assertTrue(any(q.get('sha') == ['feature-tip'] for _, q in calls))

    def test_empty_repository(self):
        with patch.object(stats, 'api', return_value=[]):
            self.assertEqual(stats.count_commits([{'full_name': 'Vicenkks/empty'}]), 0)

    def test_failure_does_not_return_partial_count(self):
        with patch.object(stats, 'api', side_effect=RuntimeError('API unavailable')):
            with self.assertRaises(RuntimeError):
                stats.count_commits([{'full_name': 'Vicenkks/repo'}])


if __name__ == '__main__':
    unittest.main()
