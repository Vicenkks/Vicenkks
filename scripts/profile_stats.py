"""Publish aggregate statistics only; never persist repository names or API responses."""
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request

OWNER = 'Vicenkks'

def api(path, body=None):
    token = os.environ.get('PROFILE_STATS_TOKEN')
    if not token:
        raise RuntimeError('Add the PROFILE_STATS_TOKEN Actions secret before running.')
    request = urllib.request.Request('https://api.github.com' + path,
        data=json.dumps(body).encode() if body else None,
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-statistics'})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if isinstance(result, dict) and result.get('errors'):
        raise RuntimeError('GraphQL query failed. Check token permissions; statistics were not updated.')
    return result

def collect():
    user = api('/user')
    if user['login'].lower() != OWNER.lower():
        raise RuntimeError('The token must belong to Vicenkks.')
    repos = []
    page = 1
    while True:
        batch = api(f'/user/repos?affiliation=owner&per_page=100&page={page}')
        repos.extend(r for r in batch if r['owner']['login'].lower() == OWNER.lower())
        if len(batch) < 100:
            break
        page += 1
    languages = collections.Counter()
    for repo in repos:
        if not repo['fork']:
            languages.update(api('/repos/' + repo['full_name'] + '/languages'))
    now = dt.datetime.now(dt.timezone.utc)
    commits = 0
    query = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){totalCommitContributions}}}'''
    for year in range(int(user['created_at'][:4]), now.year + 1):
        end = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        variables = {'login': OWNER, 'from': f'{year}-01-01T00:00:00Z', 'to': end.strftime('%Y-%m-%dT%H:%M:%SZ')}
        commits += api('/graphql', {'query': query, 'variables': variables})['data']['user']['contributionsCollection']['totalCommitContributions']
    private = sum(r['private'] for r in repos)
    return len(repos) - private, private, commits, languages, now

def render(public, private, commits, languages, now):
    top = languages.most_common(10)
    height = 265 + 32 * len(top)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Vicenkks GitHub analytics</title>',
        '<desc id="desc">Aggregate statistics for repositories accessible to the configured token.</desc>',
        f'<rect width="800" height="{height}" rx="16" fill="#0d1117"/>',
        '<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#c9d1d9;font-size:14px}.title{fill:#e63946;font-size:22px;font-weight:bold}.value{fill:#fff;font-size:30px;font-weight:bold}.muted{fill:#8b949e;font-size:12px}</style>',
        '<text x="30" y="40" class="title">GITHUB // ANALYTICS</text>']
    for x, value, label in [(30, public, 'Public repos'), (280, private, 'Private repos'), (530, commits, 'Commit contributions¹')]:
        parts += [f'<text x="{x}" y="95" class="value">{value:,}</text>', f'<text x="{x}" y="122">{label}</text>']
    parts.append('<text x="30" y="166">LANGUAGES // CODE VOLUME · EXCLUDING FORKS</text>')
    total = sum(languages.values())
    for i, (name, size) in enumerate(top):
        y = 200 + 32 * i
        percent = size / total * 100
        parts += [f'<text x="30" y="{y}">{html.escape(name)}</text>',
            f'<rect x="200" y="{y-12}" width="450" height="12" rx="6" fill="#21262d"/>',
            f'<rect x="200" y="{y-12}" width="{450*percent/100:.2f}" height="12" rx="6" fill="#e63946"/>',
            f'<text x="740" y="{y}" text-anchor="end">{percent:.1f}%</text>']
    parts += [f'<text x="30" y="{height-55}" class="muted">Scope: owned repositories accessible to the token. Private names are never published.</text>',
        f'<text x="30" y="{height-35}" class="muted">¹ Since account creation, following GitHub contribution rules; not all branches.</text>',
        f'<text x="30" y="{height-15}" class="muted">Updated {now:%Y-%m-%d %H:%M} UTC</text>', '</svg>']
    return '\n'.join(parts)

if __name__ == '__main__':
    svg = render(*collect())
    Path('assets').mkdir(exist_ok=True)
    Path('assets/github-stats.svg').write_text(svg)
