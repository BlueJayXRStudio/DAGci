import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

#Recursively delete all __pycache__ directories and stray .pyc/.pyo files.
for dirpath, dirnames, filenames in os.walk(PARENT_DIR):
    # Delete any __pycache__ directory
    if "__pycache__" in dirnames:
        cache_dir = os.path.join(dirpath, "__pycache__")
        try:
            shutil.rmtree(cache_dir)
        except Exception:
            pass

    # Delete stray .pyc or .pyo files
    for file in filenames:
        if file.endswith((".pyc", ".pyo")):
            path = os.path.join(dirpath, file)
            try:
                os.remove(path)
            except Exception:
                pass


