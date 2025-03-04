from scipy.optimize import linprog
import numpy as np

DEBUG = True

def debug(msg):
    if DEBUG:
        print(msg)

def new_a(p, n):
    return np.array([[[0]*n]*n]*p)

class ConstraintBuilder:
    def __init__(self):
        self.A = []
        self.b = []

    def add_constraint(self, a, b_i, equality=False):
        '''Add the constraint a*x <= b_i, or == when equality is True'''
        self.A.append(list(a.flatten()))
        self.b.append(b_i)
        if equality:
            self.A.append(list(-a.flatten()))
            self.b.append(-b_i)
    
    def get_A(self):
        return self.A
    
    def get_b(self):
        return self.b

def make_constraints(capacity: dict, factory: list, warehouse: list, demand: list, node_count, product_count):
    lp = ConstraintBuilder()

    # The cumulative flow can never exceed any edge's capacity
    for u, v in capacity.keys():
        # f_0uv + f_1uv + ... <= capacity(u,v)
        a = new_a(product_count, node_count)
        for i in range(product_count):
            a[i][u][v] = 1
        lp.add_constraint(a, capacity[(u,v)])
    
    # Conservation of flow: For each product, for each node, the incoming flow must equal the outgoing flow
    for i in range(product_count):
        for w in range(node_count):
            a = new_a(product_count, node_count)
            for u, v in capacity.keys():
                a[i][u][w] = 1
                a[i][w][v] = -1
            lp.add_constraint(a, 0, equality=True)
        
        # There must be "demand" amount of flow going from each product's factory to warehouse
        a = new_a(product_count, node_count)
        a[i][factory[i]][warehouse[i]] = 1
        lp.add_constraint(a, demand[i], equality=True)
    
    return lp.get_A(), lp.get_b()

def get_answer():
    node_count, edge_count, product_count = [int(x) for x in input().strip().split()]

    # debug(f'node_count, edge_count, product_count: {(node_count, edge_count, product_count)}')
    if not product_count:
        return 'Yes'
    
    factory = []
    warehouse = []
    demand = []
    for _ in range(product_count):
        factory_i, warehouse_i, demand_i = [int(x) for x in input().strip().split()]
        factory.append(factory_i)
        warehouse.append(warehouse_i)
        demand.append(demand_i)

    capacity = {}
    for _ in range(edge_count):
        src, dst, cap = [int(x) for x in input().strip().split()]
        capacity[(src, dst)] = cap

    A, b = make_constraints(capacity, factory, warehouse, demand, node_count, product_count)
    # debug(f'{b}')

    # The objective function doesn't matter - we're only interested in if the constraints can be met
    c = [0]*node_count*node_count*product_count

    result = linprog(c, A_ub=A, b_ub=b)
    return 'Yes' if result.success else 'No'

def main():
    print(get_answer())


if __name__ == '__main__':
    main()
