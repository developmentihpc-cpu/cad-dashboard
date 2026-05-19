"""
CAD Dashboard — GitHub Sync
============================
Pushes pipeline-state.json to the GitHub repo so cloud agents
always have fresh pipeline data.

Run after exporting state from the dashboard:
  python github_sync.py

Setup: add to .env
  GITHUB_TOKEN=ghp_xxxxxxxxxxxx   (Settings → Developer settings → Personal access tokens → Fine-grained → contents:write)
  GITHUB_REPO=developmentihpc-cpu/cad-dashboard
"""

import json, base64, sys, requests
from pathlib import Path
from datetime import datetime

BASE_DIR   = Path(__file__).parent
ENV_FILE   = BASE_DIR / ".env"
STATE_FILE = BASE_DIR / "pipeline-state.json"

def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    import os
    for key in ("GITHUB_TOKEN","GITHUB_REPO"):
        if key not in env and key in os.environ:
            env[key] = os.environ[key]
    return env

def push_to_github(token, repo, filepath, content_str, commit_msg):
    """Create or update a file in the GitHub repo."""
    url     = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Get current SHA if file exists (required for update)
    sha = None
    r   = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")

    # Encode content
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    body = {"message": commit_msg, "content": encoded}
    if sha:
        body["sha"] = sha

    r = requests.put(url, headers=headers, json=body)
    if r.status_code in (200, 201):
        return True, r.json().get("content",{}).get("html_url","")
    else:
        return False, r.json().get("message","Unknown error")

def main():
    env = load_env()
    token = env.get("GITHUB_TOKEN","")
    repo  = env.get("GITHUB_REPO","developmentihpc-cpu/cad-dashboard")

    if not token or token.startswith("ghp_xxx"):
        print("[ERROR] GITHUB_TOKEN not set in .env")
        print("  1. Go to github.com → Settings → Developer settings")
        print("  2. Personal access tokens → Fine-grained tokens")
        print("  3. Create token with: Contents (read & write)")
        print(f"  4. Add to .env:  GITHUB_TOKEN=ghp_...")
        sys.exit(1)

    if not STATE_FILE.exists():
        print(f"[ERROR] {STATE_FILE} not found.")
        print("  Export state from the dashboard: Settings → Export → Digest Export")
        sys.exit(1)

    content  = STATE_FILE.read_text(encoding="utf-8")
    msg      = f"Update pipeline state — {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    print(f"Pushing pipeline-state.json to {repo}...")
    ok, result = push_to_github(token, repo, "pipeline-state.json", content, msg)

    if ok:
        print(f"[OK] Pushed successfully")
        print(f"     {result}")
    else:
        print(f"[ERR] Push failed: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()
