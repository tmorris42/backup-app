"""This script contains functions to move, copy, and delete files"""

import logging
import os
import shutil

import send2trash  # type: ignore


def copy_files_from_a_to_b(dira, dirb, files, overwrite=False):
    """Copy files from source directory to backup directory.

    Arguments:
    dira -- source folder path
    dirb -- backup folder path
    files -- a list of relative filepaths for files to delete

    Return list of files that were not copied.
    """
    logger = logging.getLogger(f"{__name__}.{copy_files_from_a_to_b.__name__}")
    failed = []
    for filename in files:
        old_path = os.path.join(dira, filename)
        new_path = os.path.join(dirb, filename)
        if os.path.isdir(old_path):
            if not os.path.exists(new_path):
                logger.info("%s --> %s", old_path, new_path)
                #                os.mkdir(new_path)
                shutil.copytree(old_path, new_path)
                logger.info("Copied!")
            else:
                failed.append(filename)

        elif os.path.isfile(old_path):
            logger.info("%s --> %s", old_path, new_path)
            if os.path.exists(new_path):
                logger.warning("File already exists!")
                if overwrite:
                    logger.warning("Overwriting!")
                    send2trash.send2trash(new_path)
                    shutil.copy2(old_path, new_path)
                    logger.info("Copied!\n")
                else:
                    failed.append(filename)
            else:
                logger.info("%s --> %s", old_path, new_path)
                shutil.copy2(old_path, new_path)
                logger.info("Copied!")
        else:
            logger.info("%s --> %s", old_path, new_path)
            logger.warning("Warning! No file found!")
            failed.append(filename)
    logger.info("done copying files")
    return failed


def delete_files_from_b(dirb, files):
    """Delete files in a given folder.

    Arguments:
    dirb -- folder path
    files -- a list of relative filepaths for files to delete
    """
    logger = logging.getLogger(f"{__name__}.{delete_files_from_b.__name__}")
    failed = []
    for filepath in files:
        path = os.path.join(dirb, filepath)
        if os.path.exists(path):
            logger.info("deleting %s", path)
            logger.info(path := os.path.normpath(path))
            send2trash.send2trash(path)
        else:
            failed.append(filepath)
    logger.info("Done deleting")
    return failed


def move_files_in_b(file_sets):
    """Move files from one location to another.

    Arguments:
    file_sets -- a list of tuples of abs filepaths
                 (source_path, destination_path)
    """
    logger = logging.getLogger(f"{__name__}.{move_files_in_b.__name__}")
    failed = []
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
        dest = os.path.sep.join(dest)
        if os.path.exists(dest):
            failed.append(file_set)
        else:
            logger.info("moving FROM:\n%s\nTO:\n%s\n\n\n", src, dest)
            shutil.move(src, dest)
    logger.info("done moving")
    return failed


def update_files_a_to_b(dira, dirb, files):
    """Copy files from source directory to backup directory."""
    logger = logging.getLogger(f"{__name__}.{update_files_a_to_b.__name__}")
    failed = copy_files_from_a_to_b(dira, dirb, files, overwrite=True)
    logger.info("Done updating")
    return failed
