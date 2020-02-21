import os
import shutil
import unittest

import tkinter as tk

import backup_app as ba

class TestScan(unittest.TestCase):
    def setUp(self):
        for d in ['test_src', 'test_bak']:
            os.makedirs(f'{d}/subdir/granddir')
            with open(f'{d}/file1.txt', 'w') as out:
                out.write('this is a file')
            with open(f'{d}/subdir/file2.txt', 'w') as out:
                out.write('this is a second file')
            with open(f'{d}/subdir/granddir/file3.txt', 'w') as out:
                out.write('this is a third file')
        self.root = tk.Tk()
        self.app = ba.App(self.root, 'test_src', 'test_bak')

    def tearDown(self):
        shutil.rmtree('test_src/')
        shutil.rmtree('test_bak/')
        del self.app
        self.root.destroy()

    def test_no_differences(self):
        self.app.scan()
        self.assertEqual(self.app.examined_report['matched_files'],
                         ['file1.txt',
                          'subdir\\file2.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(self.app.examined_report['mismatched_files'],
                         [])
        self.assertEqual(self.app.examined_report['added_files'],
                         [])
        self.assertEqual(self.app.examined_report['moved_files'],
                         [])
        self.assertEqual(self.app.examined_report['removed_files'],
                         [])
        self.assertEqual(self.app.examined_report['errors'],
                         [])

    def test_new_file(self):
        with open(f'test_src/new_file.txt', 'w') as out:
            out.write('this is an added file')
        self.app.scan()
        self.assertEqual(self.app.examined_report['matched_files'],
                         ['file1.txt',
                          'subdir\\file2.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(self.app.examined_report['mismatched_files'],
                         [])
        self.assertEqual(self.app.examined_report['added_files'],
                         ['new_file.txt'])
        self.assertEqual(self.app.examined_report['moved_files'],
                         [])
        self.assertEqual(self.app.examined_report['removed_files'],
                         [])
        self.assertEqual(self.app.examined_report['errors'],
                         [])

    def test_new_file_subdir(self):
        with open(f'test_src/subdir/new_file2.txt', 'w') as out:
            out.write('this is another added file')
        self.app.scan()
        self.assertEqual(self.app.examined_report['matched_files'],
                         ['file1.txt',
                          'subdir\\file2.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(self.app.examined_report['mismatched_files'],
                         [])
        self.assertEqual(self.app.examined_report['added_files'],
                         ['subdir\\new_file2.txt'])
        self.assertEqual(self.app.examined_report['moved_files'],
                         [])
        self.assertEqual(self.app.examined_report['removed_files'],
                         [])
        self.assertEqual(self.app.examined_report['errors'],
                         [])

    def test_changed_file_subdir(self):
        with open(f'test_src/subdir/file2.txt', 'w+') as out:
            out.write('this file changed')
        self.app.scan()
        self.assertEqual(self.app.examined_report['matched_files'],
                         ['file1.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(self.app.examined_report['mismatched_files'],
                         ['subdir\\file2.txt'])
        self.assertEqual(self.app.examined_report['added_files'],
                         [])
        self.assertEqual(self.app.examined_report['moved_files'],
                         [])
        self.assertEqual(self.app.examined_report['removed_files'],
                         [])
        self.assertEqual(self.app.examined_report['errors'],
                         [])

    def test_moved_file(self):
        shutil.move('test_src/file1.txt', 'test_src/subdir/file1.txt')
        self.app.scan()
        self.assertEqual(self.app.examined_report['matched_files'],
                         ['subdir\\file2.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(self.app.examined_report['mismatched_files'],
                         [])
        self.assertEqual(self.app.examined_report['added_files'],
                         [])
        self.assertEqual(self.app.examined_report['moved_files'],
                         [('test_bak\\file1.txt', 'test_bak\\subdir\\file1.txt')])
        self.assertEqual(self.app.examined_report['removed_files'],
                         [])
        self.assertEqual(self.app.examined_report['errors'],
                         [])
        
    def test_multiple_copies_moved_file(self):
        shutil.copy('test_src/file1.txt', 'test_src/file1a.txt')
        shutil.copy('test_src/file1.txt', 'test_src/file1b.txt')
        shutil.copy('test_src/file1.txt', 'test_src/file1c.txt')
        shutil.move('test_src/file1.txt', 'test_src/subdir/file1.txt')
        self.app.scan()
        self.assertEqual(self.app.examined_report,
                         {
                             'added_files': ['file1a.txt', 'file1b.txt',
                                             'file1c.txt'],
                             'removed_files': [],
                             'matched_files': ['subdir\\file2.txt',
                                               'subdir\\granddir\\file3.txt'],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [('test_bak\\file1.txt', 'test_bak\\subdir\\file1.txt')],
                             })
        
    def test_renamed_folder(self):
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report,
                         {
                             'added_files': [],
                             'removed_files': [],
                             'matched_files': ['file1.txt'],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [('test_bak\\subdir', 'test_bak\\newdir')],
                             })
        
    def test_renamed_folder_with_missing_file(self):
        shutil.move('test_src/file1.txt', 'test_src/subdir/file1.txt')
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report,
                         {
                             'added_files': [],
                             'removed_files': [],
                             'matched_files': [],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [
                                 ('test_bak\\subdir', 'test_bak\\newdir'),
                                 ('test_bak\\file1.txt', 'test_bak\\newdir\\file1.txt')],
                             })
                             
    def test_renamed_folder_with_missing_file_in_subdir(self):
        shutil.move('test_src/file1.txt', 'test_src/subdir/granddir/file1.txt')
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report,
                         {
                             'added_files': [],
                             'removed_files': [],
                             'matched_files': [],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [
                                 ('test_bak\\subdir', 'test_bak\\newdir'),
                                 ('test_bak\\file1.txt', 'test_bak\\newdir\\granddir\\file1.txt')],
                             })

if __name__ == '__main__':
    unittest.main()
