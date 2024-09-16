import unittest
from unittest.mock import patch, MagicMock
import os
import stat
import tempfile
import shutil
from file_system_analyzer import FileSizeVisitor, PermissionVisitor, FileCategoryVisitor, DirectoryAnalyzer, Directory


class TestFileSizeVisitor(unittest.TestCase):
    def setUp(self):
        self.visitor = FileSizeVisitor(large_file_threshold=500)

    @patch('os.path.getsize')
    def test_visit_file_large_file(self, mock_getsize):
        mock_getsize.return_value = 600
        file = MagicMock()
        file.path = 'large_file.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertEqual(result['total_size'], 600)
        self.assertIn(('large_file.txt', 600), result['large_files'])

    @patch('os.path.getsize')
    def test_visit_file_small_file(self, mock_getsize):
        mock_getsize.return_value = 200
        file = MagicMock()
        file.path = 'small_file.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertEqual(result['total_size'], 200)
        self.assertNotIn(('small_file.txt', 200), result['large_files'])

    @patch('os.path.getsize')
    def test_visit_empty_file(self, mock_getsize):
        mock_getsize.return_value = 0
        file = MagicMock()
        file.path = 'empty_file.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertEqual(result['total_size'], 0)
        self.assertNotIn(('empty_file.txt', 0), result['large_files'])

    @patch('os.path.getsize')
    def test_visit_multiple_large_files(self, mock_getsize):
        mock_getsize.side_effect = [600, 800]
        file1 = MagicMock()
        file1.path = 'large_file1.txt'
        file2 = MagicMock()
        file2.path = 'large_file2.txt'

        self.visitor.visit_file(file1)
        self.visitor.visit_file(file2)

        result = self.visitor.get_result()
        self.assertEqual(result['total_size'], 1400)
        self.assertIn(('large_file1.txt', 600), result['large_files'])
        self.assertIn(('large_file2.txt', 800), result['large_files'])


class TestPermissionVisitor(unittest.TestCase):
    def setUp(self):
        self.visitor = PermissionVisitor()

    @patch('os.stat')
    def test_visit_file_writable(self, mock_stat):
        mock_stat.return_value.st_mode = stat.S_IWOTH
        file = MagicMock()
        file.path = 'writable_file.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertIn('writable_file.txt', result)

    @patch('os.stat')
    def test_visit_file_non_writable(self, mock_stat):
        mock_stat.return_value.st_mode = stat.S_IRUSR
        file = MagicMock()
        file.path = 'non_writable_file.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertNotIn('non_writable_file.txt', result)

    @patch('os.stat')
    def test_visit_files_with_different_permissions(self, mock_stat):
        # Writable
        mock_stat.return_value.st_mode = stat.S_IWOTH
        file_writable = MagicMock()
        file_writable.path = 'writable_file.txt'
        self.visitor.visit_file(file_writable)

        # Non-writable
        mock_stat.return_value.st_mode = stat.S_IRUSR
        file_non_writable = MagicMock()
        file_non_writable.path = 'non_writable_file.txt'
        self.visitor.visit_file(file_non_writable)

        result = self.visitor.get_result()
        self.assertIn('writable_file.txt', result)
        self.assertNotIn('non_writable_file.txt', result)


class TestDirectoryAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and a file inside it
        self.test_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.test_dir, 'file.txt')
        with open(self.file_path, 'w') as f:
            f.write('Test content')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_analyze_single_file(self):
        size_visitor = FileSizeVisitor()
        permission_visitor = PermissionVisitor()
        category_visitor = FileCategoryVisitor()

        analyzer = DirectoryAnalyzer(self.test_dir)
        visitors = [size_visitor, permission_visitor, category_visitor]
        results = analyzer.analyze(visitors)

        self.assertIn('total_size', results['FileSizeVisitor'])
        self.assertEqual(results['FileSizeVisitor']['total_size'], os.path.getsize(self.file_path))

        self.assertIn('Text', results['FileCategoryVisitor'])
        self.assertEqual(results['FileCategoryVisitor']['Text'], 1)

        self.assertEqual(results['PermissionVisitor'], [])


class TestDirectoryAnalyzerNestedDirectories(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(self.sub_dir)
        self.file_path = os.path.join(self.sub_dir, 'file.txt')
        with open(self.file_path, 'w') as f:
            f.write('Test content')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_analyze_nested_directories(self):
        # Test with nested directories
        size_visitor = FileSizeVisitor()
        permission_visitor = PermissionVisitor()
        category_visitor = FileCategoryVisitor()

        analyzer = DirectoryAnalyzer(self.test_dir)
        visitors = [size_visitor, permission_visitor, category_visitor]
        results = analyzer.analyze(visitors)

        self.assertIn('total_size', results['FileSizeVisitor'])
        self.assertEqual(results['FileSizeVisitor']['total_size'], os.path.getsize(self.file_path))

        self.assertIn('Text', results['FileCategoryVisitor'])
        self.assertEqual(results['FileCategoryVisitor']['Text'], 1)

        self.assertEqual(results['PermissionVisitor'], [])


if __name__ == '__main__':
    unittest.main()
