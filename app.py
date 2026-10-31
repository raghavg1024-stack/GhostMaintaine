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
from urllib.parse import urlsplit, parse_qs

import ghostmaintainer as gm
import features
from runner_setup import AI_PROFILES, find_docker, ollama_config

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


def validate_request_flags(request):
    """Validate safety-related request flags without requiring an HTTP server."""
    for key in ('network', 'prepare', 'no_cache', 'remote_ai', 'auto_pr'):
        if key in request and type(request[key]) is not bool:
            raise ValueError(f'{key} must be a boolean')
    if request.get('prepare') and not request.get('network'):
        raise ValueError('Dependency preparation requires explicit container network permission')
    profile=request.get('resource_profile','balanced')
    if request.get('auto_pr') and request.get('mode') not in ('assist','check'):
        raise ValueError('Automatic repair PRs apply only to assistant and README verification modes')
    if not isinstance(profile,str) or profile not in AI_PROFILES:
        raise ValueError('Choose low, balanced, or rules-only resource mode')
    if request.get('mode')=='assist' and profile!='rules':
        remote=ollama_config()[1]
        if remote and not request.get('remote_ai'):
            raise ValueError('Remote Ollama is configured. Explicit consent is required before sending setup data.')
    if request.get('remote_ai'):
        if request.get('mode')!='assist' or profile=='rules':
            raise ValueError('Remote inference consent applies only to AI assistant mode')
        if not ollama_config()[1]:
            raise ValueError('Remote inference requires a configured HTTPS GHOST_OLLAMA_URL')


def validate_remote_health_consent(remote_consent, token):
    if remote_consent and not secrets.compare_digest(str(token or ''), TOKEN):
        raise ValueError('Remote readiness checks require this local app session token')


def update(job_id, **values):
    with LOCK:
        JOBS[job_id].update(values)


def execute(job_id, request):
    folder = ROOT / 'runs' / 'web' / job_id
    try:
        folder.mkdir(parents=True)
        mode = request.get('mode', 'check')
        profile=request.get('resource_profile','balanced')
        if mode=='assist' and profile=='rules':
            mode='check'
        update(job_id,mode=mode,resource_profile=profile)
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
        from runner_setup import default_goal
        target = request.get('target', '').strip()
        if target:
            gm.write_json(repo / 'ghostmaintainer.json', {'cmd': target})
        elif not (repo / 'ghostmaintainer.json').is_file():
            gm.write_json(repo / 'ghostmaintainer.json', {'cmd': default_goal(repo)})
        update(job_id, message='Following the README and testing setup in Docker. This may take several minutes…')
        default_model=AI_PROFILES[profile]['model']
        if profile=='balanced' and os.environ.get('GHOST_MODEL'):
            default_model=os.environ['GHOST_MODEL']
        options = SimpleNamespace(backend='docker', net=bool(request.get('network')),
                                  labeller=request.get('model') or (default_model if mode=='assist' else 'rules'),image=os.environ.get('GHOST_IMAGE','python:3.12-slim'),prepare=request.get('prepare',False),no_cache=request.get('no_cache',False),resource_profile=profile,remote_consent=request.get('remote_ai',False),progress=lambda message:update(job_id,message=message),out=folder/'result', matrix=request.get('matrix') or 'py3.9,py3.11,py3.12')
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
        report['repo']=request['url'].removesuffix('.git')
        report['revision']=revision
        if request.get('auto_pr'):
            update(job_id,message='Publishing the verified documentation repair to a new branch and pull request…')
            from repair_pr import publish
            try:
                report['automation']=publish(repo,report,requested=True)
            except (OSError,ValueError,subprocess.SubprocessError) as error:
                report['automation']={'status':'blocked','reason':str(error)[:500]}
        gm.save_report(report, folder / 'result', repo_path=repo)
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
        if path == '/api/health':
            from runner_setup import health
            query=parse_qs(urlsplit(self.path).query)
            profile=query.get('profile',['balanced'])[0]
            if profile not in AI_PROFILES:
                return self.respond(400,{'error':'Unknown resource profile'})
            default_model=AI_PROFILES[profile]['model']
            if profile=='balanced' and os.environ.get('GHOST_MODEL'):
                default_model=os.environ['GHOST_MODEL']
            model=query.get('model',[default_model])[0]
            if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,150}',model):
                return self.respond(400,{'error':'Invalid model name'})
            remote_consent=query.get('remote',['0'])[0]=='1'
            try:
                validate_remote_health_consent(remote_consent,self.headers.get('X-Ghost-Token'))
            except ValueError as error:
                return self.respond(403,{'error':str(error)})
            try:
                return self.respond(200,health(model,remote_consent=remote_consent))
            except ValueError as error:
                return self.respond(400,{'error':str(error)})
        if path == '/api/session':
            return self.respond(200, {'token': TOKEN, 'docker': bool(find_docker()), 'git': bool(shutil.which('git'))})
        match = re.fullmatch(r'/api/jobs/([a-f0-9]{16})', path)
        if match:
            with LOCK:
                job = JOBS.get(match[1])
                return self.respond(200 if job else 404, dict(job) if job else {'error': 'Job not found'})
        match = re.fullmatch(r'/reports/([a-f0-9]{16})/([A-Za-z0-9_./-]+)', path)
        if match:
            directory = (ROOT / 'runs' / 'web' / match[1] / 'result').resolve()
            file = (directory / match[2]).resolve()
            allowed = {'replay.html','matrix.html','summary.html','report.json','events.jsonl','README.patch','README.patched.md','setup.sh','devcontainer.json','AGENTS_setup.md','verification.json','version-note.patch','matrix.json','BENCH.md','bench_models.json','SCAN.md','scan_summary.json','scan_results.jsonl','evidence.md'}
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
            validate_request_flags(request)
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
    server=ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    if os.environ.get('GHOST_OPEN_BROWSER')=='1':
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{PORT}')
    server.serve_forever()
