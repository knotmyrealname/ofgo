import os

def ensure_dir_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)