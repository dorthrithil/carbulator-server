import networkx as nx
import numpy as np


def simplify_debt_matrix(debt_matrix: np.ndarray) -> np.ndarray:
    debt_graph = nx.DiGraph()

    for i in range(debt_matrix.shape[0]):
        for j in range(debt_matrix.shape[0]):
            if debt_matrix[i, j] != 0:
                debt_graph.add_edge(i, j, weight=debt_matrix[i, j])

    debt_graph = simplify_debt_graph(debt_graph)

    debt_matrix = np.zeros(debt_matrix.shape)
    for u, v, data in debt_graph.edges(data=True):
        debt_matrix[u, v] = round(float(data['weight']), 2)

    return debt_matrix


def simplify_debt_graph(debt_graph: nx.DiGraph) -> nx.DiGraph:
    # I can only examine one cycle at a time because I delete edges
    try:
        cycle = next(nx.simple_cycles(debt_graph))
    except StopIteration:
        return debt_graph

    # Get all edges of cycle
    edges = []
    for i in range(len(cycle)):
        if i == len(cycle) - 1:
            edges.append(debt_graph[cycle[i]][cycle[0]])
        else:
            edges.append(debt_graph[cycle[i]][cycle[i + 1]])

    # Find min edge weight
    min_edge_weight = min([e['weight'] for e in edges])

    # Subtract edge min weight
    for edge in edges:
        edge['weight'] -= min_edge_weight

    # Delete edge(s) with weight zero
    ebunch = []
    for u, v, data in debt_graph.edges(data=True):
        if data['weight'] == 0:
            ebunch.append((u, v))
    debt_graph.remove_edges_from(ebunch)

    return simplify_debt_graph(debt_graph)
