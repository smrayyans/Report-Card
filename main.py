import json
import os
import re
from datetime import datetime
import pandas as pd
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                               QCheckBox, QLabel, QComboBox, QSpinBox, QTableWidget,
                               QTableWidgetItem, QDateEdit, QTabWidget, QScrollArea, QWidget,
                               QHeaderView, QFileDialog)
from PySide6.QtGui import QIcon, QFont, QColor

# Modern Stylesheet
MODERN_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f7fa;
}

QLabel {
    color: #2c3e50;
    font-size: 11px;
}

QLineEdit, QTextEdit, QSpinBox {
    background-color: #ffffff;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    padding: 8px;
    color: #2c3e50;
    font-size: 11px;
    selection-background-color: #3498db;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 2px solid #3498db;
    background-color: #f8fbff;
}

QComboBox {
    background-color: #ffffff;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    padding: 6px;
    color: #2c3e50;
    font-size: 11px;
}

QComboBox:focus {
    border: 2px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    background-color: transparent;
    width: 25px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #000000;
    selection-background-color: #3498db;
    selection-color: #ffffff;
    border: 1px solid #e1e8ed;
    outline: none;
}

QComboBox QAbstractItemView::item {
    color: #000000;
    padding: 5px;
    border: none;
    outline: none;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #3498db;
    color: #ffffff;
    border: none;
    outline: none;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1f618d;
}

QPushButton#filterBtn {
    background-color: #27ae60;
}

QPushButton#filterBtn:hover {
    background-color: #229954;
}

QPushButton#presetsBtn {
    background-color: #e74c3c;
    max-width: 80px;
}

QPushButton#presetsBtn:hover {
    background-color: #c0392b;
}

QCheckBox {
    color: #2c3e50;
    font-size: 11px;
    spacing: 5px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
}

QCheckBox::indicator:unchecked {
    background-color: #ecf0f1;
    border: 2px solid #bdc3c7;
}

QCheckBox::indicator:checked {
    background-color: #3498db;
    border: 2px solid #3498db;
}

QRadioButton {
    color: #2c3e50;
    font-size: 11px;
    spacing: 5px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
}

QRadioButton::indicator:unchecked {
    background-color: #ecf0f1;
    border: 2px solid #bdc3c7;
    border-radius: 9px;
}

QRadioButton::indicator:checked {
    background-color: #3498db;
    border: 2px solid #3498db;
    border-radius: 9px;
}

QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fbff;
    gridline-color: #e1e8ed;
    border: 1px solid #e1e8ed;
    border-radius: 6px;
}

QTableWidget::item {
    padding: 5px;
    color: #2c3e50;
}

QTableWidget::item:selected {
    background-color: #d4e6f1;
}

QHeaderView::section {
    background-color: #34495e;
    color: white;
    padding: 5px;
    border: none;
    font-weight: bold;
    font-size: 10px;
}

QScrollArea {
    border: none;
    background-color: #f5f7fa;
}

QTabWidget::pane {
    border: 1px solid #e1e8ed;
}

QTabBar::tab {
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 8px 20px;
    margin-right: 2px;
    border: 1px solid #bdc3c7;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    font-weight: bold;
    font-size: 11px;
}

QTabBar::tab:selected {
    background-color: #3498db;
    color: white;
    border: 1px solid #3498db;
}

QTabBar::tab:hover {
    background-color: #d5dbdb;
}

QMenuBar {
    background-color: #f5f5f5;
    color: #2c3e50;
    border-bottom: 1px solid #e0e0e0;
    padding: 2px;
    font-size: 11px;
}

QMenuBar::item {
    padding: 4px 12px;
    background-color: transparent;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
    color: #2c3e50;
}

QMenu {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #bdc3c7;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QListWidget {
    background-color: #ffffff;
    border: 1px solid #e1e8ed;
    border-radius: 6px;
    color: #2c3e50;
}

QListWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QListWidget::item:hover {
    background-color: #d4e6f1;
}

QScrollBar:vertical {
    background-color: #ecf0f1;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3498db;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2980b9;
}

QStatusBar {
    background-color: #34495e;
    color: white;
}

QDateEdit {
    background-color: #ffffff;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    padding: 6px;
    color: #000000;
    font-size: 11px;
}

QDateEdit:focus {
    border: 2px solid #3498db;
}

QDateEdit::drop-down {
    border: none;
    background-color: transparent;
    width: 25px;
    subcontrol-origin: padding;
    subcontrol-position: right center;
    image: url(none);
}

QDateEdit::down-arrow {
    image: url(none);
    width: 12px;
    height: 12px;
}

QCalendarWidget {
    background-color: #ffffff;
    color: #000000;
}

QCalendarWidget QAbstractItemView {
    background-color: #ffffff;
    color: #000000;
    selection-background-color: #3498db;
    selection-color: #ffffff;
}

QCalendarWidget QWidget {
    color: #000000;
}

QCalendarWidget QToolButton {
    background-color: #3498db;
    color: white;
    border: 1px solid #2980b9;
    border-radius: 4px;
    padding: 4px;
    font-weight: bold;
}

QCalendarWidget QToolButton:hover {
    background-color: #2980b9;
}

QCalendarWidget QToolButton:pressed {
    background-color: #1f618d;
}

QCalendarWidget QMenu {
    background-color: #ffffff;
    color: #000000;
}

QCalendarWidget QSpinBox {
    background-color: #ffffff;
    color: #000000;
}
"""

CONFIG_FILE = "config/config.json"
FILTERS_FILE = "settings/filters.json"
REMARKS_FILE = "settings/remarks.json"

class NoWheelComboBox(QComboBox):
    """ComboBox that doesn't change value on mouse wheel scroll"""
    def wheelEvent(self, event):
        event.ignore()

class NavigableLineEdit(QLineEdit):
    """LineEdit with arrow key navigation support"""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            # Let parent handle arrow keys for table navigation
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class NavigableComboBox(NoWheelComboBox):
    """ComboBox with arrow key navigation support"""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down) and not self.view().isVisible():
            # If dropdown not open, let parent handle for table navigation
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class LoginDialog(QDialog):
    """Login dialog for user authentication"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Faizan Academy Report System")
        self.setGeometry(400, 250, 400, 350)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fbff;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QLabel#titleLabel {
                color: #3498db;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                padding: 10px;
                color: #2c3e50;
                font-size: 12px;
                selection-background-color: #3498db;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #f8fbff;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
            QPushButton#cancelBtn {
                background-color: #95a5a6;
            }
            QPushButton#cancelBtn:hover {
                background-color: #7f8c8d;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Logo and Title
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QtGui.QPixmap("templates/faizan_academy_logo.png")
        if not logo_pixmap.isNull():
            scaled_logo = logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_logo)
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label)

        # Title
        title = QLabel("Faizan Academy")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("Report Card Management System")
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # Username
        username_layout = QVBoxLayout()
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-weight: bold;")
        username_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Password
        password_layout = QVBoxLayout()
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold;")
        password_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 11px; text-align: center;")
        self.error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)
        login_btn.clicked.connect(self.authenticate)
        login_btn.setDefault(True)
        btn_layout.addWidget(login_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Connect enter key
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.authenticate)

    def authenticate(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.error_label.setText("Please enter both username and password")
            return

        try:
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT user_id, role FROM users WHERE username = ? AND password = ? AND is_active = 1",
                (username, password)
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                self.user_id = user[0]
                self.user_role = user[1]
                self.accept()
            else:
                self.error_label.setText("Invalid username or password")

        except Exception as e:
            self.error_label.setText(f"Database error: {str(e)}")

class ConfigManager:
    """Manages application settings"""

    DEFAULT_CONFIG = {
        "sessions": ["2024-2025", "2025-2026", "2026-2027", "2027-2028"],
        "default_session": "2025-2026",
        "max_marks_options": [50, 75, 100],
        "default_max_marks": 100,
        "class_defaults": {
            "I": 220, "II": 220, "III": 220, "IV": 220, "V": 220,
            "VI": 240, "VII": 240, "VIII": 240, "IX": 240, "X": 240
        },
        "subjects": [
            "English", "Urdu", "Mathematics", "Science/Env.Sci",
            "S.St/P.St", "Islamiyat", "Sindhi", "Computer"
        ]
    }

    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return ConfigManager.DEFAULT_CONFIG.copy()
        else:
            ConfigManager.save(ConfigManager.DEFAULT_CONFIG.copy())
            return ConfigManager.DEFAULT_CONFIG.copy()

    @staticmethod
    def save(config):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

class FiltersManager:
    """Manages saved subject filters"""

    @staticmethod
    def load():
        if os.path.exists(FILTERS_FILE):
            try:
                with open(FILTERS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    def save(filters):
        try:
            with open(FILTERS_FILE, 'w') as f:
                json.dump(filters, f, indent=2)
            return True
        except:
            return False

class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 600, 500)
        self.config = ConfigManager.load()

        tabs = QTabWidget()

        # Sessions Tab
        tabs.addTab(self.create_sessions_tab(), "Sessions")

        # Subjects Tab
        tabs.addTab(self.create_subjects_tab(), "Subjects")

        # Marks Tab
        tabs.addTab(self.create_marks_tab(), "Marks")

        # Class Defaults Tab
        tabs.addTab(self.create_class_defaults_tab(), "Class Defaults")

        layout = QVBoxLayout()
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def create_sessions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Available Sessions:"))
        self.sessions_list = QListWidget()
        for session in self.config.get("sessions", []):
            self.sessions_list.addItem(session)
        layout.addWidget(self.sessions_list)

        input_layout = QHBoxLayout()
        self.new_session_input = QLineEdit()
        self.new_session_input.setPlaceholderText("e.g., 2025-2026")
        add_btn = QPushButton("Add Session")
        add_btn.clicked.connect(self.add_session)
        input_layout.addWidget(self.new_session_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        layout.addWidget(QLabel("Default Session:"))
        self.default_session_combo = NoWheelComboBox()
        self.default_session_combo.addItems(self.config.get("sessions", []))
        self.default_session_combo.setCurrentText(self.config.get("default_session", "2025-2026"))
        layout.addWidget(self.default_session_combo)

        remove_btn = QPushButton("Remove Selected Session")
        remove_btn.clicked.connect(self.remove_session)
        layout.addWidget(remove_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_subjects_tab(self):
        """Create Subjects tab in Settings Dialog"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Subjects in Database:"))

        # Create table instead of list
        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(2)
        self.subjects_table.setHorizontalHeaderLabels(["Subject Name", "Type"])
        self.subjects_table.horizontalHeader().setStretchLastSection(False)
        self.subjects_table.setColumnWidth(0, 250)
        self.subjects_table.setColumnWidth(1, 100)
        self.load_subjects_from_db()
        layout.addWidget(self.subjects_table)

        # Add new subject section
        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("Add New Subject:"))

        input_layout = QHBoxLayout()
        self.new_subject_input = QLineEdit()
        self.new_subject_input.setPlaceholderText("Enter subject name")
        input_layout.addWidget(self.new_subject_input)

        # Type dropdown (Core / Non-Core)
        input_layout.addWidget(QLabel("Type:"))
        self.subject_type_combo = NoWheelComboBox()
        self.subject_type_combo.addItems(["Core", "Non-Core"])
        input_layout.addWidget(self.subject_type_combo)

        add_btn = QPushButton("Add Subject")
        add_btn.clicked.connect(self.add_subject_to_db)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        remove_btn = QPushButton("Remove Selected Subject")
        remove_btn.clicked.connect(self.remove_subject_from_db)
        layout.addWidget(remove_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_subjects_from_db(self):
        """Load all subjects from database into table"""
        try:
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()

            cursor.execute("SELECT subject_id, subject_name, type FROM subjects ORDER BY subject_name")
            subjects = cursor.fetchall()

            self.subjects_table.setRowCount(0)
            self.subject_db_ids = {}

            for row_idx, (subject_id, subject_name, subject_type) in enumerate(subjects):
                self.subjects_table.insertRow(row_idx)

                # Subject Name column
                name_item = QTableWidgetItem(subject_name)
                self.subjects_table.setItem(row_idx, 0, name_item)

                # Type column
                type_item = QTableWidgetItem(subject_type)
                self.subjects_table.setItem(row_idx, 1, type_item)

                # Store ID for deletion
                self.subject_db_ids[row_idx] = subject_id

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading subjects: {e}")

    def add_subject_to_db(self):
        """Add new subject to database"""
        subject_name = self.new_subject_input.text().strip()
        subject_type = self.subject_type_combo.currentText()

        if not subject_name:
            QMessageBox.warning(self, "Error", "Subject name cannot be empty!")
            return

        try:
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()

            # Check if subject already exists
            cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = ?", (subject_name,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", f"Subject '{subject_name}' already exists!")
                conn.close()
                return

            # Insert new subject
            cursor.execute(
                "INSERT INTO subjects (subject_name, type) VALUES (?, ?)",
                (subject_name, subject_type)
            )
            conn.commit()
            conn.close()

            # Reload table and clear input
            self.load_subjects_from_db()
            self.new_subject_input.clear()

            QMessageBox.information(self, "Success", f"Subject '{subject_name}' added as {subject_type}!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding subject: {e}")

    def remove_subject_from_db(self):
        """Remove selected subject from database"""
        selected_row = self.subjects_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Select a subject to delete!")
            return

        subject_id = self.subject_db_ids.get(selected_row)
        subject_name = self.subjects_table.item(selected_row, 0).text()

        if not subject_id:
            QMessageBox.warning(self, "Error", "Could not find subject ID!")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{subject_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()

            cursor.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
            conn.commit()
            conn.close()

            # Reload table
            self.load_subjects_from_db()
            QMessageBox.information(self, "Success", "Subject deleted!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error deleting subject: {e}")

    def create_marks_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Maximum Marks Options:"))
        self.marks_list = QListWidget()
        for marks in self.config.get("max_marks_options", []):
            self.marks_list.addItem(str(marks))
        layout.addWidget(self.marks_list)

        input_layout = QHBoxLayout()
        self.new_marks_input = QSpinBox()
        self.new_marks_input.setMinimum(1)
        self.new_marks_input.setMaximum(500)
        add_btn = QPushButton("Add Marks Option")
        add_btn.clicked.connect(self.add_marks)
        input_layout.addWidget(self.new_marks_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_marks)
        layout.addWidget(remove_btn)

        layout.addWidget(QLabel("Default Maximum Marks:"))
        self.default_marks_combo = NoWheelComboBox()
        self.default_marks_combo.addItems([str(m) for m in self.config.get("max_marks_options", [])])
        self.default_marks_combo.setCurrentText(str(self.config.get("default_max_marks", 100)))
        layout.addWidget(self.default_marks_combo)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_class_defaults_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Total School Days by Class:"))

        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        self.class_days_inputs = {}
        for class_name in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]:
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(f"Class {class_name}:"))
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(500)
            spin.setValue(self.config.get("class_defaults", {}).get(class_name, 220))
            self.class_days_inputs[class_name] = spin
            h_layout.addWidget(spin)
            scroll_layout.addLayout(h_layout)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def add_session(self):
        text = self.new_session_input.text().strip()
        if text and text not in [self.sessions_list.item(i).text() for i in range(self.sessions_list.count())]:
            self.sessions_list.addItem(text)
            self.new_session_input.clear()
            self.default_session_combo.addItem(text)

    def remove_session(self):
        if self.sessions_list.currentItem():
            self.sessions_list.takeItem(self.sessions_list.row(self.sessions_list.currentItem()))

    def add_subject(self):
        text = self.new_subject_input.text().strip()
        if text and text not in [self.subjects_list.item(i).text() for i in range(self.subjects_list.count())]:
            self.subjects_list.addItem(text)
            self.new_subject_input.clear()

    def remove_subject(self):
        if self.subjects_list.currentItem():
            self.subjects_list.takeItem(self.subjects_list.row(self.subjects_list.currentItem()))

    def add_marks(self):
        marks = self.new_marks_input.value()
        if str(marks) not in [self.marks_list.item(i).text() for i in range(self.marks_list.count())]:
            self.marks_list.addItem(str(marks))
            self.default_marks_combo.addItem(str(marks))

    def remove_marks(self):
        if self.marks_list.currentItem():
            self.marks_list.takeItem(self.marks_list.row(self.marks_list.currentItem()))

    def save_settings(self):
        self.config["sessions"] = [self.sessions_list.item(i).text() for i in range(self.sessions_list.count())]
        self.config["default_session"] = self.default_session_combo.currentText()
        self.config["subjects"] = [self.subjects_list.item(i).text() for i in range(self.subjects_list.count())]
        self.config["max_marks_options"] = [int(self.marks_list.item(i).text()) for i in range(self.marks_list.count())]
        self.config["default_max_marks"] = int(self.default_marks_combo.currentText())

        for class_name, spin in self.class_days_inputs.items():
            self.config["class_defaults"][class_name] = spin.value()

        ConfigManager.save(self.config)
        QMessageBox.information(self, "Success", "Settings saved successfully!")
        self.accept()

class SubjectFilterDialog(QDialog):
    """Dialog to select subjects for report card"""

    def __init__(self, config, saved_filters=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Subjects")
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(350, 400)  # Set minimum size for resizing
        self.config = config
        self.saved_filters = saved_filters or {}
        self.selected_subjects = []

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Subjects to Include:"))

        # Create scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Load subjects from database instead of config
        self.checkboxes = {}
        subjects = self.load_subjects_from_db()

        for subject_name, subject_type in subjects:
            cb = QCheckBox(f"{subject_name} ({subject_type})")
            cb.setChecked(True)
            cb.setProperty("subject_name", subject_name)  # Store actual name for filtering
            self.checkboxes[subject_name] = cb
            scroll_layout.addWidget(cb)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("Saved Filters:"))

        self.filters_combo = NoWheelComboBox()
        self.filters_combo.addItem("-- New Filter --")
        if self.saved_filters:
            self.filters_combo.addItems(self.saved_filters.keys())
        self.filters_combo.currentTextChanged.connect(self.load_filter)
        layout.addWidget(self.filters_combo)

        filter_btn_layout = QHBoxLayout()
        self.save_filter_btn = QPushButton("Save as Filter")
        self.save_filter_btn.clicked.connect(self.save_filter_dialog)
        self.delete_filter_btn = QPushButton("Delete Filter")
        self.delete_filter_btn.clicked.connect(self.delete_filter)
        filter_btn_layout.addWidget(self.save_filter_btn)
        filter_btn_layout.addWidget(self.delete_filter_btn)
        layout.addLayout(filter_btn_layout)

        layout.addStretch()

        btn_layout2 = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout2.addWidget(ok_btn)
        btn_layout2.addWidget(cancel_btn)
        layout.addLayout(btn_layout2)

        self.setLayout(layout)

    def load_subjects_from_db(self):
        """Load all subjects from database"""
        try:
            import sqlite3
            conn = sqlite3.connect("report_system.db")
            cursor = conn.cursor()

            cursor.execute("SELECT subject_name, type FROM subjects ORDER BY subject_name")
            subjects = cursor.fetchall()
            conn.close()

            return subjects
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading subjects: {e}")
            return []

    def load_filter(self, filter_name):
        if filter_name == "-- New Filter --":
            # Reset all to checked
            for cb in self.checkboxes.values():
                cb.setChecked(True)
            return

        if filter_name in self.saved_filters:
            filter_subjects = self.saved_filters[filter_name]
            # Uncheck all
            for cb in self.checkboxes.values():
                cb.setChecked(False)
            # Check only the ones in filter
            for subject in filter_subjects:
                if subject in self.checkboxes:
                    self.checkboxes[subject].setChecked(True)

    def save_filter_dialog(self):
        filter_name, ok = QtWidgets.QInputDialog.getText(self, "Save Filter", "Filter Name:")
        if ok and filter_name:
            selected = self.get_selected_subjects()
            self.saved_filters[filter_name] = selected
            FiltersManager.save(self.saved_filters)

            # Add to combo if not exists
            if self.filters_combo.findText(filter_name) == -1:
                self.filters_combo.addItem(filter_name)

            QMessageBox.information(self, "Success", f"Filter '{filter_name}' saved!")

    def delete_filter(self):
        current = self.filters_combo.currentText()
        if current == "-- New Filter --":
            QMessageBox.warning(self, "Error", "Cannot delete default filter")
            return

        if current in self.saved_filters:
            reply = QMessageBox.question(self, "Confirm", f"Delete filter '{current}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.saved_filters[current]
                FiltersManager.save(self.saved_filters)
                self.filters_combo.removeItem(self.filters_combo.currentIndex())
                QMessageBox.information(self, "Success", "Filter deleted!")

    def get_selected_subjects(self):
        """Return list of selected subject names"""
        return [subject for subject, cb in self.checkboxes.items() if cb.isChecked()]

class MarksTableWidget(QWidget):
    """Widget to handle arrow key navigation in marks table"""
    def __init__(self, marks_grid):
        super().__init__()
        self.marks_grid = marks_grid
        self.current_row = 0
        self.current_col = 0
        self.setFocusPolicy(Qt.StrongFocus)  # Enable focus

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            # Tab out of table to next widget
            self.focusNextChild()
            event.accept()
        elif event.key() == Qt.Key_Backtab:
            # Shift+Tab out of table to previous widget
            self.focusPreviousChild()
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.current_row = min(self.current_row + 1, len(self.marks_grid) - 1)
            self.focus_cell()
            event.accept()
        elif event.key() == Qt.Key_Up:
            self.current_row = max(self.current_row - 1, 0)
            self.focus_cell()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.current_col = min(self.current_col + 1, 2)
            self.focus_cell()
            event.accept()
        elif event.key() == Qt.Key_Left:
            self.current_col = max(self.current_col - 1, 0)
            self.focus_cell()
            event.accept()
        else:
            super().keyPressEvent(event)

    def focus_cell(self):
        columns = ["coursework", "termexam", "maxmarks"]
        if self.current_row < len(self.marks_grid):
            cell = self.marks_grid[self.current_row].get(columns[self.current_col])
            if cell:
                cell.setFocus()

class StudentViewWidget(QWidget):
    """Widget to view and manage students"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        
        # Top buttons
        btn_layout = QHBoxLayout()
        
        download_sample_btn = QPushButton("📥 Download Sample Excel")
        download_sample_btn.clicked.connect(self.download_sample_excel)
        btn_layout.addWidget(download_sample_btn)
        
        upload_excel_btn = QPushButton("📤 Upload Excel")
        upload_excel_btn.clicked.connect(self.upload_excel)
        btn_layout.addWidget(upload_excel_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_student)
        btn_layout.addWidget(delete_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_students)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
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
        layout.addWidget(self.students_table)
        
        self.setLayout(layout)
        self.load_students()
    
    def load_students(self):
        """Load students from database"""
        import sqlite3
        conn = sqlite3.connect("report_system.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gr_no, student_name, father_name, 
                   current_class_sec, current_session, status, contact_number_resident, address
            FROM students
            ORDER BY gr_no
        """)
        
        students = cursor.fetchall()
        conn.close()
        
        self.students_table.setRowCount(len(students))
        for row_idx, student in enumerate(students):
            for col_idx, value in enumerate(student):
                item = QTableWidgetItem(str(value) if value else "")
                self.students_table.setItem(row_idx, col_idx, item)
    
    def delete_student(self):
        """Delete selected student"""
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
            # Create sample DataFrame with exact database columns
            sample_data = {
                'current_class_sec': ['I-A', 'II-B', 'III-C'],
                'gr_no': ['001', '002', '003'],
                'student_name': ['Student Name 1', 'Student Name 2', 'Student Name 3'],
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
            required_cols = ['current_class_sec', 'gr_no', 'student_name', 'address', 
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
            
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO students (
                            gr_no, student_name, current_class_sec, address,
                            contact_number_resident, contact_number_neighbour, contact_number_relative,
                            contact_number_other1, contact_number_other2, contact_number_other3, 
                            contact_number_other4, date_of_birth, joining_date
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row['gr_no']),
                        str(row['student_name']),
                        str(row['current_class_sec']),
                        str(row['address']),
                        str(row['contact_number_resident']),
                        str(row['contact_number_neighbour']),
                        str(row['contact_number_relative']),
                        str(row['contact_number_other1']),
                        str(row['contact_number_other2']),
                        str(row['contact_number_other3']),
                        str(row['contact_number_other4']),
                        str(row['date_of_birth']) if pd.notna(row['date_of_birth']) else None,
                        str(row['joining_date']) if pd.notna(row['joining_date']) else None
                    ))
                    success_count += 1
                except sqlite3.IntegrityError as e:
                    error_count += 1
                    errors.append(f"Row {idx + 2}: G.R No {row['gr_no']} already exists")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {idx + 2}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            # Show result
            msg = f"Import completed!\n\nSuccessfully added: {success_count} students"
            if error_count > 0:
                msg += f"\nFailed: {error_count} students\n\n"
                msg += "Errors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    msg += f"\n... and {len(errors) - 10} more errors"
            
            QMessageBox.information(self, "Import Result", msg)
            self.load_students()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import Excel file:\n{str(e)}")

class NavigableMainWindow(QtWidgets.QMainWindow):
    """Main window with arrow key navigation"""
    def __init__(self):
        super().__init__()
        self.focused_widget_index = 0
        self.all_widgets = []  # Will be populated after widgets are created

    def register_widgets(self, widgets_list):
        """Register widgets in navigation order"""
        self.all_widgets = widgets_list
        if self.all_widgets:
            self.all_widgets[0].setFocus()
            self.focused_widget_index = 0

    def keyPressEvent(self, event):
        """Handle arrow key navigation"""
        if event.key() == Qt.Key_Down or event.key() == Qt.Key_Right:
            self.move_to_next_widget()
            event.accept()
        elif event.key() == Qt.Key_Up or event.key() == Qt.Key_Left:
            self.move_to_previous_widget()
            event.accept()
        else:
            super().keyPressEvent(event)

    def move_to_next_widget(self):
        """Move focus to next widget"""
        if not self.all_widgets:
            return
        self.focused_widget_index = (self.focused_widget_index + 1) % len(self.all_widgets)
        self.all_widgets[self.focused_widget_index].setFocus()

    def move_to_previous_widget(self):
        """Move focus to previous widget"""
        if not self.all_widgets:
            return
        self.focused_widget_index = (self.focused_widget_index - 1) % len(self.all_widgets)
        self.all_widgets[self.focused_widget_index].setFocus()

class MainWindow(NavigableMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 Faizan Academy - Report Card System")

        # Set icon and stylesheet
        self.setStyleSheet(MODERN_STYLESHEET)

        self.config = ConfigManager.load()
        self.filters = FiltersManager.load()
        self.selected_subjects = self.config.get("subjects", [])
        self.marks_grid = [] # Initialize marks_grid

        self.create_menu()
        self.create_form()
        self.load_initial_subjects()
        # self.setup_complete_tab_order() # Removed - handled by register_widgets
        
        # Open maximized (windowed fullscreen with minimize/close buttons)
        self.showMaximized()

    def reset_form(self):
        """Clear all form fields"""
        self.student_name_input.clear()
        self.father_name_input.clear()
        self.class_sec_input.clear()
        self.gr_no_input.clear()
        self.term_combo.setCurrentIndex(0)
        self.session_combo.setCurrentText(self.config.get("default_session", "2025-2026"))
        self.rank_combo.setCurrentIndex(0)
        self.total_days_input.setValue(0)
        self.days_attended_input.setValue(0)
        self.days_absent_input.setValue(0)
        self.conduct_combo.setCurrentIndex(0)
        self.performance_combo.setCurrentIndex(0)
        self.progress_combo.setCurrentIndex(0)
        self.remarks_input.clear()
        self.status_group.setExclusive(False)
        for button in self.status_group.buttons():
            button.setChecked(False)
        self.status_group.setExclusive(True)
        self.date_input.setDate(QDate.currentDate())

        # Clear marks table
        for subject, row in self.marks_inputs.items():
            row["coursework"].clear()
            row["termexam"].clear()
            row["cw_absent"].setChecked(False)
            row["te_absent"].setChecked(False)
            row["coursework"].setEnabled(True)
            row["termexam"].setEnabled(True)
            row["maxmarks"].setEnabled(True)

        self.update_grand_totals()

    def create_menu(self):
        menubar = self.menuBar()
        
        settings_action = menubar.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.config = ConfigManager.load()
            self.update_form()

    def create_form(self):
        widget = QtWidgets.QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(60, 40, 60, 40)

        # --- Term Selection ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Term:"))
        self.term_combo = NoWheelComboBox()
        self.term_combo.addItems(["Mid Year", "Annual Year"])
        h.addWidget(self.term_combo)
        h.addStretch()
        layout.addLayout(h)

        # --- Session Selection ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Session:"))
        self.session_combo = NoWheelComboBox()
        self.session_combo.addItems(self.config.get("sessions", []))
        self.session_combo.setCurrentText(self.config.get("default_session", "2025-2026"))
        h.addWidget(self.session_combo)
        h.addStretch()
        layout.addLayout(h)

        # --- Student's Name ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Student's Name:"))
        self.student_name_input = QLineEdit()
        h.addWidget(self.student_name_input)
        layout.addLayout(h)

        # --- Father's Name ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Father's Name:"))
        self.father_name_input = QLineEdit()
        h.addWidget(self.father_name_input)
        layout.addLayout(h)

        # --- Class/Sec with Live Validation ---
        class_layout = QVBoxLayout()
        h = QHBoxLayout()
        h.addWidget(QLabel("Class/Sec:"))
        self.class_sec_input = QLineEdit()
        self.class_sec_input.setPlaceholderText("e.g., I-A, II-B, III-C")
        self.class_sec_input.textChanged.connect(self.validate_class_sec_live)
        h.addWidget(self.class_sec_input)
        layout.addLayout(h)

        self.class_sec_error = QLabel("")
        self.class_sec_error.setStyleSheet("color: #e74c3c; font-size: 9px;")
        layout.addWidget(self.class_sec_error)

        # --- G.R No with Live Validation (Numeric Only) ---
        h = QHBoxLayout()
        h.addWidget(QLabel("G.R No.:"))
        self.gr_no_input = QLineEdit()
        self.gr_no_input.setPlaceholderText("Numeric only")
        self.gr_no_input.textChanged.connect(self.validate_gr_no_live)
        h.addWidget(self.gr_no_input)
        layout.addLayout(h)

        # --- Rank in Class ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Rank in Class:"))
        self.rank_combo = NoWheelComboBox()
        items = ["N/A"] + [str(i) for i in range(1, 11)]
        self.rank_combo.addItems(items)
        self.rank_combo.setCurrentIndex(0)
        h.addWidget(self.rank_combo)
        h.addStretch()
        layout.addLayout(h)

        # --- School Days ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Total School Days:"))
        self.total_days_input = QSpinBox()
        self.total_days_input.setMaximum(500)
        self.total_days_input.valueChanged.connect(self.calculate_days_absent)
        h.addWidget(self.total_days_input)
        h.addStretch()
        layout.addLayout(h)

        h = QHBoxLayout()
        h.addWidget(QLabel("Days Attended:"))
        self.days_attended_input = QSpinBox()
        self.days_attended_input.setMaximum(500)
        self.days_attended_input.valueChanged.connect(self.calculate_days_absent)
        h.addWidget(self.days_attended_input)
        h.addStretch()
        layout.addLayout(h)

        h = QHBoxLayout()
        h.addWidget(QLabel("Days Absent:"))
        self.days_absent_input = QSpinBox()
        self.days_absent_input.setMaximum(500)
        self.days_absent_input.setReadOnly(True)
        self.days_absent_input.setStyleSheet("""
            QSpinBox {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                color: #7f8c8d;
            }
        """)
        h.addWidget(self.days_absent_input)
        h.addStretch()
        layout.addLayout(h)

        # --- Marks Section with Filter ---
        marks_header_layout = QHBoxLayout()
        marks_label = QLabel("Subject Marks")
        marks_label.setFont(QFont("Arial", 12, QFont.Bold))
        marks_header_layout.addWidget(marks_label)
        filter_btn = QPushButton("▼ Select Subjects")
        filter_btn.setObjectName("filterBtn")
        filter_btn.setMaximumWidth(150)
        filter_btn.clicked.connect(self.open_subject_filter)
        marks_header_layout.addWidget(filter_btn)
        marks_header_layout.addStretch()
        layout.addLayout(marks_header_layout)

        self.marks_container = QWidget()
        self.marks_layout = QVBoxLayout()
        self.marks_layout.setSpacing(5)
        self.marks_container.setLayout(self.marks_layout)
        layout.addWidget(self.marks_container)

        # --- Conduct/Performance Section ---
        layout.addWidget(QLabel("Conduct:"))
        self.conduct_combo = NoWheelComboBox()
        self.conduct_combo.addItems(["Good", "Fair", "Bad"])
        layout.addWidget(self.conduct_combo)

        layout.addWidget(QLabel("Daily Performance:"))
        self.performance_combo = NoWheelComboBox()
        self.performance_combo.addItems(["Excellent", "Good", "Bad"])
        layout.addWidget(self.performance_combo)

        layout.addWidget(QLabel("Progress:"))
        self.progress_combo = NoWheelComboBox()
        self.progress_combo.addItems(["Satisfactory", "Unsatisfactory"])
        layout.addWidget(self.progress_combo)

        # --- Teacher's Remarks ---
        layout.addWidget(QLabel("Teacher's Remarks:"))

        remarks_layout = QHBoxLayout()
        self.remarks_input = QtWidgets.QTextEdit()
        self.remarks_input.setMaximumHeight(80)
        self.remarks_input.setTabChangesFocus(True)
        remarks_layout.addWidget(self.remarks_input)

        preset_btn = QPushButton("💬 Presets")
        preset_btn.setObjectName("presetsBtn")
        preset_btn.clicked.connect(self.show_preset_remarks)
        remarks_layout.addWidget(preset_btn)

        layout.addLayout(remarks_layout)

        # --- Result Status ---
        layout.addWidget(QLabel("Result Status:"))
        self.status_group = QtWidgets.QButtonGroup()
        status_layout = QHBoxLayout()
        for i, status in enumerate(["Passed", "Promoted with Support", "Needs Improvement"]):
            rb = QtWidgets.QRadioButton(status)
            status_layout.addWidget(rb)
            self.status_group.addButton(rb, i)
        layout.addLayout(status_layout)

        # --- Date ---
        h = QHBoxLayout()
        h.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd MMMM yyyy")
        
        # Create calendar widget and ensure it appears on top
        from PySide6.QtWidgets import QCalendarWidget
        calendar = QCalendarWidget()
        calendar.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.date_input.setCalendarWidget(calendar)
        
        h.addWidget(self.date_input)
        h.addStretch()
        layout.addLayout(h)

        # --- Generate Button ---
        generate_btn = QPushButton("✓ Generate PDF")
        generate_btn.setObjectName("generateBtn") # Set object name
        generate_btn.setMinimumHeight(45)
        generate_btn.setFont(QFont("Arial", 12, QFont.Bold))
        generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #27ae60, stop:1 #1e8449);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #229954, stop:1 #186a3b);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e8449, stop:1 #145a32);
            }
        """)
        generate_btn.clicked.connect(self.generate_pdf)
        layout.addWidget(generate_btn)

        layout.addStretch()

        widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3498db;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #2980b9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(scroll, "Result")
        self.tab_widget.addTab(StudentViewWidget(self), "Student View")
        
        self.setCentralWidget(self.tab_widget)

        # Register all widgets in exact navigation order
        widgets_order = [
            self.term_combo,
            self.session_combo,
            self.student_name_input,
            self.father_name_input,
            self.class_sec_input,
            self.gr_no_input,
            self.rank_combo,
            self.total_days_input,
            self.days_attended_input,
        ]

        # Find Select Subjects button and add
        for btn in self.findChildren(QPushButton):
            if "Select Subjects" in btn.text():
                widgets_order.append(btn)
                break

        # Add all table fields (will populate after marks table is created)
        # Store for later update
        self.widgets_order_base = widgets_order

        # Rest will be added in populate_marks_table()

    def validate_class_sec_live(self):
        """Live validation for class/section format"""
        text = self.class_sec_input.text().strip()
        pattern = r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|\d+)-[A-Z]$'

        if not text:
            self.class_sec_error.setText("")
            return True

        if re.match(pattern, text):
            self.class_sec_error.setText("")
            self.class_sec_input.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    border: 2px solid #27ae60;
                    border-radius: 6px;
                    padding: 8px;
                    color: #2c3e50;
                }
            """)
            return True
        else:
            self.class_sec_error.setText("❌ Format: I-A, II-B, III-C, etc.")
            self.class_sec_input.setStyleSheet("""
                QLineEdit {
                    background-color: #fff5f5;
                    border: 2px solid #e74c3c;
                    border-radius: 6px;
                    padding: 8px;
                    color: #2c3e50;
                }
            """)
            return False

    def validate_gr_no_live(self):
        """Live validation for G.R number - numeric only"""
        text = self.gr_no_input.text()

        # Remove any non-numeric characters
        numeric_text = ''.join(c for c in text if c.isdigit())

        if numeric_text != text:
            self.gr_no_input.blockSignals(True)
            self.gr_no_input.setText(numeric_text)
            self.gr_no_input.blockSignals(False)

    def calculate_days_absent(self):
        """Auto-calculate days absent as total - attended"""
        total = self.total_days_input.value()
        attended = self.days_attended_input.value()
        absent = max(0, total - attended)
        self.days_absent_input.setValue(absent)

    def update_form(self):
        self.session_combo.clear()
        self.session_combo.addItems(self.config.get("sessions", []))
        self.session_combo.setCurrentText(self.config.get("default_session", "2025-2026"))

    def open_subject_filter(self):
        dialog = SubjectFilterDialog(self.config, self.filters, self)
        if dialog.exec():
            self.selected_subjects = dialog.get_selected_subjects()
            self.populate_marks_table()

    def load_initial_subjects(self):
        """Load first saved filter or all subjects by default"""
        if self.filters:
            first_filter = list(self.filters.values())[0]
            self.selected_subjects = first_filter
        else:
            self.selected_subjects = self.config.get("subjects", [])
        self.populate_marks_table()

    def get_grade(self, percentage):
        """Calculate grade based on percentage"""
        try:
            pct = float(percentage)
            if pct >= 80:
                return "A1"
            elif pct >= 70:
                return "A"
            elif pct >= 60:
                return "B"
            elif pct >= 50:
                return "C"
            elif pct >= 40:
                return "D"
            else:
                return "U"
        except:
            return "-"

    def populate_marks_table(self):
        """Populate marks table with validation, navigation support, and absent checkboxes"""
        while self.marks_layout.count():
            item = self.marks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_marks_options = self.config.get("max_marks_options", [100])

        table_container = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setSpacing(0)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        header_layout.setContentsMargins(0, 0, 0, 0)

        headers = ["Subject", "Course Work", "Term Exam", "Max", "Obt", "%", "Grade", "CW Absent", "TE Absent"]
        widths = [120, 100, 100, 70, 70, 70, 70, 80, 80]

        for header_text, width in zip(headers, widths):
            header = QLabel(header_text)
            header.setMinimumWidth(width)
            header.setMaximumWidth(width)
            header.setFont(QFont("Arial", 10, QFont.Bold))
            header.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(header)

        header_layout.addStretch()
        table_layout.addLayout(header_layout)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setLineWidth(2)
        table_layout.addWidget(separator)

        self.marks_inputs = {}
        self.marks_grid = []

        marks_rows_layout = QVBoxLayout()
        marks_rows_layout.setSpacing(0)
        marks_rows_layout.setContentsMargins(0, 0, 0, 0)

        for subject_idx, subject in enumerate(self.selected_subjects):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_data = {}

            # Subject name
            label = QLabel(subject)
            label.setMinimumWidth(120)
            label.setMaximumWidth(120)
            row_layout.addWidget(label)

            # Course Work
            coursework = NavigableLineEdit()
            coursework.setPlaceholderText("0")
            coursework.setMinimumWidth(100)
            coursework.setMaximumWidth(100)
            coursework.textChanged.connect(lambda text, s=subject: self.validate_marks_sum(s))
            row_layout.addWidget(coursework)
            row_data["coursework"] = coursework

            # Term Exam
            termexam = NavigableLineEdit()
            termexam.setPlaceholderText("0")
            termexam.setMinimumWidth(100)
            termexam.setMaximumWidth(100)
            termexam.textChanged.connect(lambda text, s=subject: self.validate_marks_sum(s))
            row_layout.addWidget(termexam)
            row_data["termexam"] = termexam

            # Max Marks
            combo = NavigableComboBox()
            combo.addItems([str(m) for m in max_marks_options])
            combo.setCurrentText(str(self.config.get("default_max_marks", 100)))
            combo.setMinimumWidth(70)
            combo.setMaximumWidth(70)
            combo.currentTextChanged.connect(lambda text, s=subject: self.validate_marks_sum(s))
            row_layout.addWidget(combo)
            row_data["maxmarks"] = combo

            # Obtained marks
            obt_label = QLabel("0")
            obt_label.setMinimumWidth(70)
            obt_label.setMaximumWidth(70)
            obt_label.setAlignment(Qt.AlignCenter)
            obt_label.setStyleSheet("color: #3498db; font-weight: bold;")
            obt_label.setFocusPolicy(Qt.NoFocus)
            row_layout.addWidget(obt_label)
            row_data["obt"] = obt_label

            # Percentage
            pct_label = QLabel("0%")
            pct_label.setMinimumWidth(70)
            pct_label.setMaximumWidth(70)
            pct_label.setAlignment(Qt.AlignCenter)
            pct_label.setStyleSheet("color: #2980b9; font-weight: bold;")
            pct_label.setFocusPolicy(Qt.NoFocus)
            row_layout.addWidget(pct_label)
            row_data["pct"] = pct_label

            # Grade
            grade_label = QLabel("-")
            grade_label.setMinimumWidth(70)
            grade_label.setMaximumWidth(70)
            grade_label.setAlignment(Qt.AlignCenter)
            grade_label.setStyleSheet("color: #27ae60; font-weight: bold; background-color: #d5f4e6; border-radius: 4px; padding: 2px;")
            grade_label.setFocusPolicy(Qt.NoFocus)
            row_layout.addWidget(grade_label)
            row_data["grade"] = grade_label

            # *** CW ABSENT CHECKBOX ***
            cw_absent_cb = QCheckBox("CW")
            cw_absent_cb.setMinimumWidth(80)
            cw_absent_cb.setMaximumWidth(80)
            cw_absent_cb.stateChanged.connect(lambda state, s=subject: self.handle_cw_absent_toggle(s, state))
            row_layout.addWidget(cw_absent_cb)
            row_data["cw_absent"] = cw_absent_cb

            # *** TE ABSENT CHECKBOX ***
            te_absent_cb = QCheckBox("TE")
            te_absent_cb.setMinimumWidth(80)
            te_absent_cb.setMaximumWidth(80)
            te_absent_cb.stateChanged.connect(lambda state, s=subject: self.handle_te_absent_toggle(s, state))
            row_layout.addWidget(te_absent_cb)
            row_data["te_absent"] = te_absent_cb

            row_layout.addStretch()

            self.marks_inputs[subject] = row_data
            self.marks_grid.append(row_data)
            marks_rows_layout.addLayout(row_layout)

        marks_table_widget = MarksTableWidget(self.marks_grid)
        marks_table_widget.setLayout(marks_rows_layout)
        table_layout.addWidget(marks_table_widget)

        # Separator
        separator2 = QtWidgets.QFrame()
        separator2.setFrameShape(QtWidgets.QFrame.HLine)
        separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator2.setLineWidth(1)
        table_layout.addWidget(separator2)

        # Grand Total row
        grand_layout = QHBoxLayout()
        grand_layout.setSpacing(5)
        grand_layout.setContentsMargins(5, 10, 0, 10)

        grand_label = QLabel("GRAND TOTAL")
        grand_label.setMinimumWidth(120)
        grand_label.setMaximumWidth(120)
        grand_label.setFont(QFont("Arial", 11, QFont.Bold))
        grand_layout.addWidget(grand_label)

        self.grand_cw = QLabel("0")
        self.grand_cw.setMinimumWidth(100)
        self.grand_cw.setMaximumWidth(100)
        self.grand_cw.setAlignment(Qt.AlignCenter)
        self.grand_cw.setFont(QFont("Arial", 11, QFont.Bold))
        self.grand_cw.setStyleSheet("color: #27ae60; background-color: #d5f4e6; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_cw)

        self.grand_te = QLabel("0")
        self.grand_te.setMinimumWidth(100)
        self.grand_te.setMaximumWidth(100)
        self.grand_te.setAlignment(Qt.AlignCenter)
        self.grand_te.setFont(QFont("Arial", 11, QFont.Bold))
        self.grand_te.setStyleSheet("color: #27ae60; background-color: #d5f4e6; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_te)

        self.grand_max = QLabel("0")
        self.grand_max.setMinimumWidth(70)
        self.grand_max.setMaximumWidth(70)
        self.grand_max.setAlignment(Qt.AlignCenter)
        self.grand_max.setFont(QFont("Arial", 11, QFont.Bold))
        self.grand_max.setStyleSheet("color: #27ae60; background-color: #d5f4e6; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_max)

        self.grand_obt = QLabel("0")
        self.grand_obt.setMinimumWidth(70)
        self.grand_obt.setMaximumWidth(70)
        self.grand_obt.setAlignment(Qt.AlignCenter)
        self.grand_obt.setFont(QFont("Arial", 11, QFont.Bold))
        self.grand_obt.setStyleSheet("color: #27ae60; background-color: #d5f4e6; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_obt)

        self.grand_pct = QLabel("0%")
        self.grand_pct.setMinimumWidth(70)
        self.grand_pct.setMaximumWidth(70)
        self.grand_pct.setAlignment(Qt.AlignCenter)
        self.grand_pct.setFont(QFont("Arial", 11, QFont.Bold))
        self.grand_pct.setStyleSheet("color: #fff; background-color: #27ae60; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_pct)

        self.grand_grade = QLabel("-")
        self.grand_grade.setMinimumWidth(70)
        self.grand_grade.setMaximumWidth(70)
        self.grand_grade.setAlignment(Qt.AlignCenter)
        self.grand_grade.setFont(QFont("Arial", 12, QFont.Bold))
        self.grand_grade.setStyleSheet("color: #fff; background-color: #1e8449; padding: 5px; border-radius: 4px;")
        grand_layout.addWidget(self.grand_grade)

        grand_layout.addStretch()
        table_layout.addLayout(grand_layout)

        table_container.setLayout(table_layout)
        self.marks_layout.addWidget(table_container)

        # Update widgets order
        widgets_order = self.widgets_order_base.copy()

        for row in self.marks_grid:
            widgets_order.append(row["coursework"])
            widgets_order.append(row["termexam"])
            widgets_order.append(row["maxmarks"])
            widgets_order.append(row["cw_absent"])  # Add CW absent checkbox to navigation
            widgets_order.append(row["te_absent"])  # Add TE absent checkbox to navigation

        widgets_order.extend([
            self.conduct_combo,
            self.performance_combo,
            self.progress_combo,
            self.remarks_input,
        ])

        for btn in self.findChildren(QPushButton):
            if "Presets" in btn.text():
                widgets_order.append(btn)
                break

        if self.status_group.buttons():
            widgets_order.append(self.status_group.buttons()[0])

        widgets_order.append(self.date_input)

        for btn in self.findChildren(QPushButton):
            if "Generate PDF" in btn.text():
                widgets_order.append(btn)
                break

        self.register_widgets(widgets_order)

    def handle_cw_absent_toggle(self, subject, state):
        """Handle when CW absent checkbox is toggled"""
        if subject not in self.marks_inputs:
            return

        row = self.marks_inputs[subject]
        is_cw_absent = (state == Qt.Checked)

        if is_cw_absent:
            # Disable CW input and clear it
            row["coursework"].setEnabled(False)
            row["coursework"].clear()
        else:
            # Enable CW input
            row["coursework"].setEnabled(True)

        # Update calculations
        self.validate_marks_sum(subject)

    def handle_te_absent_toggle(self, subject, state):
        """Handle when TE absent checkbox is toggled"""
        if subject not in self.marks_inputs:
            return

        row = self.marks_inputs[subject]
        is_te_absent = (state == Qt.Checked)

        if is_te_absent:
            # Disable TE input and clear it
            row["termexam"].setEnabled(False)
            row["termexam"].clear()
        else:
            # Enable TE input
            row["termexam"].setEnabled(True)

        # Update calculations
        self.validate_marks_sum(subject)

    def validate_marks_sum(self, subject):
        """Validate and update marks with percentage and grade calculation"""
        if subject not in self.marks_inputs:
            return

        row = self.marks_inputs[subject]

        cw_absent = row["cw_absent"].isChecked()
        te_absent = row["te_absent"].isChecked()

        # If both are absent, set everything to "Absent"
        if cw_absent and te_absent:
            row["obt"].setText("Absent")
            row["pct"].setText("Absent")
            row["grade"].setText("Absent")
            row["obt"].setStyleSheet("color: #e74c3c; font-weight: bold; font-style: italic;")
            row["pct"].setStyleSheet("color: #e74c3c; font-weight: bold; font-style: italic;")
            row["grade"].setStyleSheet("color: #e74c3c; font-weight: bold; font-style: italic; background-color: #ffe6e6; border-radius: 4px; padding: 2px;")
            self.update_grand_totals()
            return

        try:
            cw = float(row["coursework"].text() or 0) if not cw_absent else 0
            te = float(row["termexam"].text() or 0) if not te_absent else 0
            max_marks = float(row["maxmarks"].currentText())

            # Calculate based on available marks
            if cw_absent and not te_absent:
                # Only TE available
                obt = te
                pct = (obt / max_marks * 100) if max_marks > 0 else 0
            elif te_absent and not cw_absent:
                # Only CW available
                obt = cw
                pct = (obt / max_marks * 100) if max_marks > 0 else 0
            else:
                # Both available
                obt = cw + te
                pct = (obt / max_marks * 100) if max_marks > 0 else 0

            row["obt"].setText(str(int(obt)))
            row["pct"].setText(f"{pct:.1f}%")
            grade = self.get_grade(pct)
            row["grade"].setText(grade)

            # Styling
            if obt <= max_marks:
                if not cw_absent:
                    row["coursework"].setStyleSheet("""
                        QLineEdit {
                            background-color: #ffffff;
                            border: 2px solid #e1e8ed;
                            border-radius: 6px;
                            padding: 8px;
                            color: #2c3e50;
                        }
                    """)
                if not te_absent:
                    row["termexam"].setStyleSheet("""
                        QLineEdit {
                            background-color: #ffffff;
                            border: 2px solid #e1e8ed;
                            border-radius: 6px;
                            padding: 8px;
                            color: #2c3e50;
                        }
                    """)
                row["obt"].setStyleSheet("color: #3498db; font-weight: bold;")
                row["pct"].setStyleSheet("color: #2980b9; font-weight: bold;")
            else:
                if not cw_absent:
                    row["coursework"].setStyleSheet("""
                        QLineEdit {
                            background-color: #fff5f5;
                            border: 2px solid #e74c3c;
                            border-radius: 6px;
                            padding: 8px;
                            color: #2c3e50;
                        }
                    """)
                if not te_absent:
                    row["termexam"].setStyleSheet("""
                        QLineEdit {
                            background-color: #fff5f5;
                            border: 2px solid #e74c3c;
                            border-radius: 6px;
                            padding: 8px;
                            color: #2c3e50;
                        }
                    """)
                row["obt"].setStyleSheet("color: #e74c3c; font-weight: bold; background-color: #ffe6e6; padding: 2px; border-radius: 2px;")
                row["pct"].setStyleSheet("color: #e74c3c; font-weight: bold;")

            self.update_grand_totals()

        except ValueError:
            pass

    def update_grand_totals(self):
        """Update grand total row - excludes subjects where both marks are absent"""
        try:
            total_cw = 0
            total_te = 0
            total_max = 0
            total_obt = 0

            for subject, row in self.marks_inputs.items():
                cw_absent = row["cw_absent"].isChecked()
                te_absent = row["te_absent"].isChecked()

                # Skip if both are absent
                if cw_absent and te_absent:
                    continue

                cw = float(row["coursework"].text() or 0) if not cw_absent else 0
                te = float(row["termexam"].text() or 0) if not te_absent else 0
                max_m = float(row["maxmarks"].currentText())

                total_cw += cw
                total_te += te
                total_max += max_m
                total_obt += cw + te

            self.grand_cw.setText(str(int(total_cw)))
            self.grand_te.setText(str(int(total_te)))
            self.grand_max.setText(str(int(total_max)))
            self.grand_obt.setText(str(int(total_obt)))

            grand_pct = (total_obt / total_max * 100) if total_max > 0 else 0
            self.grand_pct.setText(f"{grand_pct:.1f}%")

            grand_grade = self.get_grade(grand_pct)
            self.grand_grade.setText(grand_grade)

        except ValueError:
            pass

    def show_preset_remarks(self):
        """Show dialog with preset remarks"""
        remarks_data = self.load_preset_remarks()

        dialog = QDialog(self)
        dialog.setWindowTitle("Preset Remarks")
        dialog.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select or manage preset remarks:"))

        remarks_list = QListWidget()
        for remark in remarks_data.get("presets", []):
            remarks_list.addItem(remark)
        layout.addWidget(remarks_list)

        btn_layout = QHBoxLayout()

        def insert_remark():
            if remarks_list.currentItem():
                self.remarks_input.insertPlainText(remarks_list.currentItem().text())
                dialog.close()

        def add_new_remark():
            text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Add Remark", "Enter new preset remark:")
            if ok and text:
                remarks_data["presets"].append(text)
                self.save_preset_remarks(remarks_data)
                remarks_list.addItem(text)

        def delete_remark():
            if remarks_list.currentItem():
                row = remarks_list.row(remarks_list.currentItem())
                remarks_data["presets"].pop(row)
                self.save_preset_remarks(remarks_data)
                remarks_list.takeItem(row)

        insert_btn = QPushButton("Insert Selected")
        insert_btn.clicked.connect(insert_remark)
        add_btn = QPushButton("Add New")
        add_btn.clicked.connect(add_new_remark)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(delete_remark)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)

        btn_layout.addWidget(insert_btn)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def load_preset_remarks(self):
        if os.path.exists(REMARKS_FILE):
            try:
                with open(REMARKS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"presets": []}
        return {"presets": []}

    def save_preset_remarks(self, remarks_data):
        try:
            with open(REMARKS_FILE, 'w') as f:
                json.dump(remarks_data, f, indent=2)
        except Exception as e:
            print(f"Error saving remarks: {e}")

    def get_marks_data_for_pdf(self):
        """Collects marks and grand total data, handling absent subjects"""
        marks_data = {}
        placeholder = "-"

        for subject, row in self.marks_inputs.items():
            cw_absent = row["cw_absent"].isChecked()
            te_absent = row["te_absent"].isChecked()

            if cw_absent and te_absent:
                # Both absent
                marks_data[subject] = {
                    "coursework": "Absent",
                    "termexam": "Absent",
                    "maxmarks": "Absent",
                    "obt": "Absent",
                    "pct": "Absent",
                    "grade": "Absent",
                    "is_absent": True
                }
            else:
                cw = row["coursework"].text() if not cw_absent else "Absent"
                te = row["termexam"].text() if not te_absent else "Absent"

                marks_data[subject] = {
                    "coursework": cw or placeholder,
                    "termexam": te or placeholder,
                    "maxmarks": row["maxmarks"].currentText(),
                    "obt": row["obt"].text(),
                    "pct": row["pct"].text(),
                    "grade": row["grade"].text(),
                    "is_absent": False
                }

        grand_totals = {
            "cw": self.grand_cw.text(),
            "te": self.grand_te.text(),
            "max": self.grand_max.text(),
            "obt": self.grand_obt.text(),
            "pct": self.grand_pct.text(),
            "grade": self.grand_grade.text()
        }

        return marks_data, grand_totals

    def generate_pdf(self):
        try:
            # Validate inputs
            student_name = self.student_name_input.text().strip().title()
            if not student_name:
                QMessageBox.warning(self, "Error", "Student name required!")
                return

            class_sec = self.class_sec_input.text().strip()
            if not self.validate_class_sec(class_sec):
                QMessageBox.warning(self, "Error", "Class/Sec format invalid! Use: I-A, II-B, etc.")
                return

            gr_no = self.gr_no_input.text().strip()
            if not self.validate_gr_no(gr_no):
                QMessageBox.warning(self, "Error", "G.R No must be numeric!")
                return

            # Collect all data
            father_name = self.father_name_input.text().strip().title()
            session = self.session_combo.currentText()
            rank = self.rank_combo.currentText()
            total_days = str(self.total_days_input.value())
            days_attended = str(self.days_attended_input.value())
            days_absent = str(self.days_absent_input.value())
            term = self.term_combo.currentText()

            # Get marks data
            marks_data, grand_totals = self.get_marks_data_for_pdf()

            # Collect conduct data
            conduct = self.conduct_combo.currentText()
            performance = self.performance_combo.currentText()
            progress = self.progress_combo.currentText()
            remarks = self.remarks_input.toPlainText()

            # Get status
            status_btn = self.status_group.checkedButton()
            status = status_btn.text() if status_btn else "Not Selected"

            # Get date in proper format
            date_obj = self.date_input.date()
            date_str = date_obj.toString("dd MMMM yyyy")

            # Generate PDF
            self.create_pdf_report(
                student_name, father_name, class_sec, session, gr_no, rank,
                total_days, days_attended, days_absent, term, marks_data,
                conduct, performance, progress, remarks, status, date_str,
                grand_totals # Pass new data
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def validate_class_sec(self, class_sec):
            """Validate class/section format (e.g., I-A, II-B, III-C)"""
            if not class_sec:
                return False
            # Pattern: Roman numeral or number, dash, and a letter
            pattern = r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|\d+)-[A-Z]$'
            return bool(re.match(pattern, class_sec))

    def validate_gr_no(self, gr_no):
        """Validate G.R number (must be numeric)"""
        if not gr_no:
            return False
        return gr_no.isdigit()

    def create_pdf_report(self, student_name, father_name, class_sec, session, gr_no, rank,
                         total_days, days_attended, days_absent, term, marks_data,
                         conduct, performance, progress, remarks, status, date_str,
                         grand_totals):
        """Generate PDF report using WeasyPrint and HTML template"""
        try:
            from src.managers.pdf_manager import PDFManager

            # Prepare data for template
            data = {
                "student_name": student_name,
                "father_name": father_name,
                "class_sec": class_sec,
                "session": session,
                "gr_no": gr_no,
                "rank": rank,
                "total_days": total_days,
                "days_attended": days_attended,
                "days_absent": days_absent,
                "term": term,
                "marks_data": marks_data,
                "conduct": conduct,
                "performance": performance,
                "progress": progress,
                "remarks": remarks,
                "status": status,
                "date": date_str,
                "grand_totals": grand_totals
            }

            # Generate filename
            filename = f"{student_name.replace(' ', '_')}_ReportCard_{session}"

            # Generate PDF
            success, message, pdf_path = PDFManager.generate_pdf(filename, data)

            if success:
                QMessageBox.information(self, "Success", f"PDF generated successfully!\n\nSaved at: {pdf_path}")
                self.reset_form()
            else:
                QMessageBox.critical(self, "Error", f"PDF Generation Failed:\n{message}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating PDF: {str(e)}")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # Show login dialog
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        # Login successful, show main window
        window = MainWindow()
        window.current_user_id = login_dialog.user_id
        window.current_user_role = login_dialog.user_role
        sys.exit(app.exec())
    else:
        # Login cancelled or failed
        sys.exit(0)

