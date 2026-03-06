import subprocess
import os

# ── CONFIG ── Fill in before running ──
REPO_URL = "https://github.com/user/repo.git"
# ─────────────────────────────────────

def gitclone():
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    repo_name = REPO_URL.rstrip("/").split("/")[-1].replace(".git", "")

    # Clone main
    dest = os.path.join(downloads, repo_name)
    if os.path.exists(dest):
        print(f"\n✦ Folder already exists: {dest}")
        print("  Delete it first if you want to re-clone.\n")
    else:
        print(f"\n✦ Cloning main into {dest} ...")
        subprocess.run(['git', 'clone', REPO_URL, dest], check=True)
        print(f"\n✦ Done. Repo cloned to {dest}\n")

    # Clone tools branch
    dest_tools = os.path.join(downloads, f"{repo_name}-tools")
    if os.path.exists(dest_tools):
        print(f"\n✦ Folder already exists: {dest_tools}")
        print("  Delete it first if you want to re-clone.\n")
    else:
        print(f"\n✦ Cloning tools branch into {dest_tools} ...")
        subprocess.run(['git', 'clone', '-b', 'tools', '--single-branch', REPO_URL, dest_tools], check=True)
        print(f"\n✦ Done. Tools branch cloned to {dest_tools}\n")

if __name__ == '__main__':
    gitclone()
