import sys
import os
import logging
from pathlib import Path

# This line ensures Python can find the 'src' folder regardless of where you run it from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from database import init_db
from engine import DepEdValidator
from ui.main_window import MainWindow

def main():
    # Set up logging to write to a file in the user's Documents folder
    log_dir = Path.home() / "Documents" / "CCNHS_Scheduler"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / "scheduler.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Consistent look across all PCs
    
    # Load QSS
    qss_file = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
    try:
        with open(qss_file, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: style.qss not found.")
    
    # Initialize DB and Engine
    db_path = init_db()
    engine = DepEdValidator(db_path)
    
    # Launch UI
    window = MainWindow(engine)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()