"""
run_code.py

Python script to run the code in the given directory in Deephaven.

This script looks for either .py files or .md files. If a .py file is found, then its contents are run in Deephaven.
If a .md file is found, the code within the ```python ``` tags is extracted and run in Deephaven.
"""
from pydeephaven import Session, DHError

import sys
import time
import os
import re

PYTHON_START_TAG = "```python"
PYTHON_END_TAG = "```"
PYTHON_EXTENSION = ".py"

GROOVY_START_TAG = "```groovy"
GROOVY_END_TAG = "```"
GROOVY_EXTENSION = ".groovy"

def session_type_to_tags_and_extension(session_type):
    """
    Converts the session type to the markdown start and end tags, and
    the code file extension. Only works for python and groovy

    Parameters:
        session_type (str): The session type
    Returns:
        tuple: The start tag, end tag, and code extension
    """
    if session_type == 'python':
        return (PYTHON_START_TAG, PYTHON_END_TAG, PYTHON_EXTENSION)
    elif session_type == 'groovy':
        return (GROOVY_START_TAG, GROOVY_END_TAG, GROOVY_EXTENSION)
    else:
        raise ValueError(f"Unrecognized parameter {session_type}")

def read_code_file(file_path):
    """
    Wrapper function to read the full contents of the code file and return a string

    Parameters:
        file_path (str): The path to the code file to read

    Returns:
        str: String representation of the code file contents
        dict: A dictionary of code snippets to run, and code snippets that should fail.
            Distinguished by the "should_run" and "should_fail" keys
    """
    script_string = None
    with open(file_path) as f:
        script_string = f.read()

    return {
        "should_run": [script_string],
        "should_fail": []
    }

def read_markdown_file(file_path, start_tag, end_tag):
    """
    Extracts the code scripts between the given tags in the markdown file at the given path, and
    returns them as a list of strings. Code snippets are treated as separate entities, unless
    the `test-set` tag is used in the code snippet.

    Parameters:
        file_path (str): The path to the markdown file
        start_tag (str): The tag to represent the start of a code block
        end_tag (str): The tag to represent the end of a code block

    Returns:
        dict: A dictionary of code snippets to run, and code snippets that should fail.
            Distinguished by the "should_run" and "should_fail" keys
    """
    no_test_set_should_run = []
    test_set_should_run = {}
    no_test_set_should_fail = []
    test_set_should_fail = {}
    test_set = None
    should_fail = None

    with open(file_path) as f:
        in_script = False
        current_script = None
        for line in f.readlines():
            skip_line = ("skip-test" in line) or ("syntax" in line)
            if (line.startswith(start_tag)) and (not in_script) and (not skip_line):
                in_script = True
                should_fail = "should-fail" in line
                current_script = ""
                if "test-set" in line:
                    #Grab just the first test-set
                    test_set = int(re.findall(r'test-set=(\d+)', line)[0])
            elif (line.startswith(end_tag)) and in_script:
                in_script = False

                if test_set is None:
                    current_list = no_test_set_should_fail if should_fail else no_test_set_should_run
                    current_list.append(current_script)
                else:
                    current_dictionary = test_set_should_fail if should_fail else test_set_should_run
                    if not (test_set in current_dictionary.keys()):
                        current_dictionary[test_set] = ""
                    current_dictionary[test_set] += current_script

                test_set = None
            elif in_script:
                current_script += line

    #TODO: track the test-sets?
    should_run_list = no_test_set_should_run + [test_set_should_run[key] for key in test_set_should_run.keys()]
    should_fail_list = no_test_set_should_fail + [test_set_should_fail[key] for key in test_set_should_fail.keys()]
    return {
        "should_run": should_run_list,
        "should_fail": should_fail_list
    }

def path_to_files(path: str):
    """
    Converts the directory/file at the given path to a set of files.

    Parameters:
        path (str): The path to the directory/file to read
    Returns:
        set: The set of files in the directory/file
    """
    files = set()
    if path is None:
        return files

    if os.path.isfile(path):
        with open(path) as f:
            for line in f.read().split("\n"):
                if len(line) > 0:
                    if os.path.isfile(line):
                        files.add(line)
                    else:
                        files = files.union(path_to_files(line))
    else:
        for line in os.popen(f"find {path} -type f | sort").read().split("\n"):
            files.add(line)
    
    return files

def connect_to_deephaven(host: str, port: int, max_retries: int, session_type: str):
    """
    Connects to Deephaven with retry logic

    Parameters:
        host (str): The host name of the Deephaven instance
        port (int): The port on the host to access
        max_retries (int): The maximum attempts to retry connecting to Deephaven
        session_type (str): The Deephaven session type
    Returns:
        Session: The Deephaven session
    """
    print(f"Attempting to connect to host at {host} on port {port}")

    #Simple retry loop in case the server tries to launch before Deephaven is ready
    count = 0
    session = None
    while (count < max_retries):
        try:
            session = Session(host=host, port=port, session_type=session_type)
            print("Connected to Deephaven")
            break
        except DHError as e:
            print("Failed to connect to Deephaven... Waiting to try again")
            print(e)
            time.sleep(1)
            count += 1
        except Exception as e:
            print("Unknown error when connecting to Deephaven... Waiting to try again")
            print(e)
            time.sleep(1)
            count += 1
    if session is None:
        sys.exit(f"Failed to connect to Deephaven after {max_retries} attempts")

    return session

def main(host: str, port: int, session_type: str, run_path: str, max_retries: int=25,
            ignore_path: str=None, docker_compose: str=None, reset_between_files: int=None):
    """
    Main method for the script. Reads each file line by line and grabs lines
    between the ```python ``` tags to run in Deephaven.

    Parameters:
        host (str): The host name of the Deephaven instance
        port (int): The port on the host to access
        session_type (str): The Deephaven session type
        run_path (str): The path to the file containing a line separated list of files to run, or path to the directory containing file to run
        max_retries (int): The maximum attempts to retry connecting to Deephaven. Defaults to 25
        ignore_path (str): The path to the file containing a line separated list of files to ignore. Defaults to None
        docker_compose (str): The docker-compose command to launch and reset the server if needed. Defaults to None
        reset_between_files (int): Count to reset the server via the docker-compose command after the given number of files are ran. Defaults to None. Requires docker_compose to be defined
    Returns:
        None
    """
    if (reset_between_files is not None) and (docker_compose is None):
        raise ValueError("docker_compose must be defined if reset_between_files is defined")

    start = time.time()

    if docker_compose is not None:
        os.system(f"{docker_compose} up -d")

    session = connect_to_deephaven(host, port, max_retries, session_type)

    #Grab the markdown tags and code files to look at based on the session type
    (start_tag, end_tag, code_file_extension) = session_type_to_tags_and_extension(session_type)

    #Determine the files to read and ignore
    read_files = path_to_files(run_path)
    ignore_paths = path_to_files(ignore_path)

    #Track file results
    error_files = []
    success_files = []
    skipped_files = []

    #Reset counter
    file_run_count = 0
    for file_path in read_files:
        #Skip empty paths and ignore paths. Sometimes empty paths pop up with `find` commands
        if len(file_path) > 0 and not (file_path in ignore_paths):
            print(f"Reading file {file_path}")

            #If file should be read, read the code. Otherwise skip the file
            script_strings = None
            if file_path.endswith(".md"):
                script_strings = read_markdown_file(file_path, start_tag, end_tag)
            elif file_path.endswith(code_file_extension):
                script_strings = read_code_file(file_path)
            else:
                print(f"{file_path} does not end with a supported extension. Skipping")
                skipped_files.append(file_path)
                continue

#TODO: Bundle this duplicated code as a function
            skipped = True
            failed = False
            for script_string in script_strings["should_run"]:
                if len(script_string) != 0:
                    #Code found, run it in Deephaven
                    try:
                        skipped = False
                        file_run_count += 1
                        session.run_script(script_string)
                    except DHError as e:
                        print(e)
                        print(f"Deephaven error when trying to run code in {file_path}")
                        failed = True
                    except Exception as e:
                        print(e)
                        print(f"Unexpected error when trying to run code in {file_path}")
                        failed = True

                    #If reset is enabled, shut down and restart
                    if (reset_between_files is not None) and (file_run_count > reset_between_files):
                        os.system(f"{docker_compose} stop")
                        os.system(f"{docker_compose} up -d")
                        session = connect_to_deephaven(host, port, max_retries, session_type)
                        file_run_count = 0
            for script_string in script_strings["should_fail"]:
                if len(script_string) != 0:
                    #Code found, run it in Deephaven
                    try:
                        skipped = False
                        file_run_count += 1
                        session.run_script(script_string)
                        failed = True #This will be skipped if run_script raises an error
                    except DHError as e:
                        pass #Failed as expected
                    except Exception as e:
                        print(e)
                        print(f"Unexpected error when trying to run code in {file_path}")
                        failed = True

                    #If reset is enabled, shut down and restart
                    if (reset_between_files is not None) and (file_run_count > reset_between_files):
                        os.system(f"{docker_compose} stop")
                        os.system(f"{docker_compose} up -d")
                        session = connect_to_deephaven(host, port, max_retries, session_type)
                        file_run_count = 0

            if skipped:
                print(f"No code found in {file_path}, skipping")
                skipped_files.append(file_path)
            else:
                if failed:
                    error_files.append(file_path)
                else:
                    success_files.append(file_path)


        else:
            print(f"{file_path} flagged to skip. Skipping")
            skipped_files.append(file_path)

    end = time.time()
    print(f"{end - start} seconds to run")

    if len(skipped_files) > 0:
        skipped_files_print = "\n".join(skipped_files)
        print(f"The following files were skipped:\n{skipped_files_print}")
    if len(success_files) > 0:
        success_files_print = "\n".join(success_files)
        print(f"The following files ran without error:\n{success_files_print}")
    if len(error_files) > 0:
        error_files_print = "\n".join(error_files)
        print(f"Errors were found in the following files:\n{error_files_print}")
        sys.exit("At least 1 file failed to run. Check the logs for information on what failed")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="The Deephaven host", type=str)
    parser.add_argument("port", help="The port to access Deephaven on", type=int)
    parser.add_argument("session_type", help="The Deephaven session type", choices=["python", "groovy"])
    parser.add_argument("run_path", help="Path to the file containing a line separated list of files/paths to run, or directory to run", type=str)
    parser.add_argument("-mr", "--max_retries", help="The maximum number of retries when trying to connect to Deephaven", type=int, default=25)
    parser.add_argument("-rbf", "--reset_between_files", help="If set, resets the server after the given number of files are ran. Use 0 to reset after every file. Defaults to None. Requires -dc/--docker_compose to be set", type=int, default=None)
    parser.add_argument("-dc", "--docker_compose", help="docker-compose command to run to launch the server in the form of \"docker-compose -f <path>\"", type=str)
    parser.add_argument("-ip", "--ignore_path", help="Path to the file containing a line separated list of files/paths to ignore, or directory to ignore", type=str)


    args = parser.parse_args()
    main(args.host, args.port, args.session_type, args.run_path, max_retries=args.max_retries,
            ignore_path=args.ignore_path, docker_compose=args.docker_compose,
            reset_between_files=args.reset_between_files)
