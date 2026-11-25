# RenalGuard — Explainable Clinical Risk Screening
**MCA Final Year Project | Streamlit + FastAPI + SQLite**

The app uses a streamlined runtime dependency set. Notebook and data-exploration tools are optional in `requirements-research.txt`.

> ⚠️ Academic prototype. NOT for clinical use. All findings require review by a qualified clinician.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend UI | Streamlit |
| Backend API | FastAPI |
| Database | SQLite (local, zero setup) |
| ML | scikit-learn · XGBoost · SHAP |
| Research notebooks | Jupyter (optional) |
| Reports | ReportLab (PDF) |

---

## Run in 4 Steps

### Step 1 — Install streamlined app dependencies
```cmd
pip install -r requirements.txt
```

### Step 2 — Train ML models
Place 3 CSV files in `ml/data/raw/` (download from Kaggle — see below), then:
```cmd
python ml\pipelines\train_models.py
```

### Step 3 — Seed the local database and start servers

**Terminal 1 — FastAPI backend:**
```cmd
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Seed local demo data (first time only):**
```cmd
python scripts\seed_db.py
```

**Terminal 3 — Next.js clinical frontend (recommended):**
```cmd
cd web
npm install
npm run dev
```

Open: **http://localhost:3000**

The Next.js app proxies `/api/*` requests to the FastAPI server, so no FastAPI CORS change is needed.

**Optional legacy Streamlit frontend:**
```cmd
cd frontend
streamlit run app.py
```

Open: **http://localhost:8501**

`renalguard.db` is created automatically in the project folder. PostgreSQL is not required.

**Login:**
- Doctor: `doctor@renalguard.dev` / `Doctor@1234`
- Admin:  `admin@renalguard.dev`  / `Admin@1234`

---

## Datasets (place in ml/data/raw/)

| File | Download |
|------|---------|
| `kidney_disease.csv` | https://www.kaggle.com/datasets/akshayksingh/kidney-disease-dataset |
| `diabetes_prediction.csv` | https://www.kaggle.com/datasets/iammustafatz/diabetes-prediction-dataset |
| `hypertension.csv` | https://www.kaggle.com/datasets/miadul/hypertension-risk-prediction-dataset |

---

## Run Tests
```cmd
pytest tests\test_core.py -v
```
Expected: **21 passed**

---

## Optional research notebooks
Notebook and plotting dependencies are deliberately separate from the deployed app:
```cmd
pip install -r requirements-research.txt
jupyter notebook notebooks\
```
| Notebook | Content |
|----------|---------|
| 01_data_inventory | Dataset overview |
| 02_ckd_eda | CKD exploratory analysis |
| 05_ckd_modeling | Model training & evaluation |
| 09_explainability | SHAP explanations |
| 10_integrated_risk_engine | ICRRI + rule engine demo |

---

## Project Structure
```
renalguard2/
├── backend/
│   ├── app/
│   │   ├── clinical/    engines.py (rules + ICRRI) · clinical_rules.yaml
│   │   ├── core/        config · security
│   │   ├── db/          session
│   │   ├── ml/          inference (SHAP)
│   │   ├── models/      ORM models
│   │   ├── schemas/     Pydantic schemas
│   │   └── services/    services · report (PDF)
│   └── main.py          FastAPI app (all routes)
├── frontend/
│   ├── app.py           Streamlit entry point
│   ├── api_client.py    HTTP client
│   └── pages/           dashboard · patients · assessment
│                        history · simulation · reports
│                        admin_users · admin_audit · admin_models
├── web/                 Next.js clinical intelligence frontend
│   └── src/app/         dashboard · patients · screening · insights
│                        simulations · reports · admin · API proxy
├── ml/
│   ├── data/raw/        Place Kaggle CSVs here
│   ├── models/          Trained .joblib files (after training)
│   └── pipelines/       train_models.py
├── notebooks/           5 Jupyter notebooks
├── scripts/             seed_db.py
├── tests/               test_core.py (21 tests)
└── requirements.txt
```
