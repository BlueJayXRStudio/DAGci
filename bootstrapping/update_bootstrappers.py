import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
src = os.path.join(BASE_DIR, "_bootstrap.py")

#Recursively replace **/_bootstrap.py with ./_bootstrap.py 
for dirpath, dirnames, filenames in os.walk(PARENT_DIR):
    for file in filenames:
        if file == "_bootstrap.py":
            path = os.path.join(dirpath, file)
            if src == path:
                continue
            try:
                with open(src, "rb") as fsrc, open(path, "wb") as fdest:
                    shutil.copyfileobj(fsrc, fdest)
            except Exception:
                pass
print("Successfully updated bootstrap scripts")