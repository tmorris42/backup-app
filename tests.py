#! usr/bin/env python3
"""Tests for backup_app.py."""

import os
import shutil
import unittest
#from unittest.mock import Mock, MagicMock

import tkinter as tk

import backup_app as ba

class TestCopyCreatedFiles(unittest.TestCase):
    """Tests for Copying files found only in the source folder."""
    def setUp(self):
        for fld in ['test_src', 'test_bak']:
            os.makedirs(f'{fld}/subdir/granddir')
        self.root = tk.Tk()
        self.app = ba.App(self.root, 'test_src', 'test_bak')

    def tearDown(self):
        shutil.rmtree('test_src/')
        shutil.rmtree('test_bak/')
        del self.app
        self.root.destroy()

    def test_created_file_selected(self):
        """
        Test that a file selected in the source folder list are removed
        from the display and the report.
        """
        with open(f'test_src/new_file.txt', 'w') as out:
            out.write('this is an added file')
        self.app.scan()
        self.assertEqual(self.app.source_field.get(0, tk.END), ('new_file.txt',))
        self.app.select_file_source(index=0)

        self.assertEqual(self.app.source_field.get(0, tk.END), ())
        self.assertEqual(self.app.examined_report['added_files'], [])

    def test_created_file_multiple_selected(self):
        """
        Test that files selected in the source folder list are removed
        from the display and the report.
        """
        with open(f'test_src/new_file.txt', 'w') as out:
            out.write('this is an added file')
        with open(f'test_src/new_file2.txt', 'w') as out:
            out.write('this is another added file')
        with open(f'test_src/new_file4.txt', 'w') as out:
            out.write('why not three of them')
        self.app.scan()
        self.app.source_field.selection_set(0, 1)
        self.app.copy_selected()
        self.assertEqual(self.app.source_field.get(0, tk.END),
                         ('new_file4.txt',))
        self.assertEqual(self.app.examined_report['added_files'],
                         ['new_file4.txt'])

    def test_copy_to_b(self):
        """
        Test that new files are removed from the display and the report
        when the copy all files button is pressed.
        """
        with open(f'test_src/new_file.txt', 'w') as out:
            out.write('this is an added file')
        with open(f'test_src/new_file2.txt', 'w') as out:
            out.write('this is another added file')
        with open(f'test_src/new_file4.txt', 'w') as out:
            out.write('why not three of them')
        self.app.scan()
        self.assertEqual(self.app.examined_report['added_files'],
                         ['new_file.txt', 'new_file2.txt', 'new_file4.txt'])
        self.assertEqual(self.app.source_field.get(0, tk.END),
                         ('new_file.txt', 'new_file2.txt', 'new_file4.txt'))
        self.app.copy_all_new_files()
        self.assertEqual(self.app.examined_report['added_files'], [])
        self.assertEqual(self.app.source_field.get(0, tk.END), ())


class TestScan(unittest.TestCase):
    """Tests for scanning source and backup folders and finding files."""
    def setUp(self):
        for fld in ['test_src', 'test_bak']:
            os.makedirs(f'{fld}/subdir/granddir')
            with open(f'{fld}/file1.txt', 'w') as out:
                out.write('this is a file')
            with open(f'{fld}/subdir/file2.txt', 'w') as out:
                out.write('this is a second file')
            with open(f'{fld}/subdir/granddir/file3.txt', 'w') as out:
                out.write('this is a third file')
        self.root = tk.Tk()
        self.app = ba.App(self.root, 'test_src', 'test_bak')

    def tearDown(self):
        shutil.rmtree('test_src/')
        shutil.rmtree('test_bak/')
        del self.app
        self.root.destroy()

    def test_no_differences(self):
        """
        Test that files identical folders result in all files matched in them
        report.
        """
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
        """
        Test that a created file will be put under 'added_files' in the
        report.
        """
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

    def test_multiple_new_files(self):
        """
        Test that multiple created files will all be put under 'added_files'
        in the report.
        """
        with open(f'test_src/new_file.txt', 'w') as out:
            out.write('this is an added file')
        with open(f'test_src/new_file2.txt', 'w') as out:
            out.write('this is another added file')
        with open(f'test_src/new_file4.txt', 'w') as out:
            out.write('why not three of them')
        self.app.scan()
        self.assertEqual(self.app.examined_report['added_files'],
                         ['new_file.txt', 'new_file2.txt', 'new_file4.txt'])

    def test_new_file_subdir(self):
        """
        Test that a created file in a subdirectory will be put under
        'added_files' in the report.
        """
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
        """
        Test that a modified file will be put under 'mismatched_files' in the
        report.
        """
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
        """
        Test that a moved file will be put under 'moved_files' in the
        report.
        """
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

    @unittest.skip('Known Bug')
    def test_multiple_copies_moved_file(self):
        """
        Test that a file that was duplicated doesn't cause errors and
        is reported as added_files with 1 moved file.
        """
        shutil.copy('test_src/file1.txt', 'test_src/file1a.txt')
        shutil.copy('test_src/file1.txt', 'test_src/file1b.txt')
        shutil.copy('test_src/file1.txt', 'test_src/file1c.txt')
        shutil.move('test_src/file1.txt', 'test_src/subdir/file1.txt')
        self.app.scan()
        self.assertEqual(self.app.examined_report.items,
                         {
                             'added_files': ['file1a.txt', 'file1b.txt',
                                             'file1c.txt'],
                             'removed_files': [],
                             'matched_files': ['subdir\\file2.txt',
                                               'subdir\\granddir\\file3.txt'],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [('test_bak\\file1.txt',
                                              'test_bak\\subdir\\file1.txt')],})

    def test_renamed_folder(self):
        """
        Test that a renamed folder will be put under 'moved_files' in the
        report.
        """
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report.items,
                         {
                             'added_files': [],
                             'removed_files': [],
                             'matched_files': ['file1.txt'],
                             'mismatched_files': [],
                             'errors': [],
                             'moved_files': [('test_bak\\subdir', 'test_bak\\newdir')],
                             })

    def test_renamed_folder_with_missing_file(self):
        """
        Test that a renamed folder and a file moved into it will both be put
        under 'moved_files'.
        """
        shutil.move('test_src/file1.txt', 'test_src/subdir/file1.txt')
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report.items,
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

    @unittest.skip('Feature not yet implemented')
    def test_renamed_folder_with_missing_file_in_subdir(self):
        """
        Test that a renamed folder and a file moved into its subfolder will both
        be put under 'moved_files'.
        """
        shutil.move('test_src/file1.txt', 'test_src/subdir/granddir/file1.txt')
        os.rename('test_src/subdir', 'test_src/newdir')
        self.app.scan()
        self.assertEqual(self.app.examined_report.items,
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
