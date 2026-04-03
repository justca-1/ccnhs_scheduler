from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QBrush

class NavigationPanel(QTreeWidget):
    """
    A side panel that displays a hierarchical view of Grade Levels and Class Sections.
    Replaces the standard QListWidget sidebar.
    """
    
    # Signal to switch the main stack page (passes stack index)
    page_change_requested = pyqtSignal(int)
    
    # Signal to load a specific class/person schedule (passes database ID)
    class_id_selected = pyqtSignal(int)
    
    # Signal to filter the main view by a specific section
    section_selected = pyqtSignal(str)

    def __init__(self, engine):
        """
        Initialize the navigation panel.
        :param engine: Instance of ScheduleEngine to query data.
        """
        super().__init__()
        self.engine = engine
        
        self._setup_ui()
        self.refresh_navigation()

    def _setup_ui(self):
        """Configures the visual properties of the tree."""
        self.setHeaderLabel("CCNHS Sections")
        self.setHeaderHidden(False)
        self.setIndentation(20)
        self.setRootIsDecorated(True)
        self.setAnimated(True)
        self.setFixedWidth(220)
        self.setExpandsOnDoubleClick(False) # Expand on single click, not double
        self.setFrameShape(QTreeWidget.Shape.NoFrame) # Removes the visual gap border
        
        # Connect the click signal to our handler
        self.itemClicked.connect(self._on_item_clicked)

    def refresh_navigation(self):
        """
        Queries the database and repopulates the tree.
        Call this method whenever a new class or person is added.
        """
        # Save the current expanded state of top-level items so they don't collapse on refresh
        expanded_items = set()
        for i in range(self.topLevelItemCount()):
            top_item = self.topLevelItem(i)
            if top_item.isExpanded():
                expanded_items.add(top_item.text(0))

        self.clear()
        
        # --- 2. Grade Level Parent Nodes ---
        # Map Grade Name -> Stack Index (Matches MainWindow order)
        self.grade_map = {
            "Grade 7": 1,
            "Grade 8": 2,
            "Grade 9": 3,
            "Grade 10": 4
        }
        
        # Define default Grades and Sections
        grades = {
            "Grade 7": ["Rizal", "Mabini", "Bonifacio"],
            "Grade 8": ["Luna", "Jacinto", "Silang"],
            "Grade 9": ["Aquino", "Del Pilar"],
            "Grade 10": ["Dagohoy", "Lapu-Lapu"]
        }
        
        # Merge dynamically added classes from the database
        try:
            db_classes = self.engine.get_unique_grade_levels()
            for db_c in db_classes:
                if " - " in db_c:
                    g, s = db_c.split(" - ", 1)
                    if g in grades and s not in grades[g]:
                        grades[g].append(s)
                    elif g not in grades:
                        grades[g] = [s]
        except Exception:
            pass # Failsafe
        
        self.grade_items = {}
        for grade, sections in grades.items():
            parent = QTreeWidgetItem(self, [grade])
            # Store Stack Index for Page Switching
            parent.setData(0, Qt.ItemDataRole.UserRole, self.grade_map.get(grade, 1))
            
            self.grade_items[grade] = parent
            
            for section in sections:
                child = QTreeWidgetItem(parent, [section])
                child.setData(0, Qt.ItemDataRole.UserRole, f"SECTION:{grade} - {section}")

            # Restore expanded state for the grade
            if parent.text(0) in expanded_items:
                parent.setExpanded(True)

        # --- 1. Staff Management (Fixed Node) ---
        staff_node = QTreeWidgetItem(self, ["👥 Staff Management"])
        staff_node.setData(0, Qt.ItemDataRole.UserRole, 0) 
        
        if staff_node.text(0) in expanded_items:
            staff_node.setExpanded(True)

        # --- 3. Conflict Report (Dedicated View) ---
        conflict_node = QTreeWidgetItem(self)
        conflict_node.setText(0, "⚠️ Conflict Report")
        conflict_node.setData(0, Qt.ItemDataRole.UserRole, 5) # Stack Index 5
        # Make it stand out with a soft red color
        conflict_node.setForeground(0, QBrush(QColor("#E74C3C")))

        # --- 4. Populate Children (Class Sections / Persons) ---
        try:
            persons = self.engine.get_all_persons()
        except Exception as e:
            print(f"Error fetching navigation data: {e}")
            return

        for person in persons:
            person_id = person['person_id']
            name = person['full_name']
            
            child = QTreeWidgetItem(staff_node, [name])
            child.setData(0, Qt.ItemDataRole.UserRole, f"PERSON:{person_id}")

    def _on_item_clicked(self, item, column):
        """Handles item clicks. Distinguishes between Page Navigation and Schedule Loading."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if data is None:
            return

        if isinstance(data, str) and data.startswith("SECTION:"):
            section_name = data.replace("SECTION:", "")
            self.section_selected.emit(section_name)
        elif isinstance(data, str) and data.startswith("PERSON:"):
            person_id = int(data.replace("PERSON:", ""))
            self.class_id_selected.emit(person_id)
        elif isinstance(data, int):
            # Manipulate the item BEFORE emitting the signal that triggers the refresh
            if item.childCount() > 0:
                item.setExpanded(not item.isExpanded())
                
            self.page_change_requested.emit(data)
