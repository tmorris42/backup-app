#!usr/bin/env python3

import os
import filecmp
import time
import shutil
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

import send2trash

STARTING_DIRECTORY = '.\Demo Source Location'
BACKUP_DIRECTORY = '.\Demo Backup Location'

SHALLOW = True

def showTree(directory):
    rootDir = directory
    for dirName, subdirList, fileList in os.walk(rootDir):
        print('Found directory: {0}'.format(dirName))
        for fname in fileList:
            print('\t{0}'.format(fname))

def copy_files_from_a_to_b(dira,dirb,files,overwrite=False):
    for filename in files:
        old_path = os.path.join(dira,filename)
        new_path = os.path.join(dirb,filename)
##        print('if we were copying right now...')
        if os.path.isdir(old_path):
            if not os.path.exists(new_path):
                print('{0} --> {1}'.format(old_path,new_path))
##                os.mkdir(new_path)
                shutil.copytree(old_path,new_path)
                print('Copied!')
                
        elif os.path.isfile(old_path):
            print('{0} --> {1}'.format(old_path,new_path))
            if os.path.exists(new_path):
                print('File already exists!')
                if overwrite == True:
                    print('Overwriting!')
                    send2trash.send2trash(new_path)
                    shutil.copy2(old_path,new_path)
                    print('Copied!\n')
            else:
                print('{0} --> {1}'.format(old_path,new_path))
                shutil.copy2(old_path,new_path)
                print('Copied!')
        else:
            print('{0} --> {1}'.format(old_path,new_path))
            print("Error! No file found!")
    print('done copying files')
                

def delete_files_from_b(dirb, files):
    for filepath in files:
        path = os.path.join(dirb,filepath)
        print("deleting {0}".format(path))
        print(path := os.path.normpath(path))
        send2trash.send2trash(path)
    print("Done deleting")

def move_files_in_b(dirb, file_sets):
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
##        dest = os.path.sep.join(dest[0:-1])
        dest = os.path.sep.join(dest)
##        move_file_from_a_to_b(src,dest,fn_src)
        print('moving FROM:\n',src,'\nTO:\n',dest,'\n\n\n')
        shutil.move(src,dest)
    print('done moving')        
    
def update_files_a_to_b(dira,dirb,files):
    copy_files_from_a_to_b(dira,dirb,files,overwrite=True)
    print("Done updating")

def make_changes(dira,dirb,report):
    if len(report['moved_files']) > 0:
        goto = input('Move Files? Y/N')
        if goto in ('y','Y','yes','Yes','YES'):
            move_files_in_b(dirb,report['moved_files'])
            return "recheck"
    if len(report['added_files']) > 0:
        goto = input('Copy New Files? Y/N')
        if goto in ('y','Y','yes','Yes','YES'):
            copy_files_from_a_to_b(dira,dirb,report['added_files'])
    if len(report['removed_files']) > 0:
        goto = input('Delete Old Files? Y/N')
        if goto in ('y','Y','yes','Yes','YES'):
            delete_files_from_b(dirb,report['removed_files'])    
    if len(report['mismatched_files']) > 0:
        goto = input('Update Changed Files? Y/N')
        if goto in ('y','Y','yes','Yes','YES'):
            update_files_a_to_b(dira,dirb,report['mismatched_files'])
    return "quit"


class App(object):
    def __init__(self, master, srcdir, bakdir):
        self.master = master
        self.source_dir = srcdir
        self.sourceDirVar = tk.StringVar()
        self.backup_dir = bakdir
        self.backupDirVar = tk.StringVar()
        self.refresh_directory_variables()
        self.make_window()
        self.examined_report=dict()

        self.show_tree('both')

    def show_tree(self,which):
        if which == 'source':
            folder = self.source_dir
            displayPane = self.source_field
        elif which == 'backup':
            folder = self.backup_dir
            displayPane = self.backup_field
        elif which == 'both':
            self.show_tree('source')
            self.show_tree('backup')
            return
        
##        showTree(folder) # this is just for debug

        ### change this to only display current folder
        # display file contents in source display
        displayPane.delete(0,tk.END)
##        level=0
##        for dirName, subdirList, fileList in os.walk(folder):
##            level += 1
##            displayPane.insert(tk.END,'__'*(level-1)+dirName)
##            for sub in fileList:
##                displayPane.insert(tk.END,'_'*level+sub)

    def select_file_source(self, event=None, index=None):
        if not index:
            index = self.source_field.nearest(event.y)
        #selected = self.displayEntries[index]
        filename = self.source_field.get(index)
        copy_files_from_a_to_b(self.source_dir,self.backup_dir,[filename])
        self.source_field.delete(index)
        
    def copy_selected(self):
        items = map(int, self.source_field.curselection())
        to_delete = []
        for item in items:
            #print(f"{item}: {self.source_field.get(item)}")
            filename = self.source_field.get(item)
            copy_files_from_a_to_b(self.source_dir,self.backup_dir,[filename])
            to_delete.append(item)
        to_delete.sort(reverse=True)
        for item in to_delete:
            self.source_field.delete(item)
    
    def select_file_backup(self, event):
        print(event.y)

    def make_window(self):
        self.master.winfo_toplevel().title("Backup Master")
        self.filebar = tk.Menu(self.master)
        self.filemenu = tk.Menu(self.filebar,tearoff=0)
        self.filebar.add_cascade(label="File", menu=self.filemenu)

        self.source_field = tk.Listbox(self.master,width=60,selectmode=tk.EXTENDED)
        self.backup_field = tk.Listbox(self.master,width=60)

        bw=20 #button width
        self.scanButton = tk.Button(self.master,text="Scan",command=self.scan,width=bw)
        self.moveButton = tk.Button(self.master,text="Move in Backup",command=lambda: move_files_in_b(self.backup_dir,self.examined_report['moved_files']),width=bw)
        self.copyButton = tk.Button(self.master,text="Copy to Backup",command=lambda: copy_files_from_a_to_b(self.source_dir,self.backup_dir,self.examined_report['added_files']),width=bw)
        self.copySelectedButton = tk.Button(self.master,text="Copy Selected to Backup",command=self.copy_selected,width=bw)
        self.removeButton = tk.Button(self.master,text="Remove from Backup",command=lambda: delete_files_from_b(self.backup_dir,self.examined_report['removed_files']),width=bw)
        self.updateButton = tk.Button(self.master,text="Update in Backup",command=lambda: update_files_a_to_b(self.source_dir,self.backup_dir,self.examined_report['mismatched_files']),width=bw)
        self.prog_det = tk.IntVar(self.master)
        self.progressbar = ttk.Progressbar(self.master, mode="determinate", variable=self.prog_det, maximum=100)     # testing progress bar capabillities
        
        self.source_field.grid(row=1,column=0,rowspan=7,columnspan=2,sticky='nsew')
        self.scanButton.grid(row=1,column=2)
        self.moveButton.grid(row=2,column=2)
        self.copyButton.grid(row=3,column=2)
        self.copySelectedButton.grid(row=4,column=2)
        self.removeButton.grid(row=5,column=2)
        self.updateButton.grid(row=6,column=2)
        self.progressbar.grid(row=7,column=2, sticky='new')
        self.backup_field.grid(row=1,column=3,rowspan=7,columnspan=2,sticky='nsew')

        self.sourceButton = tk.Button(self.master,text="Open Source Folder",command=self.opensource)
        self.sourceLocViewer = tk.Entry(self.master, textvariable=self.sourceDirVar,state="readonly")
        self.sourceButton.grid(row=0,column=0,sticky='nsew')
        self.sourceLocViewer.grid(row=0,column=1,sticky='nsew')

        self.backupButton = tk.Button(self.master,text="Open Backup Folder",command=self.openbackup)
        self.backupLocViewer = tk.Entry(self.master, textvariable=self.backupDirVar,state="readonly")
        self.backupButton.grid(row=0,column=3,sticky='nsew')
        self.backupLocViewer.grid(row=0,column=4,sticky='nsew')

        self.master.rowconfigure(6, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(4, weight=1)
                              
        self.master.config(menu=self.filebar)
        
        self.source_field.bind("<Double-Button-1>", self.select_file_source)
        self.backup_field.bind("<Double-Button-1>", self.select_file_backup)

    def opensource(self):
        file = filedialog.askdirectory(parent=self.master,title='Open Source Directory...',initialdir=self.source_dir)
        if file:
            self.source_dir = file
            self.finishopen()

    def openbackup(self):
        file = filedialog.askdirectory(parent=self.master,title='Open Backup Directory...',initialdir=self.backup_dir)
        if file:
            self.backup_dir = file
            self.finishopen()

    def finishopen(self):
        self.refresh_directory_variables()
        with open('log.txt','w') as file:
            file.write(self.source_dir+'\n')
            file.write(self.backup_dir+'\n')
        self.show_tree('both')
        
    def refresh_directory_variables(self):
        self.sourceDirVar.set(self.source_dir)
        self.backupDirVar.set(self.backup_dir)
        
    def scan(self):
        start = time.time()
        self.prog_det.set(0)
        self.progressbar.configure(mode="indeterminate",maximum=100)
        report = self.compareDirectories(self.source_dir,self.backup_dir)
        self.examined_report = self.examineReport(report)
        self.displayExaminedResults()
        runtime = time.time()-start
        self.prog_det.set( self.progressbar.cget('maximum') )
        print('\nruntime: {0} seconds'.format(runtime))

    def compareDirectories(self,dira,dirb,recursing=False):
        self.progressbar.step()
        simple_report = {}
        #compare directories (This uses shallow comparison!!)
        dirs_cmp = filecmp.dircmp(dira,dirb)
        # Identify files that are only in dira
        simple_report['added_files'] = [x for x in dirs_cmp.left_only]
        # Identify files that are only in dirb
        simple_report['removed_files'] = [x for x in dirs_cmp.right_only]
        # For files in both, do a deep comparison using filecmp
        (simple_report['matched_files'], simple_report['mismatched_files'], simple_report['errors']) = filecmp.cmpfiles(dira,dirb,dirs_cmp.common_files, shallow=SHALLOW)

##        self.progressbar.config(maximum=len(dirs_cmp.common_dirs)+1)
        # Check subfolders
        for common_dir in dirs_cmp.common_dirs:
            self.progressbar.step()
            new_dira = os.path.join(dira, common_dir)
            new_dirb = os.path.join(dirb, common_dir)
            sub_report = self.compareDirectories(new_dira,new_dirb,recursing=True)
            if not recursing:
                print('Checking subfolder {0}'.format(new_dira))

            #add sub report to overall report
            for item in sub_report['added_files']:
                simple_report['added_files'].append(os.path.join(common_dir,item))
            for item in sub_report['removed_files']:
                simple_report['removed_files'].append(os.path.join(common_dir,item))
            for item in sub_report['matched_files']:
                simple_report['matched_files'].append(os.path.join(common_dir,item))
            for item in sub_report['mismatched_files']:
                simple_report['mismatched_files'].append(os.path.join(common_dir,item))
            for item in sub_report['errors']:
                simple_report['errors'].append(os.path.join(common_dir,item))

    ##    for adir in dirs_cmp.left_only:
    ##        if os.path.isdir(adir):
    ##            for sub in [x[0] for x in os.walk(adir)]:
    ##                simple_report['added_files'].append(sub)

        return simple_report

    def displayExaminedResults(self):
        same = self.examined_report['matched_files']
        diff = self.examined_report['mismatched_files']
        aonly = self.examined_report['added_files']
        bonly = self.examined_report['removed_files']
        errors = self.examined_report['errors']
        moved = self.examined_report['moved_files']

        self.source_field.delete(0,tk.END)
        self.backup_field.delete(0,tk.END)
        if diff == aonly == bonly == errors == moved == []:
            print('\nNo Changes Detected!')
        else:
            if moved != []:
##                print('\nThese files have moved:')
                for item in moved:
##                    print(item[0],'-->',item[1])
                    self.backup_field.insert(tk.END,item[0]+'-->'+item[1])
                    self.backup_field.itemconfig(tk.END, {'bg':'yellow'})
            if diff != []:
##                print('\nThese files have changed:')
                for item in diff:
##                    print(item)
                    self.backup_field.insert(tk.END,item)
                    self.backup_field.itemconfig(tk.END, {'bg':'orange'})
            if aonly != []:
##                print('\nThese files are new or moved:')
                for item in aonly:
##                    print(item)
                    self.source_field.insert(tk.END,item)
                    self.source_field.itemconfig(tk.END, {'bg':'green'})
            if bonly != []:
##                print('\nThese files have been deleted or moved:')
                for item in bonly:
##                    print(item)
                    self.backup_field.insert(tk.END,item)
                    self.backup_field.itemconfig(tk.END, {'bg':'red'})
            if errors != []:
                print('\nThese files had errors (check manually!):')
                for item in errors:
                    print(item)

    def examineReport(self,report):
        dira = self.source_dir
        dirb = self.backup_dir
        examinedReport = report
        aonly = report['added_files']
        bonly = report['removed_files']
        moved = []

        # for every file that's only in a, compare to files only in b
        self.progressbar.config(maximum=len(aonly)+1)
        self.prog_det.set(0)
        for i,added in enumerate(aonly):
            self.progressbar.step()
            new_file = os.path.join(dira,added)
            # if file is a file, check for identical files
            if os.path.isfile(new_file):
                for j,removed in enumerate(bonly):
                    old_file = os.path.join(dirb,removed)
                    if os.path.isfile(old_file):
                        if filecmp.cmp(new_file, old_file, shallow=False):
                            old_path = os.path.join(dirb,bonly[j])
                            new_path = os.path.join(dirb,aonly[i])
                            moved.append((old_path,new_path))
                            del aonly[i]
                            del bonly[j]
            # If file is a dir, check for similar dirs
            elif os.path.isdir(new_file):
                for j,removed in enumerate(bonly):
                    old_file = os.path.join(dirb,removed)
                    if os.path.isdir(old_file):
                        report = filecmp.dircmp(new_file, old_file)
                        if len(report.common) > (len(report.left_only) + len(report.right_only)):
                            old_path = os.path.join(dirb,bonly[j])
                            new_path = os.path.join(dirb,aonly[i])
                            moved.append((old_path,new_path))
                            del aonly[i]
                            del bonly[j]
        self.prog_det.set( self.progressbar.cget('maximum') )

        examinedReport['moved_files'] = moved
        return examinedReport

if __name__ == '__main__':
    directories = []
    with open('log.txt','r') as file:
        for line in file:
            directories.append(line)

    STARTING_DIRECTORY, BACKUP_DIRECTORY = directories[0][0:-1], directories[1][0:-1]
    print(STARTING_DIRECTORY, BACKUP_DIRECTORY)

    root = tk.Tk()
    app = App(root, STARTING_DIRECTORY, BACKUP_DIRECTORY)
    root.mainloop()
    
##    examined_report = scan(STARTING_DIRECTORY, BACKUP_DIRECTORY)

    
##    next_act = "start"
##    while next_act != "quit":
##        if next_act == "start":
##            next_act = make_changes(STARTING_DIRECTORY,BACKUP_DIRECTORY,examined_report)
##            next_act = "recheck"
##        elif next_act == "recheck":
##            examined_report = examineReport(STARTING_DIRECTORY, BACKUP_DIRECTORY,examined_report)
##            next_act = "start"
##        force_quit = input("type q to quit!")
##        if force_quit == "q":
##            next_act = "quit"
    
