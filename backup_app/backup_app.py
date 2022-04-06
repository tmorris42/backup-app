#!usr/bin/env python3

"""This script is used to maintain an up-to-date backup folder

Compare the current state of a source folder with the current state of the
backup folder.
"""

import logging
import os
import time
import tkinter as tk
from tkinter import filedialog

from idlelib.tooltip import Hovertip  # type: ignore

from .backup_manager import BackupManager

SHALLOW = True


class ConsoleFrame(tk.Frame):
    """Class to hold console buttons"""

    def __init__(self, parent, buttons, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        for button in buttons:
            button_widget = tk.Button(self, text=button[0], command=button[1])
            button_widget.pack(
                expand=False, fill=tk.X, side=tk.TOP, anchor="n"
            )


class DirectoryFrame(tk.Frame):
    """Class to hold an instance of a directory"""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self._directory_var = tk.StringVar()

        self.listing = tk.Listbox(master=self, selectmode=tk.EXTENDED)

        open_folder_button = tk.Button(
            self,
            text="\U0001F4C2",
            command=self.open_directory,
        )
        Hovertip(open_folder_button, "Open folder")

        directory_label = tk.Entry(
            self, textvariable=self._directory_var, state="readonly"
        )
        self.directory_label_ht = Hovertip(directory_label, self.directory)

        open_folder_button.grid(row=0, column=0, sticky="nw")
        directory_label.grid(row=0, column=1, sticky="nsew")
        self.listing.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.grid_rowconfigure(index=1, weight=1)
        self.grid_columnconfigure(index=1, weight=1)

    @property
    def directory(self):
        """Directory variable to store text for tkinter directory Entry"""
        return self._directory_var.get()

    @directory.setter
    def directory(self, folderpath):
        self.directory_label_ht.text = folderpath
        return self._directory_var.set(folderpath)

    def open_directory(self):
        """Select a directory."""

        dir_name = filedialog.askdirectory(
            parent=self.master,
            title="Open Folder...",
            initialdir=self.directory,
        )
        dir_name = os.path.normpath(dir_name)
        if dir_name:
            self.directory = dir_name
            self.master.finish_open()


class App(tk.Frame):
    """App class is used to hold the backup app window and methods."""

    def __init__(
        self, master, srcdir, bakdir, *args, log_to_file=False, **kwargs
    ):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.manager = BackupManager(srcdir, bakdir, log_to_file)
        self.master = master

        self.make_window()

        self.source_panel.directory = srcdir
        self.backup_panel.directory = bakdir
        self.log(
            (
                self.source_panel.directory,
                self.backup_panel.directory,
            ),
            True,
        )
        self.redraw()
        # self.show_tree("both")

    def redraw(self):
        """Redraw the GUI."""
        # logging.info("Redrawing!")
        if self.manager and self.manager.report:
            self.display_examined_results()
        self.after(200, self.redraw)

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        self.manager.log(msg, pretty)

    def show_tree(self, which):
        """Show directory tree in display pane.

        IN DEVELOPMENT
        """
        if which == "source":
            folder = self.source_panel.directory
            display_pane = self.source_panel.listing
        elif which == "backup":
            folder = self.backup_panel.directory
            display_pane = self.backup_panel.listing
        elif which == "both":
            self.show_tree("source")
            self.show_tree("backup")
            return

        listing = os.listdir(folder)
        logging.info("%s: %s", os.path.basename(folder), listing)

        display_pane.delete(0, tk.END)
        i = 0
        for filename in listing:
            if os.path.isdir(os.path.join(folder, filename)):
                display_name = "\U0001F5BF" + f" {os.path.basename(filename)}"
            else:
                display_name = f" {os.path.basename(filename)}"
            display_pane.insert(i, display_name)
            i += 1

    def select_file_source(self, event=None, index=None):
        """Select a file from the changed files list in the source folder.

        If the file was:
            created, copy it from the source location to the backup location.
        """
        if index is None:
            index = self.source_panel.listing.nearest(event.y)
        filename = self.source_panel.listing.get(index)
        failed = self.manager.copy_added_file(filename)
        logging.error("The following files failed: %s", failed)

    def copy_selected(self):
        """Copy selected files in the changed files list to the backup folder.

        Copy each file that has been selected in the source folder list to
        the backup folder list.
        """
        items = list(map(int, self.source_panel.listing.curselection()))
        items.sort(reverse=True)
        for item in items:
            self.select_file_source(index=item)

    def copy_all_new_files(self):
        """Copy all new files in the changed files list to backup folder."""
        self.manager.copy_added_files()

    def select_file_backup(self, event=None, index=None):
        """Select a file from the changed files list in the backup folder.

        If the file was:
            moved, move it in the backup location.
            deleted, delete it in the backup location.
            changed, copy it from the source location to the backup location.
        """
        logging.debug(
            "Selecting file in backup. event: %s, index: %s", event, index
        )
        if index is None:
            index = self.backup_panel.listing.nearest(event.y)
            logging.debug("Found index: %s", index)
        filename = self.backup_panel.listing.get(index)
        moved_len = len(self.manager.report["moved_files"])
        mis_len = moved_len + len(self.manager.report["mismatched_files"])
        removed_len = mis_len + len(self.manager.report["removed_files"])

        if index < moved_len:
            filename_set = self.manager.report["moved_files"][index]
            failed = self.manager.move_files([filename_set])
        elif index < mis_len:
            failed = self.manager.copy_files_from_source_to_backup(
                [filename], overwrite=True
            )
        elif index < removed_len:
            failed = self.manager.delete_files([filename])
        logging.error("The following files failed: %s", failed)

    def update_files(self):
        """Command function to call update_files_a_to_b."""
        self.manager.update_files()

    def delete_files(self):
        """Command function to call delete_files_from_b."""
        self.manager.delete_files()

    def move_files(self):
        """Command function to call move_files_in_b."""
        self.manager.move_files()

    def make_window(self):
        """Create the window layout."""
        self.master.winfo_toplevel().title("Backup Master")
        filebar = tk.Menu(self)
        filemenu = tk.Menu(filebar, tearoff=0)
        filebar.add_cascade(label="File", menu=filemenu)
        self.master.config(menu=filebar)

        self.source_panel = DirectoryFrame(self)
        self.source_panel.listing.bind(
            "<Double-Button-1>", self.select_file_source
        )

        self.backup_panel = DirectoryFrame(self)
        self.backup_panel.listing.bind(
            "<Double-Button-1>", self.select_file_backup
        )

        buttons = (
            ("Scan", self.scan),
            ("Move in Backup", self.move_files),
            ("Copy to Backup", self.copy_all_new_files),
            ("Copy Selected to Backup", self.copy_selected),
            ("Remove from Backup", self.delete_files),
            ("Update in Backup", self.update_files),
        )
        self.console = ConsoleFrame(self, buttons)

        self.source_panel.pack(
            expand=True, fill=tk.BOTH, side=tk.LEFT, anchor="n"
        )
        self.console.pack(expand=False, fill=tk.NONE, side=tk.LEFT, anchor="n")
        self.backup_panel.pack(
            expand=True, fill=tk.BOTH, side=tk.LEFT, anchor="n"
        )

        self.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

    def finish_open(self):
        """Clean up after selecting new folder."""
        self.manager.source_directory = self.source_panel.directory
        self.manager.backup_directory = self.backup_panel.directory
        with open("last_dirs.log", "w", encoding="utf-8") as log:
            log.write(self.source_panel.directory + "\n")
            log.write(self.backup_panel.directory + "\n")
        self.manager.report.items.clear()
        # self.show_tree("both")

    def scan(self):
        """Scan the source and backup directories and display results."""
        start = time.time()
        # self.manager.report = self.compare_directories().examine()
        srcdir = self.source_panel.directory
        bakdir = self.backup_panel.directory
        self.manager.scan(srcdir, bakdir)
        runtime = time.time() - start
        logging.info("runtime: %d seconds", runtime)
        self.log(self.manager.report, True)

    def display_examined_results(self):
        """Display the results in the display lists"""
        self.source_panel.listing.delete(0, tk.END)
        self.backup_panel.listing.delete(0, tk.END)
        if self.manager and self.manager.report:
            if "moved_files" in self.manager.report:
                for item in self.manager.report["moved_files"]:
                    self.backup_panel.listing.insert(
                        tk.END, item[0] + "-->" + item[1]
                    )
                    self.backup_panel.listing.itemconfig(
                        tk.END, {"bg": "yellow"}
                    )
            if "mismatched_files" in self.manager.report:
                for item in self.manager.report["mismatched_files"]:
                    self.backup_panel.listing.insert(tk.END, item)
                    self.backup_panel.listing.itemconfig(
                        tk.END, {"bg": "orange"}
                    )
            if "added_files" in self.manager.report:
                for item in self.manager.report["added_files"]:
                    self.source_panel.listing.insert(tk.END, item)
                    self.source_panel.listing.itemconfig(
                        tk.END, {"bg": "green"}
                    )
            if "removed_files" in self.manager.report:
                for item in self.manager.report["removed_files"]:
                    self.backup_panel.listing.insert(tk.END, item)
                    self.backup_panel.listing.itemconfig(tk.END, {"bg": "red"})
            if "errors" in self.manager.report:
                for item in self.manager.report["errors"]:
                    logging.error(
                        "\nThese files had errors (check manually!):"
                    )
                    logging.error(item)


def main():
    """Launch the backup app"""
    logging.basicConfig(level=logging.DEBUG)
    dirs = []
    try:
        with open("last_dirs.log", "r", encoding="utf-8") as file:
            for line in file:
                dirs.append(line)
        starting_directory, backup_directory = dirs[0][0:-1], dirs[1][0:-1]
    except (FileNotFoundError, IndexError):
        starting_directory = ".\\__Demo Source Location"
        backup_directory = ".\\__Demo Backup Location"
    starting_directory = os.path.abspath(starting_directory)
    backup_directory = os.path.abspath(backup_directory)
    logging.debug("\n\t%s\n\n\t%s\n", starting_directory, backup_directory)

    root = tk.Tk()
    app = App(root, starting_directory, backup_directory, log_to_file=True)
    root.mainloop()
    del app


if __name__ == "__main__":
    main()
