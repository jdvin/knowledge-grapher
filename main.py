from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph
from os import listdir, sep, path, getcwd
import requests
import json 
from enum import Enum
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

class Namespace(Enum):
    ITEM = 1
    PROPERTY = 2

namespace_ids = {
    Namespace.ITEM : '0', 
    Namespace.PROPERTY : '120'
    }

class Property(Enum):
    INSTANCE_OF = 1
    SUBCLASS_OF = 2
    STUDIED_BY = 3
    HAS_QUALITY = 4
    HAS_PART = 5
    PART_OF = 6
    USES = 7

property_ids = {
    Property.INSTANCE_OF : 'P31',
    Property.SUBCLASS_OF : 'P279',
    Property.STUDIED_BY : 'P2579',
    Property.HAS_QUALITY : 'P1552',
    Property.HAS_PART : 'P527',
    Property.PART_OF : ''

}

core_path = path.dirname(path.abspath(__file__))
output_path = core_path + '/output.txt'

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

# def get_wiki_id(page_name):
      
# 	response = requests.get(f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&titles={page_name}&format=json")
# 	return get_value('wikibase_item', response.json())

def get_value(target_key, json):
    '''
    returns the first value of target_key in a json
    '''
    value = None
    if type(json) == dict:
        for key in json:
            if key == target_key:
                return json[key]
            else:
                value = get_value(target_key, json[key])
    elif type(json) == list:
        for ele in json:
            value = get_value(target_key, ele)
            if value is not None:
                break
        
    return value

def get_wiki_id(namespace, page_name):
    '''
    gets the FIRST ID for a search with page_name in namespace
    '''
    response = requests.get(f"https://www.wikidata.org/w/api.php?action=query&list=search&srsearch={page_name}&srnamespace={namespace_ids[namespace]}&format=json")
    
    if namespace == Namespace.ITEM:
        id_ = get_value('title', response.json())
    elif namespace == Namespace.PROPERTY:
        id_ = get_value('title', response.json()).split(":")[1]

    return id_

def get_properties(sparql, item, property_):
    sparql.setQuery(f"""
    SELECT ?prop ?propLabel
    WHERE
    {{
        wd:{item} wdt:{property_} ?prop.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    
    """)

    results = sparql.query().convert()

    results_df = pd.json_normalize(results['results']['bindings'])
    try:
        results_df[['prop.value', 'propLabel.value']].head()
        properties = {prop['propLabel.value']:prop['prop.value'].split('/')[-1] for i, prop in results_df.iterrows()}
        return properties
    except KeyError:
        return {}

def get_KG(sparql, graph, root_concept, property_type, depth):
    depth -=  1
    if depth >= 0:
        print(f"Not at limit - assessing layer {depth} for {root_concept}")

        root_concept_id = get_wiki_id(Namespace.ITEM, root_concept)
        property_nodes = get_properties(sparql, root_concept_id, property_ids[property_type])
        property_edges = [(root_concept, property_node) for property_node in property_nodes]
        
        graph.add_nodes_from(property_nodes)
        graph.add_edges_from(property_edges)

        for prop in property_nodes:
            graph = get_KG(sparql, graph, prop, property_type, depth)
    else:
        return graph
    return graph


sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

root_node = 'computer'
property_type = Property.HAS_QUALITY
depth = 3

g = nx.Graph()
g.add_node(root_node)
print(f"Building {property_type} Knowledge Graph of {root_node}")
g = get_KG(sparql, g, root_node, property_type, depth)
plt.subplot()
nx.draw(g, with_labels=True, font_weight='bold')
plt.show()



