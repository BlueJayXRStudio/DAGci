import subprocess
import sys, os, _bootstrap
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

result = subprocess.run(
    ["python", os.path.join(BASE_DIR, "test.py")],
    # capture_output=True,
    # check=True,
    text=True
)

if result.returncode == 0:
    result = subprocess.run(
        ["/usr/bin/env", "bash", os.path.join(BASE_DIR, "build_script")],
        # capture_output=True,
        # check=True,
        text=True
    )
    if result.returncode == 0:
        print("build successful")
        sys.exit(0)
sys.exit(1)
