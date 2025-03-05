from scipy.optimize import linprog
from scipy.sparse import lil_matrix, csr_matrix, vstack
import numpy as np

def reverse_flatten(x, node_count, product_count):
    return x.reshape((product_count, node_count, node_count))

class Constraint:
    def __init__(self, p, n):
        self.p = p
        self.n = n
        self.data = lil_matrix((1, p*n*n))
    
    def _get_index(self, i, u, v):
        n = self.n
        return i*n*n + n*u + v

    def update(self, i, u, v, val):
        self.data[0, self._get_index(i, u, v)] = val
    
    def get(self):
        return self.data.tocsr()

class ConstraintBuilder:
    def __init__(self, p, n):
        self.p = p
        self.n = n
        self.A = lil_matrix((0, p*n*n))
        self.b = []

    def add_constraint(self, new_row: csr_matrix, b_i, equality=False):
        '''Add the constraint a*x <= b_i, or == when equality is True'''
        self.A = vstack([self.A, new_row])
        self.b.append(b_i)
        if equality:
            self.A = vstack([self.A, -new_row])
            self.b.append(-b_i)
    
    def get_A(self):
        return self.A.tocsr()
    
    def get_b(self):
        return self.b
    
class ConstraintAdder:
    def __init__(self, cb: ConstraintBuilder, b_i, equality=False, description=''):
        self.p = cb.p
        self.n = cb.n
        self.cb = cb
        self.b_i = b_i
        self.equality = equality
        self.constraint = Constraint(self.p, self.n)
        self.description = description

    def __enter__(self):
        return self.constraint

    def __exit__(self, exc_type, exc_value, traceback):
        new_row = self.constraint.get()
        self.cb.add_constraint(new_row, self.b_i, equality=self.equality)
        sign = '==' if self.equality else '<='
        return False

def make_constraints(capacity: dict, outgoing: dict, incoming: dict, factory: list, warehouse: list, demand: list, node_count, product_count):
    cb = ConstraintBuilder(product_count, node_count)

    # The cumulative flow can never exceed any edge's capacity
    for pair, cap in capacity.items():
        u, v = pair
        # f_0uv + f_1uv + ... <= capacity(u,v)
        with ConstraintAdder(cb, cap, description=f'capacity {(u,v)}') as constraint:
            for i in range(product_count):
                constraint.update(i, u, v, 1)
    
    # Conservation of flow: For each product, for each intersection node, the incoming flow must equal the outgoing flow
    for i in range(product_count):
        for w in range(node_count):
            # Skip factory and warehouse
            if w in [factory[i], warehouse[i]]:
                continue

            # flow of all incoming nodes - flow of all outgoing nodes = 0
            with ConstraintAdder(cb, 0, equality=True, description=f'conserve (f{i},{w})') as constraint:
                for u in incoming[w]:
                    constraint.update(i, u, w, 1)
                for v in outgoing[w]:
                    constraint.update(i, w, v, -1)
        
        # There must be "demand" amount of flow exiting the factory and entering the warehouse
        with ConstraintAdder(cb, demand[i], equality=True, description=f'fty {i} demand') as constraint:
            for w in outgoing[factory[i]]:
                constraint.update(i, factory[i], w, 1)

        with ConstraintAdder(cb, demand[i], equality=True, description=f'whs {i} demand') as constraint:
            for w in incoming[warehouse[i]]:
                constraint.update(i, w, warehouse[i], 1)
    
    return cb.get_A(), cb.get_b()

def get_answer():
    node_count, edge_count, product_count = [int(x) for x in input().strip().split()]

    # debug(f'node_count, edge_count, product_count: {(node_count, edge_count, product_count)}')
    if not product_count:
        return 'Yes'
    
    factory = []
    warehouse = []
    demand = []
    capacity = {(u,v):0 for u in range(node_count) for v in range(node_count) if u != v}
    outgoing = incoming = {u: [] for u in range(node_count)}

    for _ in range(product_count):
        factory_i, warehouse_i, demand_i = [int(x) for x in input().strip().split()]
        factory.append(factory_i)
        warehouse.append(warehouse_i)
        demand.append(demand_i)

    for _ in range(edge_count):
        src, dst, cap = [int(x) for x in input().strip().split()]
        capacity[(src, dst)] = cap
        outgoing[src].append(dst)
        incoming[dst].append(src)

    A, b = make_constraints(capacity, outgoing, incoming, factory, warehouse, demand, node_count, product_count)

    # The objective function doesn't matter - we're only interested in if the constraints can be met
    c = np.ones(product_count * node_count * node_count)

    result = linprog(c, A_ub=A, b_ub=b)
    return 'Yes' if result.success else 'No'

def main():
    print(get_answer())


if __name__ == '__main__':
    main()
