# FuzzComparative
Research for current usage of fuzz testing in the OSS community

# Research topic:
I want to study the current usage of fuzz testing in the OSS community by studying projects written by five target languages: Python, Java, Typescript, C++ and C#.

# Approach:
1. Data collection: collecting the lists of 2500 projects per language. (Done)

2. Data processing(for each language): 
2.1 clone one project for the lastest version.
2.2 finding the test files (.py for python, .cpp for c++ etc.)
2.3 using tree-sitter to parse the code of test files, extracting the information like the function and package for anlysising the usage of fuzz testing into a psycopg2 database and delete the project after processing.
2.4 if the test file is not found, skip this project.
2.5 repeat step 2.1 - 2.4 for every version(commit) of the project. Also, record the commit message and the date, and the author of the commit in the database.
2.6 repeat step 2.1 - 2.5 for another project until 2500 projects are processed.

3. Data analysis:
3.1 using pandas to analyse the data in the psycopg2 database

# Code structure:
DataCollection

DataProcessing:
- main.py: the main function
- parser
  - pythonParser.py: the parser for python
  - cppParser.py: the parser for cpp
  - typescriptParser.py: the parser for typescript
  - csharpParser.py: the parser for csharp
  - javaParser.py: the parser for java
- dbFile.py: handles the database
- project_processor.py: the main processing loop  
- commit_processor.py: the commit processor

# Overall Architecture for DataProcessing
- Main Entry Point
  - main.py: handles the overall processing flow
- Parsers
  - pythonParser.py: the parser for python
  - cppParser.py: the parser for cpp
  - typescriptParser.py: the parser for typescript
  - csharpParser.py: the parser for csharp
  - javaParser.py: the parser for java
  - Each parser is responsible for:
    - Finding test files for its language
    - Using tree-sitter to parse code
    - Extracting fuzz testing related information
- Database Handler
  - dbFile.py: handles the database
- Project Processor
  - project_processor.py: the main processing loop
- Commit Processor
  - commit_processor.py: the commit processor
