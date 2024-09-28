"""Orb File Parser  

This file contains utilities related to parsing `.orb` files and extracting 
data needed by other functions.
"""

from os_utils import read_file

from pathlib import Path
base_path = Path(__file__).parent.parent

def parse_norad(split_line: list[str], name: str) -> dict:
    """
    Parses the second line in a NORAD platform define in an orb file.
        Expect 16 entries, the first being "STATE".

    STATE {norad_cat_id} {epoch_year} {epoch_fraction} {mean_motion_dot}
        {mean_motion_ddot} {bstar} {ephemeris_type} {element_set_no}
        {inclination} {ra_of_asc_node} {eccentricity} {arg_of_pericenter}
        {mean_anomaly} {mean_motion} {rev_at_epoch}

    Parameters
    ----------
    split_line : list[str]
        The list of tokens, split by whitespace, defining a NORAD platform in 
            an orb file. 
        This comes after a line starting with `DEFINE PLATFORM NORAD {name}`
            and begins with `STATE`.
    name : str
        This is the name of the satellite.
        This comes in the first line defining a norad platform, and is the last 
            token.
    
    Returns
    -------
    dict
        This returns a platform dictionary object which specifies the names of 
            each of the values.
    """
    assert len(split_line) == 16

    platform = {}

    platform["object_name"] = name # ex
    platform["norad_cat_id"] = float(split_line[1])
    platform["epoch_year"] = float(split_line[2])
    platform["epoch_fraction"] = float(split_line[3])
    platform["mean_motion_dot"] = float(split_line[4])
    platform["mean_motion_ddot"] = float(split_line[5])
    platform["bstar"] = float(split_line[6])
    platform["ephemeris_type"] = float(split_line[7])
    platform["element_set_no"] = float(split_line[8])
    platform["inclination"] = float(split_line[9])
    platform["ra_of_asc_node"] = float(split_line[10])
    platform["eccentricity"] = float(split_line[11])
    platform["arg_of_pericenter"] = float(split_line[12])
    platform["mean_anomaly"] = float(split_line[13])
    platform["mean_motion"] = float(split_line[14])
    platform["rev_at_epoch"] = float(split_line[15])

    return platform

if __name__ == "__main__":
    line = "STATE 48661 22 135.76775178 3.8e-05 0.0 0.00027384 0 999 53.0531 "
    line += "244.6948 0.0001725 48.601 311.5127 15.06403449 5390"

    assert len(line) == 116
    assert len(line.split()) == 16

    platform = parse_norad(line.split(), "STARLINK-2708")
    assert platform ["inclination"] == 53.0531

def parse_custom(split_line: list[str], name: str, system: str) -> dict:
    """
    Parses the second line in a custom platform defined in an orb file 
        orbiting a specified `system`.
        Expect 16 entries, the first being "STATE".

    STATE "{body}" {ic_type} {orbit_type} {semi_major_axis} {eccentricity}
        {inclination} {ra_of_asc_node} {arg_of_pericenter} {mean_anomaly}
            {year} {month} {day} {hour} {minute} {second}

    Parameters
    ----------
    split_line : list[str]
        The list of tokens, split by whitespace, defining a `system` platform in 
            an orb file. 
        This comes after a line starting with `DEFINE PLATFORM {system} {name}`
            and begins with `STATE`.
    system : str
        This is the system the platform is orbiting.
        This is in the first line defining a custom platform,
            and is the second to last token. Should always be set to `KEPLER`.
    name : str
        This is the name of the satellite.
        This comes in the first line defining a `system` platform, 
            and is the last token.
    
    Returns
    -------
    dict
        This returns a platform dictionary object which specifies the names of 
            each of the values. 
        (Note: this has different keys compared to a NORAD platform.)
    """
    assert len(split_line) == 16

    platform = {}

    platform["system"] = system
    platform["object_name"] = name
    platform["body"] = split_line[1].strip("\"")
    platform["ic_type"] = split_line[2]
    platform["orbit_type"] = split_line[3]
    platform["semi_major_axis"] = float(split_line[4])
    platform["eccentricity"] = float(split_line[5])
    platform["inclination"] = float(split_line[6])
    platform["ra_of_asc_node"] = float(split_line[7])
    platform["arg_of_pericenter"] = float(split_line[8])
    platform["mean_anomaly"] = float(split_line[9])
    platform["year"] = float(split_line[10])
    platform["month"] = float(split_line[11])
    platform["day"] = float(split_line[12])
    platform["hour"] = float(split_line[13])
    platform["minute"] = float(split_line[14])
    platform["second"] = float(split_line[15])

    return platform

if __name__ == "__main__":
    line = "STATE \"Mars\" CLASSICAL CUSTOM 32429.894046182384 "
    line += "0.5000000000000023 45.0 9.99999999999999 0.0 0.0 "
    line += "2020.0 7.0 7.0 0.0 0.0 0.0"

    assert len(line) == 124
    assert len(line.split()) == 16

    platform = parse_custom(line.split(), "MarsSat-2", "KEPLER")
    assert platform ["inclination"] == 45.0

def parse_ground(split_line: list[str], body: str, name: str) -> dict:
    """
    Parses the second line in a ground platform defined in an orb file.
        Expect 4 entries, the first being "STATE".

    STATE {latitude} {longitude} {altitude}

    Parameters
    ----------
    split_line : list[str]
        The list of tokens, split by whitespace, defining a ground platform in 
            an orb file. 
        This comes after a line starting with 
            `DEFINE PLATFORM ECR_FIXED "{name}"` and begins with `STATE`.
    name : str
        This is the name of the ground station.
        This comes in the first line defining a `system` platform, 
            and is the last token.
    body : str
        This is the body the ground platform is on.
    
    Returns
    -------
    dict
        This returns a platform dictionary object which specifies the names of 
            each of the values. 
        (Note: this has different keys compared to a NORAD or CUSTOM platform.)
    """
    assert len(split_line) == 4

    platform = {}

    platform["object_name"] = name
    platform["body"] = body
    platform["latitude"] = float(split_line[1])
    platform["longitude"] = float(split_line[2])
    platform["altitude"] = float(split_line[3])
    
    return platform

if __name__ == "__main__":
    line = "STATE 40.42940560000000261 -4.24884720000000016 0.00000000000000000"
    assert len(line) == 67
    assert len(line.split()) == 4

    platform = parse_ground(line.split(), "Earth", "DSN:Madrid")
    assert platform ["longitude"] == -4.24884720000000016


def parse_platforms(filepath: str) -> list[dict]:
    """
    Parses an orb file and extracts all the user-specified platforms.

    Parameters
    ----------
    filepath : str
        filepath pointing to a SOAP `.orb` file.
    
    Returns
    -------
    list[dict]
        This is a list of dictionary objects where each dictionary contains the
            platform data.

    """
    content = read_file(filepath)

    d = "DEFINE"

    # https://stackoverflow.com/questions/7866128/
    content = [d + e for e in content.split(d) if e]

    platforms = []
    for entry in content:
        name, system = "", ""

        lines = entry.split("\n")
        first_line = lines[0]
        if first_line.startswith("DEFINE PLATFORM"):

            if len(first_line.split("\"")) < 2: continue; # skip no names

            name = first_line.split("\"")[1]
            if name.startswith("."): continue; # skip defaults

            system = first_line.split()[2]

        else: # skip non-platform defines
            continue

        second_line = lines[1].split()
        sl_len = len(second_line)

        if second_line[0] != "STATE" or (sl_len != 4 and sl_len < 14):
            continue; # skip if no TLE

        if "CUSTOM" in second_line or second_line[1].startswith("\""):
            platform = parse_custom(second_line, name, system)
        elif sl_len == 4: # ECR_FIXED
            body = third_line = lines[2].replace("\"", "").split()[-1]
            platform = parse_ground(second_line, body, name)
        else:
            platform = parse_norad(second_line, name)
        platforms.append(platform)

    return platforms



if __name__ == "__main__":
    filepath = base_path / "data/orb/lunar_scenario_ground.orb"
    # filepath = base_path / "data/orb/lunar_scenario.orb"
    filepath = base_path / "data/orb/martian_scenario.orb"
    platforms = parse_platforms(filepath)

    print(len(platforms))
    for p in [p for p in platforms if p["body"] == "Mars"]:
        print(f"{p}")
        # print(f"{template_custom.format(**p)}")