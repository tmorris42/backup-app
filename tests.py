import os
import shutil
import unittest

import tkinter as tk

import backup_app as ba

class TestCmpDirIdenticalTree(unittest.TestCase):
    def setUp(self):
        for d in ['test_src', 'test_bak']:
            os.makedirs(f'{d}/subdir/granddir')
            with open(f'{d}/file1.txt', 'w') as out:
                out.write('this is a file')
            with open(f'{d}/subdir/file2.txt', 'w') as out:
                out.write('this is a second file')
            with open(f'{d}/subdir/granddir/file3.txt', 'w') as out:
                out.write('this is a third file')
        
    def tearDown(self):
        shutil.rmtree('test_src/')
        shutil.rmtree('test_bak/')

    def test_no_differences(self):
        root = tk.Tk()
        app = ba.App(root, 'test_src', 'test_bak')
        app.scan()
        self.assertEqual(app.examined_report['matched_files'],
                         ['file1.txt',
                          'subdir\\file2.txt',
                          'subdir\\granddir\\file3.txt'])
        self.assertEqual(app.examined_report['mismatched_files'],
                         [])
        self.assertEqual(app.examined_report['added_files'],
                         [])
        self.assertEqual(app.examined_report['moved_files'],
                         [])
        self.assertEqual(app.examined_report['removed_files'],
                         [])
        self.assertEqual(app.examined_report['errors'],
                         [])

if __name__ == '__main__':
    unittest.main()

    
