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
            logging.warning("Warning! No file found!")
            failed.append(filename)
    logging.info('done copying files')
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
    file_sets -- a list of tuples of abs filepaths (source_path, destination_path)
    """
    failed = []
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
##        dest = os.path.sep.join(dest[0:-1])
        dest = os.path.sep.join(dest)
##        move_file_from_a_to_b(src,dest,fn_src)
        if os.path.exists(dest):
            failed.append(file_set)
        else:
            logging.info('moving FROM:\n%s\nTO:\n%s\n\n\n', src, dest)
            shutil.move(src, dest)
    logging.info('done moving')
    return failed

def update_files_a_to_b(dira, dirb, files):
    """Copy files from source directory to backup directory."""
    failed = copy_files_from_a_to_b(dira, dirb, files, overwrite=True)
    logging.info("Done updating")
    return failed

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
        self.items['moved_files'] = []
        to_delete_ad = []
        to_delete_rm = []
        to_delete_rm_val = []

        # for every file that's only in a, compare to files only in b
        for i, added in enumerate(self.items['added_files']):
            new_file = os.path.join(self.source, added)
            new_path = os.path.join(self.backup, added)
            for j, removed in enumerate(self.items['removed_files']):
                old_file = os.path.join(self.backup, removed)
                # if file is a file, check for identical files
                if os.path.isfile(new_file) and os.path.isfile(old_file):
                    if filecmp.cmp(new_file, old_file, shallow=False):
                        self.items['moved_files'].append((old_file, new_path))
                        to_delete_ad.append(i)
                        to_delete_rm.append(j)
                # If file is a dir, check for similar dirs
                elif os.path.isdir(new_file) and os.path.isdir(old_file):
                    temp_report = filecmp.dircmp(new_file, old_file)
                    length = (len(temp_report.left_only) +
                              len(temp_report.right_only))
                    if len(temp_report.common) > length:
                        self.items['moved_files'].append((old_file, new_path))
                        for new_find in (n for n in temp_report.left_only
                                         if n in self.items['removed_files']):
                            to_delete_rm_val.append(new_find)
                            self.items['moved_files'].append((
                                os.path.join(self.backup, new_find),
                                os.path.join(new_path, new_find)
                            ))
                        to_delete_ad.append(i)
                        to_delete_rm.append(j)
        to_delete_ad.sort(reverse=True)
        to_delete_rm.sort(reverse=True)
        for del_index in to_delete_rm:
            del self.items['removed_files'][del_index]
        for del_index in to_delete_ad:
            del self.items['added_files'][del_index]
        self.items['removed_files'] = [x for x in self.items['removed_files']
                                       if x not in to_delete_rm_val]
        #self.items['moved_files'] = moved
        return self

class BackupManager:
    """Manage the scanning of directories and the copying of files."""
    def __init__(self, srcdir, bakdir, log_to_file=False):
        self.source_directory = srcdir
        self.backup_directory = bakdir
        if log_to_file:
            self.log_file = f'__logs/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log'
        else:
            self.log_file = None
        self.report = Report({})

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        if not self.log_file:
            return False
        if self.log_file == 'console':
            if pretty:
                pprint(msg)
            else:
                print(msg)
        else:
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

    def copy_files_from_source_to_backup(self, filenames, overwrite=False):
        """Copy files from source folder to backup folder.

        Arguments:
        filenames -- list of relative filepath names.

        Returns:
        failed -- list of files that were not copied.
        """
        failed = []
        #abs_filenames = []
        #for filename in filenames:
            #abs_filename = (os.path.abspath(os.path.join(self.source_directory,
                                                         #filename)),
                            #os.path.abspath(os.path.join(self.backup_directory,
                                                         #filename)))
            #abs_filenames.append(abs_filename)
        failed = copy_files_from_a_to_b(self.source_directory,
                                        self.backup_directory,
                                        filenames,
                                        overwrite=overwrite)
        return failed

    def copy_added_file(self, filename):
        """Copy one file from added_files list to backup folder."""
        failed = self.copy_files_from_source_to_backup([filename])
        if failed == []:
            self.report['added_files'].remove(filename)
        return failed

    def copy_added_files(self):
        """Copy files that were added to the source directory.

        Return filenames that were not copied.
        """
        failed = copy_files_from_a_to_b(self.source_directory,
                                        self.backup_directory,
                                        self.report['added_files'])
        self.report['added_files'] = failed
        return failed

    def update_files(self):
        """Update files that were changed it the source directory.

        Return filenames that were not updated.
        """
        return update_files_a_to_b(self.source_directory,
                                   self.backup_directory, self.report['mismatched_files'])

    def delete_files(self):
        """Delete files that were removed from the source directory.

        Return filenames that were not deleted.
        """
        return delete_files_from_b(self.backup_directory,
                                   self.report['removed_files'])

    def move_files(self):
        """Move files that were moved in the source directory.

        Return filenames that were not moved.
        """
        return move_files_in_b(self.report['moved_files'])

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
        self.show_tree('both')
        self.log((self.source_dir_var.get(), self.backup_dir_var.get()), True)

    def log(self, msg, pretty=False):
        """Log messages to the session log file."""
        self.manager.log(msg, pretty)

    def show_tree(self, which):
        """Show directory tree in display pane.

        IN DEVELOPMENT
        """
        if which == 'source':
            #folder = self.source_dir_var.get() # this is just for debug
            display_pane = self.source_field
        elif which == 'backup':
            #folder = self.backup_dir_var.get() # this is just for debug
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
        failed = self.manager.copy_added_file(filename)
        if failed == []:
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
        self.manager.copy_added_files()
        self.display_examined_results()

    def select_file_backup(self, event=None, index=None):
        """Select a file from the changed files list in the backup folder.

        If the file was:
            moved, move it in the backup location.
            deleted, delete it in the backup location.
            changed, copy it from the source location to the backup location.
        """
        logging.debug('Selecting file in backup. event: %s, index: %s', event,
                      index)
        if index is None:
            index = self.backup_field.nearest(event.y)
            logging.debug('Found index: %s', index)
        filename = self.backup_field.get(index)
        # Index order: moved -> mismatched -> removed
        moved_len = len(self.manager.report['moved_files'])
        mis_len = moved_len + len(self.manager.report['mismatched_files'])
        removed_len = mis_len + len(self.manager.report['removed_files'])

        if index < moved_len:
            filename_set = self.manager.report['moved_files'][index]
            failed = move_files_in_b([filename_set])
            if failed == []:
                self.manager.report['moved_files'].remove(filename_set)
                self.backup_field.delete(index)
        elif index < mis_len:
            failed = self.manager.copy_files_from_source_to_backup([filename],
                                                                   overwrite=True
                                                                   )
            if failed == []:
                self.manager.report['mismatched_files'].remove(filename)
                self.backup_field.delete(index)
        elif index < removed_len:
            failed = delete_files_from_b(self.backup_dir_var.get(),
                                         [filename])
            if failed == []:
                self.manager.report['removed_files'].remove(filename)
                self.backup_field.delete(index)

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
                                           initialdir=self.source_dir_var.get())
        dir_name = os.path.normpath(dir_name)
        if dir_name:
            self.source_dir_var.set(dir_name)
            self.manager.source_directory = dir_name
            self.finish_open()

    def open_backup_directory(self):
        """Select a backup directory."""
        dir_name = filedialog.askdirectory(parent=self.master,
                                           title='Open Backup Directory...',
                                           initialdir=self.backup_dir_var.get())
        dir_name = os.path.normpath(dir_name)
        if dir_name:
            self.backup_dir_var.set(dir_name)
            self.manager.backup_directory = dir_name
            self.finish_open()

    def finish_open(self):
        """Clean up after selecting new folder."""
        with open('last_dirs.log', 'w') as log:
            log.write(self.source_dir_var.get()+'\n')
            log.write(self.backup_dir_var.get()+'\n')
        self.show_tree('both')

    def scan(self):
        """Scan the source and backup directories and display results."""
        start = time.time()
        self.manager.report = self.compare_directories().examine()
        self.display_examined_results()
        runtime = time.time()-start
        logging.info('runtime: %d seconds', runtime)
        self.log(self.manager.report, True)

    def compare_directories(self, dira=None, dirb=None, recursing=False):
        """Compare source and backup directories."""
        if not dira:
            dira = self.source_dir_var.get()
        if not dirb:
            dirb = self.backup_dir_var.get()
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
        self.source_field.delete(0, tk.END)
        self.backup_field.delete(0, tk.END)
        for item in self.manager.report['moved_files']:
            self.backup_field.insert(tk.END, item[0]+'-->'+item[1])
            self.backup_field.itemconfig(tk.END, {'bg':'yellow'})
        for item in self.manager.report['mismatched_files']:
            self.backup_field.insert(tk.END, item)
            self.backup_field.itemconfig(tk.END, {'bg':'orange'})
        for item in self.manager.report['added_files']:
            self.source_field.insert(tk.END, item)
            self.source_field.itemconfig(tk.END, {'bg':'green'})
        for item in self.manager.report['removed_files']:
            self.backup_field.insert(tk.END, item)
            self.backup_field.itemconfig(tk.END, {'bg':'red'})
        for item in self.manager.report['errors']:
            logging.error('\nThese files had errors (check manually!):')
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
