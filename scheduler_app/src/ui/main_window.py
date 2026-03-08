from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QSplitter, QLineEdit, QTabWidget, QListWidget, QStackedWidget, QAbstractItemView,
    QGraphicsBlurEffect, QInputDialog, QMenu, QComboBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtGui import QColor, QBrush, QFont, QAction
from PyQt6.QtCore import Qt, pyqtSignal
try:
    from .dialogs import AddPersonDialog, AddScheduleDialog, PersonScheduleDialog, AddClassDialog
    from .navigation import NavigationPanel
except ImportError:
    from dialogs import AddPersonDialog, AddScheduleDialog, PersonScheduleDialog, AddClassDialog
    from navigation import NavigationPanel

class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("Offline Scheduling System - Dashboard")
        self.resize(1200, 850)
        self.undo_stack = [] # Stores lists of backup data
        # Default classes, can be expanded via "Add Class"
        self.known_classes = set(["Grade 7", "Grade 8", "Grade 9", "Grade 10"])

        # Central Container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Sidebar (Navigation)
        self.sidebar = NavigationPanel(self.engine)
        self.sidebar.page_change_requested.connect(self.change_page)
        self.sidebar.class_id_selected.connect(self.load_schedule)
        self.main_layout.addWidget(self.sidebar)

        # Main Content Area
        self.main_stack = QStackedWidget()
        self.main_layout.addWidget(self.main_stack)

        # Initialize Sections
        self.init_person_management_ui()
        self.init_schedule_grid_ui()

        # Add the Status Bar at the very bottom
        self.statusBar().showMessage(f"Database Loaded: {self.engine.db_path}")

        # Initial Data Load
        self.refresh_all()
        
        # Select first item by default
        self.change_page(0)

    def change_page(self, index):
        self.main_stack.setCurrentIndex(index)

    def show_message(self, text, duration=3000):
        """Helper to show temporary messages (like 'Saved!') on the status bar."""
        self.statusBar().showMessage(text, duration)

    def init_person_management_ui(self):
        self.staff_tab = QWidget()
        self.staff_tab.setObjectName("Card")
        # Setting layout margins creates the 'float' effect over the cream background
        layout = QVBoxLayout(self.staff_tab)
        layout.setContentsMargins(25, 25, 25, 25) 
        layout.setSpacing(15)

        # --- STATUS CARDS (Calculated Widgets) ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        def create_stat_card(title, color="#2ECC71"):
            card = QWidget()
            card.setObjectName("Card")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(15, 15, 15, 15)
            
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #555; font-size: 12px; font-weight: bold;")
            
            v_lbl = QLabel("0")
            v_lbl.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            v_lbl.setStyleSheet(f"color: {color};")
            
            c_layout.addWidget(t_lbl)
            c_layout.addWidget(v_lbl)
            stats_layout.addWidget(card)
            return v_lbl

        self.stat_staff = create_stat_card("TOTAL STAFF")
        self.stat_conflicts = create_stat_card("GLOBAL CONFLICTS", "#E74C3C")
        self.stat_schedules = create_stat_card("ACTIVE SCHEDULES")

        layout.addLayout(stats_layout)

        section_label = QLabel("Registered Persons & Management")
        section_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(section_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search by name or role...")
        self.search_bar.setFixedWidth(500)
        self.search_bar.textChanged.connect(self.filter_people_table)
        layout.addWidget(self.search_bar)

        # Action Buttons (Horizontal)
        action_layout = QHBoxLayout()
        self.add_person_btn = QPushButton("Add New Person")
        self.add_person_btn.clicked.connect(self.open_add_person_dialog)
        
        self.add_class_btn = QPushButton("Add Class")
        self.add_class_btn.clicked.connect(self.open_add_class_dialog)
        
        self.add_schedule_btn = QPushButton("Assign Busy Time")
        self.add_schedule_btn.clicked.connect(self.open_add_schedule_dialog)
        
        action_layout.addWidget(self.add_person_btn)
        action_layout.addWidget(self.add_class_btn)
        action_layout.addWidget(self.add_schedule_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        header_layout = QHBoxLayout()
        
        self.people_table = QTableWidget()
        self.people_table.setColumnCount(2)
        self.people_table.setHorizontalHeaderLabels(["ID", "Full Name"])
        self.people_table.setFixedHeight(180) 
        
        # Enable multi-row selection
        self.people_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.people_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # Hide the vertical header (row numbers) as it is redundant and often tight
        self.people_table.verticalHeader().setVisible(False)
        
        header = self.people_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.people_table.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.people_table.cellDoubleClicked.connect(self.on_person_double_clicked)
        
        # Context Menu
        self.people_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.people_table.customContextMenuRequested.connect(self.show_context_menu)
        
        header_layout.addWidget(self.people_table)

        # Button Sidebar
        btn_vbox = QVBoxLayout()
        
        # The Missing Link: The Delete Button
        self.delete_person_btn = QPushButton("Delete Selected")
        self.delete_person_btn.setStyleSheet("background-color: #FFEBEE; color: #B71C1C;")
        self.delete_person_btn.clicked.connect(self.delete_selected_person)
        
        btn_vbox.addWidget(self.delete_person_btn)
        
        self.undo_btn = QPushButton("Undo Delete")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_last_delete)
        btn_vbox.addWidget(self.undo_btn)
        
        btn_vbox.addStretch()
        
        header_layout.addLayout(btn_vbox)
        layout.addLayout(header_layout)

        # In init_person_management_ui, add the Print button:
        self.print_btn = QPushButton("Print to CSV (Excel)")
        self.print_btn.clicked.connect(self.export_to_csv)
        btn_vbox.addWidget(self.print_btn)

        self.clear_sched_btn = QPushButton("Clear All Schedules")
        self.clear_sched_btn.setStyleSheet("color: orange;")
        self.clear_sched_btn.clicked.connect(self.clear_schedules)
        btn_vbox.addWidget(self.clear_sched_btn)

        # Add to Stack and Sidebar
        self.main_stack.addWidget(self.staff_tab)

    def clear_schedules(self):
        confirm = QMessageBox.warning(
            self, "Clear All Schedules", 
            "Are you sure you want to delete ALL schedule entries?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            # We need a simple method in the engine for this
            if self.engine.clear_only_schedules():
                self.refresh_all()
                self.show_message("All schedules cleared.")

    def export_to_csv(self):
        """Exports the current grid exactly as seen to a CSV file."""
        import csv
        from PyQt6.QtWidgets import QFileDialog

        # Get the currently visible grid from the tabs
        current_grid = self.main_stack.currentWidget()
        
        # Handle the Grade View container case (if it's a widget with a grid inside)
        if isinstance(current_grid, QWidget) and not isinstance(current_grid, QTableWidget):
            current_grid = current_grid.findChild(QTableWidget)

        if not current_grid or not isinstance(current_grid, QTableWidget):
            self.show_message("No schedule grid available to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Schedule", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Write Headers
                    headers = ["Time"] + ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    writer.writerow(headers)

                    # Write Rows
                    for r in range(current_grid.rowCount()):
                        row_data = [current_grid.verticalHeaderItem(r).text()]
                        for c in range(current_grid.columnCount()):
                            item = current_grid.item(r, c)
                            row_data.append(item.text().replace("\n", " | ") if item else "")
                        writer.writerow(row_data)
                self.show_message("Export successful!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not save file: {e}")

    def init_schedule_grid_ui(self):
        """Bottom section for the Weekly Matrix."""
        self.grade_views = {} # Stores { 'Grade 7': {'combo': ..., 'grid': ...}, ... }
        
        self.time_slots = [f"{h:02d}:{m:02d}" for h in range(6, 19) for m in (0, 30)]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        # 1. All Grades (Grade 7-12) with Dropdowns
        for i in range(7, 13):
            grade_name = f"Grade {i}"
            
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(10, 10, 10, 10)
            
            top_bar = QHBoxLayout()
            top_bar.addWidget(QLabel(f"Select {grade_name} Class:"))
            combo = QComboBox()
            combo.setFixedWidth(200)
            # Connect signal using lambda to capture the specific grade name
            combo.currentTextChanged.connect(lambda text, g=grade_name: self.refresh_grade_grid(g))
            
            top_bar.addWidget(combo)
            
            # NEW: Search Bar for filtering teachers
            top_bar.addSpacing(20)
            top_bar.addWidget(QLabel("Filter Teacher:"))
            search_input = QLineEdit()
            search_input.setPlaceholderText("Type name...")
            search_input.setFixedWidth(150)
            search_input.textChanged.connect(lambda text, g=grade_name: self.refresh_grade_grid(g))
            top_bar.addWidget(search_input)
            
            top_bar.addStretch()
            layout.addLayout(top_bar)
            
            grid = QTableWidget()
            self._setup_grid(grid, days, self.time_slots)
            layout.addWidget(grid)
            
            self.main_stack.addWidget(container)
            
            self.grade_views[grade_name] = {'combo': combo, 'grid': grid, 'search': search_input}

    def _setup_grid(self, grid, days, time_slots):
        """Helper to configure a schedule table widget."""
        grid.setColumnCount(len(days))
        grid.setHorizontalHeaderLabels(days)
        grid.setRowCount(len(time_slots))
        grid.setVerticalHeaderLabels(time_slots)
        grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        grid.verticalHeader().setDefaultSectionSize(35) # Compact rows
        grid.verticalHeader().setFixedWidth(60) # Compact time column
        grid.setShowGrid(False) # Hide default grid lines for card-like look

    # --- ACTION METHODS ---

    def delete_selected_person(self):
        """Removes the highlighted person(s) from the system."""
        selected_rows = sorted(set(index.row() for index in self.people_table.selectedIndexes()))
        
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select at least one person in the table.")
            return

        persons_to_delete = []
        for row in selected_rows:
            id_item = self.people_table.item(row, 0)
            name_item = self.people_table.item(row, 1)
            if id_item and name_item:
                p_id = int(id_item.text())
                p_name = name_item.text().replace("⚠️ ", "")
                persons_to_delete.append((p_id, p_name))

        msg = f"Delete {persons_to_delete[0][1]} and all their schedules?" if len(persons_to_delete) == 1 else f"Delete {len(persons_to_delete)} selected people and all their schedules?"

        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        # 1. Prepare Backup
        batch_backup = []
        for p_id, _ in persons_to_delete:
            data = self.engine.get_person_backup(p_id)
            if data:
                batch_backup.append(data)

        if confirm == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for p_id, _ in persons_to_delete:
                if self.engine.delete_person(p_id):
                    deleted_count += 1
            
            if deleted_count > 0:
                # 2. Push to Undo Stack
                if batch_backup:
                    self.undo_stack.append(batch_backup)
                    self.update_undo_button()
                
                self.refresh_all()
                self.show_message(f"Deleted {deleted_count} people.")

    def show_context_menu(self, pos):
        """Displays a right-click menu for staff actions."""
        index = self.people_table.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)
        
        # Rename Action
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.handle_rename_context(index.row()))
        menu.addAction(rename_action)
        
        # View Schedule Action
        view_action = QAction("View Schedule", self)
        view_action.triggered.connect(lambda: self.on_person_double_clicked(index.row(), 0))
        menu.addAction(view_action)

        menu.exec(self.people_table.viewport().mapToGlobal(pos))

    def handle_rename_context(self, row):
        """Helper to trigger rename from context menu."""
        id_item = self.people_table.item(row, 0)
        name_item = self.people_table.item(row, 1)
        if id_item and name_item:
            p_id = int(id_item.text())
            name = name_item.text().replace("⚠️ ", "")
            self.open_rename_dialog(p_id, name)

    def open_rename_dialog(self, person_id, current_name):
        """Opens a blurred popup to rename the person."""
        # Apply Blur
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.central_widget.setGraphicsEffect(blur)
        
        # Get New Name
        new_name, ok = QInputDialog.getText(
            self, "Rename Staff", 
            f"Rename '{current_name}' to:", 
            text=current_name
        )
        
        # Remove Blur
        self.central_widget.setGraphicsEffect(None)
        
        if ok and new_name:
            new_name = new_name.strip()
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "Name cannot be empty.")
                return
                
            if self.engine.update_person_name(person_id, new_name):
                self.show_message(f"Renamed to {new_name}")
                self.refresh_all()
            else:
                QMessageBox.warning(self, "Update Failed", "Could not update name in database.")

    def _exec_with_blur(self, dialog):
        """Helper to execute a dialog with a background blur effect."""
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.central_widget.setGraphicsEffect(blur)
        res = dialog.exec()
        self.central_widget.setGraphicsEffect(None)
        return res

    def undo_last_delete(self):
        """Restores the last batch of deleted people."""
        if not self.undo_stack: return
        
        batch_backup = self.undo_stack.pop()
        restored_count = 0
        
        for data in batch_backup:
            if self.engine.restore_person_data(data):
                restored_count += 1
        
        self.refresh_all()
        self.update_undo_button()
        self.show_message(f"Restored {restored_count} people.")

    def update_undo_button(self):
        count = len(self.undo_stack)
        self.undo_btn.setEnabled(count > 0)
        self.undo_btn.setText(f"Undo Delete ({count})" if count > 0 else "Undo Delete")

    def load_schedule(self, person_id):
        """Loads the schedule dialog for a specific person ID."""
        # 1. Find Person Name
        persons = self.engine.get_all_persons()
        person = next((p for p in persons if p['person_id'] == person_id), None)
        
        if not person:
            return
            
        name = person['full_name']
        
        # 2. Check Overload & Popup
        stats = self.engine.validate_workload(person_id)
        if stats['overloaded']:
            msg = f"{name} is overloaded!\n"
            msg += f"Total Teaching: {int(stats['total'])} minutes\n\n"
            msg += "Breakdown of Overloaded Days:\n"
            for day in stats['overloaded']:
                day_total = int(stats['daily'][day])
                msg += f"--- {day} ({day_total} mins) ---\n"
            QMessageBox.warning(self, "Workload Alert", msg)
            
        # 3. Open Dialog
        dlg = PersonScheduleDialog(self.engine, person_id, name, self)
        self._exec_with_blur(dlg)

    def on_person_double_clicked(self, row, col):
        """Handles clicking a user: Checks overload and shows schedule."""
        id_item = self.people_table.item(row, 0)
        
        if not id_item:
            return
            
        p_id = int(id_item.text())
        self.load_schedule(p_id)

    def refresh_all(self):
        """
        Synchronizes the UI with the latest database state.
        Updates the person list and the weekly matrix.
        """
        # Block signals to prevent itemChanged from firing during population
        self.people_table.blockSignals(True)
        
        # --- 0. REFRESH NAVIGATION TREE ---
        self.sidebar.refresh_navigation()
        
        # --- 1. REFRESH PERSON TABLE ---
        persons = self.engine.get_all_persons()
        self.people_table.setRowCount(len(persons))
        
        for i, p in enumerate(persons):
            # Column 0: ID
            id_item = QTableWidgetItem(str(p['person_id']))
            id_item.setFlags(id_item.flags() ^ Qt.ItemFlag.ItemIsEditable) # Non-editable
            self.people_table.setItem(i, 0, id_item)
            
            # Column 1: Full Name
            # --- NEW FEATURE: WORKLOAD VALIDATION ---
            stats = self.engine.validate_workload(p['person_id'])
            display_name = p['full_name']
            
            # Visual Cue for Overload
            if stats['overloaded']:
                display_name = f"⚠️ {p['full_name']}"
            
            name_item = QTableWidgetItem(display_name)
            
            # Tooltip details
            tip = f"Total Teaching: {int(stats['total'])} mins"
            if stats['overloaded']:
                tip += f"\n⚠️ OVERLOADED on: {', '.join(stats['overloaded'])}"
                name_item.setForeground(QBrush(QColor("#C0392B"))) # Red text
                name_item.setFont(QFont("Arial", weight=QFont.Weight.Bold))
            
            name_item.setToolTip(tip)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.people_table.setItem(i, 1, name_item)
            
        self.people_table.blockSignals(False)

        # --- 2. REFRESH SCHEDULE GRID ---
        # Fix: Populate known_classes from DB to ensure persistence
        db_classes = self.engine.get_unique_grade_levels()
        self.known_classes.update(db_classes)

        # Get the detailed map: {(Day, Time): [info_dict1, info_dict2]}
        s_map = self.engine.get_weekly_schedule_map()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        # 1. Update Known Classes & Distribute to Grades
        # We categorize classes into buckets: "Grade 7", "Grade 8", etc.
        grade_buckets = { f"Grade {i}": set() for i in range(7, 13) }
        
        all_classes = set(self.known_classes)
        for infos in s_map.values():
            for info in infos:
                if info.get('grade_level'):
                    all_classes.add(info['grade_level'])
                    self.known_classes.add(info['grade_level'])

        for c_name in all_classes:
            # Simple heuristic to assign class to a grade bucket
            for i in range(7, 13):
                # Matches "Grade 7", "7-A", "7-Rizal", etc.
                if c_name.startswith(str(i)) or c_name.startswith(f"Grade {i}"):
                    if f"Grade {i}" in grade_buckets:
                        grade_buckets[f"Grade {i}"].add(c_name)
                    break
        
        conflict_count = 0 # Counter for our Status Bar UX

        # 2. Update Dropdowns for 7-12
        for grade, data in self.grade_views.items():
            combo = data['combo']
            current = combo.currentText()
            
            items = sorted(list(grade_buckets.get(grade, [])))
            
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(items)
            
            if current in items:
                combo.setCurrentText(current)
            elif items:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)
            
            # Refresh this specific grid and accumulate conflicts
            conflict_count += self.refresh_grade_grid(grade)

        # Update the Status Bar with the conflict tally
        status_msg = f"Database: {self.engine.db_path} | ⚠️ Conflicts: {conflict_count}"
        self.statusBar().showMessage(status_msg)

        # Update Status Cards
        self.stat_staff.setText(str(len(persons)))
        self.stat_conflicts.setText(str(conflict_count))
        self.stat_schedules.setText(str(self.engine.get_total_schedule_count()))

    def get_subject_color(self, subject):
        """Generates a consistent pastel color for a subject string."""
        if not subject:
            return QColor("#FFFDF5") # Default cream
        
        # Deterministic hash so "Math" is always the same color
        val = sum(map(ord, subject))
        # Hue: 0-359, Saturation: 100 (Pastel), Lightness: 230 (Light/Bright)
        hue = (val * 137) % 360 
        return QColor.fromHsl(hue, 100, 230)

    def refresh_grade_grid(self, grade_key):
        """Populates the grid for a specific grade view based on its dropdown."""
        view_data = self.grade_views.get(grade_key)
        if not view_data: return 0
        
        selected_class = view_data['combo'].currentText()
        grid = view_data['grid']
        
        # Get filter text
        search_widget = view_data.get('search')
        filter_text = search_widget.text().lower().strip() if search_widget else ""
        
        # Clear content AND spans (merges)
        grid.clearContents()
        grid.clearSpans()
        
        if not selected_class:
            return 0

        s_map = self.engine.get_weekly_schedule_map()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        local_conflicts = 0

        # Process Column by Column (Day by Day) to allow vertical merging
        for col, d_val in enumerate(days):
            row = 0
            while row < len(self.time_slots):
                t_val = self.time_slots[row]
                
                all_infos = s_map.get((d_val, t_val), [])
                # Filter for the selected class
                busy_infos = [info for info in all_infos if info.get('grade_level') == selected_class]
                
                # Apply Teacher Filter
                if filter_text:
                    busy_infos = [info for info in busy_infos if filter_text in info['name'].lower()]
                
                if not busy_infos:
                    row += 1
                    continue

                # --- 1. Determine Content ---
                info = busy_infos[0]
                subject = info.get('subject', '')
                name = info['name']
                is_conflict = len(busy_infos) > 1
                
                if is_conflict:
                    display_text = "⚠️ CONFLICT\n" + "\n".join([i['name'] for i in busy_infos])
                else:
                    display_text = subject if subject else name
                    if subject and name:
                        display_text += f"\n({name})"

                item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                
                # --- 2. Styling & Color Coding ---
                if is_conflict:
                    item.setBackground(QBrush(QColor("#FF7043")))
                    item.setForeground(QBrush(QColor("white")))
                    item.setToolTip("⚠️ Multiple people scheduled")
                    local_conflicts += 1
                else:
                    # Dynamic Color based on Subject
                    bg_color = self.get_subject_color(subject)
                    item.setBackground(QBrush(bg_color))
                    item.setForeground(QBrush(QColor("#2c3e50"))) # Dark text
                    item.setFont(QFont("Arial", weight=QFont.Weight.Bold))
                    item.setToolTip(f"Subject: {subject}\nTeacher: {name}\nTime: {t_val}")
                
                grid.setItem(row, col, item)

                # --- 3. Calculate Merge Span ---
                # Look ahead to see if the next slots are the exact same class
                span_height = 1
                if not is_conflict:
                    for next_r in range(row + 1, len(self.time_slots)):
                        next_t = self.time_slots[next_r]
                        next_infos = s_map.get((d_val, next_t), [])
                        next_busy = [i for i in next_infos if i.get('grade_level') == selected_class]
                        
                        # Stop if empty, conflict, or different subject/teacher
                        if len(next_busy) == 1 and \
                           next_busy[0]['name'] == name and \
                           next_busy[0].get('subject', '') == subject:
                            span_height += 1
                        else:
                            break
                
                if span_height > 1:
                    grid.setSpan(row, col, span_height, 1)
                
                # Skip the rows we just handled
                row += span_height
        
        return local_conflicts

    def open_add_person_dialog(self):
        d = AddPersonDialog(self)
        if self._exec_with_blur(d):
            data = d.get_data()
            if self.engine.add_person(data['name'], data['role']):
                self.refresh_all()
            else:
                QMessageBox.warning(self, "Error", f"Could not add '{data['name']}'.\nThis name already exists.")

    def open_add_class_dialog(self):
        """Adds a new class to the dropdown list."""
        d = AddClassDialog(self)
        if self._exec_with_blur(d):
            data = d.get_data()
            grade = data['grade']
            section = data['section']
            
            if not section:
                QMessageBox.warning(self, "Input Error", "Section name cannot be empty.")
                return

            # Construct the full class name (e.g., "Grade 7 - Rizal")
            full_class_name = f"{grade} - {section}"
            
            if full_class_name not in self.known_classes:
                self.known_classes.add(full_class_name)
                self.refresh_all()
                self.show_message(f"Class '{full_class_name}' added.")
            else:
                self.show_message(f"Class '{full_class_name}' already exists.")

    def open_add_schedule_dialog(self):
        p_list = self.engine.get_all_persons()
        if not p_list: 
            QMessageBox.warning(self, "Error", "Add a person first!")
            return
            
        # Pass available classes + senior grades to the dialog
        all_options = list(self.known_classes) + ["Grade 11", "Grade 12"]
        d = AddScheduleDialog(p_list, available_classes=all_options, parent=self)
        
        if self._exec_with_blur(d):
            res = d.get_data()
            if res is None: 
                return

            # --- THE FIX IS HERE ---
            # 'res' now contains a LIST of days called 'days'
            success_count = 0
            for day_name in res['days']:
                # Pass 'day_name' from the loop into the engine
                if self.engine.add_schedule(res['person_id'], day_name, res['start'], res['end'], res['grade_level'], res['subject']):
                    success_count += 1
            
            if success_count > 0:
                self.show_message(f"Successfully added {success_count} days.")
                self.refresh_all()

    def filter_people_table(self, text):
        """Hides rows in the people table that don't match the search text."""
        for i in range(self.people_table.rowCount()):
            name_item = self.people_table.item(i, 1) # Column 1 is 'Full Name'
            if name_item:
                # Show the row if the text matches (case-insensitive)
                is_visible = text.lower() in name_item.text().lower()
                self.people_table.setRowHidden(i, not is_visible)
                