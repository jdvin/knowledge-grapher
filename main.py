from kg_factory import KG_Factory

factory = KG_Factory()

if __name__ == '__main__':

    root_node = 'computer'
    prop = 'has part'
    depth = 2

    g = factory.root_KG(root_node, prop, depth)
    factory.draw_KG(g)
