"""
Time-Varying Network

This file contains the TVG (Time-Varying Graph) class (or TemporalNetwork).
"""
from soap_parser import report_parser as rp
from soap_parser.matrix import IntervalMatrix, upper_matrix_enumerate

from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import portion as P

plt.rcParams['keymap.quit'] = ['ctrl+w', 'cmd+w']

class TVG():

    def __init__(self, matrix: IntervalMatrix) -> None:

        # assert matrix.labels is not None
        if matrix.labels is not None:
            labels = matrix.labels
        else:
            labels = [str(k) for k in range(matrix.dim_row)]

        nodes = [(node_id, {"label" : node_label}) 
            for node_id, node_label in enumerate(labels)]
        edges = [(i, j, {"contacts" : interval}) 
            for (i, j), interval in upper_matrix_enumerate(matrix)
            if interval != P.empty() and i != j]

        self.graph = nx.Graph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)

        return None

    def get_interval_matrix(self) -> IntervalMatrix:
        k = len(self.graph)
        matrix = IntervalMatrix.identity_matrix(k)

        for (u, v, c) in self.graph.edges.data("contacts"):
            assert u < v
            matrix[u, v] = c

        labels: list[str] = []
        for i, n in enumerate(self.graph):
            assert i == n
            labels.append(self.graph.nodes[n]["label"])
        assert len(labels) == k
        matrix.set_labels(labels)
        # matrix.set_labels([self.graph.nodes[n]["label"] for n in self.graph])

        return matrix

    def get_graph_at(self, t: float) -> nx.Graph:
        filter_edge = lambda i, j : t in self.graph[i][j].get("contacts")
        return nx.subgraph_view(self.graph, filter_edge=filter_edge)

    def get_teg(self,
        K: float,
        r: float, # TODO : change to pass in sample times
        start: float | None = None,
        end: float | None = None
    ) -> nx.DiGraph:
        teg = nx.DiGraph()

        critical_times = self.get_critical_times()
        # start, end = critical_times[0], critical_times[-1]
        if start is None:
            start = critical_times[0]
        if end is None:
            end = critical_times[-1]

        steps = int((end - start) / r)
        sample_times = [start + i * r for i in range(steps)]

        previous_graph: nx.Graph | None = None

        for index, t in enumerate(sample_times):
            graph = self.get_graph_at(t)

            for n in graph.nodes():
                teg.add_node((n, t), identity = n, time = t)

            if previous_graph is not None:
                distance_matrix = nx.floyd_warshall_numpy(previous_graph)

                nodes = previous_graph.nodes()
                for i, j in [(i, j) for i in nodes for j in nodes]:
                    if distance_matrix[i][j] <= K:
                        teg.add_edge((i, sample_times[index - 1]), (j, t))

            previous_graph = graph

        return teg

    def get_reeb_graph(self,
        # clusters: list | None = None,
        # sub_slice: slice = slice(None, None, 1),
        sample_times: list[float] | None = None,
        clusters: list[list[int]] | None = None
    ) -> nx.Graph:
        rg = nx.Graph()

        if sample_times is None:
            assert clusters is None
            critical_times = self.get_critical_times()
            sample_times = [t + (critical_times[i + 1] - t) / 2
                                for i, t in enumerate(critical_times[:-1])]

        if clusters is not None:
            assert sample_times is not None
            assert len(sample_times) == len(clusters)

        # add nodes to reeb graph
        for i, t in enumerate(sample_times):
            g = self.get_graph_at(t)
            components = list(nx.connected_components(g))

            if clusters is not None:
                components = clusters[i]

            for c in components:
                representative = sorted(list(c))[0]
                rg.add_node((representative, i),
                    repr = representative,
                    column = i,
                    ec = c # equivalence class
                )

        # add edges to reeb graph
        for i, t in enumerate(sample_times[:-1]):
            nodes = []
            for n in rg.nodes(data = True):
                if n[1]["column"] == i or n[1]["column"] == (i + 1):
                    nodes.append(n)

            pairs = list(combinations(nodes, 2))
            for source, target in pairs:
                if source[1]["ec"] & target[1]["ec"]:
                    rg.add_edge(source[0], target[0])

        return rg

    def get_ball(self, u: int, K: float, t: float) -> None:

        return None

    def get_cone(self, u: int, t: float, r: float, s: float) -> None:
        
        return None

    def get_temporal_cost(self, u: int, v: int, t: float, r: float) -> None:

        return None

    def connected_at(self, u: int, v: int, t: int) -> int:
        try:
            return nx.shortest_path_length(self.get_graph_at(t), u, v)
        except nx.NetworkXNoPath:
            return 0

    def get_adjacency_matrix_at(self, t: int) -> list[list[int]]:
        graph = self.get_graph_at(t)
        array = nx.to_numpy_array(graph).astype(int).tolist()
        return array

    def get_sub_tvg(self, nodes: list[int]) -> "TVG":
        submatrix = self.get_interval_matrix().get_submatrix(nodes, nodes)
        return TVG(submatrix)

        # filter_node = lambda i : i in nodes
        # return nx.subgraph_view(self.graph, filter_node=filter_node)

    def get_tvg_window(self, interval: P.Interval) -> "TVG":
        window_matrix = self.get_interval_matrix().get_window(interval)
        return TVG(window_matrix)

    def get_edges_at(self, t: int) -> list[tuple[int, int]]:
        return [(u, v)
            for (u, v, c) in self.graph.edges.data("contacts") if t in c]

    def get_node_label(self, node: int) -> str:
        return self.graph.nodes[node]["label"]

    def get_edge_contacts(self, source: int, target: int) -> P.interval:
        return self.graph.edges[(source, target)]["contacts"]

    def edge_alive_at(self, source: int, target: int, t: int) -> bool:
        return t in self.graph.edges[(source, target)]["contacts"]

    def get_critical_times(self) -> list[float]:

        time: list[float] = []
        for u, v, c in self.graph.edges.data("contacts"):
            time += [c.lower, c.upper]

        return sorted(list(set(time)))

    def __str__(self) -> str:
        nodes = " ".join([f"{n}" for n in self.graph.nodes])
        edges = " ".join([f"{e}" for e in self.graph.edges])
        return f"{nodes} | {edges}"

TemporalNetwork = TVG



def draw_teg(teg) -> None:
    times = set()
    identities = set()

    for i in teg.nodes():
        times.add(teg.nodes[i]["time"])
        identities.add(teg.nodes[i]["identity"])

    times_list = sorted(list(times))
    identities_list = list(identities)

    pos = nx.random_layout(teg)
    x = np.linspace(0, 20, len(times))
    y = np.linspace(0, 20, len(identities))

    for i in np.arange(len(times_list)):
        for node in teg.nodes():
            if teg.nodes[node]["time"] == times_list[i]:
                pos[node][0] = x[i]
    for i in np.arange(len(identities_list)):
        for node in teg.nodes():
            if teg.nodes[node]["identity"] == identities_list[i]:
                pos[node][1] = y[i]
    nx.draw(teg, pos, with_labels = True, node_color = "lightblue", edge_color = "gray")
    plt.show()

    return None

if __name__ == "__main__":
    array_a = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(6, 10), P.empty()],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(3, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    matrix = IntervalMatrix(4, 4, array_a, labels = ["A", "B", "C", "D"])

    tn = TemporalNetwork(matrix)
    
    sub_tn = tn.get_sub_tvg([1, 2, 3])
    assert isinstance(sub_tn, TVG)
    assert [0, 1, 3, 4, 6, 7, 8, 10] == tn.get_critical_times()
    teg = tn.get_teg(K = 2, r = 0.5)
    teg = tn.get_teg(K = 2, r = 0.5, start = 2, end = 6)

    G = tn.graph
    assert tn.get_node_label(0) == "A"
    assert tn.get_edge_contacts(0, 1) == P.closed(0, 6)
    assert 3 in tn.get_edge_contacts(0, 1)
    assert 8 not in tn.get_edge_contacts(0, 1)
    assert tn.edge_alive_at(0, 1, 3)
    assert not tn.edge_alive_at(0, 1, 8)
    for e in G.edges:
        print(f"{e} : {tn.get_edge_contacts(*e)}")
        # print(f"\t{tn.edge_alive_at(*e,8)}") # WORKS but mypy not happy
        # print(f"\t{tn.edge_alive_at(e[0],e[1],8)}")

    K = tn.get_graph_at(8)
    print(nx.to_dict_of_lists(K))
    print(nx.to_numpy_array(K))
    print(tn.get_adjacency_matrix_at(8))
    print(tn)
    assert tn.connected_at(0, 1, 8) == 0
    assert tn.connected_at(0, 2, 8) == 1
    assert tn.connected_at(0, 3, 8) == 2
    # G = K
    print(f"{tn.get_edges_at(8)}")
    # exit()

    # G = tn.get_graph_on_nodes([0, 1, 2])
    G = tn.graph
    # G = K
    # pos = nx.spring_layout(G)
    # print(nx.get_node_attributes(G, "label"))

    # nx.draw_networkx(G, pos,
    #     labels = nx.get_node_attributes(G, "label"),
    #     edgelist = tn.get_edges_at(8)
    # )
    # nx.draw_networkx_nodes(G, pos)

    # nx.draw_networkx(G, pos, labels = nx.get_node_attributes(G, "label"))
    # nx.draw_networkx_edge_labels(
    #     G, 
    #     pos,
    #     edge_labels = nx.get_edge_attributes(G, "contacts")
    # )
    # plt.show()

    # start = 0
    # end = 10
    # r = 0.5
    # k = (end - start) // r
    # print(f"{k = }")
    # samples = [start + k * r for k in range(int((end - start) / r))]
    # print(f"{samples = }")

    # draw_teg(teg)
    tn.get_reeb_graph()
