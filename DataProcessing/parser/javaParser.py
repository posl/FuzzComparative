import tree_sitter_java
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Dict, Any
import json

class JavaParser:
    def __init__(self):
        """Initialize Java parser with tree-sitter"""
        self.JAVA_LANGUAGE = Language(tree_sitter_java.language())
        self.parser = Parser(self.JAVA_LANGUAGE)
        
        # Common test file patterns in Java projects
        self.test_patterns = [
            'Test.java',
            'Tests.java',
            'IT.java',     # Integration Tests
            'TestCase.java',
            'Spec.java'    # Specification Tests
        ]

    def find_test_files(self, project_path: str) -> List[str]:
        """Find all Java test files in the project directory
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of paths to test files
        """
        test_files = []
        project_path = Path(project_path)

        if not project_path.exists():
            print(f"Warning: Project path {project_path} does not exist")
            return []

        # Walk through all .java files in the directory
        for java_file in project_path.rglob("*.java"):
            file_path = str(java_file)
            # Check if file matches any test pattern or is in test directory
            if (any(pattern in file_path for pattern in self.test_patterns) or
                '/test/' in file_path.lower() or
                '/tests/' in file_path.lower()):
                test_files.append(file_path)

        if not test_files:
            print(f"Warning: No test files found in {project_path}")
        
        return test_files

    def get_code_from_file(self, filepath: str) -> str:
        """Read file content"""
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    def get_node_text(self, node, source_code) -> str:
        """Extract text from a node"""
        return source_code[node.start_byte:node.end_byte].decode("utf8")

    def extract_function_info(self, node, source_code) -> List[Dict]:
        """Extract information about methods in the code"""
        methods = []
        
        def traverse(node):
            if node.type == "method_declaration":
                # Extract method details
                method_name = ""
                parameters = ""
                is_fuzz = False
                
                # Check annotations for @FuzzTest or similar
                for child in node.children:
                    if child.type == "marker_annotation" and "Fuzz" in self.get_node_text(child, source_code):
                        is_fuzz = True
                    if child.type == "identifier":
                        method_name = self.get_node_text(child, source_code)
                    elif child.type == "formal_parameters":
                        parameters = self.get_node_text(child, source_code)
                
                # Also check method name for fuzz patterns
                if ("fuzz" in method_name.lower() or 
                    "fuzzing" in method_name.lower() or
                    "fuzzer" in method_name.lower()):
                    is_fuzz = True
                
                if is_fuzz:
                    methods.append({
                        "method_name": method_name,
                        "start_line": node.start_point[0],
                        "end_line": node.end_point[0],
                        "total_lines": node.end_point[0] - node.start_point[0] + 1,
                        "params": parameters,
                        "is_fuzz": is_fuzz
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return methods

    def extract_import_info(self, node, source_code) -> List[Dict]:
        """Extract information about imports in the code"""
        imports = []

        fuzz_patterns = [
            "fuzz",
            "fuzzer",
            "jazzer",     
            "jqf", 
        ]
        
        def traverse(node):
            if node.type == "import_declaration":
                import_path = self.get_node_text(node, source_code)
                
                # Check if it's a fuzz-related import
                is_fuzz_import = any(fuzz_pattern in import_path.lower() 
                               for fuzz_pattern in fuzz_patterns)
                
                imports.append({
                    "import_path": import_path.replace("import ", "").replace(";", "").strip(),
                    "line": node.start_point[0],
                    "is_fuzz_import": is_fuzz_import
                })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return imports

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a Java file and extract all relevant information"""
        code = self.get_code_from_file(file_path)
        tree = self.parser.parse(bytes(code, "utf8"))
        source_bytes = bytes(code, "utf8")

        return {
            'file_path': file_path,
            'methods': self.extract_function_info(tree.root_node, source_bytes),
            'imports': self.extract_import_info(tree.root_node, source_bytes)
        }

    def process_project(self, project_path: str) -> Dict[str, Any] | None:
        """Process all test files in a project
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with parsing results or None if no test files
        """
        test_files = self.find_test_files(project_path)
        
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
        
        project_name = Path(project_path).name
            
        return {
            'project_info': {
                'name': project_name,
                'path': project_path,
                'total_test_files': len(test_files),
                'test_files': test_files
            },
            'parsing_results': results
        }

# Example usage
if __name__ == "__main__":
    java_parser = JavaParser()
    project_path = "/Users/zhang/FuzzComparative/bcgit-bc-java"
    result = java_parser.process_project(project_path)
    
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