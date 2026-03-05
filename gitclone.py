import subprocess
import os

# ── CONFIG ── Fill in before running ──
REPO_URL = "https://github.com/user/repo.git"
# ─────────────────────────────────────

def gitclone():
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    repo_name = REPO_URL.rstrip("/").split("/")[-1].replace(".git", "")
    dest = os.path.join(downloads, repo_name)

    if os.path.exists(dest):
        print(f"\n✦ Folder already exists: {dest}")
        print("  Delete it first if you want to re-clone.\n")
        return

    print(f"\n✦ Cloning into {dest} ...")
    subprocess.run(['git', 'clone', REPO_URL, dest], check=True)
    print(f"\n✦ Done. Repo cloned to {dest}\n")


if __name__ == '__main__':
    gitclone()
