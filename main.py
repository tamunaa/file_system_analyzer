import os
import mimetypes
import stat
import logging
import argparse
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class FileVisitor:
    def visit_file(self, file):
        raise NotImplementedError("visit_file not implemented")

    def visit_directory(self, directory):
        raise NotImplementedError("visit_directory not implemented")

    def get_result(self):
        raise NotImplementedError("get_result not implemented")


class FileSizeVisitor(FileVisitor):
    def __init__(self, large_file_threshold=1000000):  # default threshold: 100 MB
        self.file_sizes = {}
        self.total_size = 0
        self.large_files = []
        self.large_file_threshold = large_file_threshold

    def visit_file(self, file):
        try:
            size = os.path.getsize(file.path)
            self.file_sizes[file.path] = size
            self.total_size += size

            if size > self.large_file_threshold:
                self.large_files.append((file.path, size))
        except OSError as e:
            logging.error(f"Error reading size of {file.path}: {e}")

    def visit_directory(self, directory):
        pass

    def get_result(self):
        return {
            'total_size': self.total_size,
            # 'file_sizes': self.file_sizes,
            'large_files': self.large_files
        }


class PermissionVisitor(FileVisitor):
    def __init__(self):
        self.writable_files = []

    def visit_file(self, file):
        try:
            if os.stat(file.path).st_mode & stat.S_IWOTH:
                self.writable_files.append(file.path)
        except OSError as e:
            logging.error(f"Error checking permissions of {file.path}: {e}")

    def visit_directory(self, directory):
        pass

    def get_result(self):
        return self.writable_files


class FileCategoryVisitor(FileVisitor):
    def __init__(self):
        self.file_categories = {}

    def visit_file(self, file):
        try:
            mime_type, _ = mimetypes.guess_type(file.path)
            if mime_type:
                if mime_type.startswith('text'):
                    category = 'Text'
                elif mime_type.startswith('image'):
                    category = 'Image'
                elif mime_type.startswith('video'):
                    category = 'Video'
                elif mime_type.startswith('application') and 'executable' in mime_type:
                    category = 'Executable'
                else:
                    category = 'Other'
            else:
                _, file_extension = os.path.splitext(file.path)
                category = file_extension[1:].capitalize() if file_extension else 'Unknown'

            if category not in self.file_categories:
                self.file_categories[category] = 0
            self.file_categories[category] += 1
        except OSError as e:
            logging.error(f"Error checking category of {file.path}: {e}")

    def visit_directory(self, directory):
        pass

    def get_result(self):
        return self.file_categories


class FileSystemElement:
    def accept(self, visitor):
        raise NotImplementedError("accept not implemented")


class File(FileSystemElement):
    def __init__(self, path):
        self.path = path

    def accept(self, visitor):
        visitor.visit_file(self)


class Directory(FileSystemElement):
    def __init__(self, path):
        self.path = path
        self.contents = []

    def accept(self, visitor):
        visitor.visit_directory(self)
        for element in self.contents:
            element.accept(visitor)

    def add_content(self, element):
        self.contents.append(element)


class DirectoryAnalyzer:
    def __init__(self, directory_path):
        if not os.path.isdir(directory_path):
            raise ValueError(f"Provided path is not a valid directory: {directory_path}")
        self.root_directory = Directory(directory_path)
        self._build_directory_structure(self.root_directory)

    def _build_directory_structure(self, directory):
        for entry in os.scandir(directory.path):
            if entry.is_file():
                directory.add_content(File(entry.path))
            elif entry.is_dir():
                sub_dir = Directory(entry.path)
                directory.add_content(sub_dir)
                self._build_directory_structure(sub_dir)

    def analyze(self, visitors: List[FileVisitor]) -> Dict[str, dict]:
        results = {}
        for visitor in visitors:
            visitor_result = self.root_directory.accept(visitor)
            results[visitor.__class__.__name__] = visitor.get_result()
        return results

def log_analysis_results(results: Dict[str, dict]):
    logging.info("Analysis Results:")

    # FileSizeVisitor results
    size_results = results.get('FileSizeVisitor', {})
    logging.info(f"Total Size: {size_results.get('total_size', 0)} bytes")
    large_files = size_results.get('large_files', [])
    if large_files:
        logging.info("Large Files:")
        for file_path, size in large_files:
            logging.info(f"  {file_path}: {size} bytes")
    else:
        logging.info("No large files detected.")

    # PermissionVisitor results
    permission_results = results.get('PermissionVisitor', [])
    if permission_results:
        logging.info("Writable Files:")
        for file_path in permission_results:
            logging.info(f"  {file_path}")
    else:
        logging.info("No writable files detected.")

    # FileCategoryVisitor results
    category_results = results.get('FileCategoryVisitor', {})
    logging.info("File Categories:")
    for category, count in category_results.items():
        logging.info(f"  {category}: {count} files")


def main(directory_to_analyze: str):
    try:
        analyzer = DirectoryAnalyzer(directory_to_analyze)
    except ValueError as e:
        logging.error(e)
        exit(1)

    size_visitor = FileSizeVisitor(large_file_threshold=50000000)  # Set threshold to 50 MB
    permission_visitor = PermissionVisitor()
    category_visitor = FileCategoryVisitor()

    visitors = [size_visitor, permission_visitor, category_visitor]
    results = analyzer.analyze(visitors)

    log_analysis_results(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze file system directory.")
    parser.add_argument("path", type=str, help="Path to the directory to analyze")
    args = parser.parse_args()

    main(args.path)