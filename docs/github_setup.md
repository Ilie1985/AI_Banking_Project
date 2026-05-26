# GitHub setup for AI_Banking

## Create the repository

1. Go to GitHub.
2. Click **New repository**.
3. Repository name: `AI_Banking`.
4. Choose Public or Private.
5. Do not add README if you are pushing this prepared project.
6. Click **Create repository**.

## Push from your computer

```bash
cd AI_Banking
git init
git add .
git commit -m "Initial AI Banking project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AI_Banking.git
git push -u origin main
```

## GitHub Pages

The workflow in `.github/workflows/pages.yml` deploys the `frontend` folder. Enable GitHub Pages with GitHub Actions as the source.

## Backend deployment note

GitHub Pages cannot run FastAPI. Deploy the backend separately and then update `API_BASE` inside `frontend/app.js` to the deployed backend URL.
