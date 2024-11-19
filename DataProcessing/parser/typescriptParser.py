import tree_sitter_typescript
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Dict, Any
import json

class TypescriptParser:
    def __init__(self):
        """Initialize TypeScript parser with tree-sitter"""
        self.TS_LANGUAGE = Language(tree_sitter_typescript.language())
        self.parser = Parser(self.TS_LANGUAGE)
        
        self.test_patterns = [
            '.test.ts',
            '.spec.ts',
            'test.ts',
            'tests.ts'
        ]

    def find_test_files(self, project_path: str) -> List[str]:
        """Find all TypeScript test files in the project directory"""
        test_files = []
        project_path = Path(project_path)

        if not project_path.exists():
            return []

        # Walk through all .ts files in the directory
        for ts_file in project_path.rglob("*.ts"):
            file_path = str(ts_file)
            if (any(pattern in file_path.lower() for pattern in self.test_patterns) or
                '/test/' in file_path.lower() or
                '/tests/' in file_path.lower()):
                test_files.append(file_path)

        return test_files

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
            # Check for function declarations and arrow functions
            if node.type in ["function_declaration", "arrow_function", "method_definition"]:
                function_name = ""
                parameters = ""
                statements = []
                
                # Get function details
                for child in node.children:
                    if child.type == "identifier":
                        function_name = self.get_node_text(child, source_code)
                    elif child.type == "formal_parameters":
                        parameters = self.get_node_text(child, source_code)
                    elif child.type == "statement_block":
                        # Get all statements in function body
                        for statement in child.children:
                            stmt_text = self.get_node_text(statement, source_code)
                            if "fuzz" in stmt_text.lower():
                                statements.append(stmt_text)

                # Check if function or its content is fuzz-related
                is_fuzz = (
                    "fuzz" in function_name.lower() or 
                    len(statements) > 0
                )
                
                if is_fuzz:
                    functions.append({
                        "function_name": function_name,
                        "start_line": node.start_point[0],
                        "end_line": node.end_point[0],
                        "total_lines": node.end_point[0] - node.start_point[0] + 1,
                        "params": parameters,
                        "fuzz_statements": statements
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return functions

    def extract_import_info(self, node, source_code) -> List[Dict]:
        """Extract information about imports in the code"""
        imports = []
        
        def traverse(node):
            if node.type == "import_statement":
                import_path = self.get_node_text(node, source_code)
                
                # Check if it's a fuzz-related import
                if "fuzz" in import_path.lower():
                    imports.append({
                        "import_path": import_path.replace('import', '').replace(';', '').strip(),
                        "line": node.start_point[0]
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return imports

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a TypeScript file and extract all relevant information"""
        code = self.get_code_from_file(file_path)
        tree = self.parser.parse(bytes(code, "utf8"))
        source_bytes = bytes(code, "utf8")

        return {
            'file_path': file_path,
            'functions': self.extract_function_info(tree.root_node, source_bytes),
            'imports': self.extract_import_info(tree.root_node, source_bytes)
        }

    def process_project(self, project_path: str) -> Dict[str, Any] | None:
        """Process all test files in a project"""
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
    ts_parser = TypescriptParser()
    project_path = "/path/to/typescript/project"
    result = ts_parser.process_project(project_path)

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