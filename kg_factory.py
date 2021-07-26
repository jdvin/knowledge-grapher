from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
from os import listdir, sep, path, getcwd
import requests
import json 
from enum import Enum
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import csv
import pdb

from organiser import get_id_dict, store_id_dict

colours = ['gold','darkorange','magenta','darkviolet', 'blue', 'aqua']

class KG_Factory():

    def __init__(self):

        self.data_path = getcwd() + '\\data\\'
        
        self.namespace_ids = get_id_dict(self.data_path, 'namespaces')
        self.property_ids = get_id_dict(self.data_path, 'properties')
        self.item_ids = get_id_dict(self.data_path, 'items')


        self.sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        self.sparql.setReturnFormat(JSON)

        self.k_graphs = []
    
    def get_value(self, target_key, json):
        '''
        returns the first value of target_key in a json
        '''
        value = None
        if type(json) == dict:
            for key in json:
                if key == target_key:
                    return json[key]
                else:
                    value = self.get_value(target_key, json[key])
        elif type(json) == list:
            for ele in json:
                value = self.get_value(target_key, ele)
                if value is not None:
                    break
            
        return value

    def get_wiki_id(self, namespace, page_name, id_dict):
        '''
        gets the FIRST ID for a search with page_name in namespace
        '''
        try:
            return id_dict[page_name]
        except KeyError:
            response = requests.get(f"https://www.wikidata.org/w/api.php?action=query&list=search&srsearch={page_name}&srnamespace={self.namespace_ids[namespace]}&format=json")
            
            if namespace == 'item':
                id_ = self.get_value('title', response.json())
                self.item_ids[page_name] = id_
                store_id_dict(self.data_path, 'items', self.item_ids)
                
            elif namespace == 'property':
                id_ = self.get_value('title', response.json()).split(":")[1]
                self.property_ids[page_name] = id_
                store_id_dict(self.data_path, 'properties', self.item_ids)

            return id_

    def get_properties(self, item, property_):
        self.sparql.setQuery(f"""
        SELECT ?prop ?propLabel
        WHERE
        {{
            wd:{item} wdt:{property_} ?prop.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        
        """)

        results = self.sparql.query().convert()

        results_df = pd.json_normalize(results['results']['bindings'])
        try:
            results_df[['prop.value', 'propLabel.value']].head()
            properties = {prop['propLabel.value']:prop['prop.value'].split('/')[-1] for i, prop in results_df.iterrows()}
            return properties
        except KeyError:
            return {}

    def get_branches(self, graph, root_concept, property_type, depth):
        depth -=  1
        if depth >= 0:
            root_concept_id = self.get_wiki_id('item', root_concept, self.item_ids)
            property_id = self.get_wiki_id('property', property_type, self.property_ids)
            property_nodes = self.get_properties(root_concept_id, property_id)
            property_edges = [(root_concept, property_node) for property_node in property_nodes]
            
            graph.add_nodes_from(property_nodes)
            graph.add_edges_from(property_edges, object=property_type)

            for prop in property_nodes:
                graph = self.get_branches(graph, prop, property_type, depth)

        return graph

    def root_KG(self, root_node, property_types, depth, graph=None):
        if graph == None: graph = nx.Graph()
        graph.add_node(root_node)
        for property_type in property_types:
            graph = self.get_branches(graph, root_node, property_type, depth)
        self.k_graphs.append(graph)
        return graph

    def draw_KG(self, graph, property_types):
        plt.subplot()

        # separate the edges by property_type for c o l o u r
        edges_by_property = []
        for property_type in property_types:
            edges_by_property.append([(u, v) for (u, v, d) in graph.edges(data=True) if d['object'] == property_type])
        # generate positions for all nodes and draw
        pos = nx.spring_layout(graph) 
        nx.draw_networkx_nodes(graph, pos)

        # draw edges colored by their property_type
        for i,edges in enumerate(edges_by_property):
            nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=colours[i])
        pdb.set_trace()
        # draw labels for nodes
        nx.draw_networkx_labels(graph, pos)

        plt.show()

