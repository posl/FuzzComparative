import tree_sitter_python
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Dict, Any
import json

class PythonParser:
    def __init__(self):
        """Initialize Python parser with tree-sitter"""
        self.PY_LANGUAGE = Language(tree_sitter_python.language())
        self.parser = Parser(self.PY_LANGUAGE)
        self.test_patterns = ['test_', '_test.py', 'test.py', 'tests.py']      

    def find_test_files(self, project_path: str) -> List[str]:
        """Find all Python test files in the project directory
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of paths to test files
        """
        test_files = []
        project_path = Path(project_path)

        # Check if directory exists
        if not project_path.exists():
            print(f"Warning: Project path {project_path} does not exist")
            return []

        # Walk through all .py files in the directory
        for py_file in project_path.rglob("*.py"):
            file_path = str(py_file)
            # Check if file matches any test pattern or is in test directory
            if (any(pattern in file_path.lower() for pattern in self.test_patterns) or
                '/test/' in file_path.lower() or
                '/tests/' in file_path.lower()):
                test_files.append(file_path)

        if not test_files:
            print(f"Warning: No test files found in {project_path}")
        
        return test_files   

    def process_project(self, project_path: str) -> Dict[str, Any] | None:
        """Process all test files in a project
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with parsing results or None if no test files
        """
        test_files = self.find_test_files(project_path)
        
        # Skip if no test files found
        if not test_files:
            return None
        
        results = []
        for file_path in test_files:
            try:
                parsed_info = self.parse_file(file_path)
                results.append(parsed_info)
            except Exception as e:
                print(f"Error parsing {file_path}: {str(e)}")
                continue
        
        # Get project name from path
        project_name = Path(project_path).name
            
        return {
            'project_info': {
                'name': project_name,
                'path': project_path,
                'total_test_files': len(test_files),
                'test_files': test_files  # List of all test files found
            },
            'parsing_results': results
        }

    def get_code_from_file(self, filepath: str) -> str:
        """Read file content"""
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    def get_node_text(self, node, source_code) -> str:
        """Extract text from a node"""
        return source_code[node.start_byte:node.end_byte].decode("utf8")

    def extract_function_info(self, node, source_code) -> List[Dict]:
        """Extract information about functions in the code"""
        functions = []
        
        def traverse(node):
            if node.type == "function_definition":
                # Extract function details
                function_name = ""
                parameters = ""
                is_fuzz = False

                for child in node.children:
                    if child.type == "identifier":
                        function_name = self.get_node_text(child, source_code)
                    elif child.type == "parameters":
                        parameters = self.get_node_text(child, source_code)
                
                # Calculate line information
                start_line = node.start_point[0]
                end_line = node.end_point[0]
                
                functions.append({
                    "function_name": function_name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "total_lines": end_line - start_line + 1,
                    "params": parameters,
                    "is_fuzz": is_fuzz
                })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return functions

    def extract_import_info(self, node, source_code) -> List[Dict]:
        """Extract information about imports in the code"""
        imports = []

        fuzz_patterns = [
            "hypothesis",   
            "atheris",             
        ]

        is_fuzz_import = False
        
        def traverse(node):
            if node.type == "import_statement":
                # Handle regular imports (import x)
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append({
                            "type": "import",
                            "module": self.get_node_text(child, source_code),
                            "line": node.start_point[0],
                            "is_fuzz_import": is_fuzz_import
                        })
                        
            elif node.type == "import_from_statement":
                # Handle from imports (from x import y)
                module_name = ""
                imported_names = []
                
                for child in node.children:
                    if child.type == "dotted_name":
                        module_name = self.get_node_text(child, source_code)
                    elif child.type == "import_statement":
                        for import_child in child.children:
                            if import_child.type == "dotted_name":
                                imported_names.append(
                                    self.get_node_text(import_child, source_code)
                                )
                
                imports.append({
                    "type": "from_import",
                    "module": module_name,
                    "imported_names": imported_names,
                    "line": node.start_point[0]
                })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return imports

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a Python file and extract all relevant information"""
        code = self.get_code_from_file(file_path)
        tree = self.parser.parse(bytes(code, "utf8"))
        source_bytes = bytes(code, "utf8")

        return {
            'file_path': file_path,
            'functions': self.extract_function_info(tree.root_node, source_bytes),
            'imports': self.extract_import_info(tree.root_node, source_bytes)
        }

# Example usage:
if __name__ == "__main__":
    python_parser = PythonParser()
    project_path = "/Users/zhang/FuzzComparative/xraylarch-master"
    result = python_parser.process_project(project_path)

    if result:
        print("\nProject Information:")
        print(f"Name: {result['project_info']['name']}")
        print(f"Path: {result['project_info']['path']}")
        print(f"Total Test Files: {result['project_info']['total_test_files']}")
        print("\nTest Files Found:")
        for test_file in result['project_info']['test_files']:
            print(f"- {test_file}")
        print("\nDetailed Results:")
        print(json.dumps(result['parsing_results'], indent=2)) 