# GhostMaintainer frontend

React renders the existing local app form; Tailwind builds layout utilities and src/styles.css supplies the Halloween theme. The existing API fields, local session token, progress polling, and report iframe remain connected to app.py.

## Rebuild

From this directory, run:

```sh
npm ci
npm run build
```

The build writes index.html with React, compiled CSS, inline SVG, and Inter fonts embedded. No CDN, external font request, Node server, or npm install is needed to use the checked-in page. Start the normal Python application to use repository analysis; analysis itself still requires its existing Git, Docker, and optional Ollama dependencies.

Edit src/App.jsx for content and handlers, and src/styles.css for styling. Do not hand-edit the generated index.html. CSS animation respects the system reduced-motion preference. Inter is distributed under the SIL Open Font License; see INTER-LICENSE.txt.

## Vercel

Deploy this web directory using the included vercel.json. The build outputs dist/index.html. The hosted page explicitly requires the local runner and links to it; it does not expose the PC backend to the internet. The Docker/Ollama job runner is not deployed by this configuration.

## Local runner upgrades

The form now checks /api/health for the actual Docker engine and selected installed Ollama model, offers an explicit no-cache live-AI option and a separate opt-in dependency-preparation checkbox, and displays actual stage messages from /api/jobs. Dependency preparation is refused unless the separate container-network checkbox is enabled. The fixed test field is blank by default so repository configuration or test-runner detection is respected. The hosted Vercel interface continues to require the local Python app; it does not execute Docker or Ollama in the cloud.
