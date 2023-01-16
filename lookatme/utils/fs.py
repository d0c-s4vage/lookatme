"""
Utilities related to file systems
"""


import glob
import os
import shutil


def copy_tree_update(src: str, dst: str):
    """Copy a directory from src to dst. For each directory within src,
    ensure that the directory exists, and then copy each individual file in.
    If other files exist in that same directory in dst, leave them alone.
    """
    if not os.path.exists(dst):
        shutil.copytree(src, dst)
        return

    for src_subpath in glob.glob(os.path.join(src, "*")):
        relpath = os.path.relpath(src_subpath, src)
        dst_subpath = os.path.join(dst, relpath)

        if os.path.isfile(src_subpath):
            shutil.copy(src_subpath, dst_subpath)
        elif os.path.isdir(src_subpath):
            copy_tree_update(src_subpath, dst_subpath)
