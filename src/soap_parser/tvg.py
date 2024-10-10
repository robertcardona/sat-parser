"""
Time-Varying Network

This file contains the TVG (Time-Varying Graph) class (or TemporalNetwork).
"""
from soap_parser import report_parser as rp
from soap_parser.matrix import IntervalMatrix, upper_matrix_enumerate

import matplotlib.pyplot as plt
import networkx as nx
import portion as P

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
        
        # print(f"{nodes = }")
        # print(f"{edges = }")

        self.graph = nx.Graph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)

        return None

    def get_graph_at(self, t: int) -> nx.Graph:
        filter_edge = lambda i, j : t in self.graph[i][j].get("contacts")
        return nx.subgraph_view(self.graph, filter_edge=filter_edge)

    def get_graph_on_nodes(self, nodes: list[int]) -> nx.Graph:
        filter_node = lambda i : i in nodes
        return nx.subgraph_view(self.graph, filter_node=filter_node)

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

    G = tn.graph

    K = tn.get_graph_at(8)
    print(f"{K.edges() = }")

    G = tn.get_graph_on_nodes([0, 1, 2])

    pos = nx.spring_layout(G)
    # print(nx.get_node_attributes(G, "label"))
    nx.draw_networkx(G, pos, labels = nx.get_node_attributes(G, "label"))
    nx.draw_networkx_edge_labels(
        G, 
        pos,
        edge_labels = nx.get_edge_attributes(G, "contacts")
    )
    plt.show()