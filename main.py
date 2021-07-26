from kg_factory import KG_Factory

factory = KG_Factory()

if __name__ == '__main__':

    root_node = 'cell'
    prop = ['subclass of', 'instance of', 'studied by', 'has quality', 'has part']
    depth = 4

    g = factory.root_KG(root_node, prop, depth)
    factory.draw_KG(g, prop)
