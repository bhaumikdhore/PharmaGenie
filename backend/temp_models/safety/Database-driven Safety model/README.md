# Database-driven Safety Model

This is a small hackathon-ready Python project that demonstrates a **database-driven medicine safety model**.

Instead of using hardcoded Python lists like:

- `PRESCRIPTION_ONLY = [...]`

the safety agent reads a **real database table** with these columns:

- `requires_prescription` (bool)
- `controlled_level` (int)
- `max_daily_dosage` (int, in mg)

The safety agent then evaluates user input (medicine name + daily dosage) and returns a safety assessment.

## How to set up and run

1. **Create and activate a virtual environment (optional but recommended)**

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Initialize the database with sample data**

```bash
python -m safety_model.seed_data
```

4. **Run the demo safety checker**

```bash
python -m safety_model.main
```

You can then type a medicine name and daily dosage in mg and see if it is considered safe according to the database rules.

