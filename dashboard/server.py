#!/usr/bin/env python3
"""Local bridge for the GitHub Actions runner dashboard.

Serves the dashboard UI and proxies the parts of the GitHub API that need a
token (self-hosted runner status, triggering workflow_dispatch) so the token
never gets embedded in HTML/JS, committed to the repo, or shown to students.

Usage:
    export GITHUB_TOKEN=ghp_xxx     # fine-grained PAT, repo Administration: Read-only
                                     # + Actions: Read and write (for the trigger button)
    python3 server.py               # -> http://localhost:8787

Without GITHUB_TOKEN the dashboard still works: it falls back to the public,
unauthenticated GitHub API for workflow run history. Only live runner
status and the "trigger run" button need the token.
"""
import json
import os
import urllib.error
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

REPO = os.environ.get("GITHUB_REPO", "Eyal2124/actions-exercises")
WORKFLOW = os.environ.get("GITHUB_WORKFLOW", "hello.yml")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PORT = int(os.environ.get("PORT", "8787"))

API = "https://api.github.com"


def github_request(path, method="GET", body=None):
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=10) as resp:
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else {})


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/status"):
            self.send_json({"repo": REPO, "workflow": WORKFLOW, "tokenConfigured": bool(TOKEN)})
        elif self.path.startswith("/api/runners"):
            self.proxy_get(f"/repos/{REPO}/actions/runners")
        elif self.path.startswith("/api/runs"):
            self.proxy_get(f"/repos/{REPO}/actions/runs?per_page=20")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/dispatch"):
            if not TOKEN:
                self.send_json({"error": "no_token"}, status=400)
                return
            try:
                github_request(
                    f"/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches",
                    method="POST",
                    body={"ref": "main"},
                )
                self.send_json({"ok": True})
            except urllib.error.HTTPError as e:
                self.send_json({"error": e.read().decode()}, status=e.code)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        else:
            self.send_json({"error": "not_found"}, status=404)

    def proxy_get(self, path):
        if not TOKEN:
            self.send_json({"error": "no_token"})
            return
        try:
            _, data = github_request(path)
            self.send_json(data)
        except urllib.error.HTTPError as e:
            self.send_json({"error": e.read().decode()})
        except Exception as e:
            self.send_json({"error": str(e)})

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Repo:  {REPO}")
    print(f"Token: {'configured' if TOKEN else 'NOT set — runner status & trigger button disabled'}")
    print(f"\nDashboard running at http://localhost:{PORT}\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
