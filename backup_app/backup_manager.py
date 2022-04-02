import os
from datetime import datetime
from pprint import pprint

from .filesystem import (
    copy_files_from_a_to_b,
    delete_files_from_b,
    move_files_in_b,
    update_files_a_to_b,
)
from .report import Report


class BackupManager:
    """Manage the scanning of directories and the copying of files."""

    def __init__(self, srcdir, bakdir, log_to_file=False):
        self.source_directory = srcdir
        self.backup_directory = bakdir
        if log_to_file:
            self.log_file = (
                f'__logs/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log'
            )
        else:
            self.log_file = None
        self.report = Report({})

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        if not self.log_file:
            return False
        if self.log_file == "console":
            if pretty:
                pprint(msg)
            else:
                print(msg)
        else:
            try:
                with open(self.log_file, "a+") as out:
                    if pretty:
                        pprint(msg, stream=out)
                    else:
                        out.write(msg)
            except FileNotFoundError:
                os.mkdir("__logs/")
                return self.log(msg, pretty)
        return True

    def copy_files_from_source_to_backup(self, filenames, overwrite=False):
        """Copy files from source folder to backup folder.

        Arguments:
        filenames -- list of relative filepath names.

        Returns:
        failed -- list of files that were not copied.
        """
        failed = []
        # abs_filenames = []
        # for filename in filenames:
        # abs_filename = (os.path.abspath(os.path.join(self.source_directory,
        # filename)),
        # os.path.abspath(os.path.join(self.backup_directory,
        # filename)))
        # abs_filenames.append(abs_filename)
        failed = copy_files_from_a_to_b(
            self.source_directory,
            self.backup_directory,
            filenames,
            overwrite=overwrite,
        )
        return failed

    def copy_added_file(self, filename):
        """Copy one file from added_files list to backup folder."""
        failed = self.copy_files_from_source_to_backup([filename])
        if failed == []:
            self.report["added_files"].remove(filename)
        return failed

    def copy_added_files(self):
        """Copy files that were added to the source directory.

        Return filenames that were not copied.
        """
        failed = copy_files_from_a_to_b(
            self.source_directory,
            self.backup_directory,
            self.report["added_files"],
        )
        self.report["added_files"] = failed
        return failed

    def update_files(self):
        """Update files that were changed it the source directory.

        Return filenames that were not updated.
        """
        return update_files_a_to_b(
            self.source_directory,
            self.backup_directory,
            self.report["mismatched_files"],
        )

    def delete_files(self):
        """Delete files that were removed from the source directory.

        Return filenames that were not deleted.
        """
        return delete_files_from_b(
            self.backup_directory, self.report["removed_files"]
        )

    def move_files(self):
        """Move files that were moved in the source directory.

        Return filenames that were not moved.
        """
        return move_files_in_b(self.report["moved_files"])
