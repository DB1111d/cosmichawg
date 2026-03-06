import subprocess
import os

# ── CONFIG ── Fill in before running ──
REPO_URL = "https://github.com/your-username/your-repo.git"
BRANCH = "your-branch"
# ─────────────────────────────────────

def gitclonebranch():
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    repo_name = REPO_URL.rstrip("/").split("/")[-1].replace(".git", "")

    # Clone branch
    dest = os.path.join(downloads, f"{repo_name}-{BRANCH}")
    if os.path.exists(dest):
        print(f"\n✦ Folder already exists: {dest}")
        print("  Delete it first if you want to re-clone.\n")
    else:
        print(f"\n✦ Cloning '{BRANCH}' branch into {dest} ...")
        subprocess.run(['git', 'clone', '-b', BRANCH, '--single-branch', REPO_URL, dest], check=True)
        print(f"\n✦ Done. '{BRANCH}' branch cloned to {dest}\n")

if __name__ == '__main__':
    gitclonebranch()
