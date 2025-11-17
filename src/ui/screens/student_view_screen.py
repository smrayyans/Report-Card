"""
Student View Screen - Student Management Interface  
"""
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QFileDialog, QDialog, QScrollArea, QApplication, QFrame, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.ui.widgets.custom_widgets import NoWheelComboBox
from src.utils.helpers import format_date, calculate_age, calculate_years_studying

class StudentViewScreen(QWidget):
    """Widget to view and manage students"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QHBoxLayout()
        
        # Left sidebar
        left_panel = QWidget()
        left_panel.setMaximumWidth(250)
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 12px;
                text-align: left;
                font-size: 12px;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QLabel {
                color: white;
                font-size: 11px;
                padding: 5px;
            }
        """)
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 20, 10, 10)
        left_layout.setSpacing(5)
        
        # Title
        title_label = QLabel("📚 STUDENT MANAGEMENT")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(title_label)
        
        # Action buttons
        view_all_btn = QPushButton("👥 View All Students")
        view_all_btn.clicked.connect(self.view_all_students)
        left_layout.addWidget(view_all_btn)
        
        view_single_btn = QPushButton("👤 View Single Student")
        view_single_btn.clicked.connect(self.view_single_student)
        left_layout.addWidget(view_single_btn)
        
        left_layout.addWidget(QLabel(""))
        
        download_btn = QPushButton("📥 Download Sample Excel")
        download_btn.clicked.connect(self.download_sample_excel)
        left_layout.addWidget(download_btn)
        
        upload_btn = QPushButton("📤 Upload Excel File")
        upload_btn.clicked.connect(self.upload_excel)
        left_layout.addWidget(upload_btn)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        
        # Right content area
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # Search and filter section
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name, G.R No, or Class...")
        self.search_input.textChanged.connect(self.filter_students)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        filter_label = QLabel("Filter by Class:")
        filter_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-left: 20px;")
        search_layout.addWidget(filter_label)
        
        self.class_filter = NoWheelComboBox()
        self.class_filter.addItem("All Classes")
        self.class_filter.currentTextChanged.connect(self.filter_students)
        self.class_filter.setMinimumWidth(120)
        search_layout.addWidget(self.class_filter)
        
        filter_status_label = QLabel("Status:")
        filter_status_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-left: 20px;")
        search_layout.addWidget(filter_status_label)
        
        self.status_filter = NoWheelComboBox()
        self.status_filter.addItems(["All", "Active", "Left", "Inactive"])
        self.status_filter.currentTextChanged.connect(self.filter_students)
        self.status_filter.setMinimumWidth(100)
        search_layout.addWidget(self.status_filter)
        
        right_layout.addLayout(search_layout)
        
        # Stats section
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_students_label = QLabel("Total Students: 0")
        self.total_students_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        stats_layout.addWidget(self.total_students_label)
        
        self.active_students_label = QLabel("Active: 0")
        self.active_students_label.setStyleSheet("""
            QLabel {
                background-color: #27ae60;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        stats_layout.addWidget(self.active_students_label)
        
        self.inactive_students_label = QLabel("Inactive: 0")
        self.inactive_students_label.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        stats_layout.addWidget(self.inactive_students_label)
        
        stats_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        refresh_btn.clicked.connect(self.load_students)
        stats_layout.addWidget(refresh_btn)
        
        right_layout.addLayout(stats_layout)
        
        # Students table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(8)
        self.students_table.setHorizontalHeaderLabels([
            "G.R No", "Student Name", "Father Name", 
            "Class/Sec", "Session", "Status", "Contact", "Address"
        ])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.students_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.students_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                gridline-color: #e1e8ed;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.students_table.doubleClicked.connect(self.view_single_student)
        right_layout.addWidget(self.students_table)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)
        
        self.setLayout(main_layout)
        self.all_students = []  # Store all students for filtering
        self.load_students()
        self.load_class_filter()
    
    def load_students(self):
        """Load students from database"""
        import sqlite3
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gr_no, student_name, father_name, 
                   current_class_sec, current_session, status, contact_number_resident, address
            FROM students
            ORDER BY student_name COLLATE NOCASE
        """)
        
        students = cursor.fetchall()
        conn.close()
        
        self.all_students = students  # Store for filtering
        self.display_students(students)
        self.update_stats()
    
    def display_students(self, students):
        """Display students in table"""
        self.students_table.setRowCount(len(students))
        for row_idx, student in enumerate(students):
            for col_idx, value in enumerate(student):
                item = QTableWidgetItem(str(value) if value else "")
                self.students_table.setItem(row_idx, col_idx, item)
    
    def update_stats(self):
        """Update statistics labels"""
        import sqlite3
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM students")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE status = 'Active'")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE status != 'Active'")
        inactive = cursor.fetchone()[0]
        
        conn.close()
        
        self.total_students_label.setText(f"Total Students: {total}")
        self.active_students_label.setText(f"Active: {active}")
        self.inactive_students_label.setText(f"Inactive: {inactive}")
    
    def load_class_filter(self):
        """Load unique classes for filter dropdown"""
        import sqlite3
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT current_class_sec FROM students WHERE current_class_sec IS NOT NULL ORDER BY current_class_sec")
        classes = cursor.fetchall()
        conn.close()
        
        self.class_filter.clear()
        self.class_filter.addItem("All Classes")
        for cls in classes:
            if cls[0]:
                self.class_filter.addItem(cls[0])
    
    def filter_students(self):
        """Filter students based on search and filter criteria"""
        search_text = self.search_input.text().lower()
        selected_class = self.class_filter.currentText()
        selected_status = self.status_filter.currentText()
        
        filtered = []
        for student in self.all_students:
            # Search filter
            if search_text:
                student_text = " ".join(str(s).lower() for s in student if s)
                if search_text not in student_text:
                    continue
            
            # Class filter
            if selected_class != "All Classes":
                if student[3] != selected_class:  # current_class_sec is index 3
                    continue
            
            # Status filter
            if selected_status != "All":
                if student[5] != selected_status:  # status is index 5
                    continue
            
            filtered.append(student)
        
        self.display_students(filtered)
    
    def view_all_students(self):
        """Reset filters and show all students"""
        self.search_input.clear()
        self.class_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.load_students()
    
    def view_single_student(self):
        """View detailed information of a single student with modern card-based UI"""
        selected_row = self.students_table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a student to view!")
            return
        
        # Get student details
        gr_no = self.students_table.item(selected_row, 0).text()
        
        import sqlite3
        from datetime import datetime
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT student_id, gr_no, student_name, father_name, current_class_sec, current_session, 
                status, joining_date, left_date, left_reason, date_of_birth, 
                contact_number_resident, contact_number_neighbour, contact_number_relative,
                contact_number_other1, contact_number_other2, contact_number_other3,
                contact_number_other4, address, created_at, updated_at
            FROM students WHERE gr_no = ?
        """, (gr_no,))
        
        student = cursor.fetchone()
        conn.close()
        
        if not student:
            return
        
        # Format date helper
        def format_date(date_str):
            if not date_str:
                return "N/A"
            try:
                if " " in date_str:
                    date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                else:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day = date_obj.day
                month = date_obj.strftime("%B")
                year = date_obj.year
                return f"{day} {month} {year}"
            except:
                return date_str
        
         # Calculate age
        age_str = "N/A"
        dob_formatted = format_date(student[10])
        if student[10]:
            try:
                date_part = student[10].split()[0] if " " in student[10] else student[10]
                dob = datetime.strptime(date_part, "%Y-%m-%d")
                today = datetime.now()
                age_years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                age_months = (today.year - dob.year) * 12 + today.month - dob.month
                if (today.day < dob.day):
                    age_months -= 1
                age_str = f"{age_years} years ({age_months} months)"
            except:
                age_str = "N/A"
        
        # Calculate years studying
        years_studying_str = "N/A"
        joining_date_formatted = format_date(student[7])
        if student[7]:
            try:
                date_part = student[7].split()[0] if " " in student[7] else student[7]
                join_date = datetime.strptime(date_part, "%Y-%m-%d")
                today = datetime.now()
                years = today.year - join_date.year - ((today.month, today.day) < (join_date.month, join_date.day))
                months = (today.year - join_date.year) * 12 + today.month - join_date.month
                if (today.day < join_date.day):
                    months -= 1
                years_studying_str = f"{years} years {months % 12} months"
            except:
                years_studying_str = "N/A"
        
        # Format left date
        left_date_formatted = format_date(student[8])
        
        # Create detailed view dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Student Details - {student[2]}")
        dialog.setMinimumSize(900, 750)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main header card with gradient background
        header_card = QWidget()
        header_card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:0.5 #3b82f6, stop:1 #60a5fa);
                border-radius: 0px;
            }
        """)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(40, 35, 40, 35)
        header_layout.setSpacing(8)

        # Student name - large and bold
        student_name = QLabel(student[2].upper())
        student_name.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: white;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(student_name)

        # GR Number
        gr_label = QLabel(f"G.R No: {student[1]}")
        gr_label.setStyleSheet("""
            font-size: 16px; 
            color: rgba(255, 255, 255, 0.95);
            font-weight: 500;
        """)
        header_layout.addWidget(gr_label)

        # Address with icon
        if student[18]:
            address_label = QLabel(f"📍 {student[18]}")
            address_label.setStyleSheet("""
                font-size: 14px; 
                color: rgba(255, 255, 255, 0.9);
                margin-top: 5px;
            """)
            address_label.setWordWrap(True)
            header_layout.addWidget(address_label)
        
        header_card.setLayout(header_layout)
        layout.addWidget(header_card)
        
        # Contact numbers card - positioned below header
        contacts_card = QWidget()
        contacts_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)

        contacts_layout = QVBoxLayout()
        contacts_layout.setContentsMargins(25, 20, 25, 20)
        contacts_layout.setSpacing(12)
        
        # Contact header
        contact_header = QLabel("Contact:")
        contact_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        """)
        contacts_layout.addWidget(contact_header)
        
        # Collect and display contact numbers
        contacts_list = [
            ("Resident", student[11]),
            ("Neighbour", student[12]),
            ("Relative", student[13]),
            ("Other 1", student[14]),
            ("Other 2", student[15]),
            ("Other 3", student[16]),
            ("Other 4", student[17]),
        ]

        has_contacts = False
        for label, contact in contacts_list:
            if contact and str(contact).lower() not in ['', 'nan', 'none', 'null']:
                has_contacts = True
                contact_row = QHBoxLayout()
                contact_row.setSpacing(10)
                
                # Contact number with icon
                contact_label = QLabel(f"📱  {contact}")
                contact_label.setStyleSheet("""
                    font-size: 15px;
                    color: #374151;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                """)
                contact_row.addWidget(contact_label)
                contact_row.addStretch()
                
                # Copy button
                copy_btn = QPushButton("Copy")
                copy_btn.setFixedSize(70, 32)
                copy_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e0f2fe;
                        color: #0284c7;
                        border: 1px solid #bae6fd;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background-color: #bae6fd;
                        border-color: #7dd3fc;
                    }
                    QPushButton:pressed {
                        background-color: #7dd3fc;
                    }
                """)
                copy_btn.clicked.connect(lambda checked, num=contact: self.copy_to_clipboard(str(num)))
                contact_row.addWidget(copy_btn)
                
                contacts_layout.addLayout(contact_row)
                
                # Add separator line between contacts
                if contacts_list.index((label, contact)) < len([c for c in contacts_list if c[1]]) - 1:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setStyleSheet("background-color: #f3f4f6; max-height: 1px;")
                    contacts_layout.addWidget(separator)
        
        if not has_contacts:
            no_contact = QLabel("No contact numbers available")
            no_contact.setStyleSheet("""
                font-size: 14px;
                color: #9ca3af;
                font-style: italic;
            """)
            contacts_layout.addWidget(no_contact)
        
        contacts_card.setLayout(contacts_layout)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: transparent;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(25, 25, 25, 25)
        
        # Add contact card first
        content_layout.addWidget(contacts_card)
        
        # Create information cards
        # Personal Information Card
        content_layout.addWidget(self.create_info_card("Personal Information", [
            ("Student ID", str(student[0])),
            ("G.R Number", student[1]),
            ("Student Name", student[2]),
            ("Father's Name", student[3]),
            ("Date of Birth", dob_formatted),
            ("Current Age", age_str),
        ], "#8b5cf6"))

        # Academic Information Card
        content_layout.addWidget(self.create_info_card("Academic Information", [
            ("Current Class/Section", student[4] or "N/A"),
            ("Current Session", student[5] or "N/A"),
            ("Joining Date", joining_date_formatted),
            ("Years Studying", years_studying_str),
            ("Status", student[6]),
        ], "#10b981"))
        
        # Left/Inactive Status Card (if applicable)
        if student[6] in ['Left', 'Inactive']:
            content_layout.addWidget(self.create_info_card("Status Information", [
                ("Status", student[6]),
                ("Left Date", left_date_formatted),
                ("Reason for Leaving", student[9] or "N/A"),
            ], "#ef4444"))
        
        # System Information Card
        content_layout.addWidget(self.create_info_card("System Information", [
            ("Record Created", student[19] or "N/A"),
            ("Last Updated", student[20] or "N/A"),
        ], "#6366f1"))
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Action buttons at bottom
        button_container = QWidget()
        button_container.setStyleSheet("background-color: white; border-top: 1px solid #e5e7eb;")
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(25, 15, 25, 15)
        button_layout.setSpacing(10)
        
        button_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete Student")
        delete_btn.setFixedSize(160, 40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_current_student(dialog, student[1]))
        button_layout.addWidget(delete_btn)
        
        # Close button
        close_btn = QPushButton("✖ Close")
        close_btn.setFixedSize(120, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #5d6d7e;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        button_container.setLayout(button_layout)
        layout.addWidget(button_container)
        
        dialog.setLayout(layout)
        dialog.exec()

    def create_info_card(self, title, fields, accent_color="#3b82f6"):
        """Create a modern information card with colored accent"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 12px;
                border-left: 4px solid {accent_color};
                border-top: 1px solid #e5e7eb;
                border-right: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
            }}
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(25, 20, 25, 20)
        card_layout.setSpacing(15)
        
        # Card title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 17px;
            font-weight: bold;
            color: {accent_color};
            margin-bottom: 8px;
        """)
        card_layout.addWidget(title_label)
        
        # Add fields
        for label, value in fields:
            field_layout = QHBoxLayout()
            field_layout.setSpacing(15)
            
            # Label
            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet("""
                font-size: 14px;
                color: #6b7280;
                font-weight: 500;
                min-width: 180px;
            """)
            field_layout.addWidget(label_widget)
            
            # Value
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("""
                font-size: 14px;
                color: #1f2937;
                font-weight: 600;
            """)
            value_widget.setWordWrap(True)
            field_layout.addWidget(value_widget, 1)
            
            card_layout.addLayout(field_layout)
        
        card.setLayout(card_layout)
        return card

    def copy_to_clipboard(self, text):
        """Copy text to clipboard and show notification"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # Show temporary success message
        QMessageBox.information(self, "Copied", f"'{text}' copied to clipboard!", 
                            QMessageBox.StandardButton.Ok)
    
    def create_simple_section(self, title, fields):
        """Create a simple flat section without boxes"""
        section = QWidget()
        section.setStyleSheet("QWidget { background-color: transparent; }")
        
        section_layout = QVBoxLayout()
        section_layout.setSpacing(8)
        section_layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #2c3e50;
            padding-bottom: 8px;
            border-bottom: 2px solid #3498db;
        """)
        section_layout.addWidget(title_label)
        
        # Fields in a simple list
        for label, value in fields:
            field_layout = QHBoxLayout()
            field_layout.setContentsMargins(10, 5, 0, 5)
            
            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet("""
                font-weight: bold;
                color: #34495e;
                font-size: 12px;
                min-width: 180px;
            """)
            field_layout.addWidget(label_widget)
            
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("""
                color: #2c3e50;
                font-size: 12px;
            """)
            value_widget.setWordWrap(True)
            field_layout.addWidget(value_widget, 1)
            
            section_layout.addLayout(field_layout)
        
        section.setLayout(section_layout)
        return section
    
    def delete_current_student(self, dialog, gr_no):
        """Delete student from detail view"""
        # Get student name for confirmation
        import sqlite3
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT student_name FROM students WHERE gr_no = ?", (gr_no,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            QMessageBox.warning(self, "Error", "Student not found!")
            return
        
        student_name = result[0]
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete this student?\n\nG.R No: {gr_no}\nName: {student_name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("report_system.db")
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM students WHERE gr_no = ?", (gr_no,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Success", f"Student {student_name} deleted successfully!")
                dialog.accept()  # Close the detail view
                self.load_students()  # Refresh the main list
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete student:\n{str(e)}")
    
    def delete_student(self):
        """Delete selected student from main table"""
        selected_row = self.students_table.currentRow()
        
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a student to delete!")
            return
        
        # Get GR No from first column (index 0)
        gr_no = self.students_table.item(selected_row, 0).text()
        student_name = self.students_table.item(selected_row, 1).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete this student?\n\nG.R No: {gr_no}\nName: {student_name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import sqlite3
                conn = sqlite3.connect("report_system.db")
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM students WHERE gr_no = ?", (gr_no,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "Success", f"Student {student_name} deleted successfully!")
                self.load_students()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete student:\n{str(e)}")
    
    def download_sample_excel(self):
        """Download sample Excel file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Sample Excel", "student_sample.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            # Create sample DataFrame with exact database columns including father_name
            sample_data = {
                'current_class_sec': ['I-A', 'II-B', 'III-C'],
                'gr_no': ['001', '002', '003'],
                'student_name': ['Student Name 1', 'Student Name 2', 'Student Name 3'],
                'father_name': ['Father Name 1', 'Father Name 2', 'Father Name 3'],
                'address': ['Address 1', 'Address 2', 'Address 3'],
                'contact_number_resident': ['0300-1234567', '0321-9876543', '0333-1112222'],
                'contact_number_neighbour': ['', '', ''],
                'contact_number_relative': ['', '', ''],
                'contact_number_other1': ['', '', ''],
                'contact_number_other2': ['', '', ''],
                'contact_number_other3': ['', '', ''],
                'contact_number_other4': ['', '', ''],
                'date_of_birth': ['2010-01-15', '2011-05-20', '2009-12-10'],
                'joining_date': ['2024-01-01', '2024-01-01', '2024-01-01']
            }
            
            df = pd.DataFrame(sample_data)
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Success", "Sample Excel file downloaded successfully!")
    
    def upload_excel(self):
        """Upload Excel file and import students"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Validate required columns - exact schema fields
            required_cols = ['current_class_sec', 'gr_no', 'student_name', 'father_name', 'address', 
                           'contact_number_resident', 'contact_number_neighbour', 'contact_number_relative',
                           'contact_number_other1', 'contact_number_other2', 'contact_number_other3',
                           'contact_number_other4', 'date_of_birth', 'joining_date']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                QMessageBox.warning(
                    self, "Error", 
                    f"Missing required columns: {', '.join(missing_cols)}\n\n"
                    f"Required columns: {', '.join(required_cols)}"
                )
                return
            
            # Import to database
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()
            
            added_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    gr_no = str(row['gr_no']).strip()
                    
                    # Check if student already exists
                    cursor.execute("SELECT student_id, father_name, contact_number_resident, contact_number_neighbour, contact_number_relative, contact_number_other1, contact_number_other2, contact_number_other3, contact_number_other4 FROM students WHERE gr_no = ?", (gr_no,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Student exists - check for updates
                        student_id, db_father_name, db_res, db_neigh, db_rel, db_oth1, db_oth2, db_oth3, db_oth4 = existing
                        
                        # Prepare update fields
                        updates = []
                        update_values = []
                        
                        # Check father_name
                        new_father = str(row['father_name']).strip() if pd.notna(row['father_name']) and str(row['father_name']).strip() else ""
                        if new_father and (not db_father_name or db_father_name.strip() == ""):
                            updates.append("father_name = ?")
                            update_values.append(new_father)
                        
                        # Check contact numbers - add if not empty and different
                        contact_fields = [
                            ('contact_number_resident', db_res),
                            ('contact_number_neighbour', db_neigh),
                            ('contact_number_relative', db_rel),
                            ('contact_number_other1', db_oth1),
                            ('contact_number_other2', db_oth2),
                            ('contact_number_other3', db_oth3),
                            ('contact_number_other4', db_oth4)
                        ]
                        
                        for col_name, db_value in contact_fields:
                            new_value = str(row[col_name]).strip() if pd.notna(row[col_name]) and str(row[col_name]).strip() not in ['', 'nan', 'None'] else ""
                            if new_value and (not db_value or db_value.strip() == ""):
                                updates.append(f"{col_name} = ?")
                                update_values.append(new_value)
                        
                        # Perform update if there are changes
                        if updates:
                            updates.append("updated_at = CURRENT_TIMESTAMP")
                            update_values.append(gr_no)
                            cursor.execute(f"UPDATE students SET {', '.join(updates)} WHERE gr_no = ?", update_values)
                            updated_count += 1
                        
                    else:
                        # New student - insert
                        cursor.execute("""
                            INSERT INTO students (
                                gr_no, student_name, father_name, current_class_sec, address,
                                contact_number_resident, contact_number_neighbour, contact_number_relative,
                                contact_number_other1, contact_number_other2, contact_number_other3, 
                                contact_number_other4, date_of_birth, joining_date
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            gr_no,
                            str(row['student_name']).strip(),
                            str(row['father_name']).strip() if pd.notna(row['father_name']) else "",
                            str(row['current_class_sec']).strip(),
                            str(row['address']).strip(),
                            str(row['contact_number_resident']).strip() if pd.notna(row['contact_number_resident']) else "",
                            str(row['contact_number_neighbour']).strip() if pd.notna(row['contact_number_neighbour']) else "",
                            str(row['contact_number_relative']).strip() if pd.notna(row['contact_number_relative']) else "",
                            str(row['contact_number_other1']).strip() if pd.notna(row['contact_number_other1']) else "",
                            str(row['contact_number_other2']).strip() if pd.notna(row['contact_number_other2']) else "",
                            str(row['contact_number_other3']).strip() if pd.notna(row['contact_number_other3']) else "",
                            str(row['contact_number_other4']).strip() if pd.notna(row['contact_number_other4']) else "",
                            str(row['date_of_birth']) if pd.notna(row['date_of_birth']) else None,
                            str(row['joining_date']) if pd.notna(row['joining_date']) else None
                        ))
                        added_count += 1
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {idx + 2}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Show result
            msg = f"Import completed!\n\n"
            if added_count > 0:
                msg += f"Successfully added: {added_count} students\n"
            if updated_count > 0:
                msg += f"Successfully updated: {updated_count} students\n"
            if error_count > 0:
                msg += f"\nFailed: {error_count} students\n\n"
                msg += "Errors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    msg += f"\n... and {len(errors) - 10} more errors"
            
            QMessageBox.information(self, "Import Result", msg)
            self.load_students()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import Excel file:\n{str(e)}")
