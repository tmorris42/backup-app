#!usr/bin/env python3

"""This script is used to maintain an up-to-date backup folder

Compare the current state of a source folder with the current state of the backup folder.
"""

import logging
import os
import filecmp
import time
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

from pprint import pprint
import send2trash

SHALLOW = True

def show_tree(directory):
    """Print the directory tree."""
    root_directory = directory
    for directory_name, _, file_list in os.walk(root_directory):
        logging.info('Found directory: %s', directory_name)
        for fname in file_list:
            logging.info('\t%s', fname)

def copy_files_from_a_to_b(dira, dirb, files, overwrite=False):
    """Copy files from source directory to backup directory."""
    failed = []
    for filename in files:
        old_path = os.path.join(dira, filename)
        new_path = os.path.join(dirb, filename)
##        logging.debug('if we were copying right now...')
        if os.path.isdir(old_path):
            if not os.path.exists(new_path):
                logging.info('%s --> %s', old_path, new_path)
##                os.mkdir(new_path)
                shutil.copytree(old_path, new_path)
                logging.info('Copied!')
            else: failed.append(filename)

        elif os.path.isfile(old_path):
            logging.info('%s --> %s', old_path, new_path)
            if os.path.exists(new_path):
                logging.warning('File already exists!')
                if overwrite:
                    logging.warning('Overwriting!')
                    send2trash.send2trash(new_path)
                    shutil.copy2(old_path, new_path)
                    logging.info('Copied!\n')
                else: failed.append(filename)
            else:
                logging.info('%s --> %s', old_path, new_path)
                shutil.copy2(old_path, new_path)
                logging.info('Copied!')
        else:
            logging.info('%s --> %s', old_path, new_path)
            logging.error("Error! No file found!")
            failed.append(filename)
    logging.info('done copying files')
    return failed

def delete_files_from_b(dirb, files):
    """Delete files in a given folder.

    Arguments:
    dirb -- folder path
    files -- a list of relative filepaths for files to delete
    """
    for filepath in files:
        path = os.path.join(dirb, filepath)
        logging.info("deleting %s", path)
        logging.info(path := os.path.normpath(path))
        send2trash.send2trash(path)
    logging.info("Done deleting")

def move_files_in_b(file_sets):
    """Move files from one location to another.

    Arguments:
    file_sets -- a list of tuples of filepaths (source_path, destination_path)
    """
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
##        dest = os.path.sep.join(dest[0:-1])
        dest = os.path.sep.join(dest)
##        move_file_from_a_to_b(src,dest,fn_src)
        logging.info('moving FROM:\n%s\nTO:\n%s\n\n\n', src, dest)
        shutil.move(src, dest)
    logging.info('done moving')

def update_files_a_to_b(dira, dirb, files):
    """Copy files from source directory to backup directory."""
    copy_files_from_a_to_b(dira, dirb, files, overwrite=True)
    logging.info("Done updating")

def make_changes(dira, dirb, report):
    """Use CLI to update the backup folder."""
    if len(report['moved_files']) > 0:
        goto = input('Move Files? Y/N')
        if goto in ('y', 'Y', 'yes', 'Yes', 'YES'):
            move_files_in_b(report['moved_files'])
            return "recheck"
    if len(report['added_files']) > 0:
        goto = input('Copy New Files? Y/N')
        if goto in ('y', 'Y', 'yes', 'Yes', 'YES'):
            copy_files_from_a_to_b(dira, dirb, report['added_files'])
    if len(report['removed_files']) > 0:
        goto = input('Delete Old Files? Y/N')
        if goto in ('y', 'Y', 'yes', 'Yes', 'YES'):
            delete_files_from_b(dirb, report['removed_files'])
    if len(report['mismatched_files']) > 0:
        goto = input('Update Changed Files? Y/N')
        if goto in ('y', 'Y', 'yes', 'Yes', 'YES'):
            update_files_a_to_b(dira, dirb, report['mismatched_files'])
    return "quit"

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

    def examine(self):
        """Return examined report as dictionary

        Look for files that were moved from one location to another.
        Update report and return self.items.
        """
        dira = self.source
        dirb = self.backup
        examined_report = self.items
        aonly = self.items['added_files']
        bonly = self.items['removed_files']
        moved = []
        to_delete = []

        # for every file that's only in a, compare to files only in b
        for i, added in enumerate(aonly):
            new_file = os.path.join(dira, added)
            # if file is a file, check for identical files
            if os.path.isfile(new_file):
                for j, removed in enumerate(bonly):
                    old_file = os.path.join(dirb, removed)
                    if os.path.isfile(old_file):
                        if filecmp.cmp(new_file, old_file, shallow=False):
                            old_path = os.path.join(dirb, bonly[j])
                            new_path = os.path.join(dirb, aonly[i])
                            moved.append((old_path, new_path))
                            del aonly[i]
                            del bonly[j]
            # If file is a dir, check for similar dirs
            elif os.path.isdir(new_file):
                for j, removed in enumerate(bonly):
                    old_file = os.path.join(dirb, removed)
                    if os.path.isdir(old_file):
                        temp_report = filecmp.dircmp(new_file, old_file)
                        length = (len(temp_report.left_only) +
                                  len(temp_report.right_only))
                        if len(temp_report.common) > length:
                            old_path = os.path.join(dirb, bonly[j])
                            new_path = os.path.join(dirb, aonly[i])
                            moved.append((old_path, new_path))
                            for newly_discovered in temp_report.left_only:
                                if newly_discovered in examined_report['removed_files']:
                                    to_delete.append(newly_discovered)
                                    moved.append((os.path.join(dirb,
                                                               newly_discovered),
                                                  os.path.join(new_path,
                                                               newly_discovered)
                                                  ))
                            del aonly[i]
                            del bonly[j]

        for deleteable in to_delete:
            examined_report['removed_files'].remove(deleteable)
        examined_report['moved_files'] = moved
        return self

class App:
    """App class is used to hold the backup app window and methods."""
    def __init__(self, master, srcdir, bakdir, log_to_file=False):
        self.master = master
        self.source_dir = srcdir
        self.source_dir_var = tk.StringVar()
        self.backup_dir = bakdir
        self.backup_dir_var = tk.StringVar()
        self.refresh_directory_variables()
        self.make_window()
        self.log_to_file = log_to_file
        self.log_file = f'__logs/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log'
        self.log((self.source_dir, self.backup_dir), True)
        self.examined_report = Report({})

        self.show_tree('both')

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        if not self.log_to_file:
            return False
        try:
            with open(self.log_file, 'a+') as out:
                if pretty:
                    pprint(msg, stream=out)
                else:
                    out.write(msg)
        except FileNotFoundError:
            os.mkdir('__logs/')
            return self.log(msg, pretty)
        return True

    def show_tree(self, which):
        """Show directory tree in display pane.

        IN DEVELOPMENT
        """
        if which == 'source':
            #folder = self.source_dir # this is just for debug
            display_pane = self.source_field
        elif which == 'backup':
            #folder = self.backup_dir # this is just for debug
            display_pane = self.backup_field
        elif which == 'both':
            self.show_tree('source')
            self.show_tree('backup')
            return

##        show_tree(folder) # this is just for debug

        ### change this to only display current folder
        # display file contents in source display
        display_pane.delete(0, tk.END)
##        level=0
##        for directory_name, subdirectory_list, file_list in os.walk(folder):
##            level += 1
##            display_pane.insert(tk.END,'__'*(level-1)+directory_name)
##            for sub in file_list:
##                display_pane.insert(tk.END,'_'*level+sub)

    def select_file_source(self, event=None, index=None):
        """Select a file from the changed files list in the source folder.

        If the file was:
            created, copy it from the source location to the backup location.
        """
        if index is None:
            index = self.source_field.nearest(event.y)
        #selected = self.displayEntries[index]
        filename = self.source_field.get(index)
        failed = copy_files_from_a_to_b(self.source_dir, self.backup_dir, [filename])
        if failed == []:
            self.examined_report['added_files'].remove(filename)
            self.source_field.delete(index)

    def copy_selected(self):
        """Copy selected files in the changed files list to the backup folder.

        Copy each file that has been selected in the source folder list to the backup folder list.
        """
        items = list(map(int, self.source_field.curselection()))
        items.sort(reverse=True)
        for item in items:
            self.select_file_source(index=item)

    def copy_all_new_files(self):
        """Copy all new files in the changed files list to the backup folder."""
        failed = copy_files_from_a_to_b(self.source_dir, self.backup_dir,
                                        self.examined_report['added_files'])
        self.examined_report['added_files'] = failed
        self.display_examined_results()

    def select_file_backup(self, event):
        """Select a file from the changed files list in the backup folder.

        If the file was:
            moved, move it in the backup location.
            deleted, delete it in the backup location.
            changed, copy it from the source location to the backup location.
        """
        logging.debug("%s ::: %s", self.backup_field, event.y)

    def update_files(self):
        """Command function to call update_files_a_to_b."""
        update_files_a_to_b(self.source_dir,
                            self.backup_dir, self.examined_report['mismatched_files'])

    def delete_files(self):
        """Command function to call delete_files_from_b."""
        delete_files_from_b(self.backup_dir,
                            self.examined_report['removed_files'])

    def move_files(self):
        """Command function to call move_files_in_b."""
        move_files_in_b(self.examined_report['moved_files'])

    def make_window(self):
        """Create the window layout."""
        self.master.winfo_toplevel().title("Backup Master")
        filebar = tk.Menu(self.master)
        self.filemenu = tk.Menu(filebar, tearoff=0)
        filebar.add_cascade(label="File", menu=self.filemenu)

        self.source_field = tk.Listbox(self.master, width=60,
                                       selectmode=tk.EXTENDED)
        self.backup_field = tk.Listbox(self.master, width=60)

        button_width = 20 #button width
        scan_button = tk.Button(self.master, text="Scan",
                                command=self.scan, width=button_width)
        move_button = tk.Button(self.master, text="Move in Backup",
                                command=self.move_files, width=button_width)
        copy_button = tk.Button(self.master, text="Copy to Backup",
                                command=self.copy_all_new_files,
                                width=button_width)
        copy_selected_button = tk.Button(self.master,
                                         text="Copy Selected to Backup",
                                         command=self.copy_selected, width=button_width)
        remove_button = tk.Button(self.master, text="Remove from Backup",
                                  command=self.delete_files,
                                  width=button_width)
        update_button = tk.Button(self.master, text="Update in Backup",
                                  command=self.update_files,
                                  width=button_width)

        self.source_field.grid(row=1, column=0, rowspan=7, columnspan=2,
                               sticky='nsew')
        scan_button.grid(row=1, column=2)
        move_button.grid(row=2, column=2)
        copy_button.grid(row=3, column=2)
        copy_selected_button.grid(row=4, column=2)
        remove_button.grid(row=5, column=2)
        update_button.grid(row=6, column=2)
        self.backup_field.grid(row=1, column=3, rowspan=7, columnspan=2,
                               sticky='nsew')

        source_button = tk.Button(self.master,
                                  text="Open Source Folder",
                                  command=self.open_source_directory)
        source_dir_field = tk.Entry(self.master,
                                    textvariable=self.source_dir_var, state="readonly")
        source_button.grid(row=0, column=0, sticky='nsew')
        source_dir_field.grid(row=0, column=1, sticky='nsew')

        backup_button = tk.Button(self.master,
                                  text="Open Backup Folder",
                                  command=self.open_backup_directory)
        backup_dir_field = tk.Entry(self.master,
                                    textvariable=self.backup_dir_var, state="readonly")
        backup_button.grid(row=0, column=3, sticky='nsew')
        backup_dir_field.grid(row=0, column=4, sticky='nsew')

        self.master.rowconfigure(6, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(4, weight=1)

        self.master.config(menu=filebar)

        self.source_field.bind("<Double-Button-1>", self.select_file_source)
        self.backup_field.bind("<Double-Button-1>", self.select_file_backup)

    def open_source_directory(self):
        """Select a source directory."""
        dir_name = filedialog.askdirectory(parent=self.master,
                                           title='Open Source Directory...',
                                           initialdir=self.source_dir)
        if dir_name:
            self.source_dir = dir_name
            self.finish_open()

    def open_backup_directory(self):
        """Select a backup directory."""
        dir_name = filedialog.askdirectory(parent=self.master,
                                           title='Open Backup Directory...',
                                           initialdir=self.backup_dir)
        if dir_name:
            self.backup_dir = dir_name
            self.finish_open()

    def finish_open(self):
        """Clean up after selecting new folder."""
        self.refresh_directory_variables()
        with open('last_dirs.log', 'w') as log:
            log.write(self.source_dir+'\n')
            log.write(self.backup_dir+'\n')
        self.show_tree('both')

    def refresh_directory_variables(self):
        """Set TK variables to the selected directories."""
        self.source_dir_var.set(self.source_dir)
        self.backup_dir_var.set(self.backup_dir)

    def scan(self):
        """Scan the source and backup directories and display results."""
        start = time.time()
        self.examined_report = self.compare_directories().examine()
        self.display_examined_results()
        runtime = time.time()-start
        logging.info('runtime: %d seconds', runtime)
        self.log(self.examined_report, True)

    def compare_directories(self, dira=None, dirb=None, recursing=False):
        """Compare source and backup directories."""
        if not dira:
            dira = self.source_dir
        if not dirb:
            dirb = self.backup_dir
        simple_report = Report({}, source=dira, backup=dirb)
        #compare directories (This uses shallow comparison!!)
        dirs_cmp = filecmp.dircmp(dira, dirb)
        # Identify files that are only in dira
        simple_report['added_files'] = dirs_cmp.left_only[:]
        # Identify files that are only in dirb
        simple_report['removed_files'] = dirs_cmp.right_only[:]
        # For files in both, do a deep comparison using filecmp
        (simple_report['matched_files'],
         simple_report['mismatched_files'],
         simple_report['errors']) = filecmp.cmpfiles(dira,
                                                     dirb,
                                                     dirs_cmp.common_files,
                                                     shallow=SHALLOW)

        # Check subfolders
        for common_dir in dirs_cmp.common_dirs:
            new_dira = os.path.join(dira, common_dir)
            new_dirb = os.path.join(dirb, common_dir)
            sub_report = self.compare_directories(new_dira,
                                                  new_dirb,
                                                  recursing=True)
            if not recursing:
                logging.info('Checking subfolder\n\n\t%s\n', new_dira)

            #add sub report to overall report
            for key in ('added_files', 'removed_files',
                        'matched_files', 'mismatched_files',
                        'errors'):
                for item in sub_report[key]:
                    simple_report[key].append(os.path.join(common_dir,
                                                           item))

    ##    for adir in dirs_cmp.left_only:
    ##        if os.path.isdir(adir):
    ##            for sub in [x[0] for x in os.walk(adir)]:
    ##                simple_report['added_files'].append(sub)

        return simple_report

    def display_examined_results(self):
        """Display the results in the display lists"""
        #same = self.examined_report['matched_files']
        diff = self.examined_report['mismatched_files']
        aonly = self.examined_report['added_files']
        bonly = self.examined_report['removed_files']
        errors = self.examined_report['errors']
        moved = self.examined_report['moved_files']

        self.source_field.delete(0, tk.END)
        self.backup_field.delete(0, tk.END)
        if diff == aonly == bonly == errors == moved == []:
            logging.info('No Changes Detected!')
        else:
            if moved != []:
##                logging.debug('\nThese files have moved:')
                for item in moved:
##                    logging.debug(item[0],'-->',item[1])
                    self.backup_field.insert(tk.END, item[0]+'-->'+item[1])
                    self.backup_field.itemconfig(tk.END, {'bg':'yellow'})
            if diff != []:
##                logging.info('\nThese files have changed:')
                for item in diff:
##                    logging.debug(item)
                    self.backup_field.insert(tk.END, item)
                    self.backup_field.itemconfig(tk.END, {'bg':'orange'})
            if aonly != []:
##                logging.debug('\nThese files are new or moved:')
                for item in aonly:
##                    logging.debug(item)
                    self.source_field.insert(tk.END, item)
                    self.source_field.itemconfig(tk.END, {'bg':'green'})
            if bonly != []:
##                logging.debug('\nThese files have been deleted or moved:')
                for item in bonly:
##                    logging.debug(item)
                    self.backup_field.insert(tk.END, item)
                    self.backup_field.itemconfig(tk.END, {'bg':'red'})
            if errors != []:
                logging.error('\nThese files had errors (check manually!):')
                for item in errors:
                    logging.error(item)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    DIRS = []
    try:
        with open('last_dirs.log', 'r') as file:
            for line in file:
                DIRS.append(line)
        STARTING_DIRECTORY, BACKUP_DIRECTORY = DIRS[0][0:-1], DIRS[1][0:-1]
    except (FileNotFoundError, IndexError):
        STARTING_DIRECTORY = '.\\__Demo Source Location'
        BACKUP_DIRECTORY = '.\\__Demo Backup Location'
    STARTING_DIRECTORY = os.path.abspath(STARTING_DIRECTORY)
    BACKUP_DIRECTORY = os.path.abspath(BACKUP_DIRECTORY)
    logging.debug('\n\t%s\n\n\t%s\n', STARTING_DIRECTORY, BACKUP_DIRECTORY)

    ROOT = tk.Tk()
    APP = App(ROOT, STARTING_DIRECTORY, BACKUP_DIRECTORY, log_to_file=True)
    ROOT.mainloop()
