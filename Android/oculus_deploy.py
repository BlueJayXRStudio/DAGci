import sys, os, _bootstrap
import subprocess
from dotenv import load_dotenv
# from Validation.VersionValidation.version_validation import simple_semver_validator, simple_increment_version
# from Tools.ref_container import RefContainer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PARENT_DIR, "envs/paths.env"))
load_dotenv(os.path.join(PARENT_DIR, "envs/secrets.env"))
OCULUS_APP_ID = os.getenv("OCULUS_APP_ID")
OCULUS_APP_SECRET = os.getenv("OCULUS_APP_SECRET")
OCULUS_PLATFORM_TOOL_PATH = os.getenv("OCULUS_PLATFORM_TOOL_PATH")

result = subprocess.run(
    ["python", os.path.join(BASE_DIR, "build.py")],
    # capture_output=True,
    # check=True,
    text=True
)

if result.returncode == 1:
    print(f"[{sys.argv[0]}]: Build failed. Aborting deployment.")
    sys.exit(1)

print(f"[{sys.argv[0]}]:Build successful. Continuing deployment.")

result = subprocess.run(
    [
        OCULUS_PLATFORM_TOOL_PATH,
        "upload-quest-build",
        "--app-id", OCULUS_APP_ID,
        "--app-secret", OCULUS_APP_SECRET,
        "--channel", "alpha",
        "--apk", os.path.join(BASE_DIR, "builds/app.apk")
    ],
    # capture_output=True,
    # check=True,
    text=True,
)

if result.returncode == 1:
    print(f"[{sys.argv[0]}]: Deployment failed. Exiting.")
    sys.exit(1)

print(f"[{sys.argv[0]}]: Oculus platform deployment successful.")
sys.exit(0)
