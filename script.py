"""
script.py

Python script to run the code in the given directory in Deephaven.

This script looks for either .py files or .md files. If a .py file is found, then its contents are run in Deephaven.
If a .md file is found, the code within the ```python ``` tags is extracted and run in Deephaven.
"""
from pydeephaven import Session, DHError

import sys
import time
import os

PYTHON_START_TAG = "```python"
PYTHON_END_TAG = "```"
PYTHON_EXTENSION = ".py"

GROOVY_START_TAG = "```groovy"
GROOVY_END_TAG = "```"
GROOVY_EXTENSION = ".groovy"

def session_type_to_tags_and_extension(session_type='python'):
    """
    Converts the session type to the markdown start and end tags, and
    the code file extension. Assumes "python" as the default

    Parameters:
        session_type (str): The session type
    Returns:
        tuple: The start tag, end tag, and code extension
    """
    if session_type == 'python':
        return (PYTHON_START_TAG, PYTHON_END_TAG, PYTHON_EXTENSION)
    elif session_type == 'groovy':
        return (GROOVY_START_TAG, GROOVY_END_TAG, GROOVY_EXTENSION)

def read_code_file(file_path):
    """
    Wrapper function to read the full contents of the code file and return a string

    Parameters:
        file_path (str): The path to the code file to read

    Returns:
        str: String representation of the code file contents
    """
    script_string = None
    with open(file_path) as f:
        script_string = f.read()

    return script_string

def read_markdown_file(file_path, start_tag, end_tag):
    """
    Extracts the code scripts between the given tags in the markdown file at the given path, and
    returns them combined as a single string

    Parameters:
        file_path (str): The path to the markdown file
        start_tag (str): The tag to represent the start of a code block
        end_tag (str): The tag to represent the end of a code block

    Returns:
        str: The combined string of code scripts in the markdown file
    """
    scripts = []
    with open(file_path) as f:
        in_script = False
        current_script = None
        for line in f.readlines():
            if (line.startswith(start_tag)) and (not in_script) and (not "skip-test" in line):
                in_script = True
                current_script = ""
            elif (line.startswith(end_tag)) and in_script:
                in_script = False
                scripts.append(current_script)
            elif in_script:
                current_script += line

    return "\n".join(scripts)

def main(directory: str, host: str, port: int, session_type: str, max_retries: int = 5):
    """
    Main method for the script. Reads each file line by line and grabs lines
    between the ```python ``` tags to run in Deephaven.

    Parameters:
        directory (str): The path to the directory containing the files to run
        host (str): The host name of the Deephaven instance
        port (int): The port on the host to access
        session_type (str): The Deephaven session type
        max_retries (int): The maximum attempts to retry connecting to Deephaven. Defaults to 5

    Returns:
        None
    """

    print(f"Attempting to connect to host at {host} on port {port}")

    #Simple retry loop in case the server tries to launch before Deephaven is ready
    count = 0
    session = None
    while (count < max_retries):
        try:
            session = Session(host=host, port=port)#, session_type=session_type) #TODO: uncomment this out when https://github.com/deephaven/deephaven-core/pull/2107 is merged
            print("Connected to Deephaven")
            break
        except DHError as e:
            print("Failed to connect to Deephaven... Waiting to try again")
            print(e)
            time.sleep(5)
            count += 1
        except Exception as e:
            print("Unknown error when connecting to Deephaven... Waiting to try again")
            print(e)
            time.sleep(5)
            count += 1
    if session is None:
        sys.exit(f"Failed to connect to Deephaven after {max_retries} attempts")

    #Grab the markdown tags and code files to look at based on the session type
    (start_tag, end_tag, code_file_extension) = session_type_to_tags_and_extension(session_type)

    #Track file results
    error_files = []
    success_files = []

    for file_path in os.popen(f"find {directory} -type f | sort").read().split("\n"):
        if len(file_path) > 0: #Skip empty paths. Sometimes this pops up with `find` commands
            print(f"Reading file {file_path}")

            #If file should be read, read the code. Otherwise skip the file
            script_string = None
            if file_path.endswith(".md"):
                script_string = read_markdown_file(file_path, start_tag, end_tag)
            elif file_path.endswith(code_file_extension):
                script_string = read_code_file(file_path)
            else:
                print(f"Skipping file {file_path}")
                continue

            if len(script_string) == 0:
                print(f"No code found in {file_path}, skipping")
            else:
                #Code found, run it in Deephaven
                try:
                    session.run_script(script_string)
                    success_files.append(file_path)
                except DHError as e:
                    print(e)
                    print(f"Deephaven error when trying to run code in {file_path}")
                    error_files.append(file_path)
                except Exception as e:
                    print(e)
                    print(f"Unexpected error when trying to run code in {file_path}")
                    error_files.append(file_path)

    if len(success_files) > 0:
        success_files_print = "\n".join(success_files)
        print(f"The following files ran without error:\n{success_files_print}")
    if len(error_files) > 0:
        error_files_print = "\n".join(error_files)
        print(f"Errors were found in the following files:\n{error_files_print}")
        sys.exit("At least 1 file failed to run. Check the logs for information on what failed")

usage = """
usage: python script.py directory host port session_type -r max_retries
"""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Path to the directory of files to view")
    parser.add_argument("host", help="The Deephaven host")
    parser.add_argument("port", help="The port to access Deephaven on", type=int)
    parser.add_argument("session_type", help="The Deephaven session type", choices=["python", "groovy"])
    parser.add_argument("-mr", "--max_retries", help="The maximum number of retries when trying to connect to Deephaven", type=int, default=5)
    parser.add_argument("-rbf", "--reset_between_files", help="Boolean value on whether or not to reset the server between Runs. Defaults to false. Requires -dc/--docker_compose to be set", type=bool, default=False)
    parser.add_argument("-dc", "--docker_compose", help="docker-compose command to run to launch the server", type=str)

    args = parser.parse_args()
    directory = args.directory
    host = args.host
    port = args.port
    session_type = args.session_type
    max_retries = args.max_retries

    main(directory, host, port, session_type, max_retries=max_retries)
