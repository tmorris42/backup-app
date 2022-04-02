"""This script is handle reports from backup_app scans

Compare the current state of a source folder with the current state of the
backup folder.
"""

import filecmp
import os


class Report:
    """Stores a directory scan report."""

    def __init__(self, report_dict, source=None, backup=None):
        self.items = report_dict
        self.source = source
        self.backup = backup

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def _file_already_in_moved_files(self, filename):
        for file_pair in self.items["moved_files"]:
            if filename == file_pair[0]:
                return True
        return False

    def examine(self):
        """Return examined report as dictionary

        Look for files that were moved from one location to another.
        Update report and return self.items.
        """
        self.items["moved_files"] = []
        to_delete_ad = []
        to_delete_rm = []
        to_delete_rm_val = []

        # for every file that's only in a, compare to files only in b
        for i, added in enumerate(self.items["added_files"]):
            new_file = os.path.join(self.source, added)
            new_path = os.path.join(self.backup, added)
            for j, removed in enumerate(self.items["removed_files"]):
                old_file = os.path.join(self.backup, removed)
                # if file is a file, check for identical files
                if os.path.isfile(new_file) and os.path.isfile(old_file):
                    if filecmp.cmp(new_file, old_file, shallow=False):
                        if not self._file_already_in_moved_files(old_file):
                            self.items["moved_files"].append(
                                (old_file, new_path)
                            )
                            to_delete_ad.append(i)
                            to_delete_rm.append(j)
                # If file is a dir, check for similar dirs
                elif os.path.isdir(new_file) and os.path.isdir(old_file):
                    temp_report = filecmp.dircmp(new_file, old_file)
                    length = len(temp_report.left_only) + len(
                        temp_report.right_only
                    )
                    if len(temp_report.common) > length:
                        self.items["moved_files"].append((old_file, new_path))
                        suspected_moved_files = (
                            n
                            for n in temp_report.left_only
                            if n in self.items["removed_files"]
                        )
                        for new_find in suspected_moved_files:
                            to_delete_rm_val.append(new_find)
                            self.items["moved_files"].append(
                                (
                                    os.path.join(self.backup, new_find),
                                    os.path.join(new_path, new_find),
                                )
                            )
                        to_delete_ad.append(i)
                        to_delete_rm.append(j)
        to_delete_ad = list(set(to_delete_ad))
        to_delete_ad.sort(reverse=True)
        to_delete_rm = list(set(to_delete_rm))
        to_delete_rm.sort(reverse=True)
        for del_index in to_delete_rm:
            del self.items["removed_files"][del_index]
        for del_index in to_delete_ad:
            del self.items["added_files"][del_index]
        self.items["removed_files"] = [
            x for x in self.items["removed_files"] if x not in to_delete_rm_val
        ]
        # self.items['moved_files'] = moved
        return self
