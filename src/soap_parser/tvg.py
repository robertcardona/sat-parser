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
        sample_times: list[float] | None = None,
        limit: float = float("inf"),
        start: float | None = None,
        end: float | None = None
    ) -> nx.DiGraph:
        teg = nx.DiGraph()

        critical_times = self.get_critical_times()
        if start is None:
            start = critical_times[0]
        if end is None:
            end = critical_times[-1]
        
        if sample_times is None:
            sample_times = critical_times

        sample_times = list(filter(lambda t : start <= t <= end, sample_times))

        previous_graph: nx.Graph | None = None

        for index, t in enumerate(sample_times):
            graph = self.get_graph_at(t)

            for n in graph.nodes():
                teg.add_node((n, t), identity = n, time = t)

            if previous_graph is not None:
                distance_matrix = nx.floyd_warshall_numpy(previous_graph)

                nodes = previous_graph.nodes()
                for i, j in [(i, j) for i in nodes for j in nodes]:
                    if distance_matrix[i][j] <= limit:
                        teg.add_edge((i, sample_times[index - 1]), (j, t))

            previous_graph = graph

        return teg

    # TODO : rename to build
    def get_reeb_graph(self,
        sample_times: list[float] | None = None,
        clusters_list: list[list[list[int]]] | None = None,
        start: float | None = None,
        end: float | None = None
    ) -> nx.Graph:
        rg = nx.Graph()

        critical_times = self.get_critical_times()
        if start is None:
            start = critical_times[0]
        if end is None:
            end = critical_times[-1]

        if sample_times is None:
            assert clusters_list is None
            # critical_times = self.get_critical_times()
            sample_times = [t + (critical_times[i + 1] - t) / 2
                                for i, t in enumerate(critical_times[:-1])]

        if clusters_list is not None:
            assert sample_times is not None
            assert len(sample_times) == len(clusters_list)

            # filter clusters between start and end
            clusters_list = [c for t, c in zip(sample_times, clusters_list) 
                            if start <= t <= end]

        # filter sample_times between start and end
        sample_times = list(filter(lambda t : start <= t <= end, sample_times))

        # add nodes to reeb graph
        for i, t in enumerate(sample_times):
            g = self.get_graph_at(t)
            components = list(nx.connected_components(g))

            if clusters_list is not None:
                components = clusters_list[i]

            for c in components:
                representative = sorted(list(c))[0]
                rg.add_node((representative, i),
                    repr = representative,
                    column = i,
                    ec = set(c) # equivalence class
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

    def connected_at(self, u: int, v: int, t: float) -> int:
        try:
            return nx.shortest_path_length(self.get_graph_at(t), u, v)
        except nx.NetworkXNoPath:
            return 0

    def get_adjacency_matrix_at(self, t: float) -> list[list[int]]:
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
            for i in c:
                time += [i.lower, i.upper]

        return sorted(list(set(time)))

    def __format__(self, spec: str) -> str:
        if spec == "n":
            g = self.graph

            nodes = "\n".join([f"{n}:{g.nodes[n]['label']}" for n in g.nodes])
            # edges = " ".join([f"{e}" for e in self.graph.edges])
            return f"{nodes}"
        return str(self)

    def __str__(self) -> str:
        # nodes = " ".join([f"{self.graph.nodes[n]['label']}:{n}" for n in self.graph.nodes])
        nodes = " ".join([f"{n}" for n in self.graph.nodes])
        edges = " ".join([f"{e}" for e in self.graph.edges])
        return f"{nodes} | {edges}"

TemporalNetwork = TVG

def build_cycle_tvg(n: int) -> TVG:
    matrix = IntervalMatrix(n, n, labels = [str(k) for k in range(n)])

    for k in range(n - 1):
        matrix[k, k + 1] = P.closed(-P.inf, P.inf)
    matrix[0, n - 1] = P.closed(-P.inf, P.inf)

    # print(matrix)

    return TVG(matrix)

def build_complete_tvg(n: int) -> TVG:
    matrix = IntervalMatrix(n, n, labels = [str(k) for k in range(n)])

    for (i, j), _ in upper_matrix_enumerate(matrix):
        if i != j:
            matrix[i, j] = P.closed(-P.inf, P.inf)

    # print(matrix)

    return TVG(matrix)


def draw_teg(teg) -> None:
    times = set()
    identities = set()

    for i in teg.nodes():
        times.add(teg.nodes[i]["time"])
        identities.add(teg.nodes[i]["identity"])

    times_list = sorted(list(times))
    identities_list = list(identities)

    pos = nx.random_layout(teg)
    x = np.linspace(0, 20, len(times_list))
    y = np.linspace(0, 20, len(identities_list))

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

# def draw_reeb_graph(rg: nx.Graph) -> None:
#     # TODO : add legend based on if representative reaches threshold

#     # times = set()
#     # for i in rg.nodes():
#     #     times.add(rg.nodes[i]["column"])

#     times_list = sorted(list({rg.nodes[i]["column"] for i in rg.nodes()}))
#     identities_list = [n for n in rg.nodes() if rg.nodes[n]["column"] == 0]

#     pos = nx.random_layout(rg)
#     x = np.linspace(0, 20, len(times_list))
#     y = np.linspace(0, 20, len(identities_list))

#     for i in np.arange(len(times_list)):
#         for node in rg.nodes():
#             if rg.nodes[node]["column"] == times_list[i]:
#                 pos[node][0] = x[i]
#     for i in np.arange(len(identities_list)):
#         for node in rg.nodes():
#             pos[node][1] = rg.nodes[node]["repr"]
#             # if rg.nodes[node]["repr"] == identities_list[i]:
#             #     pos[node][1] = y[i]
#     nx.draw(rg, pos, with_labels = False, node_color = "lightblue", node_size = 10, edge_color = "gray")
#     plt.show()

#     return None

if __name__ == "__main__":
    array_a = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(6, 10), P.empty()],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(3, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    matrix = IntervalMatrix(4, 4, array_a, labels = ["A", "B", "C", "D"])

    tn = TemporalNetwork(matrix)
    # print(f"{len(tn.graph)}")
    
    sub_tn = tn.get_sub_tvg([1, 2, 3])
    assert isinstance(sub_tn, TVG)
    assert [0, 1, 3, 4, 6, 7, 8, 10] == tn.get_critical_times()
    # teg = tn.get_teg(K = 2, r = 0.5)
    # teg = tn.get_teg(K = 2, r = 0.5, start = 2, end = 6)

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
    rg = tn.get_reeb_graph()
    # draw_reeb_graph(rg)

    # print(np.inf == float("inf"))

    im = build_complete_tvg(4)
    print(f"im = {im}")
