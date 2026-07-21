# Runner Live Dashboard

A live view of `.github/workflows/hello.yml` and the self-hosted runner
executing it — built for showing the class what's happening in real time.

## Quick start (no setup)

```bash
cd dashboard
python3 server.py
```

Open **http://localhost:8787**. Run history, the duration chart, and the
success-rate stats work immediately — no token needed, since they read the
public GitHub API.

## Full demo (runner status + trigger button)

Runner online/busy status and the "Trigger run" button need a GitHub token,
because GitHub only exposes those over an authenticated API. The token stays
on your machine — `server.py` holds it server-side and the browser never
sees it, so it's safe to run this on the projector.

1. Create a fine-grained personal access token scoped to this repo:
   - **Administration: Read-only** (lists self-hosted runners)
   - **Actions: Read and write** (reads run history at higher rate limits, triggers `workflow_dispatch`)
2. Before class:
   ```bash
   export GITHUB_TOKEN=github_pat_xxx
   cd dashboard
   python3 server.py
   ```
3. Open http://localhost:8787 — the runner card, live status dot, and
   trigger button light up.

Never commit the token or paste it into `index.html` — it only ever lives
in your shell's environment variable.

## Files

- `server.py` — stdlib-only local server. Serves the dashboard and proxies
  the token-gated GitHub endpoints (`/api/runners`, `/api/runs`, `/api/dispatch`).
- `index.html` — the dashboard itself (vanilla HTML/CSS/JS, no build step).
