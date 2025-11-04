import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import sys, os, _bootstrap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_result(path):
    if not path.exists():
        print(f"{str(path)} not found")
    else:
        tree = ET.parse(path)
        root = tree.getroot()

        result = str(root.attrib.get("result", 0))
        testcasecount = int(root.attrib.get("testcasecount", 0))
        passed = int(root.attrib.get("passed", 0))
        failed = int(root.attrib.get("failed", 0))
        skipped = int(root.attrib.get("skipped", 0))
        duration = float(root.attrib.get("duration", 0.0))

        print(f"File: {path}")
        print(f"Result: {result}")
        print(f"Test Cases: {testcasecount}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Duration: {duration:.2f}s")

        for test in root.iter("test-case"):
            if test.attrib.get("result") == "Failed":
                print("Failed test:", test.attrib.get("fullname", "(unknown)"))
        print('\n')
        if result == "Passed":
            return 0
    return 1

result = subprocess.run(
    ["/usr/bin/env", "bash", os.path.join(BASE_DIR, "test")],
    # capture_output=True,
    # check=True,
    text=True
)

if result.returncode == 0:
    print("tests ran successfully\n")
    print("Play Mode Tests: \n")
    result1 = parse_result(Path(os.path.join(BASE_DIR, "logs/results.xml")))
    print("Edit Mode Tests: \n")
    result2 = parse_result(Path(os.path.join(BASE_DIR, "logs/results_edit_mode.xml")))
    if result1 == 0 and result2 == 0:
        sys.exit(0)
else: # Gracefully handle failed run
    print("tests failed to run")
sys.exit(1)