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


class TestFileCategoryVisitor(unittest.TestCase):
    def setUp(self):
        self.visitor = FileCategoryVisitor()

    @patch('mimetypes.guess_type')
    def test_visit_file_text(self, mock_guess_type):
        mock_guess_type.return_value = ('text/plain', None)
        file = MagicMock()
        file.path = 'document.txt'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertEqual(result['Text'], 1)

    @patch('mimetypes.guess_type')
    def test_visit_file_image(self, mock_guess_type):
        mock_guess_type.return_value = ('image/jpeg', None)
        file = MagicMock()
        file.path = 'photo.jpg'

        self.visitor.visit_file(file)

        result = self.visitor.get_result()
        self.assertEqual(result['Image'], 1)


class TestDirectoryAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and a file inside it
        self.test_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.test_dir, 'file.txt')
        with open(self.file_path, 'w') as f:
            f.write('Test content')

    def tearDown(self):
        # Remove the temporary directory after test
        shutil.rmtree(self.test_dir)

    @patch('os.scandir')
    def test_build_directory_structure(self, mock_scandir):
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.path = self.file_path

        mock_directory = MagicMock()
        mock_directory.is_file.return_value = False
        mock_directory.path = self.test_dir

        mock_scandir.side_effect = [
            [mock_file],
            []
        ]

        analyzer = DirectoryAnalyzer(self.test_dir)

        # Access the root directory and its contents
        root_dir = analyzer.root_directory
        self.assertIsInstance(root_dir, Directory)
        self.assertEqual(len(root_dir.contents), 1)  # Should contain 1 file
        self.assertEqual(root_dir.contents[0].path, self.file_path)


class TestDirectoryAnalyzerNestedDirectories(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure with nested directories
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(self.sub_dir)
        self.file_path = os.path.join(self.sub_dir, 'file.txt')
        with open(self.file_path, 'w') as f:
            f.write('Test content')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('os.scandir')
    def test_build_directory_structure_with_nested_directories(self, mock_scandir):
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.is_dir.return_value = False
        mock_file.path = self.file_path

        mock_subdir = MagicMock()
        mock_subdir.is_file.return_value = False
        mock_subdir.is_dir.return_value = True
        mock_subdir.path = self.sub_dir

        mock_scandir.side_effect = [
            [mock_subdir],  # Root directory contains the sub-directory
            [mock_file]  # Sub-directory contains the file
        ]

        analyzer = DirectoryAnalyzer(self.test_dir)

        root_dir = analyzer.root_directory
        self.assertIsInstance(root_dir, Directory)
        self.assertEqual(len(root_dir.contents), 1)
        self.assertEqual(root_dir.contents[0].path, self.sub_dir)

        subdir_contents = root_dir.contents[0].contents
        self.assertEqual(len(subdir_contents), 1)
        self.assertEqual(subdir_contents[0].path, self.file_path)


if __name__ == '__main__':
    unittest.main()
