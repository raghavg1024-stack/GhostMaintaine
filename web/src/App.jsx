import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
function GhostIcon() {
  return <svg className="ghost" viewBox="0 0 28 32" fill="none" aria-hidden="true"><path d="M5 27V13a9 9 0 0 1 18 0v14l-4-3-5 3-5-3-4 3Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/><ellipse cx="11" cy="13" rx="1.3" ry="1.8" fill="currentColor"/><ellipse cx="17" cy="13" rx="1.3" ry="1.8" fill="currentColor"/></svg>;
}
function App() {
  const hostedInterface = !['127.0.0.1', 'localhost'].includes(window.location.hostname);
  useEffect(() => {
    let token='', busy=false, ready=false, healthRequest=0;
    const $=id=>document.getElementById(id);
    const localRunner=!hostedInterface;
    const profileModel=profile=>profile==='low'?'qwen3:1.7b':'qwen3:4b-instruct';
    const selectedModel=()=> $('model').value.trim()||profileModel($('resourceProfile').value);
    const rulesOnly=()=> $('resourceProfile').value==='rules';
    function status(message,error=false){$('status').className=error?'error':'';$('status').textContent=message;const log=$('progressLog');if(log.lastElementChild?.textContent!==message){const item=document.createElement('li');item.textContent=message;log.append(item);}}
    function setBusy(value){busy=value;$('submit').disabled=value||!ready;$('mode').disabled=value;}

    async function refreshHealth(){
      const sequence=++healthRequest,profile=$('resourceProfile').value,model=selectedModel();
      const ai=$('mode').value==='assist'&&!rulesOnly();
      if(!ai&&$('remoteAi').checked)$('remoteAi').checked=false;
      const remote=$('remoteAi').checked;
      $('modelField').className=ai?'field':'field hidden';
      $('readiness').textContent='Checking Docker and the selected inference option…';
      try{
        const query=new URLSearchParams({model,profile,remote:remote?'1':'0'});
        const response=await fetch('/api/health?'+query,{headers:{'X-Ghost-Token':token}});
        if(!response.ok){const detail=await response.json().catch(()=>({}));throw Error(detail.error||'Readiness check failed');}
        const h=await response.json();if(sequence!==healthRequest)return;
        const remoteVisible=ai&&h.remote_configured;
        $('remoteField').className=remoteVisible?'field':'field hidden';
        $('remoteHost').textContent=h.ollama_origin||'configured host';
        const waitingForConsent=remoteVisible&&!remote;
        const missing=[!h.git?'Git':null,($('mode').value!=='drift'&&!h.docker)?'running Docker engine':null,
          ai&&!waitingForConsent&&!h.ollama?(remote?'connecting to the configured remote Ollama':'running Ollama'):null,
          ai&&!waitingForConsent&&h.ollama&&!h.model_installed?'installed model '+model:null].filter(Boolean);
        ready=missing.length===0&&!waitingForConsent;
        $('readiness').textContent=waitingForConsent?'Remote Ollama is configured. It receives no repository data until you enable the consent checkbox below.':ready
          ?'Ready · '+(rulesOnly()?'rules-only; no AI model used':model+(remote?' on the configured remote server':' on this PC'))+' · repository setup runs in Docker.'
          :'Needs: '+missing.join(', ')+'. Run start.cmd for setup instructions.';
        $('submit').disabled=busy||!ready;
      }catch(error){ready=false;$('submit').disabled=true;$('readiness').textContent=error.message;}
    }

    async function start(){
      if(!localRunner){window.location.assign('http://127.0.0.1:8765/?repo='+encodeURIComponent($('url').value.trim()));return;}
      if(busy||!ready)return;
      $('progressLog').replaceChildren();
      if($('prepare').checked&&!$('network').checked){status('Enable container network access before opting into dependency preparation.',true);return;}
      setBusy(true);$('result').className='hidden';status('Preparing the repository setup check…');
      try{
        const response=await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json','X-Ghost-Token':token},body:JSON.stringify({
          mode:$('mode').value,resource_profile:$('resourceProfile').value,models:$('models').value,matrix:$('matrix').value,
          urls:$('scanUrls').value.split('\n').map(x=>x.trim()).filter(Boolean),url:$('url').value,target:$('target').value,
          model:selectedModel(),remote_ai:$('remoteAi').checked,network:$('network').checked,prepare:$('prepare').checked,no_cache:$('noCache').checked
        })});
        const data=await response.json();if(!response.ok)throw Error(data.error);await poll(data.id);
      }catch(error){status(error.message,true);setBusy(false);}
    }
    async function poll(id){
      try{
        const response=await fetch('/api/jobs/'+id);if(!response.ok)throw Error('Could not read check status.');
        const job=await response.json();status(job.message,job.state==='error');
        if(job.state==='running'){setTimeout(()=>poll(id),1200);return;}
        setBusy(false);
        if(job.state==='done'){
          $('result').className='';
          $('resultTitle').textContent=({repaired:'A setup-document fix passed verification',healthy:'The documented setup passed',inconclusive:'Setup could not be verified',needs_human:'Maintainer input is needed',feature_complete:'Your analysis is ready'})[job.status]||'Check complete';
          $('resultNote').textContent=({'bench-models':'Small hand-labelled v0 comparison. Read sample sizes and cache policy before interpreting results.',scan:'Local aggregate only. Skipped repositories are not healthy; no ecosystem-wide conclusions.',drift:'Static advisory scan. These notes do not change files or execute project commands.',matrix:'The same instructions were checked across Python versions.',ship:'Only setup.sh is separately verified. Other artifacts are generated from the passing commands.'})[job.mode]||'Review the reproducible command evidence and verified patch before applying it.';
          $('revision').textContent=job.revision?'Checked commit: '+job.revision:'';$('openReport').href=job.report;$('report').src=job.report;
          $('result').scrollIntoView({behavior:'smooth',block:'start'});
        }
      }catch(error){status(error.message,true);setBusy(false);}
    }

    if(!localRunner){
      ready=true;setBusy(false);$('submit').textContent='Open local assistant →';
      document.querySelector('.badge').textContent='Local runner required';
      $('readiness').textContent='The check runs on your PC. Enter a repo and open the local assistant; run start.cmd first if needed. ';
      const link=document.createElement('a');link.href='http://127.0.0.1:8765/';link.textContent='Open local app ↗';link.target='_blank';link.rel='noopener';$('readiness').append(link);
    }else{
      const incoming=new URLSearchParams(window.location.search).get('repo');
      if(incoming&&/^https:\/\/github\.com\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+\/?$/.test(incoming))$('url').value=incoming;
      fetch('/api/session').then(r=>{if(!r.ok)throw Error('Session unavailable');return r.json();}).then(session=>{token=session.token;return refreshHealth();}).catch(()=>{ready=false;setBusy(false);status('Cannot reach the local server. Run start.cmd on this PC.',true);});
    }

    const modeHints={assist:'Reproduce contributor setup in a clean environment, explain the failure with file evidence, and verify a documentation repair.',check:'Follow the README, run the fixed check, and verify a documentation repair.',ship:'Create setup.sh, a devcontainer, and agent instructions; setup.sh gets a separate Docker verification.',drift:'Static advisory audit for undocumented environment variables and conflicting version declarations. No commands run.',matrix:'Run the same instructions in up to three concurrent Python containers.','bench-models':'Compare rules and installed Ollama models on the bundled hand-labelled v0 dataset.',scan:'Check selected public repositories and report local aggregate setup outcomes.'};
    const buttonLabels={assist:'Summon Assistant →',check:'Check repository →',ship:'Build setup artifacts →',drift:'Audit configuration →',matrix:'Run runtime matrix →','bench-models':'Run benchmark →',scan:'Scan repositories →'};
    function updateModeCopy(){
      const mode=$('mode').value;
      $('modeHint').textContent=mode==='assist'&&rulesOnly()?'Rules-only setup check: no model is used. It cannot interpret free-text setup instructions.':modeHints[mode];
      $('submit').textContent=mode==='assist'&&rulesOnly()?'Run rules-only setup check →':buttonLabels[mode];
      if(!localRunner)$('submit').textContent='Open local assistant →';
    }
    $('resourceProfile').addEventListener('change',()=>{updateModeCopy();refreshHealth();});
    $('remoteAi').addEventListener('change',refreshHealth);
    $('model').addEventListener('change',()=>{if(localRunner&&!busy)refreshHealth();});
    $('mode').addEventListener('change',()=>{
      if(localRunner)refreshHealth();
      const mode=$('mode').value;$('url').required=!['bench-models','scan'].includes(mode);
      $('repoField').className=['bench-models','scan'].includes(mode)?'hidden':'';$('scanField').className=mode==='scan'?'':'hidden';
      updateModeCopy();
    });
    $('resourceProfile').addEventListener('change',()=>{
      $('profileHint').textContent=({low:'Uses Qwen3 1.7B by default with a 4K model context and up to 6,000 characters of selected evidence. Model weights are about 1.4 GB; runtime and Docker need additional memory.',balanced:'Uses Qwen3 4B by default with an 8K model context and up to 16,000 characters of selected evidence. Model weights are about 2.5 GB; runtime and Docker need additional memory.',rules:'Uses no LLM. The deterministic check can follow supported commands but cannot interpret setup prose.'})[$('resourceProfile').value];
      updateModeCopy();
    });
    $('form').addEventListener('submit',event=>{event.preventDefault();start();});



    const targets = document.querySelectorAll('.materialize');
    if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const observer = new IntersectionObserver(entries => entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
      }), {threshold:.06});
      document.documentElement.classList.add('motion-ready');
      targets.forEach(target => observer.observe(target));
      return () => observer.disconnect();
    }
  }, []);
  return <>
    <div className="atmosphere" aria-hidden="true"><div className="fog fog-one"/><div className="fog fog-two"/><div className="particles"/></div>

  <nav aria-label="Main navigation" className="mx-auto flex max-w-[840px] items-center justify-between gap-4 px-6 py-6 sm:px-10">
    <div className="brand flex items-center gap-2">GhostMaintainer <GhostIcon /></div>
    <span className="badge">Runs on your PC</span>
  </nav>
  <main className="mx-auto w-full max-w-[840px] px-6 pb-10 pt-14 sm:px-10 sm:pt-16">
    <header className="hero materialize mb-9">
      <div className="eyebrow">// A FRESH START FOR EVERY CONTRIBUTOR</div>
      <h1>Your AI assistant for getting repositories running.</h1>
      <p>Check whether a new contributor can follow a repository’s setup on a clean machine. GhostMaintainer reproduces the steps, points to the evidence, proposes a documentation fix, and reruns the check to verify it.</p>
    </header>

    <section className="panel materialize relative rounded-xl border border-white/10 bg-[#171020]/75 p-6 backdrop-blur-md sm:p-8" aria-label="Repository configuration">
      <div className="window-caption" aria-hidden="true">
        <span className="sequence">// DRILL_SEQUENCE_INITIATED</span>
        <div className="window-lights"><span></span><span></span><span></span></div>
      </div>
      {hostedInterface&&<div className="hosted-notice"><strong>Hosted interface only</strong><p>Repository checks run on your PC. Start Docker Desktop and run <code>start.cmd</code> from the GhostMaintainer folder. For AI mode, start Ollama too.</p><a href="http://127.0.0.1:8765/">Open the local assistant ↗</a></div>}
      <form id="form">
        <label htmlFor="mode">Choose an analysis</label>
        <select id="mode" defaultValue="assist">
          <option value="assist">AI setup maintainer assistant</option>
          <option value="check">Verify &amp; heal the README</option>
          <option value="ship">Generate and verify setup artifacts</option>
          <option value="drift">Audit environment variables &amp; versions</option>
          <option value="matrix">Compare Python runtimes</option>
          <option value="bench-models">Benchmark local models</option>
          <option value="scan">Scan a repository list</option>
        </select>
        <p id="modeHint" className="hint">Reproduce contributor setup in a clean environment, explain the failure with file evidence, and verify a documentation repair.</p>

        <div id="repoField">
          <label htmlFor="url">Public GitHub repository</label>
          <input id="url" name="url" type="url" placeholder="https://github.com/owner/repository" spellCheck="false" required />
          <p className="hint">Python/Linux repositories with a root README.md are supported by this prototype.</p>
        </div>
        <div id="scanField" className="hidden">
          <label htmlFor="scanUrls">Public GitHub URLs · one per line, up to 20</label>
          <textarea id="scanUrls" rows="4" placeholder="https://github.com/owner/repository" spellCheck="false"></textarea>
          <p className="hint">Local aggregate only. A safety filter may skip repositories. Network access is optional below.</p>
        </div>

        <details>
          <summary><span className="chevron" aria-hidden="true">▼</span>Check settings</summary>
          <div className="settings-content">
            <div className="field">
              <label htmlFor="resourceProfile">AI resource mode</label>
              <select id="resourceProfile" defaultValue="balanced">
                <option value="low">Low memory · Qwen3 1.7B · 4K context</option>
                <option value="balanced">Balanced · Qwen3 4B · 8K context</option>
                <option value="rules">Rules only · no model</option>
              </select>
              <p id="profileHint" className="hint">Uses Qwen3 4B by default with an 8K model context and up to 16,000 characters of selected evidence. Model weights are about 2.5 GB; runtime and Docker need additional memory.</p>
            </div>
            <div className="field">
              <label htmlFor="target">What test command should pass?</label>
              <input type="text" id="target" placeholder="Auto: project config, pytest, or unittest" spellCheck="false" />
              <p className="hint">Leave blank to use ghostmaintainer.json or detect pytest/unittest from the project. At least one test must run. Set this for projects using pytest or another runner.</p>
            </div>
            <div id="modelField" className="field">
              <label htmlFor="model">Optional Ollama model override</label>
              <input type="text" id="model" placeholder="Uses the selected profile’s default" spellCheck="false" />
              <p className="hint">Low memory defaults to qwen3:1.7b. Balanced defaults to qwen3:4b-instruct. Install the selected model with Ollama before running.</p>
            </div>
            <div id="remoteField" className="field hidden">
              <label className="check" htmlFor="remoteAi"><input type="checkbox" id="remoteAi" /><span>Allow optional remote inference at <code id="remoteHost">configured host</code>.</span></label>
              <p className="hint">When enabled, GhostMaintainer sends selected setup documents, configuration excerpts, and trimmed failure logs to that HTTPS Ollama server. It does not send the full repository. Leave unchecked to keep model calls local.</p>
            </div>
            <div className="field">
              <label htmlFor="models">Benchmark model list</label>
              <input type="text" id="models" defaultValue="rules,qwen3:4b-instruct" spellCheck="false" />
            </div>
            <div className="field">
              <label htmlFor="matrix">Python runtime matrix</label>
              <input type="text" id="matrix" defaultValue="py3.9,py3.11,py3.12" spellCheck="false" />
              <p className="hint">Matrix images must be available in Docker; pull the corresponding python:VERSION-slim images first. Assistant mode defaults to qwen3:4b-instruct. A named model must already be installed and Ollama must be running. Other modes use rules when this field is blank.</p>
            </div>
            <label className="check" htmlFor="noCache"><input type="checkbox" id="noCache" /><span>Live AI demo: bypass saved model responses.</span></label>
            <label className="check" htmlFor="prepare"><input type="checkbox" id="prepare" /><span>Prepare project-declared Python test dependencies in every fresh container.</span></label>
            <p className="hint">Opt-in. Requires network access below. Installs declared test/build dependencies and the project inside Docker. Preparation logs and sources are included in the report.</p>
            <label className="check" htmlFor="network"><input type="checkbox" id="network" /><span>Allow network inside test containers for dependency installation.</span></label>
            <p className="hint safety-note">Run only repositories you trust and have inspected. Their commands execute inside Docker on this PC. Missing tools or unsupported setup can block verification.</p>
          </div>
        </details>

        <div className="row"><button type="submit" id="submit" disabled>Summon Assistant →</button></div>
        <p id="readiness" className="hint" role="status">Checking local dependencies…</p>
      </form>
      <div id="status" className="hidden" role="status" aria-live="polite"></div>
      <ol id="progressLog" className="progress-log" aria-label="Actual analysis stages"></ol>
    </section>

    <div className="steps">
      <div><strong>01 · Reproduce setup</strong><span>Follow the docs in a clean Docker environment. Record the commands and failures.</span></div>
      <div><strong>02 · Propose a sourced repair</strong><span>A small model reads selected setup and failure evidence. Review its exact documentation diff.</span></div>
      <div><strong>03 · Prove the chosen check</strong><span>Rerun in a fresh environment against the same test. An unverified fix stays unverified.</span></div>
    </div>
    <div id="result" className="hidden">
      <h2 id="resultTitle">Your result</h2>
      <p id="resultNote"></p>
      <a className="link" id="openReport" target="_blank" rel="noopener">Open full report ↗</a>
      <p id="revision" className="hint"></p>
      <iframe id="report" title="Repository setup check result" sandbox="allow-scripts allow-downloads"></iframe>
    </div>
    <p className="hint guard-link"><a href="https://github.com/raghavg1024-stack/git_test/pull/1" target="_blank" rel="noopener">PR Guard: view the passing test and bot patch comment ↗</a></p>
    <p className="hint guard-link"><a href="https://ghostmaintainer.vercel.app/evidence/" target="_blank" rel="noopener">Recorded execution evidence, all real-repository results, and judge guide ↗</a></p>
    <p className="hint guard-link"><a href="https://ghostmaintainer.vercel.app/evidence/PRESENTATION_ALIGNMENT.md" target="_blank" rel="noopener">Presentation promises: implementation and evidence audit ↗</a></p>
    <footer>GitHub Issues track reported bugs. GhostMaintainer tests contributor setup before that issue exists, then verifies a documentation repair. No automatic commits or pull requests. A passing check verifies the chosen test, not every feature.</footer>
  </main>

  </>;
}
createRoot(document.getElementById('root')).render(<App />);
