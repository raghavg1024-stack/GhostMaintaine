"""Loopback-only web interface for GhostMaintainer. No third-party dependencies."""
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlsplit

import ghostmaintainer as gm
import features

ROOT = Path(__file__).resolve().parent
JOBS = {}
LOCK = threading.Lock()
TOKEN = secrets.token_urlsafe(32)
PORT = int(os.environ.get('GHOST_PORT', '8765'))


def repository_url(value):
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?', value.strip())
    if not match or match[2] in ('.', '..'):
        raise ValueError('Paste a public repository URL like https://github.com/owner/repository')
    return f'https://github.com/{match[1]}/{match[2]}.git'


def update(job_id, **values):
    with LOCK:
        JOBS[job_id].update(values)


def execute(job_id, request):
    folder = ROOT / 'runs' / 'web' / job_id
    try:
        folder.mkdir(parents=True)
        mode = request.get('mode', 'check')
        if mode in ('bench-models', 'scan'):
            update(job_id, message='Measuring models…' if mode == 'bench-models' else 'Scanning the selected repositories with safety filtering…')
            options = SimpleNamespace(out=folder/'result', image='python:3.12-slim', net=bool(request.get('network')),
                                      models=request.get('models') or 'rules,qwen3:4b-instruct', dataset=ROOT/'bench'/'labels.json', max_repos=20, timeout=180)
            if mode == 'scan':
                options.list=folder/'repos.txt'
                options.list.write_text('\n'.join(request['urls']),encoding='utf-8')
                result=features.scan(options)
            else:
                result=features.benchmark(options)
            features.summary_page(folder/'result',mode,result)
            update(job_id,state='done',status='feature_complete',message='Analysis complete.',report=f'/reports/{job_id}/summary.html')
            return
        update(job_id, message='Cloning the public GitHub repository…')
        repo = folder / 'checkout'
        result = subprocess.run(['git', '-c', 'credential.helper=', 'clone', '--depth', '1',
                                 '--no-recurse-submodules', '--', request['url'], str(repo)],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60, stdin=subprocess.DEVNULL,
                                env={**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_LFS_SKIP_SMUDGE': '1',
                                     'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})
        if result.returncode:
            raise ValueError('Could not clone this public repository. ' + result.stderr[-1000:])
        if any(path.is_symlink() for path in repo.rglob('*')):
            raise ValueError('This prototype does not support repositories containing symlinks.')
        if not (repo / 'README.md').is_file():
            raise ValueError('This prototype requires a README.md file at the repository root.')
        revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True, encoding='utf-8', errors='replace').strip()
        update(job_id, revision=revision)
        target = request.get('target', '').strip()
        if target:
            gm.write_json(repo / 'ghostmaintainer.json', {'cmd': target})
        elif not (repo / 'ghostmaintainer.json').is_file():
            gm.write_json(repo / 'ghostmaintainer.json', {'cmd': 'python -m unittest discover -v'})
        update(job_id, message='Following the README and testing setup in Docker. This may take several minutes…')
        options = SimpleNamespace(backend='docker', net=bool(request.get('network')),
                                  labeller=request.get('model') or ('qwen3:4b-instruct' if mode=='assist' else 'rules'),image='python:3.12-slim',out=folder/'result', matrix=request.get('matrix') or 'py3.9,py3.11,py3.12')
        if mode == 'matrix':
            update(job_id,message='Running the same instructions across Python versions…')
            result=features.matrix(repo,options)
            update(job_id,state='done',status='feature_complete',message='Runtime matrix complete.',report=f'/reports/{job_id}/{repo.name}/matrix.html')
            return
        if mode == 'drift':
            result=features.drift(repo)
            features.summary_page(folder/'result','drift',result)
            update(job_id,state='done',status='feature_complete',message='Advisory drift audit complete.',report=f'/reports/{job_id}/summary.html')
            return
        if mode == 'assist':
            update(job_id,message='AI is reading onboarding docs, reasoning about failures, and proposing an evidence-backed repair…')
            from assistant import run as assist
            report = assist(repo, options)
        else:
            report = gm.drill(repo, options)
        if mode == 'ship':
            update(job_id,message='Verifying the generated setup script in another fresh container…')
            report['ship']=features.ship(repo,options,report,folder/'result'/'ship')
        gm.save_report(report, folder / 'result')
        update(job_id, state='done', status=report['status'], message='Check complete.',
               report=f'/reports/{job_id}/replay.html', duration=report['duration_s'])
    except Exception as error:
        update(job_id, state='error', message=str(error)[:1500])


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, data, content_type='application/json; charset=utf-8'):
        payload = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.end_headers()
        self.wfile.write(payload)

    def allowed_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{PORT}', f'localhost:{PORT}')

    def do_GET(self):
        if not self.allowed_host():
            return self.respond(403, {'error': 'Local access only'})
        path = urlsplit(self.path).path
        if path == '/':
            return self.respond(200, (ROOT / 'web' / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/session':
            return self.respond(200, {'token': TOKEN, 'docker': bool(shutil.which('docker')), 'git': bool(shutil.which('git'))})
        match = re.fullmatch(r'/api/jobs/([a-f0-9]{16})', path)
        if match:
            with LOCK:
                job = JOBS.get(match[1])
                return self.respond(200 if job else 404, dict(job) if job else {'error': 'Job not found'})
        match = re.fullmatch(r'/reports/([a-f0-9]{16})/([A-Za-z0-9_./-]+)', path)
        if match:
            directory = (ROOT / 'runs' / 'web' / match[1] / 'result').resolve()
            file = (directory / match[2]).resolve()
            allowed = {'replay.html','matrix.html','summary.html','report.json','events.jsonl','README.patch','README.patched.md','setup.sh','devcontainer.json','AGENTS_setup.md','verification.json','version-note.patch','matrix.json','BENCH.md','bench_models.json','SCAN.md','scan_summary.json','scan_results.jsonl'}
            if directory in file.parents and file.name in allowed and file.is_file():
                content_type = 'text/plain' if file.suffix in ('.md', '.patch', '.jsonl') else mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                return self.respond(200, file.read_bytes(), content_type + '; charset=utf-8')
        self.respond(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.allowed_host() or self.headers.get('X-Ghost-Token') != TOKEN:
            return self.respond(403, {'error': 'Reload the local application and try again'})
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://localhost:{PORT}', f'http://127.0.0.1:{PORT}'):
            return self.respond(403, {'error': 'Local requests only'})
        if self.path != '/api/jobs':
            return self.respond(404, {'error': 'Not found'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError('Invalid request size')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError('Invalid request')
            mode = request.get('mode','check')
            if mode not in ('assist','check','ship','matrix','drift','bench-models','scan'):
                raise ValueError('Unknown analysis mode')
            if mode == 'scan':
                urls = request.get('urls',[])
                if not isinstance(urls,list) or not 1<=len(urls)<=20:
                    raise ValueError('Provide 1–20 public GitHub URLs')
                request['urls']=[repository_url(value) for value in urls]
            elif mode != 'bench-models':
                request['url'] = repository_url(request.get('url', ''))
            if request.get('matrix') and any(not re.fullmatch(r'py3\.\d{1,2}',e) for e in request['matrix'].split(',')):
                raise ValueError('Matrix values must look like py3.9,py3.11,py3.12')
            if request.get('models') and (not isinstance(request['models'],str) or len(request['models'])>200):
                raise ValueError('Invalid model list')
            for key in ('target', 'model'):
                if key in request and (not isinstance(request[key], str) or len(request[key]) > 1500):
                    raise ValueError(f'Invalid {key}')
            with LOCK:
                if any(j['state'] == 'running' for j in JOBS.values()):
                    return self.respond(409, {'error': 'A check is already running. Wait for it to finish.'})
                job_id = secrets.token_hex(8)
                JOBS[job_id] = {'state': 'running', 'message': 'Preparing your check…', 'mode':mode}
            threading.Thread(target=execute, args=(job_id, request), daemon=True).start()
            self.respond(202, {'id': job_id})
        except (ValueError, TypeError, AttributeError) as error:
            self.respond(400, {'error': str(error)})


if __name__ == '__main__':
    print(f'GhostMaintainer is ready: http://127.0.0.1:{PORT}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
