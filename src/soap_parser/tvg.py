"""
Time-Varying Network

This file contains the TVG (Time-Varying Graph) class (or TemporalNetwork).
"""
from soap_parser import report_parser as rp
from soap_parser.matrix import IntervalMatrix, upper_matrix_enumerate

import matplotlib.pyplot as plt
import networkx as nx
import portion as P

plt.rcParams['keymap.quit'] = ['ctrl+w', 'cmd+w']

# class ContactPlan():

#     def __init__(self, matrix: IntervalMatrix) -> None:
#         # self.nodes = nodes
#         # self.edges = edges

#         return None

class TVG():

    def __init__(self, matrix: IntervalMatrix) -> None:

        assert matrix.labels is not None

        nodes = [(node_id, {"label" : node_label}) 
            for node_id, node_label in enumerate(matrix.labels)]
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

    def get_graph_at(self, t: int) -> nx.Graph:
        filter_edge = lambda i, j : t in self.graph[i][j].get("contacts")
        return nx.subgraph_view(self.graph, filter_edge=filter_edge)

    def get_sub_tvg(self, nodes: list[int]) -> "TVG": # nx.Graph:
        submatrix = self.get_interval_matrix().get_submatrix(nodes, nodes)
        return TVG(submatrix)


        # filter_node = lambda i : i in nodes
        # return nx.subgraph_view(self.graph, filter_node=filter_node)

    def get_edges_at(self, t: int) -> list[tuple[int, int]]:
        return [(u, v)
            for (u, v, c) in self.graph.edges.data("contacts") if t in c]

    def get_node_label(self, node: int) -> str:
        return self.graph.nodes[node]["label"]

    def get_edge_contacts(self, source: int, target: int) -> P.interval:
        return self.graph.edges[(source, target)]["contacts"]

    def edge_alive_at(self, source: int, target: int, t: int) -> bool:
        return t in self.graph.edges[(source, target)]["contacts"]
        # return False

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

if __name__ == "__main__":
    array_a = [
        [P.open(-P.inf,P.inf), P.closed(0, 6), P.closed(6, 10), P.empty()],
        [P.empty(), P.open(-P.inf,P.inf), P.closed(1, 4), P.closed(3, 7)],
        [P.empty(), P.empty(), P.open(-P.inf,P.inf), P.closed(0, 8)],
        [P.empty(), P.empty(), P.empty(), P.open(-P.inf,P.inf)]
    ]

    matrix = IntervalMatrix(4, 4, array_a, labels = ["A", "B", "C", "D"])

    tn = TemporalNetwork(matrix)
    # sub_tn = tn.get_sub_tvg([0, 1, 2])
    sub_tn = tn.get_sub_tvg([1, 2, 3])
    print(sub_tn)
    print(f"{tn.get_critical_times()}")

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
    print(tn)
    # G = K
    print(f"{tn.get_edges_at(8)}")
    # exit()

    # G = tn.get_graph_on_nodes([0, 1, 2])
    G = tn.graph
    # G = K
    pos = nx.spring_layout(G)
    # print(nx.get_node_attributes(G, "label"))

    nx.draw_networkx(G, pos,
        labels = nx.get_node_attributes(G, "label"),
        edgelist = tn.get_edges_at(8)
    )
    # nx.draw_networkx_nodes(G, pos)

    # nx.draw_networkx(G, pos, labels = nx.get_node_attributes(G, "label"))
    # nx.draw_networkx_edge_labels(
    #     G, 
    #     pos,
    #     edge_labels = nx.get_edge_attributes(G, "contacts")
    # )
    plt.show()