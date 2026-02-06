# Tax Prep - 2025 Federal Tax Return

A TurboTax-style tax preparation application for individual Form 1040 filers (tax year 2025). Guided interview wizard, tax calculation engine, IRS-compliant PDF generation, and OCR document import.

## Features

- **Guided Interview** - Step-by-step wizard: Personal Info, Income, Deductions, Credits, Review
- **Tax Engine** - Form-based dependency solver computing Form 1040, Schedules A/B/D, Schedule 1-3, Forms 8949/8812/8863/8880
- **Income Support** - W-2, 1099-INT, 1099-DIV, 1099-B (capital gains), 1099-R, 1099-G, SSA-1099
- **Deductions** - Standard deduction, full Schedule A itemized (medical, SALT with $40K cap, mortgage interest, charitable)
- **Credits** - Child Tax Credit ($2,200), AOTC ($2,500), Lifetime Learning ($2,000), Saver's Credit, EIC
- **PDF Generation** - Fills official IRS PDF templates + generates human-readable summary report
- **OCR Import** - Upload W-2/1099 PDFs, auto-extract data via OCR for review
- **Validation** - IRS rule checking: required fields, math consistency, deduction limits, credit eligibility
- **Filing Status** - Single and Married Filing Jointly

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite |
| Tax Engine | Custom form-based dependency solver with topological ordering |
| PDF | PyPDFForm (IRS templates), ReportLab (summary), pypdf (merge) |
| OCR | pdfplumber + pytesseract |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4 |
| State | Zustand + TanStack Query |
| Forms | React Hook Form |
| Deploy | Docker Compose |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- Tesseract OCR (`brew install tesseract` / `apt install tesseract-ocr`)
- Poppler (`brew install poppler` / `apt install poppler-utils`)

### Option 1: Docker Compose

```bash
cp .env.example .env
# Edit .env to set ENCRYPTION_KEY
docker compose up --build
```

Frontend: http://localhost:3000 | API: http://localhost:8000 | Docs: http://localhost:8000/docs

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Download IRS PDF templates
python ../scripts/download_irs_templates.py

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
cd backend
pytest -v
```

## Project Structure

```
Tax-Prep/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── tax_engine/      # Core tax calculation engine
│   │   │   ├── engine.py    # TaxEngine orchestrator
│   │   │   ├── solver.py    # Topological dependency solver
│   │   │   ├── parameters.py # 2025 tax brackets/limits/rates
│   │   │   └── forms/       # One module per IRS form
│   │   ├── interview/       # YAML-driven interview flow engine
│   │   ├── pdf/             # PDF generation + field mappings
│   │   ├── ocr/             # Document OCR pipeline
│   │   └── validation/      # IRS validation rules
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/             # API client layer
│       ├── components/      # React components
│       ├── pages/           # Route pages
│       ├── stores/          # Zustand state stores
│       └── types/           # TypeScript interfaces
├── scripts/                 # IRS template download + field inspection
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/returns` | Create a new tax return |
| GET | `/api/v1/returns` | List all tax returns |
| PUT | `/api/v1/returns/{id}/taxpayer` | Update taxpayer info |
| POST | `/api/v1/returns/{id}/income/w2` | Add a W-2 |
| PUT | `/api/v1/returns/{id}/deductions` | Upsert itemized deductions |
| POST | `/api/v1/returns/{id}/calculate` | Run tax calculation |
| GET | `/api/v1/returns/{id}/pdf/forms` | Download filled IRS PDFs |
| GET | `/api/v1/returns/{id}/pdf/summary` | Download summary report |
| POST | `/api/v1/returns/{id}/documents/upload` | Upload + OCR a document |
| POST | `/api/v1/returns/{id}/validate` | Validate return |
| GET | `/api/v1/returns/{id}/interview/current` | Get current interview step |

Full API docs available at http://localhost:8000/docs when running.

## 2025 Tax Parameters

- Standard deduction: $15,750 (Single) / $31,500 (MFJ)
- SALT cap: $40,000
- Child Tax Credit: $2,200 per qualifying child
- Capital loss limit: $3,000/year
- AOTC: up to $2,500 (40% refundable)
- Medical expense floor: 7.5% of AGI
