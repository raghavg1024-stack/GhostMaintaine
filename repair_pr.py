"""Publish only an independently verified documentation repair, when requested."""
import difflib
import json
import os
from pathlib import PurePosixPath
import re
import secrets
import subprocess
import urllib.error
import urllib.request


def api(method, path, token, data=None):
    request=urllib.request.Request('https://api.github.com'+path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                 'Content-Type':'application/json','User-Agent':'GhostMaintainer'},method=method)
    try:
        with urllib.request.urlopen(request,timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(f'GitHub rejected {method} (HTTP {error.code}). Check repository permissions and token access.') from None


def publish(repo, report, requested=False):
    if not requested:
        return {'status':'disabled'}
    if report.get('status')!='repaired' or report.get('original',{}).get('ok',True) or not report.get('verification',{}).get('ok') or not report.get('verification',{}).get('non_vacuous') or not report.get('negative_control') or report['negative_control'].get('ok'):
        return {'status':'skipped','reason':'Only a verified repair with a failing original control can be published.'}
    token=os.environ.get('GHOST_GITHUB_TOKEN','')
    if not token:
        return {'status':'blocked','reason':'Set GHOST_GITHUB_TOKEN on the local backend with Contents and Pull requests write permissions. No repository change was published.'}
    match=re.fullmatch(r'https://github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?',report.get('repo',''))
    if not match:
        raise ValueError('Automatic repair requires a public GitHub repository root URL')
    documents=report.get('patched_documents') or {'README.md':report.get('patched_readme')}
    changes={};diff=''
    for name,text in documents.items():
        path=PurePosixPath(name)
        if not isinstance(text,str) or len(text)>2000000 or path.is_absolute() or '..' in path.parts or '\\' in name or not (name in ('README.md','CONTRIBUTING.md') or (name.startswith('docs/') and name.endswith('.md'))):
            raise ValueError('Automatic repair accepts existing onboarding Markdown documents only')
        source=repo.joinpath(*path.parts)
        if not source.is_file() or any(p.is_symlink() for p in (source,*source.parents)):
            raise ValueError('Automatic repair source must be an existing regular document')
        before=source.read_text(encoding='utf-8-sig')
        if before!=text:
            changes[name]=text
            diff+=''.join(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    if not changes or diff!=report.get('diff'):
        raise ValueError('Publication documents do not exactly match the verified documentation diff')
    revision=report.get('revision','')
    local_revision=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if not re.fullmatch('[0-9a-f]{40}',revision) or local_revision!=revision:
        raise ValueError('Publication requires the exact tested Git revision')
    root='/repos/'+match[1]+'/'+match[2]
    info=api('GET',root,token)
    if not info.get('permissions',{}).get('push'):
        return {'status':'blocked','reason':'Your GitHub token cannot write this repository. Run the check on your own fork to open an automatic repair PR there.'}
    base=info['default_branch']
    from urllib.parse import quote
    head=api('GET',root+'/git/ref/heads/'+quote(base,safe=''),token)['object']['sha']
    if head!=revision:
        return {'status':'blocked','reason':'The default branch changed or a different revision was tested. Rerun against the current default branch before publishing.'}
    base_tree=api('GET',root+'/git/commits/'+revision,token)['tree']['sha']
    entries=[{'path':name,'mode':'100644','type':'blob','content':text} for name,text in changes.items()]
    tree=api('POST',root+'/git/trees',token,{'base_tree':base_tree,'tree':entries})
    commit=api('POST',root+'/git/commits',token,{'message':'Fix verified contributor setup documentation','tree':tree['sha'],'parents':[revision]})
    branch='ghostmaintainer/repair-'+secrets.token_hex(6)
    api('POST',root+'/git/refs',token,{'ref':'refs/heads/'+branch,'sha':commit['sha']})
    body='GhostMaintainer verified this documentation repair in a fresh Docker environment.\n\nTested commit: '+revision+'\n\nFixed check: `'+report['goal']['cmd']+'`\n\nOnly the documentation diff shown in the run report is included. The original failure was repeated before verification. Passing verifies this chosen check and environment only.\n\nDependency preparation: '+('enabled' if report.get('preparation') else 'disabled')+'.\n\nReview before merging. This PR is not merged automatically.'
    try:
        pr=api('POST',root+'/pulls',token,{'title':'Fix verified contributor setup documentation','head':branch,'base':base,'body':body})
    except ValueError:
        return {'status':'branch_created','branch':branch,'reason':'The verified commit was pushed to a new branch, but PR creation failed. Check Pull requests write permission. The default branch was not modified.'}
    return {'status':'pr_created','branch':branch,'url':pr['html_url'],'commit':commit['sha']}
