import os

from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
API_KEY = os.getenv("API_KEY", "lm-studio")
MODEL_NAME = os.getenv("MODEL_NAME", "local-model")

SQL_DB_PATH = os.getenv("SQL_DB_PATH", "enterprise_hr.db")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_hr_db")

EMPLOYEES_CSV_PATH = os.getenv("EMPLOYEES_CSV_PATH", "data/employees.csv")
POLICIES_CSV_PATH = os.getenv("POLICIES_CSV_PATH", "data/hr_policies.csv")