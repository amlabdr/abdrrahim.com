# Abderrahim Amlou Portfolio

Static local portfolio for `abdrrahim.com`.

## Run locally

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Update publications

```powershell
python scripts/sync_publications.py
```

Optional Google Scholar merge:

```powershell
python scripts/sync_publications.py --scholar-url "https://scholar.google.com/citations?user=YOUR_ID&hl=en"
```

Your configured profile already includes Google Scholar, so the plain command now uses it automatically.

## Automation

If this project is pushed to GitHub, [sync-publications.yml](c:/Users/ana35/OneDrive%20-%20NIST/Desktop/cooding/portfolio/.github/workflows/sync-publications.yml) will:

- run every Monday at 10:00 UTC
- allow manual runs from the GitHub Actions tab
- refresh `data/publications.json`
- commit and push the updated file if anything changed

## Notes

- The current content is seeded from your resume and public NIST profile.
- Google Scholar has no official public API, so Scholar sync is implemented as an optional best-effort import from a public profile page.
- ORCID and NIST are more stable for automatic publication updates.
