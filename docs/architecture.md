# AI_Banking Architecture

## Frontend

The frontend is a static HTML, CSS and JavaScript application that can be hosted using GitHub Pages. It calls the FastAPI backend using `fetch`.

Pages/sections included:

- Home
- Dashboard
- Budget Tracker
- Manual Transaction Entry
- AI Forecast Preview
- AI Insights

## Backend

The backend uses FastAPI. It loads cleaned CSV data, stores manual entries in SQLite and returns analytics through API endpoints.

Endpoints:

- `GET /health`
- `GET /dashboard`
- `GET /budget`
- `POST /transactions`
- `POST /budget`
- `GET /forecast`
- `GET /insights`

## Data cleaning

The cleaning script reads uploaded raw CSV files from `backend/data/raw` and writes cleaned files to `backend/data/cleaned`. The backend reads the cleaned files only.

## Machine learning

The forecast uses monthly spending totals and a simple Linear Regression model. It returns the predicted next month spending, MAE and R² score.

## Deployment

GitHub Pages can host only the frontend. The backend must be deployed separately on a Python-compatible service such as Render, Railway, Fly.io or a university server.
