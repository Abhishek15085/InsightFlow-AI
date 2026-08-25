"""
InsightFlow AI -- Dependency Verification Script (ASCII-safe)
Task 0.2: Verifies all required imports are available
Run: python verify_imports.py
"""

import sys

REQUIRED = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("streamlit", "Streamlit"),
    ("pandas", "Pandas"),
    ("numpy", "NumPy"),
    ("plotly", "Plotly"),
    ("sklearn", "Scikit-learn"),
    ("matplotlib", "Matplotlib"),
    ("xgboost", "XGBoost"),
    ("joblib", "Joblib"),
    ("multipart", "python-multipart"),
    ("pydantic", "Pydantic"),
    ("dotenv", "python-dotenv"),
    ("httpx", "HTTPX"),
]

print("=" * 55)
print("  InsightFlow AI -- Import Verification")
print("=" * 55)

passed = 0
failed = 0

for module, label in REQUIRED:
    try:
        pkg = __import__(module)
        version = getattr(pkg, "__version__", "unknown")
        print(f"  [OK]  {label:<20} v{version}")
        passed += 1
    except ImportError as e:
        print(f"  [FAIL]{label:<20} NOT FOUND -- {e}")
        failed += 1

print("=" * 55)
print(f"  Result: {passed} passed, {failed} failed")
print("=" * 55)

if failed > 0:
    print("\n  Run: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n  All dependencies verified! Phase 0 complete.")
    sys.exit(0)
