from pathlib import Path
import sys

root = Path(__file__).resolve().parent

sys.path.insert(0, str(root / "shared"))
sys.path.insert(0, str(root / "lambda" / "inbound"))
sys.path.insert(0, str(root / "lambda" / "summary_agent"))
sys.path.insert(0, str(root / "lambda" / "scheduler_agent"))
sys.path.insert(0, str(root / "lambda" / "daily_setup"))
print("CONFTEST LOADED")
print(sys.path)
