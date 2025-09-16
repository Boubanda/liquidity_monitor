#!/usr/bin/env python3
"""
Lance le dashboard Streamlit
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Lance le dashboard Streamlit"""
    dashboard_path = Path(__file__).parent / "src" / "dashboard" / "streamlit_app.py"
    
    print("🚀 Lancement du dashboard...")
    print(f"📊 URL: http://localhost:8501")
    print("📝 Ctrl+C pour arrêter")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n⚠️ Dashboard arrêté")

if __name__ == "__main__":
    main()