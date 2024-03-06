from .model import Model
from graphviz import Source

class DotOutput:
    """
    A class to generate DOT (graph description language) representation for nodes.
    """
    def __init__(self):
        """
        Initializes the DotOutput instance.
        """
        self.from_node = None
        self.colisions=0
        self.nodes = {}  # Key: Node hash; Value: Tuple (Node Label, Counter)
        self.relations = []
        self.tree_size = 1000
        self.task_limit = 10
        self.state_limit = 10
        self.tree_count = 0
        self.fringe_count = 0
        self.invalid_node_counter = 0
        self.visited_node_counter = 0
        
        self.solution_path_nodes = []  # List of solution path node hashes

    def add_node(self, newnode, model):
        """
        Add a node to the DOT representation based on the Model instance.
        """
        if self.tree_count >= self.tree_size:
            return
        else:
            self.tree_count += 1
        
        hash_node = self._get_hash(newnode)
        
        # STATES
        _, facts = model.print_binary_state_info(newnode.state)
        state_string = "\\n".join(str(e) for e in facts[:min(len(facts),self.state_limit)]) + "\\n..."
        
        
        # TASKS
        tsn = newnode.task_network
        tsn_string = "\\n".join(str(m) for m in tsn[:min(len(tsn),self.task_limit)]) + "\\n..."
        
        
        # Using simple prefixes and separators to structure the content.
        label = f"{state_string}\\n------\\n{tsn_string}\\n"
        
        # Store label and counter in the nodes dictionary
        self.nodes[hash_node] = {'label': label, 'counter': -1}


    def open(self, opennode: Model):
        """
        Set the 'from_node' attribute for future relations.
        """
        if self.tree_count >= self.tree_size:
            return
        
        self.from_node = self._get_hash(opennode)
        self.nodes[self.from_node]['counter'] = self.fringe_count
        self.fringe_count += 1


    def close(self):
        """
        Reset the 'from_node' attribute.
        """
        if self.tree_count >= self.tree_size:
            return
        self.from_node = None

    def not_applicable(self, str_relation=''):
        if self.tree_count >= self.tree_size:
            return
        hash_invalid = hash('invalid' + str(self.invalid_node_counter))
        self.nodes[hash_invalid] = {'label': "NOT APPLICABLE", 'counter': -1}
        self.invalid_node_counter += 1
        self.relations.append((self.from_node, hash_invalid, str_relation))
        self.tree_count+=1

    def already_visited(self, str_relation=''):
        if self.tree_count >= self.tree_size:
            return
        hash_invalid = hash('visited' + str(self.visited_node_counter))
        self.nodes[hash_invalid] = {'label': "ALREADY VISITED", 'counter': -1}
        self.visited_node_counter += 1
        self.relations.append((self.from_node, hash_invalid, str_relation))



    def add_relation(self, node_to, str_relation=''):
        """
        Add a relation between 'from_node' and 'node_to'.
        """
        if self.tree_count >= self.tree_size:
            return
        if self.from_node:
            hash_to = self._get_hash(node_to)
            self.relations.append((self.from_node, hash_to, str_relation))
        else:
            self.colisions+=1
            pass

    def _get_hash(self, node):
        return hash(node)+node.seq_num

    def mark_solution_path(self, node):
        """Mark nodes and relations as part of the solution path."""
        self.solution_path_nodes.append(self._get_hash(node))

    def to_graphviz(self, filename="output.dot"):
        """
        Generates a DOT file for Graphviz.
        """
        graph = ["digraph G {"]
        
        # Add nodes
        for node_hash, node_data in self.nodes.items():
            label = f"Node {node_data['counter']}\\l{node_data['label']}".replace("\n", "\\l").replace("\"", "\\\"") + "\\l"
            node_attributes = [f'label="{label}"', 'shape="box"']
            
            # If the node is on the solution path, give it a different style or color
            if node_hash in self.solution_path_nodes:
                node_attributes.append('style="filled, bold"')
                node_attributes.append('fillcolor="green"')
            elif "\\n \\n " in label:
                node_attributes.append('style="filled"')
                node_attributes.append('fillcolor="lightblue"')
            
            graph.append(f'    "{node_hash}" [{" ".join(node_attributes)}];')
        
        # Add relations
        for from_node, to_node, rel_label in self.relations:
            edge_style = 'dashed' if from_node == to_node else 'solid'
            # if (from_node, to_node) in self.solution_path_relations:
            #     edge_style = 'bold'
            graph.append(f'    "{from_node}" -> "{to_node}" [style="{edge_style}" label="{rel_label}"];') 
        
        graph.append("}")
        with open(filename, "w") as file:
            file.write("\n".join(graph))

        source = Source("\n".join(graph))
        source.render(filename="output", format="svg", cleanup=True)

    def __str__(self):
        nodes_str = "\n".join(self.nodes.values())
        relations_str = "\n".join(f"{from_node} -> {to_node}" for from_node, to_node in self.relations)
        return f"Nodes:\n{nodes_str}\n\nRelations:\n{relations_str}"
