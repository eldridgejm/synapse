import networkx as nx
import matplotlib.pyplot as plt


def topic_graph(network):
    g = nx.Graph()

    for topic in network.topics:
        g.add_node(topic.key)

        linked_topics = [n for n in topic.successors if n.type == 'topic']
        for neighbor in linked_topics:
            g.add_edge(topic.key, neighbor.key)

    nx.draw_networkx(g, with_labels=True)
    plt.show()
