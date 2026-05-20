# Sync code between fork and team repository

## Current situation

| Remote | Repository | Role |
|--------|------------|------|
| `origin` | `avbento67793/Financial-Agent` | Your fork (where `git push` goes today) |
| `upstream` | `afonsobento10/Financial-Agent` | Team repo (colleagues pull from here) |

Commits on the fork (`6b8f0ae`, `04003e0`, etc.) are **not** on `afonsobento10/Financial-Agent` until someone merges them.

---

## Option A — Repo owner merges (fastest for the team)

**Who:** GitHub user `afonsobento10` (or anyone with write access on the team repo)

1. Open this link and create a Pull Request:

   **https://github.com/afonsobento10/Financial-Agent/compare/main...avbento67793:Financial-Agent:main**

2. Click **Create pull request** → **Merge pull request**.

3. Colleagues run:

   ```bash
   git pull origin main
   ```

---

## Option B — Owner pulls from the fork locally

**Who:** Person with clone of `afonsobento10/Financial-Agent`

```bash
cd Financial-Agent
git remote add fork https://github.com/avbento67793/Financial-Agent.git
git fetch fork
git merge fork/main -m "Merge fork: tools, agent, app.py"
git push origin main
```

Colleagues then: `git pull origin main`

---

## Option C — You get write access on the team repo (best long-term)

**Who:** `afonsobento10` → Settings → Collaborators → add `avbento67793`

Then on your machine:

```bash
git remote set-url origin https://github.com/afonsobento10/Financial-Agent.git
git remote add fork https://github.com/avbento67793/Financial-Agent.git
git push origin main
```

After this, `git push` updates the team repo directly. Use `git push fork main` only if you want a backup on the fork.

---

## Recommended remotes (after Option C)

```bash
git remote -v
# origin   https://github.com/afonsobento10/Financial-Agent.git
# fork     https://github.com/avbento67793/Financial-Agent.git
```

```bash
git push origin main    # team sees your code
git push fork main      # optional backup on fork
```

---

## Why `git push upstream main` failed

```
Permission to afonsobento10/Financial-Agent.git denied to avbento67793
```

Your GitHub user can push to the **fork**, not the **team repo**, until you are a collaborator or use a Pull Request (Option A).
