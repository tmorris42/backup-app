import logging
import os
import shutil

import send2trash  # type: ignore


# pylint: disable=C0330
def copy_files_from_a_to_b(dira, dirb, files, overwrite=False):
    """Copy files from source directory to backup directory.

    Arguments:
    dira -- source folder path
    dirb -- backup folder path
    files -- a list of relative filepaths for files to delete

    Return list of files that were not copied.
    """
    failed = []
    for filename in files:
        old_path = os.path.join(dira, filename)
        new_path = os.path.join(dirb, filename)
        #        logging.debug('if we were copying right now...')
        if os.path.isdir(old_path):
            if not os.path.exists(new_path):
                logging.info("%s --> %s", old_path, new_path)
                #                os.mkdir(new_path)
                shutil.copytree(old_path, new_path)
                logging.info("Copied!")
            else:
                failed.append(filename)

        elif os.path.isfile(old_path):
            logging.info("%s --> %s", old_path, new_path)
            if os.path.exists(new_path):
                logging.warning("File already exists!")
                if overwrite:
                    logging.warning("Overwriting!")
                    send2trash.send2trash(new_path)
                    shutil.copy2(old_path, new_path)
                    logging.info("Copied!\n")
                else:
                    failed.append(filename)
            else:
                logging.info("%s --> %s", old_path, new_path)
                shutil.copy2(old_path, new_path)
                logging.info("Copied!")
        else:
            logging.info("%s --> %s", old_path, new_path)
            logging.warning("Warning! No file found!")
            failed.append(filename)
    logging.info("done copying files")
    return failed


def delete_files_from_b(dirb, files):
    """Delete files in a given folder.

    Arguments:
    dirb -- folder path
    files -- a list of relative filepaths for files to delete
    """
    failed = []
    for filepath in files:
        path = os.path.join(dirb, filepath)
        if os.path.exists(path):
            logging.info("deleting %s", path)
            logging.info(path := os.path.normpath(path))
            send2trash.send2trash(path)
        else:
            failed.append(filepath)
    logging.info("Done deleting")
    return failed


def move_files_in_b(file_sets):
    """Move files from one location to another.

    Arguments:
    file_sets -- a list of tuples of abs filepaths
                 (source_path, destination_path)
    """
    failed = []
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
        #        dest = os.path.sep.join(dest[0:-1])
        dest = os.path.sep.join(dest)
        #        move_file_from_a_to_b(src,dest,fn_src)
        if os.path.exists(dest):
            failed.append(file_set)
        else:
            logging.info("moving FROM:\n%s\nTO:\n%s\n\n\n", src, dest)
            shutil.move(src, dest)
    logging.info("done moving")
    return failed


def update_files_a_to_b(dira, dirb, files):
    """Copy files from source directory to backup directory."""
    failed = copy_files_from_a_to_b(dira, dirb, files, overwrite=True)
    logging.info("Done updating")
    return failed
