# AI_Banking

AI_Banking is a mobile-friendly personal finance prototype. It uses a static frontend suitable for GitHub Pages and a Python FastAPI backend for data cleaning, SQLite storage, analytics, machine learning forecasts and AI-style financial insights.

## What this project demonstrates

- HTML, CSS and JavaScript frontend
- FastAPI backend
- SQLite database for manual transactions and budgets
- Cleaned uploaded transaction and budget datasets
- Dashboard analytics
- Budget tracking
- Manual transaction and budget entry
- Linear Regression forecast using monthly spending
- Plain-English AI-style insights
- GitHub Pages frontend deployment workflow

## Project structure

```text
AI_Banking/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── services.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── config.py
│   ├── data/
│   │   ├── raw/
│   │   └── cleaned/
│   ├── database/
│   ├── clean_data.py
│   └── requirements.txt
├── docs/
├── .github/workflows/pages.yml
├── .gitignore
└── README.md
```

## Step 1: Clean the uploaded data

From the backend folder run:

```bash
cd backend
python clean_data.py
```

This creates:

```text
backend/data/cleaned/personal_transactions_cleaned.csv
backend/data/cleaned/budget_cleaned.csv
backend/data/cleaned/cleaning_report.json
```

The cleaning process standardises dates, normalises categories, converts amounts to numeric values, standardises transaction types, removes duplicate rows and creates a JSON cleaning report.

## Step 2: Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

## Step 3: Run the frontend locally

Open a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

## Step 4: Connect to GitHub repo named AI_Banking

Create a new GitHub repository called `AI_Banking`, then run these commands from inside the project folder:

```bash
git init
git add .
git commit -m "Initial AI Banking project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AI_Banking.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 5: GitHub Pages frontend deployment

This repository includes `.github/workflows/pages.yml`. After pushing to GitHub:

1. Go to your GitHub repository.
2. Open **Settings**.
3. Open **Pages**.
4. Set the source to **GitHub Actions**.
5. The frontend will deploy from the `frontend` folder.

## Important security note

This is a prototype. It must not collect real bank login details or private banking credentials. A production version would need authentication, encryption, access control, secure API hosting and data protection compliance.
