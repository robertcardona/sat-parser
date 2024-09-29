import logging
import subprocess
import random
import time

from itertools import islice

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_commands(
        commands: list[list[str]], 
        hacks: list[list[str]], 
        max_workers: int = 10, 
        randomize: bool =False
    ) -> None:
    """
    This function runs all the terminal commands specified in `commands` on
        `max_workers` cores / threads.

    Parameters
    ----------
    commands : List[str]
        A list of valid MacOS unix commands
    hacks : List[str]
        A list of MacOS unix commands to be run after each main command completes
    max_workers : int, optional
        The number of threads to be created to run the jobs
    randomize : bool, optional
        Specifies if the commands should be randomized
    """
    logger.info(f"Running `execute_commands` with {len(commands)} commands and {len(hacks)} hacks.")

    if randomize:
        random.shuffle(commands)

    processes = (subprocess.Popen(cmd) for cmd in commands)
    running_processes = list(islice(processes, max_workers))  # start new processes

    while running_processes:
        for i, process in enumerate(running_processes):
            if process.poll() is not None:  # the process has finished
                running_processes[i] = next(processes, None)  # start new process
                if running_processes[i] is None: # no new processes
                    del running_processes[i]
                    break
            else:
                time.sleep(0.5)

                for hack in hacks:
                    subprocess.run(hack)        

    return None

def run_soap_mac(orb_paths: list[str], max_workers: int = 10) -> None:
    """
    This function prepares the macOS-specific commands for SOAP to be run 
        and any hacks that are needed to get around soap specific bugs.

    Parameters
    ----------
    orb_paths : List[str]
        A list of `.orb` filepaths, relative to the main python file, that 
        will be fed into SOAP.
    max_workers : int, optional
        The number of threads to be created to run the jobs
    """
    logger.info(f"Running `run_soap_mac` with {len(orb_paths)} simulations on {max_workers} threads.")

    osascript_unfocus = [
        'osascript',
        '-e',
        'tell application "System Events"',
        '-e',
        'set visible of application process "SOAP" to false',
        '-e',
        'end tell'
    ]

    osascript_focus = [
        'osascript',
        '-e',
        'tell application "System Events"',
        '-e',
        'tell process "SOAP"',
        '-e',
        'set frontmost to true',
        '-e',
        'end tell',
        '-e',
        'end tell'
    ]

    commands = []
    for path in orb_paths:
        # args = ["open", "-n", "-W", f"{folder}/{filename}"]
        args = ["open", "-n", "-j", "-W", path]
        commands.append(args)

    # print(f"len(commands)={len(commands)}")

    hacks = [osascript_unfocus, osascript_focus]
    execute_commands(commands, hacks, max_workers)
    
    return None

def run_soap_linux() -> None:
    """
    This function prepares the Linux/GNU-specific commands for SOAP to be run.
    """

    return None

def run_soap_windows() -> None:
    """
    This function prepares the Windows-specific commands for SOAP to be run.
    """

    return None

if __name__ == "__main__":
    pass
