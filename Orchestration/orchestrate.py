import sys, os, _bootstrap
import subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Make MacOS server build
result = subprocess.run(
    ["python", os.path.join(PARENT_DIR, "MacOS/build.py")],
    # capture_output=True,
    # check=True,
    text=True,
)

# Deploy to Meta Horizon Store alpha channel
result = subprocess.run(
    ["python", os.path.join(PARENT_DIR, "Android/oculus_deploy.py")],
    # capture_output=True,
    # check=True,
    text=True,
)

# print(result.stdout)