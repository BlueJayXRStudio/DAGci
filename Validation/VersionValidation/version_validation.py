import sys, os
import _bootstrap
from Tools.ref_container import RefContainer

def simple_semver_validator(version: str) -> bool:
    ''' returns true if version is valid '''
    components = version.split('.')
    # print(components)
    return len(components) == 3 and all(i.isdigit() and len(i) == 1 for i in components)

def simple_increment_version(version: str, ref_container: RefContainer) -> bool:
    ''' increment version if version is valid and lower than 9.9.9 '''
    if not simple_semver_validator(version) or version == "9.9.9":
        return False
    ref_container.item = '.'.join(list(str(int(''.join(version.split('.')))+1)))
    return True

if __name__ == "__main__":
    print(simple_semver_validator("0.1.1"))