"""
dialogs.py - Contains popup windows for user input.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QMessageBox, QCheckBox, QPushButton, 
    QLabel, QHBoxLayout, QComboBox, QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QCompleter
)
from PyQt6.QtCore import QTime, Qt
from PyQt6.QtGui import QColor, QBrush


class AddPersonDialog(QDialog):
    """A standard popup to capture a new person's name and role."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Person")
        self.setFixedWidth(300)
        
        # Layout
        self.layout = QVBoxLayout(self)
        
        # Input Fields
        self.layout.addWidget(QLabel("Full Name:"))
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)
        
        self.layout.addWidget(QLabel("Role (Optional):"))
        self.role_input = QLineEdit()
        self.layout.addWidget(self.role_input)
        
        # Buttons
        self.btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept) # Closes dialog and returns 'True'
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.btn_layout.addWidget(self.save_btn)
        self.btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(self.btn_layout)

    def get_data(self) -> dict:
        """Returns the collected input as a dictionary."""
        return {
            "name": self.name_input.text().strip().title(),
            "role": self.role_input.text().strip()
        }
    

class AddClassDialog(QDialog):
    """Popup to create a new class section (e.g. Grade 7 - Rizal)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Class")
        self.setFixedWidth(300)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Grade Level:"))
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Grade 7", "Grade 8", "Grade 9", "Grade 10"])
        layout.addWidget(self.grade_combo)
        
        layout.addWidget(QLabel("Section Name:"))
        self.section_input = QLineEdit()
        self.section_input.setPlaceholderText("e.g. Rizal, Emerald, A")
        layout.addWidget(self.section_input)
        
        self.btn_save = QPushButton("Add Class")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def get_data(self) -> dict:
        return {
            "grade": self.grade_combo.currentText(),
            "section": self.section_input.text().strip()
        }

class AddScheduleDialog(QDialog):
    def __init__(self, engine, persons: list, available_classes: list = None, parent=None):
        super().__init__(parent)
        self.engine = engine # Store engine for conflict checking
        self.setWindowTitle("Add Busy Time (Multi-Day)")
        layout = QVBoxLayout(self)

        # 1. MULTI-DAY SELECTION
        layout.addWidget(QLabel("Select Days:"))
        days_layout = QHBoxLayout()
        self.day_boxes = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            cb = QCheckBox(day)
            self.day_boxes[day] = cb
            cb.toggled.connect(self.check_conflicts) # Real-time check
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)

        # 2. PERSON SELECTION
        layout.addWidget(QLabel("Select Person (Type to Search):"))
        self.person_selector = QComboBox()
        self.person_selector.setEditable(True)
        self.person_selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        for p in persons:
            self.person_selector.addItem(p['full_name'], p['person_id'])
            
        self.person_selector.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.person_selector.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.person_selector.currentIndexChanged.connect(self.check_conflicts)
        
        layout.addWidget(self.person_selector)

        layout.addWidget(QLabel("Select Grade Level:"))
        self.grade_selector = QComboBox()
        if available_classes:
            self.grade_selector.addItems(sorted(available_classes))
        else:
            self.grade_selector.addItems(["Grade 7", "Grade 8", "Grade 9", "Grade 10"])
        layout.addWidget(self.grade_selector)

        # NEW: Subject Input
        layout.addWidget(QLabel("Subject:"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("e.g. Math, Science (Optional)")
        layout.addWidget(self.subject_input)

        # 3. TIME SELECTION
        time_layout = QHBoxLayout()
        # ... (Keep your Start/End QTimeEdit code here) ...
        self.start_time = QTimeEdit(); self.start_time.setTime(QTime(9, 0))
        self.end_time = QTimeEdit(); self.end_time.setTime(QTime(10, 0))
        
        self.start_time.timeChanged.connect(self.check_conflicts)
        self.end_time.timeChanged.connect(self.check_conflicts)
        
        time_layout.addWidget(self.start_time); time_layout.addWidget(self.end_time)
        layout.addLayout(time_layout)
        
        # Conflict Feedback Label
        self.conflict_lbl = QLabel("")
        self.conflict_lbl.setStyleSheet("color: #E74C3C; font-size: 11px;")
        layout.addWidget(self.conflict_lbl)

        self.btn_save = QPushButton("Save to Schedule")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def check_conflicts(self):
        """Real-time validation against the database."""
        person_id = self.person_selector.currentData()
        if not person_id: return

        start = self.start_time.time().toString("HH:mm")
        end = self.end_time.time().toString("HH:mm")
        
        conflicts = []
        
        # Check each selected day
        for day, cb in self.day_boxes.items():
            if cb.isChecked():
                # Query Engine
                if not self.engine.can_assign(person_id, day, start, end):
                    conflicts.append(day)

        # Visual Feedback
        if conflicts:
            style = "border: 1px solid #E74C3C; background-color: #FDEDEC;"
            msg = f"⚠️ Conflict detected on: {', '.join(conflicts)}"
            self.conflict_lbl.setText(msg)
            self.btn_save.setEnabled(False) # Prevent saving
        else:
            style = ""
            self.conflict_lbl.setText("")
            self.btn_save.setEnabled(True)

        self.person_selector.setStyleSheet(style)
        self.start_time.setStyleSheet(style)
        self.end_time.setStyleSheet(style)

    def get_data(self) -> dict:
        selected_days = [day for day, cb in self.day_boxes.items() if cb.isChecked()]
        
        if self.person_selector.currentIndex() == -1:
            QMessageBox.warning(self, "Validation", "Please select a valid person from the list.")
            return None

        if not selected_days:
            QMessageBox.warning(self, "Validation", "Please select at least one day.")
            return None
        if self.end_time.time() <= self.start_time.time():
            QMessageBox.warning(self, "Validation", "End time must be after start time.")
            return None

        return {
            "days": selected_days, # This is now a LIST
            "person_id": self.person_selector.currentData(),
            "grade_level": self.grade_selector.currentText(),
            "subject": self.subject_input.text().strip(),
            "start": self.start_time.time().toString("HH:mm"),
            "end": self.end_time.time().toString("HH:mm")
        }

class PersonScheduleDialog(QDialog):
    """Displays a read-only weekly schedule for a specific person."""
    def __init__(self, engine, person_id, name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Schedule: {name}")
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        
        # Grid Setup
        self.grid = QTableWidget()
        self.grid.setColumnCount(5)
        self.grid.setHorizontalHeaderLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        # Time slots (Consistent with Main Window)
        self.time_slots = [f"{h:02d}:{m:02d}" for h in range(6, 19) for m in (0, 30)]
        self.grid.setRowCount(len(self.time_slots))
        self.grid.setVerticalHeaderLabels(self.time_slots)
        
        # Increase dimensions for better readability
        self.grid.verticalHeader().setDefaultSectionSize(30)
        self.grid.verticalHeader().setFixedWidth(65)
        
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.grid)
        
        # Load Data
        self.load_data(engine, person_id)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_data(self, engine, person_id):
        # Reuse the engine's map logic, filtered by this person
        s_map = engine.get_weekly_schedule_map(person_id=person_id)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        for row, t_val in enumerate(self.time_slots):
            for col, d_val in enumerate(days):
                infos = s_map.get((d_val, t_val), [])
                
                if infos:
                    # Show Grade Level and Role
                    text = "\n".join([f"{x['grade_level']} ({x['role']})" for x in infos])
                    item = QTableWidgetItem(text)
                    item.setBackground(QBrush(QColor("#C8E6C9")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    if len(infos) > 1:
                         item.setBackground(QBrush(QColor("#FF7043"))) # Conflict color
                         item.setText(text + "\n(Double Booked!)")
                    
                    self.grid.setItem(row, col, item)