from scipy.optimize import linprog as lp

DEBUG = False

def debug(msg):
    if DEBUG:
        print(msg)

class Product:
    def __init__(self, factory_index, warehouse_index, demand):
        self.factory_index = factory_index
        self.warehouse_index = warehouse_index
        self.demand = demand
        
class Graph:
    def __init__(self, node_count):
        self.data = [[0]*node_count]*node_count

    def set_capacity(self, src, des, capacity):
        self.data[src][des] = capacity
    
    def get_capacity(self, src, des) -> int:
        return self.data[src][des]

def main():
    node_count, edge_count, product_count = [int(x) for x in input().strip().split()]
    products: list[Product] = []
    for _ in range(product_count):
        factory_index, warehouse_index, demand = [int(x) for x in input().strip().split()]
        products.append(Product(factory_index, warehouse_index, demand))

    graph = Graph(node_count)
    for _ in range(edge_count):
        src, des, capacity = [int(x) for x in input().strip().split()]
        graph.set_capacity(src, des, capacity)

if __name__ == '__main__':
    main()
