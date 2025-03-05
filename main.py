from scipy.optimize import linprog
import numpy as np

DEBUG = True

def debug(msg):
    if DEBUG:
        print(msg)

def new_a(p, n):
    return np.array([[[0]*n]*n]*p)

def reverse_flatten(x, node_count, product_count):
    return x.reshape((product_count, node_count, node_count))

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

def make_constraints(capacity: dict, outgoing: dict, incoming: dict, factory: list, warehouse: list, demand: list, node_count, product_count):
    lp = ConstraintBuilder()

    # The cumulative flow can never exceed any edge's capacity
    for pair, cap in capacity.items():
        u, v = pair
        # f_0uv + f_1uv + ... <= capacity(u,v)
        a = new_a(product_count, node_count)
        for i in range(product_count):
            a[i][u][v] = 1
        lp.add_constraint(a, cap)
    
    # Conservation of flow: For each product, for each intersection node, the incoming flow must equal the outgoing flow
    for i in range(product_count):
        for w in range(node_count):
            # Skip factory and warehouse
            if w in [factory[i], warehouse[i]]:
                continue

            # flow of all incoming nodes - flow of all outgoing nodes = 0
            a = new_a(product_count, node_count)
            for u in incoming[w]:
                debug(f'{u} -> {w}')
                a[i][u][w] = 1
            for v in outgoing[w]:
                debug(f'{v} <- {w}')
                a[i][w][v] = -1
            lp.add_constraint(a, 0, equality=True)
        
        # There must be "demand" amount of flow exiting the factory and entering the warehouse
        a = new_a(product_count, node_count)
        for w in outgoing[factory[i]]:
            a[i][factory[i]][w] = 1
        lp.add_constraint(a, demand[i], equality=True)

        a = new_a(product_count, node_count)
        for w in incoming[warehouse[i]]:
            a[i][w][warehouse[i]] = 1
        lp.add_constraint(a, demand[i], equality=True)
    
    return lp.get_A(), lp.get_b()

def format_linprog_result(res, node_count, product_count):
    output = []
    output.append(f"Success: {res.success}")
    output.append(f"Message: {res.message}")

    if res.success:
        output.append(f"Optimal Objective Value: {res.fun}")
        output.append("Flow Values:")
        flow = reverse_flatten(np.array(res.x), node_count, product_count)
        for i in range(product_count):
            for u in range(node_count):
                for v in range(node_count):
                    f = flow[i][u][v]
                    if not f == 0:
                        output.append(f' flow[{i}] [{u}][{v}] = {f}')
            output.append('\n')
    else:
        output.append("No optimal solution found.")

    return "\n".join(output)

def get_answer():
    node_count, edge_count, product_count = [int(x) for x in input().strip().split()]

    # debug(f'node_count, edge_count, product_count: {(node_count, edge_count, product_count)}')
    if not product_count:
        return 'Yes'
    
    factory = []
    warehouse = []
    demand = []
    # capacity = {(u,v):0 for u in range(node_count) for v in range(node_count) if u != v}
    outgoing = incoming = {u: [] for u in range(node_count)}
    capacity = {}

    for _ in range(product_count):
        factory_i, warehouse_i, demand_i = [int(x) for x in input().strip().split()]
        factory.append(factory_i)
        warehouse.append(warehouse_i)
        demand.append(demand_i)

        # Add an artificial edge from warehouse to factory to maintain flow conservation
        # capacity[(warehouse_i, factory_i)] = demand_i
        # debug(f' {warehouse_i}--{demand_i}->{factory_i}')


    for _ in range(edge_count):
        src, dst, cap = [int(x) for x in input().strip().split()]
        capacity[(src, dst)] = cap
        outgoing[src].append(dst)
        incoming[dst].append(src)
        debug(f' {src}--{cap}->{dst}')

    A, b = make_constraints(capacity, outgoing, incoming, factory, warehouse, demand, node_count, product_count)

    # The objective function doesn't matter - we're only interested in if the constraints can be met
    c = [1]*node_count*node_count*product_count

    result = linprog(c, A_ub=A, b_ub=b)
    debug(format_linprog_result(result, node_count, product_count))
    return 'Yes' if result.success else 'No'

def main():
    print(get_answer())


if __name__ == '__main__':
    main()
