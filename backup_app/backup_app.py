#!usr/bin/env python3

"""This script is used to maintain an up-to-date backup folder

Compare the current state of a source folder with the current state of the
backup folder.
"""

import logging
import os
import time
import tkinter as tk
from enum import Enum
from tkinter import filedialog

from .backup_manager import BackupManager

SHALLOW = True

E_DIRS = Enum("Directory", "SRC BAK")


class App:
    """App class is used to hold the backup app window and methods."""

    def __init__(self, master, srcdir, bakdir, log_to_file=False):
        self.manager = BackupManager(srcdir, bakdir, log_to_file)
        self.master = master
        self.source_dir_var = tk.StringVar()
        self.backup_dir_var = tk.StringVar()

        self.source_dir_var.set(srcdir)
        self.backup_dir_var.set(bakdir)

        self.make_window()
        # self.show_tree("both")
        self.log((self.source_dir_var.get(), self.backup_dir_var.get()), True)
        self.source_field.after(200, self.redraw)

    def redraw(self):
        # logging.info("Redrawing!")
        if self.manager and self.manager.report:
            self.display_examined_results()
        # self.source_field.after(200, self.redraw)
        self.backup_field.after(200, self.redraw)

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        self.manager.log(msg, pretty)

    def show_tree(self, which):
        """Show directory tree in display pane.

        IN DEVELOPMENT
        """
        if which == "source":
            folder = self.source_dir_var.get()
            display_pane = self.source_field
        elif which == "backup":
            folder = self.backup_dir_var.get()
            display_pane = self.backup_field
        elif which == "both":
            self.show_tree("source")
            self.show_tree("backup")
            return

        listing = os.listdir(folder)
        logging.info(f"{os.path.basename(folder)}: {listing}")

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
            index = self.source_field.nearest(event.y)
        # selected = self.displayEntries[index]
        filename = self.source_field.get(index)
        failed = self.manager.copy_added_file(filename)
        logging.error(f"The following files failed: {failed}")

    def copy_selected(self):
        """Copy selected files in the changed files list to the backup folder.

        Copy each file that has been selected in the source folder list to
        the backup folder list.
        """
        items = list(map(int, self.source_field.curselection()))
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
            index = self.backup_field.nearest(event.y)
            logging.debug("Found index: %s", index)
        filename = self.backup_field.get(index)
        # Index order: moved -> mismatched -> removed
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
        logging.error(f"The following files failed: {failed}")

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
        filebar = tk.Menu(self.master)
        filemenu = tk.Menu(filebar, tearoff=0)
        filebar.add_cascade(label="File", menu=filemenu)

        self.source_field = tk.Listbox(
            self.master, width=60, selectmode=tk.EXTENDED
        )
        self.backup_field = tk.Listbox(self.master, width=60)

        button_width = 20  # button width
        scan_button = tk.Button(
            self.master, text="Scan", command=self.scan, width=button_width
        )
        move_button = tk.Button(
            self.master,
            text="Move in Backup",
            command=self.move_files,
            width=button_width,
        )
        copy_button = tk.Button(
            self.master,
            text="Copy to Backup",
            command=self.copy_all_new_files,
            width=button_width,
        )
        copy_selected_button = tk.Button(
            self.master,
            text="Copy Selected to Backup",
            command=self.copy_selected,
            width=button_width,
        )
        remove_button = tk.Button(
            self.master,
            text="Remove from Backup",
            command=self.delete_files,
            width=button_width,
        )
        update_button = tk.Button(
            self.master,
            text="Update in Backup",
            command=self.update_files,
            width=button_width,
        )

        self.source_field.grid(
            row=1, column=0, rowspan=7, columnspan=2, sticky="nsew"
        )
        scan_button.grid(row=1, column=2)
        move_button.grid(row=2, column=2)
        copy_button.grid(row=3, column=2)
        copy_selected_button.grid(row=4, column=2)
        remove_button.grid(row=5, column=2)
        update_button.grid(row=6, column=2)
        self.backup_field.grid(
            row=1, column=3, rowspan=7, columnspan=2, sticky="nsew"
        )

        source_button = tk.Button(
            self.master,
            text="Open Source Folder",
            command=lambda: self.open_directory(E_DIRS.SRC),
        )
        source_dir_field = tk.Entry(
            self.master, textvariable=self.source_dir_var, state="readonly"
        )
        source_button.grid(row=0, column=0, sticky="nsew")
        source_dir_field.grid(row=0, column=1, sticky="nsew")

        backup_button = tk.Button(
            self.master,
            text="Open Backup Folder",
            command=lambda: self.open_directory(E_DIRS.BAK),
        )
        backup_dir_field = tk.Entry(
            self.master, textvariable=self.backup_dir_var, state="readonly"
        )
        backup_button.grid(row=0, column=3, sticky="nsew")
        backup_dir_field.grid(row=0, column=4, sticky="nsew")

        self.master.rowconfigure(6, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(4, weight=1)

        self.master.config(menu=filebar)

        self.source_field.bind("<Double-Button-1>", self.select_file_source)
        self.backup_field.bind("<Double-Button-1>", self.select_file_backup)

        self.redraw()

    def open_directory(self, e_dir):
        """Select a directory."""

        if e_dir == E_DIRS.SRC:
            dir_var = self.source_dir_var
        elif e_dir == E_DIRS.BAK:
            dir_var = self.backup_dir_var

        dir_name = filedialog.askdirectory(
            parent=self.master,
            title="Open Directory...",
            initialdir=dir_var.get(),
        )
        dir_name = os.path.normpath(dir_name)
        if dir_name:
            dir_var.set(dir_name)
            self.finish_open()

    def finish_open(self):
        """Clean up after selecting new folder."""
        self.manager.source_directory = self.source_dir_var.get()
        self.manager.backup_directory = self.backup_dir_var.get()
        with open("last_dirs.log", "w") as log:
            log.write(self.source_dir_var.get() + "\n")
            log.write(self.backup_dir_var.get() + "\n")
        self.manager.report.items.clear()
        # self.show_tree("both")

    def scan(self):
        """Scan the source and backup directories and display results."""
        start = time.time()
        # self.manager.report = self.compare_directories().examine()
        srcdir = self.source_dir_var.get()
        bakdir = self.backup_dir_var.get()
        self.manager.scan(srcdir, bakdir)
        self.redraw()
        runtime = time.time() - start
        logging.info("runtime: %d seconds", runtime)
        self.log(self.manager.report, True)

    def display_examined_results(self):
        """Display the results in the display lists"""
        self.source_field.delete(0, tk.END)
        self.backup_field.delete(0, tk.END)
        if self.manager and self.manager.report:
            if "moved_files" in self.manager.report:
                for item in self.manager.report["moved_files"]:
                    self.backup_field.insert(tk.END, item[0] + "-->" + item[1])
                    self.backup_field.itemconfig(tk.END, {"bg": "yellow"})
            if "mismatched_files" in self.manager.report:
                for item in self.manager.report["mismatched_files"]:
                    self.backup_field.insert(tk.END, item)
                    self.backup_field.itemconfig(tk.END, {"bg": "orange"})
            if "added_files" in self.manager.report:
                for item in self.manager.report["added_files"]:
                    self.source_field.insert(tk.END, item)
                    self.source_field.itemconfig(tk.END, {"bg": "green"})
            if "removed_files" in self.manager.report:
                for item in self.manager.report["removed_files"]:
                    self.backup_field.insert(tk.END, item)
                    self.backup_field.itemconfig(tk.END, {"bg": "red"})
            if "errors" in self.manager.report:
                for item in self.manager.report["errors"]:
                    logging.error(
                        "\nThese files had errors (check manually!):"
                    )
                    logging.error(item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    DIRS = []
    try:
        with open("last_dirs.log", "r") as file:
            for line in file:
                DIRS.append(line)
        STARTING_DIRECTORY, BACKUP_DIRECTORY = DIRS[0][0:-1], DIRS[1][0:-1]
    except (FileNotFoundError, IndexError):
        STARTING_DIRECTORY = ".\\__Demo Source Location"
        BACKUP_DIRECTORY = ".\\__Demo Backup Location"
    STARTING_DIRECTORY = os.path.abspath(STARTING_DIRECTORY)
    BACKUP_DIRECTORY = os.path.abspath(BACKUP_DIRECTORY)
    logging.debug("\n\t%s\n\n\t%s\n", STARTING_DIRECTORY, BACKUP_DIRECTORY)

    ROOT = tk.Tk()
    APP = App(ROOT, STARTING_DIRECTORY, BACKUP_DIRECTORY, log_to_file=True)
    ROOT.mainloop()
