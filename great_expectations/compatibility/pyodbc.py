from great_expectations.compatibility.not_imported import NotImported

PYODBC_NOT_IMPORTED = NotImported(
    "pyodbc dependencies are not installed, please 'pip install pyodbc'"
)

try:
    import pyodbc
except ImportError:
    pyodbc = PYODBC_NOT_IMPORTED
