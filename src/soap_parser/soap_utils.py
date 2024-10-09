from soap_parser import os_utils as osu

from itertools import islice
from pathlib import Path
from typing import Generator

import logging
import platform
import random
import subprocess
import time

logger = logging.getLogger("report_parser")
level = logging.WARNING
logger.setLevel(level)
logging.basicConfig(level=level)

base_path = Path(__file__).parent

def execute_commands(
        commands: list[list[str]], 
        max_workers: int = 10, 
        randomize: bool = False,
        shell: bool = False
    ) -> None:
    """
    This function runs all the terminal commands specified in `commands` on
        `max_workers` cores / threads.

    Parameters
    ----------
    commands : List[str]
        A list of valid MacOS unix commands
    max_workers : int, optional
        The number of threads to be created to run the jobs
    randomize : bool, optional
        Specifies if the commands should be randomized
    """
    logger.info(f"Running `execute_commands` with {len(commands)} commands.")

    if randomize:
        random.shuffle(commands)

    processes: Generator[subprocess.Popen[bytes] | None, None, None] = \
        (subprocess.Popen(cmd, shell=shell) for cmd in commands)
    running_processes = list(islice(processes, max_workers))  # start new processes

    while running_processes:
        for i, process in enumerate(running_processes):
            assert process is not None
            if process.poll() is not None:  # the process has finished
                running_processes[i] = next(processes, None)  # start new process
                if running_processes[i] is None:
                    del running_processes[i]
                    break
            else:
                time.sleep(0.5)
    return None

def run_soap_mac(
    orb_paths: list[str],
    max_workers: int = 10,
    soap_path: str | None = None
) -> None:
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

    if soap_path is None:
        soap_path = "/Applications/SOAP/SOAP 15.5.0/SOAP.app/Contents/MacOS/SOAP"
    commands = [[soap_path, path, "-nogui"] for path in orb_paths]

    execute_commands(commands, max_workers)
    
    return None

def run_soap_linux(
    orb_paths: list[str], 
    max_workers: int = 10,
    soap_path: str | None = None
) -> None:
    """
    This function prepares the Linux/GNU-specific commands for SOAP to be run.
    """

    if soap_path is None:
        soap_path = "soap"
    commands = [[soap_path, "-nogui", path] for path in orb_paths]

    execute_commands(commands, max_workers, shell = True)

    return None

def run_soap_windows(
    orb_paths: list[str], 
    max_workers: int = 10,
    soap_path: str | None = None
) -> None:
    """
    This function prepares the Windows-specific commands for SOAP to be run.
    """
    if soap_path is None:
        soap_path = "C:\\soap15\\bin64\\soap.exe"
    commands = [[soap_path, "-nogui", path] for path in orb_paths]

    execute_commands(commands, max_workers, shell = True)

    return None

def run_soap(
    orb_paths: list[str], 
    max_workers: int = 10,
    soap_path: str | None = None
) -> None:

    system = platform.system()

    match system:
        case "Linux":
            run_soap_linux(orb_paths, max_workers, soap_path)
        case "Darwin":
            run_soap_mac(orb_paths, max_workers, soap_path)
        case "Windows":
            run_soap_windows(orb_paths, max_workers, soap_path)
        case _:
            raise OSError(f"Unsupported OS ({system})")
    return None

if __name__ == "__main__":
    filepaths = osu.get_ext_files(base_path / "outputs/", "orb")
    # print(f"{osu.check_os()}")
    # print(filepaths)
    # run_soap_mac(filepaths)
    # filepaths = [p for p in filepaths if "50" in p]
    run_soap(filepaths)
    # cmd = ["echo"]
    # process = subprocess.Popen(cmd, shell=True)
    # print(f"{process.args = }")
    # pass
