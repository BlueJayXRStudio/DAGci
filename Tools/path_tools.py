import os, _bootstrap

def scanfiles(dir):
    """ Generate file paths for given directory (non-recursive) """
    for item in os.listdir(dir):
        path = os.path.join(dir, item)
        if os.path.isfile(path):
            yield path

def scandirs(dir):
    """ Generate directory paths for given directory (non-recursive) """
    for item in os.listdir(dir):
        path = os.path.join(dir, item)
        if os.path.isdir(path):
            yield path

class PathResolveNormalizer:
    def __init__(self, root):
        self.root = root

    def resolved(self, path):
        return os.path.abspath(os.path.join(self.root, path))