"""Explicit, evidence-recorded Python dependency preparation. Never runs on the host."""
import json
import os
from pathlib import Path
import re
import shlex
import tomllib
from urllib.parse import urlsplit


AI_PROFILES = {
    'low': {'model': 'qwen3:1.7b', 'num_ctx': 4096, 'max_chars': 6000, 'num_predict': 800},
    'balanced': {'model': 'qwen3:4b-instruct', 'num_ctx': 8192, 'max_chars': 16000, 'num_predict': 1400},
    'rules': {'model': 'rules', 'num_ctx': 0, 'max_chars': 0, 'num_predict': 0},
}


def ollama_config():
    """Return a validated Ollama endpoint, remote flag, and safe display origin."""
    value = os.environ.get('GHOST_OLLAMA_URL', 'http://127.0.0.1:11434').strip().rstrip('/')
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('GHOST_OLLAMA_URL must be an HTTP(S) base URL without credentials, query, or fragment')
    remote = parts.hostname.lower() not in ('localhost', '127.0.0.1', '::1')
    if remote and parts.scheme != 'https':
        raise ValueError('Remote Ollama endpoints must use HTTPS')
    return value, remote, f'{parts.scheme}://{parts.netloc}'


def default_goal(repo):
    config=repo/'ghostmaintainer.json'
    if config.is_file():
        return json.loads(config.read_text(encoding='utf-8-sig'))['cmd']
    project=repo/'pyproject.toml'
    text=project.read_text(encoding='utf-8-sig') if project.is_file() else ''
    if '[tool.pytest' in text or any('pytest' in p.read_text(encoding='utf-8',errors='replace') for p in list((repo/'tests').rglob('test*.py'))[:8]):
        return 'python -m pytest -q'
    return 'python -m unittest discover -v'


def dependency_plan(repo):
    """Only project-declared dependencies; no guessed package names or host commands."""
    steps=[]
    project=repo/'pyproject.toml'
    data=tomllib.loads(project.read_text(encoding='utf-8-sig')) if project.is_file() else {}
    prefix='python -m pip install --user --disable-pip-version-check --no-input --timeout 15 --retries 0 '
    dependencies=[]
    groups=data.get('dependency-groups',{})
    def group(name,seen):
        if name in seen: raise ValueError('Cyclic dependency group')
        result=[]
        for item in groups.get(name,[]):
            if isinstance(item,str): result.append(item)
            elif isinstance(item,dict) and set(item)=={'include-group'}: result+=group(item['include-group'],seen|{name})
            else: raise ValueError('Unsupported dependency group declaration')
        return result
    dependencies+=data.get('build-system',{}).get('requires',[])
    for name in ('test','tests','testing'):
        dependencies+=group(name,set())
        dependencies+=data.get('project',{}).get('optional-dependencies',{}).get(name,[])
    if not all(isinstance(d,str) and len(d)<500 and re.match(r'^[A-Za-z0-9]',d) for d in dependencies):
        raise ValueError('Unsupported dependency specifier')
    if dependencies:
        text=project.read_text(encoding='utf-8-sig').splitlines()
        refs=[f'pyproject.toml:{i}' for i,line in enumerate(text,1) if line.strip() in ('[build-system]','[dependency-groups]','[project.optional-dependencies]')]
        steps.append({'cmd':prefix+' '.join(shlex.quote(d) for d in dict.fromkeys(dependencies)), 'source':', '.join(refs),'stage':'preparation'})
    for name in ('requirements.txt','requirements-dev.txt','requirements-test.txt'):
        if (repo/name).is_file():
            steps.append({'cmd':prefix+'-r '+shlex.quote(name),'source':name+':1','stage':'preparation'})
    if data.get('build-system') or (repo/'setup.py').is_file():
        steps.append({'cmd':prefix+('--no-build-isolation ' if data.get('build-system') else '')+'-e .','source':'pyproject.toml:1' if project.is_file() else 'setup.py:1','stage':'preparation'})
    return steps


def find_docker():
    import os
    import shutil
    found=shutil.which('docker')
    if found: return found
    if os.name=='nt':
        candidates=[Path(os.environ.get('LOCALAPPDATA',''))/'Programs/DockerDesktop/resources/bin/docker.exe',Path('C:/Program Files/Docker/Docker/resources/bin/docker.exe')]
        return next((str(path) for path in candidates if path.is_file()),None)
    return None


def health(model='qwen3:4b-instruct', remote_consent=False):
    import shutil
    import subprocess
    import urllib.error
    import urllib.request
    endpoint, remote, origin = ollama_config()
    checks={'git':bool(shutil.which('git')), 'docker':False, 'ollama':False, 'model':model,
            'model_installed':False, 'remote_configured':remote, 'ollama_origin':origin,
            'remote_consent_required':remote and not remote_consent}
    docker=find_docker()
    if docker:
        try:
            result=subprocess.run([docker,'info','--format','{{.ServerVersion}}'],capture_output=True,text=True,timeout=5)
            checks['docker']=result.returncode==0
            checks['docker_version']=result.stdout.strip() if checks['docker'] else ''
        except (OSError,subprocess.TimeoutExpired): pass
    try:
        if remote and not remote_consent:
            checks['ready']=False
            return checks
        headers={}
        if remote and os.environ.get('GHOST_OLLAMA_API_KEY'):
            headers['Authorization']='Bearer '+os.environ['GHOST_OLLAMA_API_KEY']
        request=urllib.request.Request(endpoint+'/api/tags',headers=headers)
        with urllib.request.urlopen(request,timeout=3) as response:
            names=[item['name'] for item in json.load(response).get('models',[])]
        checks['ollama']=True
        checks['model_installed']=model in names or model+':latest' in names
        checks['models']=names
    except (OSError,ValueError,urllib.error.URLError): pass
    checks['ready']=all(checks[k] for k in ('git','docker','ollama','model_installed'))
    return checks
