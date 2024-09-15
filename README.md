# File System Analyzer

## Overview

The File System Analyzer is a Python application designed to analyze file systems by traversing directories and collecting various types of information about the files and directories. It uses the Visitor design pattern to perform different types of analyses, such as file size, permissions, and file categories. 

## Features

- **File Size Analysis:** Identifies files exceeding a specified size threshold.
- **Permission Analysis:** Detects files with write permissions.
- **File Category Analysis:** Categorizes files based on MIME types or extensions.

## Requirements

- Python 3.x
- Standard Python libraries (`os`, `mimetypes`, `stat`, `logging`, `argparse`, `typing`)

## Components

### Components of the Visitor Pattern

1. **Visitor Interface (`FileVisitor`)**
   - **Purpose:** Defines the interface for visiting elements (files and directories). It declares methods like `visit_file()` and `visit_directory()` which concrete visitors will implement to perform specific operations.
   - **Implementation:** The `FileVisitor` class is an abstract base class with these methods defined as placeholders.

2. **Concrete Visitors**
   - **FileSizeVisitor:** Implements the visitor interface to compute file sizes, identify large files based on a specified threshold, and aggregate these results.
   - **PermissionVisitor:** Checks if files have write permissions and collects these writable files.
   - **FileCategoryVisitor:** Categorizes files based on MIME types or extensions and counts occurrences of each category.

3. **Element Interface (`FileSystemElement`)**
   - **Purpose:** Represents the elements (files and directories) that can be visited by the visitors. It defines the `accept()` method which accepts a visitor.
   - **Implementation:** The `FileSystemElement` class is an abstract base class with the `accept()` method.

4. **Concrete Elements**
   - **File:** Represents a file in the file system and implements the `accept()` method to allow visitors to process the file.
   - **Directory:** Represents a directory and contains other file system elements (files and sub-directories). It implements `accept()` to process itself and recursively visit its contents.

5. **Object Structure (`DirectoryAnalyzer`)**
   - **Purpose:** Manages the traversal of the directory structure and aggregates the results from different visitors.
   - **Implementation:** The `DirectoryAnalyzer` class builds the directory structure and provides a method `analyze()` to apply visitors to the directory tree.

## How It Works

1. **Initialization:**
   - The `DirectoryAnalyzer` initializes with a root directory and builds the entire directory structure using the `File` and `Directory` classes.

2. **Visitor Application:**
   - Different visitor objects (like `FileSizeVisitor`, `PermissionVisitor`, and `FileCategoryVisitor`) are created and passed to the `analyze()` method of `DirectoryAnalyzer`.

3. **Traversal and Analysis:**
   - The `accept()` method in `File` and `Directory` elements is called, which in turn calls the appropriate `visit_file()` or `visit_directory()` method on the visitor. This allows each visitor to perform its specific analysis on each file or directory.

4. **Result Collection:**
   - Each visitor accumulates its results during the traversal. After all visitors have been applied, results are collected and logged or processed as needed.


## Usage

1. **Command-Line Execution**

   To run the analyzer, execute the script from the command line with the path to the directory you want to analyze:

   ```bash
   python your_script_name.py /path/to/directory

