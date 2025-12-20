"""
FastAPI backend for the Discord-inspired Report Card application.
Provides authentication, student management, configuration, and PDF generation.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import psycopg2
from psycopg2 import extras
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from backend.core.config_manager import ConfigManager
from backend.core.pdf_manager import PDFManager
from backend.core.helpers import calculate_age, calculate_years_studying, format_date

SAMPLE_EXCEL = BASE_DIR / "student_sample.xlsx"
FILTERS_FILE = BASE_DIR / "settings" / "filters.json"
REMARKS_FILE = BASE_DIR / "settings" / "remarks.json"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "report_system")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rayyanshah04")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


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


class FiltersPayload(BaseModel):
    filters: Dict[str, list[str]]


class RemarksPayload(BaseModel):
    presets: list[str]


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


@app.on_event("startup")
def initialize_report_queue():
    try:
        ensure_report_queue_table()
    except Exception as exc:  # pragma: no cover
        print(f"Unable to prepare report queue table: {exc}")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/auth/login")
def login(payload: LoginRequest):
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
            "(student_name ILIKE %s OR father_name ILIKE %s OR gr_no ILIKE %s OR current_class_sec ILIKE %s)"
        )
        params.extend([like, like, like, like])
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
    try:
        df = pd.read_excel(BytesIO(content))
    except Exception as exc:  # pragma: no cover - pandas raises many error types
        raise HTTPException(status_code=400, detail=f"Unable to read Excel file: {exc}") from exc

    required_columns = [
        "gr_no",
        "student_name",
        "current_class_sec",
        "address",
        "contact_number_resident",
        "contact_number_neighbour",
        "contact_number_relative",
        "contact_number_other1",
        "contact_number_other2",
        "contact_number_other3",
        "contact_number_other4",
        "date_of_birth",
        "joining_date",
    ]
    for column in required_columns:
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {column}")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    success = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            cursor.execute(
                """
                INSERT INTO students (
                    gr_no, student_name, current_class_sec, address,
                    contact_number_resident, contact_number_neighbour, contact_number_relative,
                    contact_number_other1, contact_number_other2, contact_number_other3, 
                    contact_number_other4, date_of_birth, joining_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                tuple(
                    str(row.get(column)) if pd.notna(row.get(column)) else None
                    for column in required_columns
                ),
            )
            success += 1
        except psycopg2.IntegrityError:
            errors.append(f"Row {idx + 2}: G.R No {row.get('gr_no')} already exists")
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"Row {idx + 2}: {exc}")

    conn.commit()
    conn.close()

    return {"imported": success, "errors": errors}


@app.get("/students/sample")
def sample_excel():
    if not SAMPLE_EXCEL.exists():
        raise HTTPException(status_code=404, detail="Sample file not found")
    return FileResponse(SAMPLE_EXCEL, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/subjects")
def list_subjects():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute("SELECT subject_name, type FROM subjects ORDER BY subject_name")
    rows = cursor.fetchall()
    conn.close()
    return [{"subject_name": row["subject_name"], "type": row["type"]} for row in rows]


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
def save_report(payload: ReportRequest):
    data = payload.dict(by_alias=True)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO report_queue (payload) VALUES (%s)", (json.dumps(data),))
        cursor.execute("SELECT COUNT(*) AS count FROM report_queue")
        count = cursor.fetchone()[0]
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
            raise HTTPException(status_code=500, detail=message)

        cursor.execute("DELETE FROM report_queue")
        conn.commit()

        pdf_file = Path(pdf_path)
        return {
            "message": message,
            "file": pdf_file.name,
            "download_url": f"/reports/files/{pdf_file.name}",
        }
    finally:
        conn.close()


@app.post("/reports/pdf")
def generate_pdf(payload: ReportRequest):
    data = payload.dict(by_alias=True)
    filename = f"{data['student_name'].replace(' ', '_')}_ReportCard_{data['session']}"
    success, message, pdf_path = PDFManager.generate_pdf(filename, data)
    if not success:
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


@app.get("/reports/files/{file_name}")
def download_pdf(file_name: str):
    safe_name = Path(file_name).name
    pdf_path = PDFManager.OUTPUT_DIR / safe_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(pdf_path, media_type="application/pdf", filename=safe_name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
