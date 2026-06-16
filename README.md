# AI Banking — Personal Finance Analytics and Forecasting Prototype

AI Banking is a full-stack personal finance web application prototype that helps users understand income, expenses, budgets, spending patterns and future financial behaviour using data analytics and machine learning.

The application allows users to sign up, log in, add manual transactions, create and manage monthly category budgets, upload CSV transaction data, switch between different data sources, view analytics dashboards, generate spending forecasts and review audit logs.

This project was developed as an academic and portfolio project to demonstrate full-stack development, authentication, database integration, data processing, data visualisation and machine learning concepts.

---

## Live Demo

### Backend API

```text
https://ai-banking-backend-x040.onrender.com
```

### Backend Health Check

```text
https://ai-banking-backend-x040.onrender.com/health
```

### Frontend Live Demo

```text
Add your Netlify or Vercel frontend link here
```

---

## Project Overview

AI Banking is designed as a prototype banking and budgeting tool.

It does not connect to real bank accounts and does not use Open Banking. Instead, it works with demo data, uploaded CSV data and manually entered user data.

The system supports user authentication through Supabase. Each logged-in user has their own budgets, transactions, uploaded data, active data mode and audit logs.

---

## Key Features

### Authentication

- Supabase email/password sign up
- Supabase login and logout
- User session handling
- Logged-in user email displayed in the interface
- Banking dashboard hidden until the user is authenticated

### User-Specific Data

Each logged-in user has their own:

- Budgets
- Manual transactions
- Uploaded CSV transactions
- Active dataset mode
- Audit logs
- Dashboard results
- Forecasts and insights

### Data Modes

The application supports multiple data modes so the user can choose which data source should drive the dashboard, analysis, forecast and insights.

| Data Mode | Description |
|---|---|
| Mock Data | Uses the original demo dataset for presentation and testing |
| Uploaded CSV | Uses the user-uploaded CSV transaction data |
| Manual Data | Uses manually entered transactions and budgets |
| Combined Data | Uses available uploaded and manual data together, with mock data available for demonstration |

### Budget Tracker

- Add monthly income
- Add category budgets
- View budgets grouped by month
- Newest budget month shown first
- View total budget, spent amount, remaining amount and safe daily spending
- Edit budget category names
- Edit category budget amounts
- Delete budget categories
- Budget status indicators:
  - Healthy
  - Close to limit
  - Over budget

### Manual Transactions

- Add manual income or expense transactions
- Store transaction date, description, amount, type, category and payment method
- View recent or all transactions
- Manual transactions are stored per logged-in user
- Manual transactions are used in budget calculations, dashboard analysis and forecasting where applicable

### CSV Upload

- Upload bank-style CSV transaction data
- Map CSV columns to expected application fields
- Clean and process uploaded data
- Replace uploaded CSV data without deleting the original mock/demo dataset
- Uploaded transactions are stored separately from manual transactions

### Dashboard

- Total income
- Total expenses
- Net savings
- Transaction count
- Data source summary
- Spending category visualisations
- Monthly spending visualisations

### Spending Analysis

- Average monthly spending
- Highest spending month
- Lowest spending month
- Top spending categories
- Monthly spending trends
- Source summary by selected data mode

### AI Spending Forecast

- Machine learning forecast for next month’s spending
- Actual vs predicted monthly spending chart
- Mean Absolute Error evaluation metric
- R² score evaluation metric
- Reliability explanation for low R² scores

When the R² score is low, the app explains that the selected data has irregular spending patterns and that the forecast should be treated as an estimate rather than a precise prediction.

### AI Insights

- Plain-English financial insights
- Spending pattern feedback
- Budgeting guidance
- Data-mode-aware recommendations

### Audit Log

The audit log records important user actions such as:

- Switching dataset mode
- Adding budgets
- Editing budgets
- Deleting budgets
- Adding manual transactions
- Uploading CSV data

---

## Technology Stack

### Frontend

- HTML
- CSS
- JavaScript
- Chart.js
- Supabase JavaScript client

### Backend

- Python
- FastAPI
- Uvicorn
- Pandas
- Scikit-learn
- Supabase REST API

### Database and Authentication

- Supabase Authentication
- Supabase Postgres
- Row Level Security policies
- User-specific data separation using `user_id`

### Deployment

- Backend: Render
- Frontend: Netlify or Vercel
- Authentication and database: Supabase

---

## Project Structure

```text
AI_Banking/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── services.py
│   │
│   ├── data/
│   │   ├── cleaned/
│   │   └── raw/
│   │
│   ├── database/
│   │   └── .gitkeep
│   │
│   ├── clean_data.py
│   └── requirements.txt
│
├── docs/
│   ├── architecture.md
│   └── github_setup.md
│
├── frontend/
│   ├── app.js
│   ├── build_config.js
│   ├── config.example.js
│   ├── config.js
│   ├── dev_server.py
│   ├── index.html
│   ├── netlify.toml
│   └── style.css
│
├── .env
├── .env.example
├── .gitignore
├── generate_config.py
├── README.md
├── start_backend.bat
└── start_frontend.bat
```

---

## Security Notes

This is a prototype project. It does not connect to real bank accounts and should not be used for real financial decision-making.

The project uses Supabase authentication and user-specific database records. Each user-related table stores rows using a `user_id` column.

Sensitive values must not be committed to GitHub.

Do not commit:

```text
.env
frontend/config.js
```

Commit only safe example files:

```text
.env.example
frontend/config.example.js
```

---

## Environment Variables

Create a `.env` file in the root project folder.

Example:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_or_publishable_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

The frontend `config.js` file is generated from `.env` using:

```bash
python generate_config.py
```

The frontend automatically chooses the correct backend API:

```text
Local frontend → http://127.0.0.1:8000
Deployed frontend → Render backend URL
```

This means the app can run locally and online without manually editing `config.js`.

---

## Supabase Tables

The project uses the following Supabase tables.

### app_settings

Stores each user’s active dataset mode.

Important columns:

```text
id
user_id
active_dataset
created_at
updated_at
```

### budgets

Stores monthly category budgets.

Important columns:

```text
id
user_id
month
monthly_income
category
budget_amount
created_at
updated_at
```

### manual_transactions

Stores transactions manually entered by the user.

Important columns:

```text
id
user_id
date
month
description
amount
transaction_type
category
payment_method
source
created_at
```

### uploaded_transactions

Stores cleaned CSV uploaded transactions.

Important columns:

```text
id
user_id
date
month
description
amount
transaction_type
category
payment_method
source
created_at
```

### audit_log

Stores important user actions.

Important columns:

```text
id
user_id
action
record_type
record_id
source
details
created_at
```

---

## Row Level Security Policies

The project uses Supabase Row Level Security policies so users can only access their own data.

Recommended policy setup:

### app_settings

```text
SELECT
INSERT
UPDATE
```

### audit_log

```text
SELECT
INSERT
```

### budgets

```text
SELECT
INSERT
UPDATE
DELETE
```

### manual_transactions

```text
SELECT
INSERT
```

### uploaded_transactions

```text
SELECT
INSERT
DELETE
```

Each policy should use logic based on:

```sql
auth.uid() = user_id
```

---

## Running the Project Locally

Use two terminals.

### Terminal 1 — Backend

```bash
cd ~/Projects2026/AI_Banking_project/AI_Banking/backend
source .venv/Scripts/activate
python -m uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Backend API documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 — Frontend

```bash
cd ~/Projects2026/AI_Banking_project/AI_Banking/frontend
python dev_server.py
```

Frontend runs at:

```text
http://127.0.0.1:5500
```

---

## Generating Frontend Config

Before running the frontend, generate `frontend/config.js` from `.env`:

```bash
cd ~/Projects2026/AI_Banking_project/AI_Banking
python generate_config.py
```

This creates:

```text
frontend/config.js
```

The generated file contains only the Supabase frontend configuration.

---

## Backend API Endpoints

### Health

```text
GET /health
```

### Data Status

```text
GET /data-status
```

### Dataset Mode

```text
POST /dataset-mode
```

### Dashboard

```text
GET /dashboard
```

### Budget

```text
GET /budget
POST /budget
PUT /budget/{budget_id}
DELETE /budget/{budget_id}
```

### Transactions

```text
GET /transactions
POST /transactions
```

### Analysis

```text
GET /analysis
```

### Forecast

```text
GET /forecast
```

### Insights

```text
GET /insights
```

### Audit Log

```text
GET /audit-log
```

### CSV Upload

```text
POST /upload-csv
```

---

## Deployment

### Backend Deployment — Render

The backend is deployed using Render.

Recommended Render settings:

```text
Environment: Python
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required Render environment variables:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

Backend health check:

```text
https://ai-banking-backend-x040.onrender.com/health
```

### Frontend Deployment — Netlify or Vercel

The frontend can be deployed using Netlify or Vercel.

For Netlify:

```text
Base directory: frontend
Publish directory: frontend
```

The frontend uses JavaScript to automatically choose the correct backend API based on the hostname:

```text
localhost or 127.0.0.1 → local backend
deployed site → Render backend
```

---

## Machine Learning Forecast

The app uses historical spending data to estimate next month’s spending.

The forecast includes:

- Next month prediction
- Mean Absolute Error
- R² score
- Actual vs predicted spending chart

The model is intended for demonstration and learning purposes. It should not be treated as financial advice.

A low R² score means the selected data has irregular spending patterns, so the forecast should be treated as an estimate rather than a precise prediction.

---

## Limitations

This is a prototype and has the following limitations:

- It does not connect to real bank accounts
- It does not use Open Banking
- It does not make real financial decisions
- Forecasting accuracy depends heavily on data quality
- A small or irregular dataset can reduce model accuracy
- Uploaded CSV files must be mapped correctly
- Manual transactions need enough history before machine learning results become meaningful

---

## Future Improvements

Possible future improvements include:

- Edit and delete manual transactions
- CSV transaction editing
- More advanced forecasting models
- Outlier detection
- Recurring transaction detection
- More detailed financial health scoring
- Email verification improvements
- Password reset flow
- Better deployment pipeline
- User profile page
- Export reports as PDF
- Admin dashboard for demonstration purposes

---

## Academic Value

This project demonstrates:

- Full-stack web development
- REST API development with FastAPI
- Frontend development with HTML, CSS and JavaScript
- Authentication with Supabase
- User-specific database design
- Row Level Security concepts
- Data cleaning and transformation
- CSV upload and column mapping
- Data visualisation with Chart.js
- Basic machine learning forecasting
- Model evaluation using MAE and R²
- Audit logging
- Deployment planning

---

## Disclaimer

AI Banking is an educational prototype. It is not a real banking application and should not be used for real financial management, banking operations or investment decisions.

No real bank login is used. No Open Banking connection is implemented. All data is demo, uploaded or manually entered by users.

---

## Author

Developed by Marian as an academic and portfolio project.