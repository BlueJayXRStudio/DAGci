import sys, os, _bootstrap
import subprocess
from Tools.path_tools import PathResolveNormalizer
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base_resolver = PathResolveNormalizer(BASE_DIR)
project_resolver = PathResolveNormalizer(_bootstrap.project_root)

class ConfigGetter:
    def __init__(self):
        self.config = None

        # Open file dialog to retrieve workflow config
        result = subprocess.run(["python", base_resolver.resolved("filedialog.py")], capture_output=True, text=True)
        if result.returncode == 0:
            workflow = result.stdout.strip()
            # Open config
            with open(workflow, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            print("No valid file selected.")
    