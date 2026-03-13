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
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setRootIsDecorated(True)
        self.setAnimated(True)
        self.setFixedWidth(220)
        self.setExpandsOnDoubleClick(False) # Expand on single click, not double
        
        # Connect the click signal to our handler
        self.itemClicked.connect(self._on_item_clicked)

    def refresh_navigation(self):
        """
        Queries the database and repopulates the tree.
        Call this method whenever a new class or person is added.
        """
        self.clear()
        
        # --- 1. Staff Management (Fixed Top Node) ---
        staff_node = QTreeWidgetItem(self)
        staff_node.setText(0, "👥 Staff Management")
        # Store Page Index 0 for Staff Management
        staff_node.setData(0, Qt.ItemDataRole.UserRole, 0) 
        
        # --- 2. Grade Level Parent Nodes ---
        # Map Grade Name -> Stack Index (Matches MainWindow order)
        self.grade_map = {
            "Grade 7": 1,
            "Grade 8": 2,
            "Grade 9": 3,
            "Grade 10": 4
        }
        
        self.grade_items = {}
        for grade, stack_idx in self.grade_map.items():
            item = QTreeWidgetItem(self)
            item.setText(0, grade)
            # Store Stack Index for Page Switching
            item.setData(0, Qt.ItemDataRole.UserRole, stack_idx)
            
            self.grade_items[grade] = item

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
            role = str(person['role']) if person['role'] else ""

            # Determine which Grade Level this class/person belongs to.
            target_node = None
            for grade in self.grade_map.keys():
                if grade in role:
                    target_node = self.grade_items[grade]
                    break
            
            if target_node:
                child = QTreeWidgetItem(target_node)
                child.setText(0, name)
                
                # Store the UNIQUE DATABASE ID for retrieval
                child.setData(0, Qt.ItemDataRole.UserRole, person_id)

    def _on_item_clicked(self, item, column):
        """Handles item clicks. Distinguishes between Page Navigation and Schedule Loading."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if data is None:
            return

        # Logic: If item has no parent, it's a Category (Page Switch).
        # If it has a parent, it's a Class/Person (Load Schedule).
        if item.parent() is None:
            # It's a Page Index (0-6)
            self.page_change_requested.emit(data)
            
            # Toggle visibility of children (Accordion style)
            if item.childCount() > 0:
                item.setExpanded(not item.isExpanded())
        else:
            # It's a Person ID (Database Integer)
            self.class_id_selected.emit(data)
