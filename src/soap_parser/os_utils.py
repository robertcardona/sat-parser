
# This file contains file access and OS-related utilities

import os

#Is this thing a file?
def file_check(filepath: str | os.PathLike) -> bool:
    """
    This functions takes in a filepath and returns True if it is a file and 
        False otherwise.

    Parameters
    ----------
    filepath : str | os.PathLike
        A string which contains a path

    Returns
    -------
    bool
        True if the path is a file, False otherwise.
    """
    try:
        open(filepath, "r")
        return True
    except IOError:
        print("Error: Needs a file")
        return False

def read_file(filepath: str | os.PathLike) -> str:
    """
    This function opens a file and returns all the data as a string.

    Parameters
    ----------
    filepath : str | os.PathLike
        The path to a file as a string

    Returns
    -------
    str
        The content of the file as a string
    """
    data = ""
    with open(filepath) as f:
        data = f.read()
    return data


def get_csv_files(folder : str) -> list[str]:
    """"
    This function returns a list of all files in a folder which are `.csv` 
        files.

    Parameters
    ----------
    folder : str
        The path to a folder as a string

    Returns
    -------
    list[str]
        A list of strings which are any files in the specfiied folder ending
        with `.csv`
    """
    filepaths = []

    for filename in os.listdir(folder):
        f = os.path.join(folder, filename)
        if os.path.isfile(f) and f.endswith(".csv"):
            filepaths.append(f)
    return filepaths

def get_ext_files(folder:  str | os.PathLike, ext: str) -> list[str]:
    """
    Returns a list of all files in a given folder with given extension.
        `get_ext_files("./outputs/", "tle")`

    Parameters
    ----------
    folder : str
        A path to a folder as a string
    ext : str
        The filetype extension that we want to select in the filter, as a string

    Returns
    -------
    List[str]
        A list of strings consisting of all the file paths in the specified 
        folder which end with the specified extension `ext`
    """
    filepaths = []

    for filename in os.listdir(folder):
        f = os.path.join(folder, filename)
        if os.path.isfile(f) and f.endswith("." + ext):
            filepaths.append(f)

    return filepaths

def save_to_outputs_file(
        content: str, 
        filename: str, 
        extension: str
    ) -> None:
    """
    This function saves a string to a file in the folder `/outputs/`

    Parameters
    ----------
    content : str
        A string which is to be saved fo a file
    filename : str
        The filename, without extension, to be saved in the outputs folder
    extension : str
        The extension of the file to be saved
    """
    f = open("./outputs/" + filename + "." + extension, "w") # TODO : change this
    f.write(content)
    f.close()

def make_folder(path: str) -> None:
    """
    If the folder specified by 'path' doesn't exist, this creates it including
        any missing folders leading up to it.

    Parameters
    ----------
    path : str
        The system path to a folder
    """
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == "__main__":
    pass
