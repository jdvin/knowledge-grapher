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

from organiser import get_id_dict, store_id_dict


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

    def get_wiki_id(self, namespace, page_name):
        '''
        gets the FIRST ID for a search with page_name in namespace
        '''
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
            root_concept_id = self.get_wiki_id('item', root_concept)
            property_nodes = self.get_properties(root_concept_id, self.property_ids[property_type])
            property_edges = [(root_concept, property_node) for property_node in property_nodes]
            
            graph.add_nodes_from(property_nodes)
            graph.add_edges_from(property_edges)

            for prop in property_nodes:
                graph = self.get_branches(graph, prop, property_type, depth)
        else:
            return graph
        return graph

    def root_KG(self, root_node, property_types, depth, graph=None):
        if graph == None: graph = nx.Graph()
        graph.add_node(root_node)
        graph = self.get_branches(graph, root_node, property_types, depth)
        self.k_graphs.append(graph)
        return graph

    def draw_KG(self, graph):
        plt.subplot()
        nx.draw(graph, with_labels=True, font_weight='bold')
        plt.show()

