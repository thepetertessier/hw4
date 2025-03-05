from scipy.optimize import linprog
from scipy.sparse import lil_matrix, csr_matrix, vstack
import numpy as np

DEBUG = False

def debug(msg):
    if DEBUG:
        print(msg)

def reverse_flatten(x, node_count, product_count):
    return x.reshape((product_count, node_count, node_count))

def format_flow(flow, p, n) -> list[str]:
    output = []
    for i in range(p):
        for u in range(n):
            for v in range(n):
                f = flow[i][u][v]
                if not f == 0:
                    output.append(f' flow[{i}] [{u}][{v}] = {f}')
        output.append('\n')
    return output

def format_linprog_result(res, node_count, product_count):
    output = []
    output.append(f"Success: {res.success}")
    output.append(f"Message: {res.message}")

    if res.success:
        output.append(f"Optimal Objective Value: {res.fun}")
        flow = reverse_flatten(np.array(res.x), node_count, product_count)
        output.append(f'Raw Flow:\n{flow}')
        output.append("Formatted Flow:")
        output.extend(format_flow(flow, product_count, node_count))
    else:
        output.append("No optimal solution found.")

    return "\n".join(output)

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
    
    def __str__(self) -> str:
        output = []
        for i in range(self.p):
            for u in range(self.n):
                for v in range(self.n):
                    f = self.data[0, self._get_index(i, u, v)]
                    if not f == 0:
                        prefix = '-' if f < 0 else '+'
                        output.append(f' {prefix} f{i}{u}{v}')
        return ''.join(output)

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
        debug(f'Raw A:\n{self.A.toarray()}')
        return self.A.tocsr()
    
    def get_b(self):
        debug(f'Raw b (len {len(self.b)}): {self.b}')
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
        debug(f"[Constraint] {self.description:<15}: {self.constraint} {sign} {self.b_i}")
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
        debug(f' {src}--{cap}->{dst}')

    A, b = make_constraints(capacity, outgoing, incoming, factory, warehouse, demand, node_count, product_count)

    # The objective function doesn't matter - we're only interested in if the constraints can be met
    c = [1]*node_count*node_count*product_count

    result = linprog(c, A_ub=A.toarray(), b_ub=b)
    debug(format_linprog_result(result, node_count, product_count))
    return 'Yes' if result.success else 'No'

def main():
    print(get_answer())


if __name__ == '__main__':
    main()
