"""Networked, local-only real-repository evaluation; records every attempted outcome."""
import argparse
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
import assistant
import ghostmaintainer as gm
from runner_setup import default_goal

CASES=[
    {'url':'https://github.com/pallets/itsdangerous','blind':False,'prior':'Previously manually inspected for a coverage config issue; not a blind test.'},
    {'url':'https://github.com/python-humanize/humanize','blind':True,'prior':'No repository-specific changes before first evaluation.'},
    {'url':'https://github.com/pypa/sampleproject','blind':False,'prior':'Previously attempted before dependency preparation.'},
]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--net',action='store_true',help='Explicit permission to install dependencies inside Docker')
    parser.add_argument('--model',default='qwen3:4b-instruct')
    parser.add_argument('--out',type=Path,default=gm.ROOT/'runs'/'real-evaluation')
    parser.add_argument('--no-cache',action='store_true')
    args=parser.parse_args()
    if not args.net: parser.error('This evaluation uses --prepare and requires explicit --net')
    args.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for case in CASES:
        started=time.perf_counter();name=case['url'].split('/')[-1];folder=args.out/name
        row={**case,'repository':name,'model':args.model,'preparation':True,'network':True,'status':'inconclusive'}
        try:
            repo=folder/'checkout'
            folder.mkdir(parents=True,exist_ok=True)
            if repo.exists(): raise ValueError('Choose a fresh output directory; evaluation will not overwrite a checkout')
            subprocess.run(['git','-c','credential.helper=','clone','--depth','1','--no-recurse-submodules','--',case['url']+'.git',str(repo)],check=True,capture_output=True,timeout=60)
            row['revision']=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            if any(p.is_symlink() for p in repo.rglob('*')): raise ValueError('Symlinks unsupported')
            gm.write_json(repo/'ghostmaintainer.json',{'cmd':default_goal(repo)}) if not (repo/'ghostmaintainer.json').is_file() else None
            row['goal']=json.loads(gm.read(repo/'ghostmaintainer.json'))['cmd']
            options=SimpleNamespace(backend='docker',net=True,prepare=True,no_cache=args.no_cache,labeller=args.model,image='python:3.12-slim',progress=lambda message:print(name+': '+message,flush=True))
            report=assistant.run(repo,options)
            report['repo']=case['url'];report['revision']=row['revision'];report['evaluation_case']=case
            gm.save_report(report,folder/'result',repo_path=repo)
            row.update(status=report['status'],report=str((folder/'result'/'replay.html').resolve()),reason=report.get('reason') or report.get('assistant',{}).get('diagnosis',{}).get('diagnosis',''),cache_calls=report.get('assistant',{}).get('calls',[]))
        except Exception as error:
            row['error']=str(error)[:1500]
        row['wall_seconds']=round(time.perf_counter()-started,3)
        results.append(row)
        gm.write_json(args.out/'results.json',results)
        lines=['# Real repository evaluation','', 'All attempted cases are included. Preparation was explicitly enabled; a healthy result is not proof that README-only setup worked. One blind case; no population-level success-rate claim.','', '| Repository | Commit | Blind | Status | Seconds |','|---|---|---|---|---|']
        lines += [f"| {r['url']} | {r.get('revision','unknown')[:12]} | {r['blind']} | {r['status']} | {r['wall_seconds']} |" for r in results]
        for r in results: lines += ['', '## '+r['repository'],r.get('reason') or r.get('error') or 'Read the execution report.',r['prior']]
        (args.out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        print(json.dumps(row,ensure_ascii=True),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
