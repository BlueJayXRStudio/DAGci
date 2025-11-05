import os, _bootstrap

class PathResolveNormalizer:
    def __init__(self, root):
        self.root = root

    def resolved(self, path):
        return os.path.abspath(os.path.join(self.root, path))