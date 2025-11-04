import subprocess
import sys, os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PARENT_DIR, "envs/paths.env"))
adb_path = os.getenv("ADB_PATH")

result = subprocess.run(
    ["python", os.path.join(BASE_DIR, "build.py")],
    # capture_output=True,
    # check=True,
    text=True
)

if result.returncode == 1:
    print("Build failed. Aborting deployment.")
    sys.exit(1)

print("Build successful. Continuing deployment.")

result = subprocess.run(
    [adb_path, "install", "-r", os.path.join(BASE_DIR, "builds/app.apk")],
    # capture_output=True,
    # check=True,
    text=True
)

if result.returncode == 1:
    print("Deployment failed. Exiting.")
    sys.exit(1)

print("ADB deployment successful.")
sys.exit(0)
