import sys
import os

# Add 'src' to python path so we can import from core and ui
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from PyQt6.QtWidgets import QApplication
from core.database import init_db
from core.engine import DepEdValidator
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    # Load QSS from assets
    qss_file = os.path.join(os.path.dirname(__file__), "src", "assets", "style.qss")
    try:
        with open(qss_file, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: style.qss not found at {qss_file}")
    
    # Initialize DB and Engine
    db_path = init_db()
    engine = DepEdValidator(db_path)
    
    # Launch UI
    window = MainWindow(engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()