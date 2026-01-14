from __future__ import annotations

import json
import os
import sys
import logging
import threading
from datetime import datetime
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional
from collections import defaultdict

import pandas as pd
import psycopg2
from psycopg2 import extras
from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

def resolve_base_dir() -> Path:
    env_base = os.getenv("FAIZAN_BASE_DIR")
    if env_base:
        return Path(env_base)
    if getattr(sys, "frozen", False) and getattr(sys, "executable", None):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = resolve_base_dir()
LOG_DIR = Path(os.getenv("LOCALAPPDATA") or BASE_DIR) / "FaizanReportStudio" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from backend.core.config_manager import ConfigManager
from backend.core.pdf_manager import PDFManager
from backend.core.helpers import calculate_age, calculate_years_studying, format_date
from backend.core.db_config import load_db_config, save_db_config

SAMPLE_EXCEL = BASE_DIR / "student_sample.xlsx"
FILTERS_FILE = BASE_DIR / "settings" / "filters.json"
REMARKS_FILE = BASE_DIR / "settings" / "remarks.json"
REQUIRED_STUDENT_COLUMNS = [
    "gr_no",
    "student_name",
    "father_name",
    "current_class_sec",
    "current_session",
    "date_of_birth",
    "contact_number_resident",
    "contact_number_neighbour",
    "contact_number_relative",
    "contact_number_other1",
    "contact_number_other2",
    "contact_number_other3",
    "contact_number_other4",
    "address",
]

def get_connection():
    config = load_db_config()
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", config.get("host")),
            dbname=os.getenv("DB_NAME", config.get("dbname")),
            user=os.getenv("DB_USER", config.get("user")),
            password=os.getenv("DB_PASSWORD", config.get("password")),
            port=int(os.getenv("DB_PORT", config.get("port", 5432))),
        )
    except Exception:
        logging.exception("Database connection failed")
        raise


def require_admin(request: Request):
    role = request.headers.get("x-user-role", "").lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def ensure_user_exists(user_id: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT user_id, role FROM users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


def set_user_teacher_role(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users SET role = 'teacher'
        WHERE user_id = %s AND role != 'admin'
        """,
        (user_id,),
    )
    conn.commit()
    conn.close()


def row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def migrate_principal_roles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE role = 'principal'")
    conn.commit()
    conn.close()


DATE_COLUMNS = {"date_of_birth"}


def normalize_cell(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "none", "null", "nan"}:
        return None
    return text


def parse_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if hasattr(value, "date") and callable(getattr(value, "date")):
        try:
            return value.date().isoformat()
        except Exception:
            pass
    text = normalize_cell(value)
    if not text:
        return None
    parts = [p for p in re.split(r"\D+", text) if p]
    if len(parts) != 3:
        return None
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    yearfirst = len(parts[0]) == 4
    if yearfirst:
        year, month, day = nums
    else:
        dayfirst = None
        if nums[0] > 12 and nums[1] <= 12:
            dayfirst = True
        elif nums[1] > 12 and nums[0] <= 12:
            dayfirst = False
        elif len(parts[2]) == 4:
            dayfirst = True
        else:
            dayfirst = True
        if dayfirst:
            day, month, year = nums
        else:
            month, day, year = nums
        if year < 100:
            year += 2000 if year < 50 else 1900
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def normalize_value(value: Any, column: str) -> Optional[str]:
    if column in DATE_COLUMNS:
        return parse_date(value)
    return normalize_cell(value)


def extract_student_rows(content: bytes) -> tuple[list[Dict[str, Optional[str]]], list[Optional[str]]]:
    try:
        df = pd.read_excel(BytesIO(content))
    except Exception as exc:  # pragma: no cover - pandas raises many error types
        raise HTTPException(status_code=400, detail=f"Unable to read Excel file: {exc}") from exc

    for column in REQUIRED_STUDENT_COLUMNS:
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {column}")

    rows = []
    row_errors: list[Optional[str]] = []
    for _, row in df.iterrows():
        error = None
        row_data = {}
        for column in REQUIRED_STUDENT_COLUMNS:
            value = row.get(column) if pd.notna(row.get(column)) else None
            normalized = normalize_value(value, column)
            if column in DATE_COLUMNS and value and not normalized:
                error = f"Invalid date in {column}: {value}"
            row_data[column] = normalized
        if row_data.get("gr_no"):
            row_data["gr_no"] = str(row_data["gr_no"]).strip()
        rows.append(row_data)
        row_errors.append(error)
    return rows, row_errors


class LoginRequest(BaseModel):
    username: str
    password: str


class ReportRequest(BaseModel):
    student_name: str = Field(..., alias="student_name")
    father_name: str
    class_sec: str
    session: str
    gr_no: str
    rank: str
    total_days: str
    days_attended: str
    days_absent: str
    term: str
    marks_data: Dict[str, Dict[str, Any]]
    conduct: str
    performance: str
    progress: str
    remarks: str
    status: str
    date: str
    grand_totals: Dict[str, Any]


class DiagnosticsRequest(BaseModel):
    student_name: str
    father_name: str
    class_sec: str
    gr_no: str
    rank: str
    total_days: str
    days_attended: str
    days_absent: str
    attendance_dates: str
    overall_remark: str
    term: str
    comment: str
    diagnostics_sections: list[Dict[str, Any]]


class FiltersPayload(BaseModel):
    filters: Dict[str, list[str]]


class RemarksPayload(BaseModel):
    presets: list[str]


class DbConfigPayload(BaseModel):
    host: str
    port: int = 5432
    dbname: str
    user: str
    password: str
    output_dir: Optional[str] = None


class UserCreatePayload(BaseModel):
    username: str
    password: str
    role: str = "teacher"


class UserUpdatePayload(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordResetPayload(BaseModel):
    password: str


class PasswordChangePayload(BaseModel):
    current_password: str
    new_password: str


class UserAccountPayload(BaseModel):
    username: str
    password: str
    role: str = "teacher"
    full_name: str


class UserAccountUpdatePayload(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


class StudentUpdateRequest(BaseModel):
    student_name: Optional[str] = None
    father_name: Optional[str] = None
    current_class_sec: Optional[str] = None
    current_session: Optional[str] = None
    status: Optional[str] = None
    date_of_birth: Optional[str] = None
    joining_date: Optional[str] = None
    left_date: Optional[str] = None
    left_reason: Optional[str] = None
    contact_number_resident: Optional[str] = None
    contact_number_neighbour: Optional[str] = None
    contact_number_relative: Optional[str] = None
    contact_number_other1: Optional[str] = None
    contact_number_other2: Optional[str] = None
    contact_number_other3: Optional[str] = None
    contact_number_other4: Optional[str] = None
    address: Optional[str] = None


app = FastAPI(
    title="Faizan Report Studio API",
    version="2.0.0",
    description="Backend service powering the Discord-inspired React client",
)

app.mount("/templates", StaticFiles(directory=str(PDFManager.TEMPLATES_DIR)), name="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_report_queue_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS report_queue (
            id SERIAL PRIMARY KEY,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    conn.commit()
    conn.close()


def ensure_report_results_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS report_results (
            id SERIAL PRIMARY KEY,
            gr_no TEXT,
            student_name TEXT,
            class_sec TEXT,
            session TEXT,
            term TEXT,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    conn.commit()
    conn.close()


def ensure_diagnostics_queue_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnostics_queue (
            id SERIAL PRIMARY KEY,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def initialize_report_queue():
    def init_task():
        try:
            ensure_report_queue_table()
            ensure_report_results_table()
            ensure_diagnostics_queue_table()
            migrate_principal_roles()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM report_queue")
            cursor.execute("DELETE FROM diagnostics_queue")
            conn.commit()
            conn.close()
        except Exception as exc:  # pragma: no cover
            print(f"Unable to prepare queue tables: {exc}")

    threading.Thread(target=init_task, daemon=True).start()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/db/config")
def get_db_config():
    return load_db_config()


@app.put("/db/config")
def update_db_config(payload: DbConfigPayload):
    return save_db_config(payload.dict(exclude_none=True))


@app.post("/auth/login")
def login(payload: LoginRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        cursor.execute(
            """
            SELECT user_id, role FROM users 
            WHERE username = %s AND password = %s AND is_active = TRUE
            """,
            (payload.username, payload.password),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"user_id": user["user_id"], "role": user["role"], "username": payload.username}
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Login failed")
        raise HTTPException(status_code=500, detail=f"Login failed: {exc}")


@app.get("/students")
def list_students(
    search: Optional[str] = None,
    class_sec: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 15,
    offset: int = 0,
):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

    query = """
        SELECT gr_no, student_name, father_name, 
               current_class_sec, current_session, status, 
               contact_number_resident as contact, address
        FROM students
    """
    count_query = "SELECT COUNT(*) as total FROM students"
    
    clauses = []
    params: list[Any] = []

    if search:
        like = f"%{search}%"
        clauses.append(
            "("
            "student_name ILIKE %s OR father_name ILIKE %s OR gr_no ILIKE %s OR current_class_sec ILIKE %s OR "
            "contact_number_resident ILIKE %s OR contact_number_neighbour ILIKE %s OR "
            "contact_number_relative ILIKE %s OR contact_number_other1 ILIKE %s OR "
            "contact_number_other2 ILIKE %s OR contact_number_other3 ILIKE %s OR contact_number_other4 ILIKE %s"
            ")"
        )
        params.extend([like] * 11)
    if class_sec and class_sec.lower() != "all":
        clauses.append("current_class_sec = %s")
        params.append(class_sec)
    if status and status.lower() != "all":
        clauses.append("status = %s")
        params.append(status)

    if clauses:
        where_clause = " WHERE " + " AND ".join(clauses)
        query += where_clause
        count_query += where_clause

    # Get total count
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    # Add ordering and pagination
    query += " ORDER BY LOWER(student_name)"
    query += f" LIMIT {limit} OFFSET {offset}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return {
        "students": [row_to_dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/students/classes")
def list_classes():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT DISTINCT current_class_sec FROM students WHERE current_class_sec IS NOT NULL")
    rows = [row["current_class_sec"] for row in cursor.fetchall() if row["current_class_sec"]]
    conn.close()

    custom_order = [
        "NURA",
        "NURB",
        "KGA",
        "KGB",
        "KGIA",
        "KGIB",
        "KGIIA",
        "KGIIB",
        "IA",
        "IB",
        "IC",
        "IIA",
        "IIB",
        "IIC",
        "IIIAN",
        "IIIBN",
        "IVAN",
        "IVBN",
        "VAN",
        "VBN",
        "IIIA",
        "IIIB",
        "IVA",
        "IVB",
        "VA",
        "VB",
        "VIA",
        "VIB",
        "VIIA",
        "VIIB",
        "VIIIA",
        "VIIIB",
        "IXA",
        "IXB",
        "XA",
        "XB",
        "FDHIIIA",
        "FDHIIIB",
        "FDHIVA",
        "FDHIVB",
        "FDHVA",
        "FDHVB",
    ]

    def normalize(value: str) -> str:
        return value.upper().replace(" ", "").replace("-", "")

    sorted_classes: list[str] = []
    seen = set()
    for preferred in custom_order:
        for cls in rows:
            if normalize(cls) == preferred and cls not in seen:
                sorted_classes.append(cls)
                seen.add(cls)

    for cls in rows:
        if cls not in seen:
            sorted_classes.append(cls)

    return sorted_classes


@app.get("/students/stats")
def student_stats():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS active FROM students WHERE status = 'Active'")
    active = cursor.fetchone()["active"]
    cursor.execute("SELECT COUNT(*) AS inactive FROM students WHERE status != 'Active'")
    inactive = cursor.fetchone()["inactive"]
    conn.close()
    return {"total": total, "active": active, "inactive": inactive}


@app.get("/students/sample")
def sample_excel():
    output_dir = PDFManager.ensure_output_dir()
    filename = "student_sample.xlsx"
    file_path = output_dir / filename
    sample = pd.DataFrame(columns=REQUIRED_STUDENT_COLUMNS)
    sample.to_excel(file_path, index=False)
    return {
        "message": "Sample Excel saved",
        "file": filename,
    }


@app.get("/students/export")
def export_students():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT gr_no, student_name, father_name, current_class_sec, current_session,
               date_of_birth, contact_number_resident, contact_number_neighbour,
               contact_number_relative, contact_number_other1, contact_number_other2,
               contact_number_other3, contact_number_other4, address
        FROM students
        ORDER BY LOWER(student_name)
        """
    )
    rows = cursor.fetchall()
    conn.close()

    data = [row_to_dict(row) for row in rows]
    df = pd.DataFrame(data, columns=REQUIRED_STUDENT_COLUMNS)
    output_dir = PDFManager.ensure_output_dir()
    filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = output_dir / filename
    df.to_excel(file_path, index=False)
    return {
        "message": "Students exported",
        "file": filename,
    }


@app.get("/students/{gr_no}")
def student_detail(gr_no: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT student_id, gr_no, student_name, father_name, current_class_sec, current_session, 
               status, joining_date, left_date, left_reason, date_of_birth, 
               contact_number_resident, contact_number_neighbour, contact_number_relative,
               contact_number_other1, contact_number_other2, contact_number_other3,
               contact_number_other4, address, created_at, updated_at
        FROM students WHERE gr_no = %s
        """,
        (gr_no,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    detail = row_to_dict(row)
    detail["date_of_birth_display"] = format_date(detail.get("date_of_birth"))
    detail["joining_date_display"] = format_date(detail.get("joining_date"))
    detail["left_date_display"] = format_date(detail.get("left_date"))
    detail["age_display"] = calculate_age(detail.get("date_of_birth"))
    detail["years_studying"] = calculate_years_studying(detail.get("joining_date"))

    contact_fields = [
        ("Resident", detail.get("contact_number_resident")),
        ("Neighbour", detail.get("contact_number_neighbour")),
        ("Relative", detail.get("contact_number_relative")),
        ("Other 1", detail.get("contact_number_other1")),
        ("Other 2", detail.get("contact_number_other2")),
        ("Other 3", detail.get("contact_number_other3")),
        ("Other 4", detail.get("contact_number_other4")),
    ]
    detail["contacts"] = [
        {"label": label, "value": number}
        for label, number in contact_fields
        if number and str(number).strip().lower() not in {"", "none", "null", "nan"}
    ]
    return detail


@app.put("/students/{gr_no}")
def update_student(gr_no: str, payload: StudentUpdateRequest):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    # Check if student exists
    cursor.execute("SELECT student_id FROM students WHERE gr_no = %s", (gr_no,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Student with G.R No '{gr_no}' not found")
    
    # Build dynamic update query based on provided fields
    update_fields = []
    params = []
    
    for field, value in payload.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = %s")
        params.append(value)
    
    if not update_fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Add updated_at timestamp
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(gr_no)
    
    query = f"UPDATE students SET {', '.join(update_fields)} WHERE gr_no = %s"
    
    try:
        cursor.execute(query, params)
        conn.commit()
        
        # Fetch and return updated student
        cursor.execute(
            """
            SELECT student_id, gr_no, student_name, father_name, current_class_sec, current_session, 
                   status, joining_date, left_date, left_reason, date_of_birth, 
            contact_number_resident, contact_number_neighbour, contact_number_relative,
            contact_number_other1, contact_number_other2, contact_number_other3,
            contact_number_other4, address, created_at, updated_at
            FROM students WHERE gr_no = %s
            """,
            (gr_no,),
        )
        row = cursor.fetchone()
        conn.close()
        
        detail = row_to_dict(row)
        detail["date_of_birth_display"] = format_date(detail.get("date_of_birth"))
        detail["joining_date_display"] = format_date(detail.get("joining_date"))
        detail["left_date_display"] = format_date(detail.get("left_date"))
        detail["age_display"] = calculate_age(detail.get("date_of_birth"))
        detail["years_studying"] = calculate_years_studying(detail.get("joining_date"))
        
        contact_fields = [
            ("Resident", detail.get("contact_number_resident")),
            ("Neighbour", detail.get("contact_number_neighbour")),
            ("Relative", detail.get("contact_number_relative")),
            ("Other 1", detail.get("contact_number_other1")),
            ("Other 2", detail.get("contact_number_other2")),
            ("Other 3", detail.get("contact_number_other3")),
            ("Other 4", detail.get("contact_number_other4")),
        ]
        detail["contacts"] = [
            {"label": label, "value": number}
            for label, number in contact_fields
            if number and str(number).strip().lower() not in {"", "none", "null", "nan"}
        ]
        
        return detail
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update student: {exc}")


@app.delete("/students/{gr_no}")
def delete_student(gr_no: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT student_id FROM students WHERE gr_no = %s", (gr_no,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        cursor.execute("DELETE FROM students WHERE gr_no = %s", (gr_no,))
        conn.commit()
        return {"status": "ok", "message": f"Student '{gr_no}' deleted successfully"}
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to delete student: {exc}")
    finally:
        conn.close()


@app.post("/students/import")
async def import_students(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")

    content = await file.read()
    rows, row_errors = extract_student_rows(content)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    success = 0
    errors: list[str] = []

    for idx, row in enumerate(rows):
        if row_errors[idx]:
            errors.append(f"Row {idx + 2}: {row_errors[idx]}")
            continue
        if not row.get("gr_no"):
            errors.append(f"Row {idx + 2}: Missing G.R No")
            continue
        try:
            cursor.execute(
                """
                INSERT INTO students (
                    gr_no, student_name, father_name, current_class_sec, current_session,
                    date_of_birth, contact_number_resident, contact_number_neighbour,
                    contact_number_relative, contact_number_other1, contact_number_other2,
                    contact_number_other3, contact_number_other4, address
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    tuple(row.get(column) for column in REQUIRED_STUDENT_COLUMNS),
            )
            success += 1
        except psycopg2.IntegrityError:
            errors.append(f"Row {idx + 2}: G.R No {row.get('gr_no')} already exists")
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"Row {idx + 2}: {exc}")

    conn.commit()
    conn.close()

    return {"imported": success, "errors": errors}


@app.post("/students/import/preview")
async def preview_import(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")

    content = await file.read()
    rows, row_errors = extract_student_rows(content)

    gr_nos = [row.get("gr_no") for row in rows if row.get("gr_no")]
    dup_counts = {}
    for gr_no in gr_nos:
        dup_counts[gr_no] = dup_counts.get(gr_no, 0) + 1
    duplicates = {gr_no for gr_no, count in dup_counts.items() if count > 1}

    existing = {}
    if gr_nos:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        cursor.execute(
            f"""
            SELECT {", ".join(REQUIRED_STUDENT_COLUMNS)}
            FROM students
            WHERE gr_no = ANY(%s)
            """,
            (gr_nos,),
        )
        for row in cursor.fetchall():
            existing[row["gr_no"]] = row_to_dict(row)
        conn.close()

    preview_rows = []
    counts = {"new": 0, "update": 0, "conflict": 0, "skip": 0, "error": 0}

    for idx, row in enumerate(rows):
        gr_no = row.get("gr_no")
        entry = {
            "rowIndex": idx + 2,
            "gr_no": gr_no,
            "status": "new",
            "diffs": {},
            "name_conflict": False,
            "excel": row,
            "db": existing.get(gr_no),
            "error": None,
        }

        if row_errors[idx]:
            entry["status"] = "error"
            entry["error"] = row_errors[idx]
            counts["error"] += 1
            preview_rows.append(entry)
            continue

        if not gr_no:
            entry["status"] = "error"
            entry["error"] = "Missing G.R No"
            counts["error"] += 1
            preview_rows.append(entry)
            continue

        if gr_no in duplicates:
            entry["status"] = "error"
            entry["error"] = "Duplicate G.R No in file"
            counts["error"] += 1
            preview_rows.append(entry)
            continue

        if gr_no not in existing:
            entry["status"] = "new"
            counts["new"] += 1
            preview_rows.append(entry)
            continue

        db_row = existing[gr_no]
        diffs = {}
        for column in REQUIRED_STUDENT_COLUMNS:
            excel_val = row.get(column)
            db_val = db_row.get(column)
            if normalize_value(excel_val, column) != normalize_value(db_val, column):
                diffs[column] = {"excel": excel_val, "db": db_val}

        if not diffs:
            entry["status"] = "skip"
            counts["skip"] += 1
        else:
            entry["status"] = "update"
            counts["update"] += 1
            if "student_name" in diffs:
                entry["status"] = "conflict"
                entry["name_conflict"] = True
                counts["conflict"] += 1
                counts["update"] -= 1

        entry["diffs"] = diffs
        preview_rows.append(entry)

    return {
        "summary": {
            "total": len(rows),
            "new": counts["new"],
            "update": counts["update"],
            "conflict": counts["conflict"],
            "skip": counts["skip"],
            "error": counts["error"],
        },
        "rows": preview_rows,
    }


@app.post("/students/import/apply")
async def apply_import(file: UploadFile = File(...), decisions: str = Form(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx or .xls)")

    content = await file.read()
    rows, row_errors = extract_student_rows(content)
    try:
        decision_data = json.loads(decisions)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid decisions payload: {exc}") from exc

    decision_map = {item.get("gr_no"): item for item in decision_data or []}
    gr_nos = [row.get("gr_no") for row in rows if row.get("gr_no")]

    existing = {}
    if gr_nos:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        cursor.execute(
            f"""
            SELECT {", ".join(REQUIRED_STUDENT_COLUMNS)}
            FROM students
            WHERE gr_no = ANY(%s)
            """,
            (gr_nos,),
        )
        for row in cursor.fetchall():
            existing[row["gr_no"]] = row_to_dict(row)
    else:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

    applied = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    errors = []
    seen = set()

    for idx, row in enumerate(rows):
        gr_no = row.get("gr_no")
        if row_errors[idx]:
            applied["errors"] += 1
            errors.append(f"Row {idx + 2}: {row_errors[idx]}")
            continue
        if not gr_no:
            applied["errors"] += 1
            errors.append(f"Row {idx + 2}: Missing G.R No")
            continue
        if gr_no in seen:
            applied["errors"] += 1
            errors.append(f"Row {idx + 2}: Duplicate G.R No in file")
            continue
        seen.add(gr_no)

        decision = decision_map.get(gr_no, {})
        action = decision.get("action", "skip")
        name_choice = decision.get("nameChoice", "excel")

        if action == "skip":
            applied["skipped"] += 1
            continue

        exists = gr_no in existing
        if exists:
            if action == "insert":
                applied["errors"] += 1
                errors.append(f"Row {idx + 2}: G.R No already exists (cannot insert)")
                continue
            if name_choice == "db":
                row["student_name"] = existing[gr_no].get("student_name")

            try:
                cursor.execute(
                    f"""
                    UPDATE students
                    SET {", ".join([f"{col} = %s" for col in REQUIRED_STUDENT_COLUMNS if col != "gr_no"])}
                    WHERE gr_no = %s
                    """,
                    tuple(
                        row.get(col) for col in REQUIRED_STUDENT_COLUMNS if col != "gr_no"
                    )
                    + (gr_no,),
                )
                applied["updated"] += 1
            except Exception as exc:
                applied["errors"] += 1
                errors.append(f"Row {idx + 2}: {exc}")
        else:
            if action == "skip":
                applied["skipped"] += 1
                continue
            try:
                cursor.execute(
                    """
                    INSERT INTO students (
                        gr_no, student_name, father_name, current_class_sec, current_session,
                        date_of_birth, contact_number_resident, contact_number_neighbour,
                        contact_number_relative, contact_number_other1, contact_number_other2,
                        contact_number_other3, contact_number_other4, address
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    tuple(row.get(column) for column in REQUIRED_STUDENT_COLUMNS),
                )
                applied["inserted"] += 1
            except Exception as exc:
                applied["errors"] += 1
                errors.append(f"Row {idx + 2}: {exc}")

    conn.commit()
    conn.close()

    return {"status": "ok", "applied": applied, "errors": errors}


@app.get("/subjects")
def list_subjects():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT subject_id, subject_name, type FROM subjects ORDER BY subject_name")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "type": row["type"],
        }
        for row in rows
    ]


class SubjectCreateRequest(BaseModel):
    subject_name: str
    type: str = "Core"


class SubjectUpdateRequest(BaseModel):
    new_name: str
    type: str


@app.post("/subjects")
def create_subject(payload: SubjectCreateRequest):
    if not payload.subject_name or not payload.subject_name.strip():
        raise HTTPException(status_code=400, detail="Subject name cannot be empty")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    try:
        cursor.execute(
            "INSERT INTO subjects (subject_name, type) VALUES (%s, %s)",
            (payload.subject_name.strip(), payload.type)
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "subject_name": payload.subject_name.strip(), "type": payload.type}
    except psycopg2.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Subject '{payload.subject_name}' already exists")
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to create subject: {exc}")


@app.put("/subjects/{subject_name}")
def update_subject(subject_name: str, payload: SubjectUpdateRequest):
    if not payload.new_name or not payload.new_name.strip():
        raise HTTPException(status_code=400, detail="Subject name cannot be empty")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    # Check if the subject exists
    cursor.execute("SELECT subject_name FROM subjects WHERE subject_name = %s", (subject_name,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Subject '{subject_name}' not found")
    
    try:
        cursor.execute(
            "UPDATE subjects SET subject_name = %s, type = %s WHERE subject_name = %s",
            (payload.new_name.strip(), payload.type, subject_name)
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "subject_name": payload.new_name.strip(), "type": payload.type}
    except psycopg2.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Subject '{payload.new_name}' already exists")
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update subject: {exc}")


@app.delete("/subjects/{subject_name}")
def delete_subject(subject_name: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    # Check if the subject exists
    cursor.execute("SELECT subject_name FROM subjects WHERE subject_name = %s", (subject_name,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Subject '{subject_name}' not found")
    
    try:
        cursor.execute("DELETE FROM subjects WHERE subject_name = %s", (subject_name,))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Subject '{subject_name}' deleted successfully"}
    except Exception as exc:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete subject: {exc}")



@app.get("/config")
def get_config():
    return ConfigManager.load()


@app.put("/config")
def update_config(data: Dict[str, Any]):
    if not ConfigManager.save(data):
        raise HTTPException(status_code=500, detail="Unable to save config")
    return {"status": "ok"}


@app.get("/filters")
def get_filters():
    if FILTERS_FILE.exists():
        with open(FILTERS_FILE, "r", encoding="utf-8") as handle:
            return {"filters": json.load(handle)}
    return {"filters": {}}


@app.put("/filters")
def save_filters(payload: FiltersPayload):
    FILTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FILTERS_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload.filters, handle, indent=2)
    return {"status": "ok"}


@app.get("/remarks")
def get_remarks():
    if REMARKS_FILE.exists():
        with open(REMARKS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return {"presets": data.get("presets", [])}
    return {"presets": []}


@app.put("/remarks")
def save_remarks(payload: RemarksPayload):
    REMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REMARKS_FILE, "w", encoding="utf-8") as handle:
        json.dump({"presets": payload.presets}, handle, indent=2)
    return {"status": "ok"}


@app.post("/reports/save")
def save_report(payload: ReportRequest, overwrite: bool = False):
    data = payload.dict(by_alias=True)
    gr_no = data.get("gr_no")
    session = data.get("session")
    term = data.get("term")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT id, payload FROM report_results
            WHERE gr_no = %s AND session = %s AND term = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (gr_no, session, term),
        )
        history_row = cursor.fetchone()

        cursor.execute(
            """
            SELECT id, payload FROM report_queue
            WHERE (payload->>'gr_no') = %s AND (payload->>'session') = %s AND (payload->>'term') = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (gr_no, session, term),
        )
        queue_row = cursor.fetchone()

        if history_row and not overwrite:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"{term} result for session {session} already exists for this student.",
                    "type": "history",
                    "result_id": history_row["id"],
                },
            )
        if queue_row and not overwrite:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"{term} result for session {session} is already saved in the queue.",
                    "type": "queue",
                    "queue_id": queue_row["id"],
                    "payload": queue_row["payload"],
                },
            )

        if overwrite and history_row:
            cursor.execute(
                """
                UPDATE report_results
                SET payload = %s, student_name = %s, class_sec = %s, session = %s, term = %s, gr_no = %s
                WHERE id = %s
                """,
                (
                    json.dumps(data),
                    data.get("student_name"),
                    data.get("class_sec"),
                    session,
                    term,
                    gr_no,
                    history_row["id"],
                ),
            )
            if queue_row:
                cursor.execute(
                    "UPDATE report_queue SET payload = %s WHERE id = %s",
                    (json.dumps(data), queue_row["id"]),
                )
            else:
                cursor.execute("INSERT INTO report_queue (payload) VALUES (%s)", (json.dumps(data),))
        elif overwrite and queue_row:
            cursor.execute(
                "UPDATE report_queue SET payload = %s WHERE id = %s",
                (json.dumps(data), queue_row["id"]),
            )
        else:
            cursor.execute("INSERT INTO report_queue (payload) VALUES (%s)", (json.dumps(data),))

        cursor.execute("SELECT COUNT(*) AS count FROM report_queue")
        count = cursor.fetchone()["count"]
        conn.commit()
        return {"status": "ok", "count": count}
    finally:
        conn.close()


@app.get("/reports/queue")
def report_queue():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM report_queue")
    count = cursor.fetchone()[0]
    conn.close()
    return {"count": count}


@app.get("/reports/queue/items")
def report_queue_items():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT id, payload FROM report_queue ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return {"items": [row_to_dict(row) for row in rows]}


@app.delete("/reports/queue")
def clear_report_queue():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM report_queue")
        conn.commit()
        return {"status": "ok", "count": 0}
    finally:
        conn.close()


@app.put("/reports/queue/{queue_id}")
def update_report_queue(queue_id: int, payload: ReportRequest):
    data = payload.dict(by_alias=True)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE report_queue SET payload = %s WHERE id = %s", (json.dumps(data), queue_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Queued report not found")
        cursor.execute("SELECT COUNT(*) AS count FROM report_queue")
        count = cursor.fetchone()[0]
        conn.commit()
        return {"status": "ok", "count": count}
    finally:
        conn.close()


@app.get("/reports/queue/{queue_id}/pdf")
def report_queue_pdf(queue_id: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute("SELECT payload FROM report_queue WHERE id = %s", (queue_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Queued report not found")
        payload = row["payload"]
        safe_name = str(payload.get("student_name", "student")).replace(" ", "_")
        session = payload.get("session", "session")
        filename = f"{safe_name}_Report_{session}_queue_{queue_id}"
        success, message, pdf_path = PDFManager.generate_pdf(
            filename,
            payload,
            template_name="report_card.html",
        )
        if not success:
            raise HTTPException(status_code=500, detail=message)
        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    finally:
        conn.close()


@app.get("/reports/history/{gr_no}")
def report_history(gr_no: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT id, gr_no, student_name, class_sec, session, term, created_at, payload
        FROM report_results
        WHERE gr_no = %s
        ORDER BY created_at DESC
        """,
        (gr_no,),
    )
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        payload = row.get("payload") or {}
        items.append(
            {
                "id": row["id"],
                "gr_no": row.get("gr_no"),
                "student_name": row.get("student_name"),
                "class_sec": row.get("class_sec"),
                "session": row.get("session"),
                "term": row.get("term"),
                "date": payload.get("date"),
                "created_at": row.get("created_at"),
            }
        )
    return {"items": items}


@app.get("/reports/history")
def report_history_all():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT id, gr_no, student_name, class_sec, session, term, created_at, payload
        FROM report_results
        ORDER BY session DESC, class_sec ASC, term ASC, created_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        payload = row.get("payload") or {}
        items.append(
            {
                "id": row["id"],
                "gr_no": row.get("gr_no"),
                "student_name": row.get("student_name"),
                "class_sec": row.get("class_sec"),
                "session": row.get("session"),
                "term": row.get("term"),
                "date": payload.get("date"),
                "created_at": row.get("created_at"),
            }
        )
    return {"items": items}


@app.get("/admin/users")
def list_users(request: Request):
    require_admin(request)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT user_id, username, role, password, is_active, created_at
        FROM users
        ORDER BY LOWER(username)
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return {"users": [row_to_dict(row) for row in rows]}


@app.get("/admin/user-accounts")
def list_user_accounts(request: Request):
    require_admin(request)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT user_id, username, role, password, is_active, full_name
        FROM users
        ORDER BY LOWER(username)
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return {"users": [row_to_dict(row) for row in rows]}


@app.post("/admin/user-accounts")
def create_user_account(payload: UserAccountPayload, request: Request):
    require_admin(request)
    if payload.role not in {"admin", "teacher"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute(
            """
            INSERT INTO users (username, password, role, is_active, full_name)
            VALUES (%s, %s, %s, TRUE, %s)
            RETURNING user_id, username, role, password, is_active, full_name
            """,
            (payload.username.strip(), payload.password, payload.role, payload.full_name.strip()),
        )
        user = cursor.fetchone()
        conn.commit()
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.put("/admin/user-accounts/{user_id}")
def update_user_account(user_id: int, payload: UserAccountUpdatePayload, request: Request):
    require_admin(request)
    updates = []
    params = []
    if payload.username is not None:
        updates.append("username = %s")
        params.append(payload.username.strip())
    if payload.role is not None:
        if payload.role not in {"admin", "teacher"}:
            raise HTTPException(status_code=400, detail="Invalid role")
        updates.append("role = %s")
        params.append(payload.role)
    if payload.password is not None:
        updates.append("password = %s")
        params.append(payload.password)
    if payload.is_active is not None:
        updates.append("is_active = %s")
        params.append(payload.is_active)
    if payload.full_name is not None:
        updates.append("full_name = %s")
        params.append(payload.full_name.strip())

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        if updates:
            params.append(user_id)
            cursor.execute(
                f"""
                UPDATE users
                SET {", ".join(updates)}
                WHERE user_id = %s
                RETURNING user_id, username, role, password, is_active
                """,
                params,
            )
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            cursor.execute(
                "SELECT user_id, username, role, password, is_active FROM users WHERE user_id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        conn.commit()
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.post("/admin/users")
def create_user(payload: UserCreatePayload, request: Request):
    require_admin(request)
    if payload.role not in {"admin", "teacher"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute(
            """
            INSERT INTO users (username, password, role, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING user_id, username, role, is_active
            """,
            (payload.username.strip(), payload.password, payload.role),
        )
        user = cursor.fetchone()
        conn.commit()
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.put("/admin/users/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, request: Request):
    require_admin(request)
    updates = []
    params = []
    if payload.username is not None:
        updates.append("username = %s")
        params.append(payload.username.strip())
    if payload.role is not None:
        if payload.role not in {"admin", "teacher"}:
            raise HTTPException(status_code=400, detail="Invalid role")
        updates.append("role = %s")
        params.append(payload.role)
    if payload.is_active is not None:
        updates.append("is_active = %s")
        params.append(payload.is_active)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(user_id)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute(
            f"""
            UPDATE users
            SET {", ".join(updates)}
            WHERE user_id = %s
            RETURNING user_id, username, role, is_active
            """,
            params,
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        return user
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.put("/admin/users/{user_id}/password")
def reset_user_password(user_id: int, payload: PasswordResetPayload, request: Request):
    require_admin(request)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        UPDATE users
        SET password = %s
        WHERE user_id = %s
        RETURNING user_id, username
        """,
        (payload.password, user_id),
    )
    user = cursor.fetchone()
    conn.commit()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user_id": user["user_id"], "username": user["username"]}


@app.put("/users/me/password")
def change_own_password(payload: PasswordChangePayload, request: Request):
    username = request.headers.get("x-user-name")
    if not username:
        raise HTTPException(status_code=401, detail="Missing user context")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(
        """
        SELECT user_id FROM users WHERE username = %s AND password = %s
        """,
        (username, payload.current_password),
    )
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Current password incorrect")
    cursor.execute(
        """
        UPDATE users SET password = %s WHERE user_id = %s
        """,
        (payload.new_password, user["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/reports/analytics")
def report_analytics(
    session: Optional[str] = None,
    class_sec: Optional[str] = None,
    term: Optional[str] = None,
    search: Optional[str] = None,
):
    def parse_pct(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace("%", "")
        try:
            return float(text)
        except ValueError:
            return 0.0

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

    query = """
        SELECT id, gr_no, student_name, class_sec, session, term, created_at, payload
        FROM report_results
    """
    clauses = []
    params: list[Any] = []
    if session:
        clauses.append("session = %s")
        params.append(session)
    if class_sec:
        clauses.append("class_sec = %s")
        params.append(class_sec)
    if term:
        clauses.append("term = %s")
        params.append(term)
    if search:
        like = f"%{search}%"
        clauses.append("(student_name ILIKE %s OR gr_no ILIKE %s)")
        params.extend([like, like])

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    grade_counts: dict[str, int] = defaultdict(int)
    session_agg: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "sum_pct": 0.0})
    class_agg: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "sum_pct": 0.0})
    term_agg: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "sum_pct": 0.0})
    timeline_agg: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "sum_pct": 0.0})
    subject_agg: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "sum_pct": 0.0})
    available_sessions = set()
    available_classes = set()
    available_terms = set()

    total_pct = 0.0
    total_count = 0
    recent = []

    for row in rows:
        payload = row.get("payload") or {}
        totals = payload.get("grand_totals") or {}
        pct = parse_pct(totals.get("pct"))
        grade = totals.get("grade") or "N/A"

        total_pct += pct
        total_count += 1
        grade_counts[grade] += 1

        session_key = row.get("session") or "Unknown"
        class_key = row.get("class_sec") or "Unknown"
        term_key = row.get("term") or "Unknown"
        timeline_key = f"{session_key} | {term_key}"

        session_agg[session_key]["count"] += 1
        session_agg[session_key]["sum_pct"] += pct
        class_agg[class_key]["count"] += 1
        class_agg[class_key]["sum_pct"] += pct
        term_agg[term_key]["count"] += 1
        term_agg[term_key]["sum_pct"] += pct
        timeline_agg[timeline_key]["count"] += 1
        timeline_agg[timeline_key]["sum_pct"] += pct

        available_sessions.add(session_key)
        available_classes.add(class_key)
        available_terms.add(term_key)

        marks_data = payload.get("marks_data") or {}
        if isinstance(marks_data, dict):
            for subject, data in marks_data.items():
                subject_pct = parse_pct((data or {}).get("pct"))
                subject_agg[subject]["count"] += 1
                subject_agg[subject]["sum_pct"] += subject_pct

        recent.append(
            {
                "id": row.get("id"),
                "gr_no": row.get("gr_no"),
                "student_name": row.get("student_name"),
                "class_sec": row.get("class_sec"),
                "session": row.get("session"),
                "term": row.get("term"),
                "pct": round(pct, 1),
                "grade": grade,
                "created_at": row.get("created_at"),
            }
        )

    def agg_to_list(source: dict[str, dict[str, float]], key_name: str) -> list[dict[str, Any]]:
        items = []
        for key, data in source.items():
            count = data["count"]
            avg_pct = round(data["sum_pct"] / count, 1) if count else 0.0
            items.append({key_name: key, "count": count, "avg_pct": avg_pct})
        return sorted(items, key=lambda item: (-item["count"], item[key_name]))

    summary = {
        "total_results": total_count,
        "avg_pct": round(total_pct / total_count, 1) if total_count else 0.0,
        "grade_counts": dict(grade_counts),
    }

    response = {
        "summary": summary,
        "sessions": agg_to_list(session_agg, "session"),
        "classes": agg_to_list(class_agg, "class_sec"),
        "terms": agg_to_list(term_agg, "term"),
        "timeline": agg_to_list(timeline_agg, "period"),
        "subjects": agg_to_list(subject_agg, "subject"),
        "recent": recent[:50],
        "available": {
            "sessions": sorted(available_sessions),
            "classes": sorted(available_classes),
            "terms": sorted(available_terms),
        },
    }

    if search:
        response["student_trend"] = [
            {
                "session": item.get("session"),
                "term": item.get("term"),
                "pct": item.get("pct"),
                "grade": item.get("grade"),
                "created_at": item.get("created_at"),
            }
            for item in reversed(recent)
        ]

    return response


@app.get("/reports/history-term")
def report_history_batch(session: str, class_sec: str, term: str):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT payload FROM report_results
            WHERE session = %s AND class_sec = %s AND term = %s
            ORDER BY created_at DESC
            """,
            (session, class_sec, term),
        )
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No results found for the selected term.")

        records = [row["payload"] for row in rows]
        safe_session = session.replace(" ", "_")
        safe_class = class_sec.replace(" ", "_")
        safe_term = term.replace(" ", "_")
        filename = f"Results_{safe_session}_{safe_class}_{safe_term}"
        success, message, pdf_path = PDFManager.generate_pdf(
            filename,
            {"records": records},
            template_name="report_batch.html",
        )
        if not success:
            raise HTTPException(status_code=500, detail=message)

        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    finally:
        conn.close()


@app.get("/reports/history/{result_id}/pdf")
def report_history_pdf(result_id: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute("SELECT payload FROM report_results WHERE id = %s", (result_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Result not found")
        payload = row["payload"]
        safe_name = str(payload.get("student_name", "student")).replace(" ", "_")
        session = payload.get("session", "session")
        filename = f"{safe_name}_Report_{session}_{result_id}"
        success, message, pdf_path = PDFManager.generate_pdf(
            filename,
            payload,
            template_name="report_card.html",
        )
        if not success:
            raise HTTPException(status_code=500, detail=message)
        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    finally:
        conn.close()


@app.delete("/reports/results")
def clear_report_results():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM report_results")
        conn.commit()
        return {"status": "ok", "count": 0}
    finally:
        conn.close()


@app.post("/reports/export")
def export_saved_reports():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute("SELECT id, payload FROM report_queue ORDER BY id")
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=400, detail="No saved reports available for export.")

        records = [row["payload"] for row in rows]
        filename = f"Faizan_Report_Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success, message, pdf_path = PDFManager.generate_pdf(
            filename,
            {"records": records},
            template_name="report_batch.html",
        )
        if not success:
            logging.error("Report batch export failed: %s", message)
            raise HTTPException(status_code=500, detail=message)

        insert_rows = [
            (
                record.get("gr_no"),
                record.get("student_name"),
                record.get("class_sec"),
                record.get("session"),
                record.get("term"),
                json.dumps(record),
            )
            for record in records
        ]
        cursor.executemany(
            """
            INSERT INTO report_results (gr_no, student_name, class_sec, session, term, payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            insert_rows,
        )

        cursor.execute("DELETE FROM report_queue")
        conn.commit()

        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Unexpected error exporting report batch")
        raise HTTPException(status_code=500, detail=f"Unable to export reports: {exc}")
    finally:
        conn.close()


@app.post("/diagnostics/save")
def save_diagnostics(payload: DiagnosticsRequest):
    data = payload.dict()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO diagnostics_queue (payload) VALUES (%s)", (json.dumps(data),))
        cursor.execute("SELECT COUNT(*) AS count FROM diagnostics_queue")
        count = cursor.fetchone()[0]
        conn.commit()
        return {"status": "ok", "count": count}
    finally:
        conn.close()


@app.get("/diagnostics/queue")
def diagnostics_queue():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM diagnostics_queue")
    count = cursor.fetchone()[0]
    conn.close()
    return {"count": count}


@app.get("/diagnostics/queue/items")
def diagnostics_queue_items():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT id, payload FROM diagnostics_queue ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return {"items": [row_to_dict(row) for row in rows]}


@app.delete("/diagnostics/queue")
def clear_diagnostics_queue():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM diagnostics_queue")
        conn.commit()
        return {"status": "ok", "count": 0}
    finally:
        conn.close()


@app.put("/diagnostics/queue/{queue_id}")
def update_diagnostics_queue(queue_id: int, payload: DiagnosticsRequest):
    data = payload.dict()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE diagnostics_queue SET payload = %s WHERE id = %s", (json.dumps(data), queue_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Queued diagnostics not found")
        cursor.execute("SELECT COUNT(*) AS count FROM diagnostics_queue")
        count = cursor.fetchone()[0]
        conn.commit()
        return {"status": "ok", "count": count}
    finally:
        conn.close()


@app.post("/diagnostics/export")
def export_saved_diagnostics():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    try:
        cursor.execute("SELECT id, payload FROM diagnostics_queue ORDER BY id")
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=400, detail="No saved diagnostics available for export.")

        records = [row["payload"] for row in rows]
        filename = f"Faizan_Diagnostics_Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success, message, pdf_path = PDFManager.generate_pdf(
            filename,
            {"records": records},
            template_name="report_diagnostics_batch.html",
            css_name="diagnostics_styles.css",
        )
        if not success:
            logging.error("Diagnostics batch export failed: %s", message)
            raise HTTPException(status_code=500, detail=message)

        cursor.execute("DELETE FROM diagnostics_queue")
        conn.commit()

        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Unexpected error exporting diagnostics batch")
        raise HTTPException(status_code=500, detail=f"Unable to export diagnostics: {exc}")
    finally:
        conn.close()


@app.post("/reports/pdf")
def generate_pdf(payload: ReportRequest):
    data = payload.dict(by_alias=True)
    filename = f"{data['student_name'].replace(' ', '_')}_ReportCard_{data['session']}"
    success, message, pdf_path = PDFManager.generate_pdf(filename, data)
    if not success:
        logging.error("Report PDF export failed: %s", message)
        raise HTTPException(status_code=500, detail=message)

    pdf_file = Path(pdf_path)
    return {
        "message": message,
        "file": pdf_file.name,
        "download_url": f"/reports/files/{pdf_file.name}",
    }


@app.post("/reports/preview", response_class=HTMLResponse)
def preview_report(payload: ReportRequest):
    data = payload.dict(by_alias=True)
    html_content = PDFManager.render_template(data, asset_base="/templates")
    return HTMLResponse(content=html_content)


@app.get("/reports/preview", response_class=HTMLResponse)
def preview_report_sample():
    sample = {
        "student_name": "Student Name",
        "father_name": "Father Name",
        "class_sec": "X-A",
        "session": "2025-2026",
        "gr_no": "00000",
        "rank": "N/A",
        "total_days": "0",
        "days_attended": "0",
        "days_absent": "0",
        "term": "Annual Year",
        "conduct": "Good",
        "performance": "Excellent",
        "progress": "Satisfactory",
        "remarks": "Remarks will appear here.",
        "status": "Passed",
        "date": "01 January 2026",
        "grand_totals": {
            "cw": "0",
            "te": "0",
            "max": "0",
            "obt": "0",
            "pct": "0.0%",
            "grade": "A1",
        },
        "marks_data": {
            "Subject 1": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 2": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 3": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 4": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 5": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 6": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 7": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
            "Subject 8": {
                "coursework": "0",
                "termexam": "0",
                "maxmarks": "100",
                "obt": "0",
                "pct": "0.0%",
                "grade": "A1",
                "is_absent": False,
            },
        },
    }
    html_content = PDFManager.render_template(
        sample,
        template_name="report_preview.html",
        asset_base="/templates",
    )
    return HTMLResponse(content=html_content)


@app.get("/reports/preview/diagnostics", response_class=HTMLResponse)
def preview_diagnostics_sample():
    sample = {
        "student_name": "Muhammad Hashim",
        "father_name": "Taha",
        "class_sec": "KG-A",
        "gr_no": "3779",
        "rank": "N/A",
        "total_days": "82",
        "days_attended": "75",
        "days_absent": "7",
        "attendance_dates": "01 Feb - 28 Feb",
        "overall_remark": "Excellent",
        "term": "Mid Term",
        "comment": "Muhammad Hashim has shown excellent performance in all academic areas. Well done!",
        "diagnostics_sections": [
            {
                "title": "General Progress",
                "rows": [
                    {"label": "Punctuality", "value": "Good"},
                    {"label": "Conduct", "value": "Very Good"},
                    {"label": "Tidiness", "value": "Excellent"},
                    {"label": "Works Independently & Neatly", "value": "Excellent"},
                    {"label": "Shows Interest & Efforts", "value": "Excellent"},
                    {"label": "Follows Instructions", "value": "Excellent"},
                    {"label": "Confidence", "value": "Excellent"},
                ],
            },
            {
                "title": "Maths",
                "rows": [
                    {"label": "Oral Counting", "value": "Excellent"},
                    {"label": "Recognition of Numbers", "value": "Very Good"},
                    {"label": "Tracing / Writing of Numbers", "value": "Excellent"},
                    {"label": "Recognition of Shapes", "value": "Excellent"},
                    {"label": "Understanding of Concept", "value": "Excellent"},
                ],
            },
            {
                "title": "English",
                "rows": [
                    {"label": "Recognition of Sound / Letter", "value": "Fair"},
                    {"label": "Tracing / Writing of Letter", "value": "Excellent"},
                    {"label": "Listening / Speaking", "value": "Fair"},
                    {"label": "Recitation of Rhymes", "value": "Good"},
                    {"label": "Reading", "value": "Fair"},
                ],
            },
            {
                "title": "Urdu",
                "rows": [
                    {"label": "Recognition of Sound / Letter", "value": "Very Good"},
                    {"label": "Tracing / Writing of Letter", "value": "Excellent"},
                    {"label": "Recitation of Rhymes", "value": "Excellent"},
                    {"label": "Reading", "value": "Very Good"},
                ],
            },
            {
                "title": "Other Subjects",
                "rows": [
                    {"label": "General Knowledge - Oral", "value": "Excellent"},
                    {"label": "Art / Drawing", "value": "Excellent"},
                ],
            },
            {
                "title": "Islamiyat",
                "rows": [
                    {"label": "Islamiyat - Oral", "value": "Excellent"},
                ],
            },
        ],
    }
    html_content = PDFManager.render_template(
        sample,
        template_name="report_diagnostics_preview.html",
        asset_base="/templates",
        css_name="diagnostics_styles.css",
    )
    return HTMLResponse(content=html_content)


@app.get("/reports/files/{file_name}")
def download_pdf(file_name: str):
    safe_name = Path(file_name).name
    pdf_path = PDFManager.get_output_dir() / safe_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(pdf_path, media_type="application/pdf", filename=safe_name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
