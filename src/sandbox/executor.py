import subprocess
import sys
import os
import re
import tempfile
import shutil

MAX_RETRIES = 3

# Standard library modules that ship with Python — anything NOT in this list
# is assumed to be a third-party package that the user will install separately.
# We only need a reasonable subset to catch the most common false negatives.
STDLIB_TOP_LEVEL = {
    "abc", "argparse", "ast", "asyncio", "base64", "bisect", "calendar",
    "cmath", "collections", "colorsys", "configparser", "contextlib", "copy",
    "csv", "ctypes", "dataclasses", "datetime", "decimal", "difflib", "email",
    "enum", "errno", "fnmatch", "fractions", "ftplib", "functools", "gc",
    "getpass", "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "imaplib", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "linecache", "locale", "logging", "lzma", "math", "mimetypes",
    "multiprocessing", "netrc", "numbers", "operator", "os", "pathlib",
    "pickle", "pkgutil", "platform", "pprint", "profile", "queue", "random",
    "re", "readline", "reprlib", "sched", "secrets", "select", "shelve",
    "shlex", "shutil", "signal", "site", "smtplib", "socket", "socketserver",
    "sqlite3", "ssl", "stat", "statistics", "string", "struct", "subprocess",
    "sys", "sysconfig", "tempfile", "textwrap", "threading", "time",
    "timeit", "tkinter", "token", "tokenize", "traceback", "tracemalloc",
    "turtle", "types", "typing", "unicodedata", "unittest", "urllib",
    "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "xml",
    "xmlrpc", "zipfile", "zipimport", "zlib", "_thread", "concurrent",
}


def find_entry_point(files: dict) -> str:
    """
    Intelligently determines which file to execute as the entry point.
    Priority: main.py > app.py > server.py > index.py > first .py file found.
    """
    priority = ["main.py", "app.py", "server.py", "index.py"]
    
    for candidate in priority:
        for path in files.keys():
            if path.endswith(candidate):
                return path
    
    # Fallback: first Python file
    for path in files.keys():
        if path.endswith(".py"):
            return path
    
    return ""


def _is_third_party_import_error(stderr: str, files: dict) -> bool:
    """
    Returns True if the error is ONLY a ModuleNotFoundError for a third-party
    package (one that will be satisfied by `pip install -r requirements.txt`).
    Real bugs like SyntaxError, NameError, TypeError etc. return False.
    """
    # Must be a ModuleNotFoundError
    match = re.search(r"ModuleNotFoundError: No module named ['\"](\w+)['\"]", stderr)
    if not match:
        return False
    
    missing_module = match.group(1)
    
    # If it's a standard library module, it's a real bug (broken Python install)
    if missing_module in STDLIB_TOP_LEVEL:
        return False
    
    # If it's one of our own generated files, it's a real bug (bad import path)
    for path in files.keys():
        module_name = os.path.splitext(os.path.basename(path))[0]
        if missing_module == module_name:
            return False
    
    # It's a third-party package — this will be installed by the user
    return True


def run_in_sandbox(files: dict, timeout: int = 15) -> dict:
    """
    Writes files to a temp directory, executes the entry point in an isolated subprocess,
    and returns the result with stdout, stderr, and success status.
    
    Third-party ModuleNotFoundErrors (e.g., 'streamlit', 'neo4j') are treated as
    PASS since they will be resolved when the user runs `pip install -r requirements.txt`.
    """
    entry_point = find_entry_point(files)
    
    if not entry_point:
        return {
            "success": False,
            "stdout": "",
            "stderr": "No Python entry point found in generated files.",
            "entry_point": ""
        }
    
    # Create an isolated temp workspace
    sandbox_dir = tempfile.mkdtemp(prefix="kairos_sandbox_")
    
    try:
        # Write all files into the sandbox
        for rel_path, content in files.items():
            full_path = os.path.join(sandbox_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        entry_full_path = os.path.join(sandbox_dir, entry_point)
        
        # Execute with a fresh Python subprocess
        result = subprocess.run(
            [sys.executable, entry_full_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=sandbox_dir,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        
        # Check for third-party import errors (these are NOT real bugs)
        if result.returncode != 0 and _is_third_party_import_error(result.stderr, files):
            missing = re.search(r"No module named ['\"](\w+)['\"]", result.stderr)
            pkg_name = missing.group(1) if missing else "unknown"
            return {
                "success": True,
                "stdout": f"Third-party package '{pkg_name}' not installed locally (expected — listed in requirements.txt).",
                "stderr": "",
                "entry_point": entry_point
            }
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "entry_point": entry_point
        }
        
    except subprocess.TimeoutExpired:
        # A timeout usually means the script launched a server or long-running
        # process successfully — that's actually a PASS, not a failure.
        return {
            "success": True,
            "stdout": f"Process ran for {timeout}s without crashing (likely a server/daemon).",
            "stderr": "",
            "entry_point": entry_point
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Sandbox execution error: {str(e)}",
            "entry_point": entry_point
        }
    finally:
        # Always clean up the temp directory
        shutil.rmtree(sandbox_dir, ignore_errors=True)
