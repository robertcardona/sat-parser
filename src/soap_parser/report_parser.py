"""Report File Parser

This file contains functions related to parsing reports generated by SOAP as 
    specified in `orb_builder`.
"""

from soap_parser import orb_parser as op
from soap_parser import os_utils as osu
from soap_parser.matrix import IntervalMatrix

import numpy as np
import portion as P

from itertools import combinations
from datetime import datetime
from pathlib import Path

import os
import logging

logger = logging.getLogger("report_parser")
level = logging.WARNING
logger.setLevel(level)
logging.basicConfig(level=level)

base_path = Path(__file__).parent

def contact_analysis_parser_v14(content: str) -> list[dict]:
    """
    This function takes in the content of a contact analysis csv output
        from SOAP version 14 and returns a list of contacts.
    """
    logger.info("Running `contact_analysis_parser_v14`")

    contact_plan: list[dict] = [{}]
    return contact_plan

def contact_analysis_parser_v15(content: str) -> list[dict]:
    """
    This function takes in the text of a contact analysis csv output
        from SOAP version 15 and returns a list of contacts.

    Parameters
    ----------
    content : str
        This is the text of the contact analysis csv file.

    Returns
    -------
    list[dict]
        This is a list of contacts. Each contact is a dictionary with four 
            keys : link, source, target and connections. 
            
            `link` is the name of the link usually "{source} - {target}",
            `source` is the name of the source platform,
            `target` is the name of the target platform,
            `connections` is a list of rist-set times for this link.
    """
    logger.info("Running `contact_analysis_parser_v15`")

    # special case ()
    content = content.replace(" sees ", " - ")

    content = content.replace("\nContact ", "\n")

    content = content.split("Analysis,")[1]
    lines = content.split("\n")[2:-1]

    connections_dict: dict[str, list[dict[str, float]]] = {}
    for line in lines:
        entries = line.split(",")
        link = entries[0]

        connection = {
            "rise" : float(entries[1]),
            "set" : float(entries[2]),
            "duration" : float(entries[3])
        }

        connections_dict.setdefault(link, []).append(connection)

    contacts = []
    for link, connections in connections_dict.items():
        source, target = link.split(" - ")
        contact = {
            "link" : link,
            "source" : source,
            "target" : target,
            "connections" : connections
        }
        contacts.append(contact)

    return contacts

# TODO : check if filepath is str type or path
def contact_analysis_report_parser(
    filepath: str | os.PathLike, 
    delta: int = 1
) -> tuple[dict[str, int], dict[tuple[int, int], list[float]]]:
    """
    Main function used to parse a contact analysis csv output from SOAP.
        It takes in a csv from soap v14 or v15 and parses it appropriately.

    Parameters
    ----------
    filepath : str | os.PathLike
        This is the filepath for the contact analysis report in `.csv` format.
    delta : int
        If an edge turns off for time less than `delta`, then we ignore the off
            time and treat it as having been connected the whole time.
            
            Say (u, v) is alive for [0, 49] and [51, 100]. 
            If delta = 5 we treat this as (u, v) is alive for [0, 100].

    Returns
    -------
    nodes : dict[str, int]
        This is a dictionary of nodes where the key is the platform name as 
            extracted from the report and the value is an integer id assigned
            to represent it.
    edges : dict[tuple[int, int], list[float]]
        This is a dictionary of edges where the key is a tuple of node id's,
            ordered from least to greatest id, and the keys are a list of 
            rise-set times.
    """
    logger.info(f"Running `contact_analysis_report_parser` on `{filepath}`")

    content = osu.read_file(filepath)

    # check which version of soap generated it
    #   v14 reports begin with a new line; v15 don't. 
    #   if any updates are made this will have to be updated.
    if content[0] == "\n":
        contacts = contact_analysis_parser_v14(content)
    else:
        contacts = contact_analysis_parser_v15(content)

    nodes: dict[str, int] = {}
    edges: dict[tuple[int, int], list[float]] = {}
    node_counter = 0

    for contact in contacts:

        link = contact["link"]
        source = contact["source"]
        target = contact["target"]
        connections = contact["connections"]

        if source not in nodes:
            nodes[source] = node_counter
            node_counter += 1
        
        if target not in nodes:
            nodes[target] = node_counter
            node_counter += 1

        source_id, target_id = nodes[source], nodes[target]

        sorted_ids = sorted([source_id, target_id])
        edge_id = (sorted_ids[0], sorted_ids[1])

        prev_set = -1
        for connection in connections:

            rise_time = connection["rise"]
            set_time = connection["set"]

            if prev_set == rise_time or (rise_time - prev_set < delta):
                # SOAP bug workaround
                edges[edge_id].pop()
            else:
                edges.setdefault(edge_id, []).append(rise_time)
            
            edges.setdefault(edge_id, []).append(set_time)

            previous_set_time = set_time

    # contact_plan = {"nodes" : nodes, "edges" : edges}
    # return contact_plan
    return nodes, edges

def contact_plan_to_matrix(
    nodes: dict[str, int],
    edges: dict[tuple[int, int], list[float]]
) -> IntervalMatrix:

    n = len(nodes)
    matrix = IntervalMatrix(n, n, labels = sorted(nodes, key=nodes.__getitem__))
    
    for i in range(n):
        matrix[(n, n)] = P.open(-P.inf, P.inf)

    for (source, target), connections in edges.items():
        print(f"{source} -- {target} -> {connections}")

        for i in range(0, n, 2):
            rise_time = connections[i]
            set_time = connections[i + 1]

            matrix[(source, target)] |= P.closed(rise_time, set_time)
            matrix[(target, source)] |= P.closed(rise_time, set_time)

    return matrix

def extract_critical_times(
    edges: dict[tuple[int, int], list[float]]
) -> list[float]:
    logger.info("Running `extract_critical_times`")

    return sorted(list(set(sum([c for _, c in edges.items()], []))))

def parse_contact_analysis_time(
    filepath: str | os.PathLike
) -> tuple[datetime, datetime]:
    """
    This function extracts the start end end times of a simulation from a 
        given contact analysis report.

    Parameters
    ----------
    filepath : str | os.PathLike
        This is the filepath for the contact analysis report in `.csv` format.

    Returns
    -------
    start, stop : (datetime, datetime)
        These are the starting and stopping times of the simulation as a 
            datetime object.
    """
    logger.info(f"Running `parse_contact_analysis_time` on `{filepath}`")

    content = osu.read_file(filepath)

    line = content[(i := content.find("Start")):content.find("\n", i)]
    start, stop = (s[7:-3] for s in line.split(",")[0:2])
    # start, stop = start[7:-3], stop[7:-3]

    start_dt = datetime.strptime(start, "%Y/%m/%d %H:%M:%S")
    stop_dt = datetime.strptime(stop, "%Y/%m/%d %H:%M:%S")

    return start_dt, stop_dt

def distances_report_parser(filepath: str | os.PathLike) -> dict[str, list[float]]:
    logger.info(f"Running `distances_report_parser` on `{filepath}`")

    content = osu.read_file(filepath)

    # special cases
    content = content.replace("Dist ", "Distance ")
    content = content.replace(" to ", " - ")
    content = content.replace(" sees ", " - ")
    content = content.replace("km\n", "km,\n")

    line = content[(i := content.find("TIME_UNITS")):content.find("\n", i)]
    line = line.replace("Distance ", "")
    labels = line.split(",")[:-1]
    # print(labels)

    lines = content[content.find("SECONDS"):].split("\n")[1:-1]
    # print(lines)

    distances: dict[str, list[float]] = {}
    for line in lines:
        for index, column in enumerate(line.split(",")[:-1]):
            # print(f"{labels[index]} : {index = } : {column = }")
            distances.setdefault(labels[index], []).append(float(column))
    # for key, value in distances.items():
    #     print(f"distances[{key}] = {value} : len(value) = {len(value)}")
        # print(86_400 // 24)
    return distances

def coordinates_report_parser(filepath: str | os.PathLike) -> dict[str, list[float | list[float]]]:
    logger.info(f"Running `coordinates_report_parser` on `{filepath}`")

    content = osu.read_file(filepath)

    line = content[(i := content.find("TIME_UNITS")):content.find("\n", i)]
    # line = line.replace("Distance ", "")
    labels = line.split(",")[:-1]

    lines = content[content.find("SECONDS"):].split("\n")[1:-1]

    INF = float("inf")
    axes: dict[str, int] = {"X-Coordinate" : 0, "Y-Coordinate" : 1, "Z-Coordinate" : 2}
    coordinates: dict[str, list[float | list[float]]] = {}
    
    for line in lines:
        columns = line.split(",")

        step: dict[str, list[float]] = {}
        for index, column in enumerate(columns[1:-1]):
            # print(f"{labels[index]} : {index = } : {column = }")
            key, axis = labels[index + 1].split(" - ")
            j = axes[axis]
            step.setdefault(key, [INF, INF, INF])[j] = float(column)

        coordinates.setdefault(labels[0], []).append(float(columns[0]))
        for key, value in step.items():
            coordinates.setdefault(key, []).append(value)

    return coordinates

def approximate_distance(
    distances: dict[str, list[float]], 
    link: str, 
    t: float
) -> float:

    return 0.0

if __name__ == "__main__":
    filepath = base_path / "outputs/test_20_0 Contact Analysis.csv"
    nodes, edges = contact_analysis_report_parser(filepath)
    print(f"There are {len(nodes)} sats")
    # print(contact_plan)
    start, stop = parse_contact_analysis_time(filepath)
    # print(f"{start = } | {stop = }")
    filepath = base_path / "outputs/test_20_0 Distances.csv"
    distances = distances_report_parser(filepath)

    filepath = base_path / "outputs/test_20_0 Coordinates.csv"
    coordinates = coordinates_report_parser(filepath)

    print(coordinates["TIME_UNITS"])
    for key, value in coordinates.items():
        print(f"{key} : {value[0:2]}")