import sys
import os

# This line ensures Python can find the 'src' folder regardless of where you run it from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from database import init_db
from engine import DepEdValidator
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Consistent look across all PCs
    
    # Custom CSS for a cleaner look
    # main.py
    app.setStyleSheet("""
    QMainWindow {
        background-color: #FFFDF5; 
    }
    
    /* Card Container */
    #Card {
        background-color: #FFFFFF;
        border: 1px solid #E8EEDD;
        border-radius: 15px;
    }

    /* Modern Inputs */
    QLineEdit {
        padding: 10px;
        border: 2px solid #E8EEDD;
        border-radius: 8px;
        background-color: #FFFFFF;
    }
    QLineEdit:focus {
        border: 2px solid #2ECC71;
    }

    /* Standard Buttons */
    QPushButton {
        background-color: #FFFFFF;
        border: 1px solid #2ECC71;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        color: #2ECC71;
    }
    QPushButton:hover {
        background-color: #F1F8E9;
    }
    
    /* Primary Action (Solid Green) */
    QPushButton#PrimaryAction {
        background-color: #2ECC71;
        color: white;
        border: none;
    }
    QPushButton#PrimaryAction:hover {
        background-color: #27AE60;
    }
    
    /* Danger Action (Red stays for safety) */
    QPushButton#DangerAction {
        color: #E74C3C;
        border: 1px solid #E74C3C;
    }
    QPushButton#DangerAction:hover {
        background-color: #FDEDEC;
    }

    /* Table Headers */
    QHeaderView::section {
        background-color: #F1F8E9;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #2ECC71;
        font-weight: bold;
        color: #1B5E20;
    }

    /* Grid Styling */
    QTableWidget {
        background-color: white;
        gridline-color: #F1F8E9;
        border-radius: 10px;
        border: 1px solid #E8EEDD;
        font-size: 11px;
    }
    QTableWidget::item {
        padding-top: 2px;
        padding-bottom: 2px;
    }

    /* Sidebar Navigation */
    QListWidget, QTreeWidget {
        background-color: #FFFFFF;
        border: 1px solid #E8EEDD;
        border-radius: 10px;
        outline: none;
        padding: 5px;
        font-size: 14px;
    }
    QListWidget::item, QTreeWidget::item {
        padding: 12px;
        border-radius: 8px;
        color: #555;
        margin-bottom: 5px;
    }
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: #F1F8E9;
        color: #1B5E20;
        border: 1px solid #C8E6C9;
        font-weight: bold;
    }
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: #FAFAFA;
    }
""")
    
    # Initialize DB and Engine
    db_path = init_db()
    engine = DepEdValidator(db_path)
    
    # Launch UI
    window = MainWindow(engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()