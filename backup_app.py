#! usr/bin/env python3

import os
import filecmp
import time
import shutil
import send2trash
import tkinter as tk

#### If a directory is created/deleted check to see if the contents of the new dir
#### matches the contents of the deleted one

STARTING_DIRECTORY = '.\Demo Source Location'
BACKUP_DIRECTORY = '.\Demo Backup Location'

##STARTING_DIRECTORY = 'C:\\Users\\HeeHe\\Music'
##BACKUP_DIRECTORY = 'F:\\2017-06-28 Toshiba\\_Media\\_Music'

##STARTING_DIRECTORY = 'C:\\Users\\HeeHe\\Documents\\_THM\\For External Backup'
##BACKUP_DIRECTORY = 'E:\\2017-06-28 Toshiba'
##
####STARTING_DIRECTORY = 'C:\\Users\\HeeHe\\Documents\\_THM\\For External Backup\\_Media\\_Music'
####BACKUP_DIRECTORY = 'C:\\Users\\HeeHe\\Music'
##
##STARTING_DIRECTORY = 'C:\\Users\\HeeHe\\Documents\\_THM\\For External Backup'
##BACKUP_DIRECTORY = 'E:\\2017-08-08 - Backup'

SHALLOW = True

def showTree(directory):
    rootDir = directory
    for dirName, subdirList, fileList in os.walk(rootDir):
        print('Found directory: {0}'.format(dirName))
        for fname in fileList:
            print('\t{0}'.format(fname))

def compareDirectories(dira,dirb,recursing=False):
    simple_report = {}
    #compare directories (This uses shallow comparison!!)
    dirs_cmp = filecmp.dircmp(dira,dirb)
    # Identify files that are only in dira
    simple_report['added_files'] = [x for x in dirs_cmp.left_only]
    # Identify files that are only in dirb
    simple_report['removed_files'] = [x for x in dirs_cmp.right_only]
    # For files in both, do a deep comparison using filecmp
    (simple_report['matched_files'], simple_report['mismatched_files'], simple_report['errors']) = filecmp.cmpfiles(dira,dirb,dirs_cmp.common_files, shallow=SHALLOW)

    # Check subfolders
    for common_dir in dirs_cmp.common_dirs:
        new_dira = os.path.join(dira, common_dir)
        new_dirb = os.path.join(dirb, common_dir)
        sub_report = compareDirectories(new_dira,new_dirb,recursing=True)
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

    return simple_report

def copy_files_from_a_to_b(dira,dirb,files,overwrite=False):
    for filename in files:
        old_path = os.path.join(dira,filename)
        new_path = os.path.join(dirb,filename)
##        print('if we were copying right now...')
        if os.path.isdir(old_path):
            if not os.path.exists(new_path):
                print('{0} --> {1}'.format(old_path,new_path))
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
                

def delete_files_from_b(dirb, files):
    for filepath in files:
        path = os.path.join(dirb,filepath)
        print("deleting {0}".format(path))
        send2trash.send2trash(path)

def move_files_in_b(dirb, file_sets):
    for file_set in file_sets:
        src = file_set[0]
        dest = file_set[1].split(os.path.sep)
        dest = os.path.sep.join(dest[0:-1])
##        move_file_from_a_to_b(src,dest,fn_src)
        shutil.move(src,dest)
    
def update_files_a_to_b(dira,dirb,files):
    copy_files_from_a_to_b(dira,dirb,files,overwrite=True)

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

    def make_window(self):
        self.master.winfo_toplevel().title("Backup Master")
        self.filebar = tk.Menu(self.master)
        self.filemenu = tk.Menu(self.filebar,tearoff=0)
        self.filebar.add_cascade(label="File", menu=self.filemenu)

        self.mid_section = tk.Frame(self.master)
        self.top_section = tk.Frame(self.master)
        self.source_field = tk.Listbox(self.mid_section,width=25)
        self.backup_field = tk.Listbox(self.mid_section,width=25)

        self.buttons = tk.Frame(self.mid_section)
        bw=20 #button width
        self.scanButton = tk.Button(self.buttons,text="Scan",command=self.scan,width=bw)
        self.moveButton = tk.Button(self.buttons,text="Move in Backup",command=lambda: move_files_in_b(self.backup_dir,self.examined_report['moved_files']),width=bw)
        self.copyButton = tk.Button(self.buttons,text="Copy to Backup",command=lambda: copy_files_from_a_to_b(self.source_dir,self.backup_dir,self.examined_report['added_files']),width=bw)
        self.removeButton = tk.Button(self.buttons,text="Remove from Backup",command=lambda: delete_files_from_b(self.backup_dir,self.examined_report['removed_files']),width=bw)
        self.updateButton = tk.Button(self.buttons,text="Update in Backup",command=lambda: update_files_a_to_b(self.source_dir,self.backup_dir,self.examined_report['mismatched_files']),width=bw)

        self.source_field.pack(side=tk.LEFT)
        self.scanButton.pack()
        self.moveButton.pack()
        self.copyButton.pack()
        self.removeButton.pack()
        self.updateButton.pack()
        self.buttons.pack(side=tk.LEFT)
        self.backup_field.pack(side=tk.LEFT)

        self.sourceButton = tk.Button(self.top_section,text="Open Source Folder",command=self.opensource)
        self.sourceLocViewer = tk.Entry(self.top_section, textvariable=self.sourceDirVar,state="readonly")
        self.sourceButton.pack(side=tk.LEFT)
        self.sourceLocViewer.pack(side=tk.LEFT)

        self.top_section.pack(side=tk.TOP)
        self.mid_section.pack(side=tk.TOP)

        self.master.config(menu=self.filebar)

    def opensource(self):
        file = tk.filedialog.askdirectory(parent=self.master,title='Open Source Directory...')
        self.source_dir = file
        self.refresh_directory_variables()

    def refresh_directory_variables(self):
        self.sourceDirVar.set(self.source_dir)
        self.backupDirVar.set(self.backup_dir)
        
    def scan(self):
        start = time.time()
        report = compareDirectories(self.source_dir,self.backup_dir)
        self.examined_report = self.examineReport(report)
        self.displayExaminedResults()
        runtime = time.time()-start
        print('\nruntime: {0} seconds'.format(runtime))

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
                print('\nThese files have moved:')
                for item in moved:
                    print(item[0],'-->',item[1])
                    self.backup_field.insert(tk.END,item[0]+'-->'+item[1])
            if diff != []:
                print('\nThese files have changed:')
                for item in diff:
                    print(item)
                    self.backup_field.insert(tk.END,item)
            if aonly != []:
                print('\nThese files are new or moved:')
                for item in aonly:
                    print(item)
                    self.backup_field.insert(tk.END,item)
            if bonly != []:
                print('\nThese files have been deleted or moved:')
                for item in bonly:
                    print(item)
                    self.backup_field.insert(tk.END,item)
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
        
        for i,added in enumerate(aonly):
            new_file = os.path.join(dira,added)
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
            elif os.path.isdir(new_file):
                for j,removed in enumerate(bonly):
                    old_file = os.path.join(dirb,removed)
                    if os.path.isdir(old_file):
                        if added == removed:
                            old_path = os.path.join(dirb,bonly[j])
                            new_path = os.path.join(dirb,aonly[i])
                            moved.append((old_path,new_path))
                            del aonly[i]
                            del bonly[j]

        examinedReport['moved_files'] = moved
        return examinedReport

if __name__ == '__main__':

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
    
