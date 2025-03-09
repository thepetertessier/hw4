from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from collections import defaultdict
import numpy as np

DEBUG = False

def debug(msg):
    if DEBUG:
        print(msg)

def get_index(i, u, v, n):
    return i*n*n + n*u + v

def reverse_flatten(x, node_count, product_count):
    return x.reshape((product_count, node_count, node_count))

def format_constraint(p, n, A, i_row):
    output = []
    for i in range(p):
        for u in range(n):
            for v in range(n):
                f = A[i_row, get_index(i, u, v, n)]
                if not f == 0:
                    prefix = '-' if f < 0 else '+'
                    output.append(f' {prefix} f{i}{u}{v}')
    return ''.join(output)

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


class ConstraintBuilder:
    def __init__(self, p, n, e):
        self.p = p
        self.n = n
        # self.row_count = e + p*(2*n + 4)
        self.data = []
        self.row_indices = []
        self.col_indices = []
        self.b = []
        self.i_row = 0
    
    def update_row(self, i, u, v, val, equality=False):
        index = get_index(i, u, v, self.n)
        self.data.append(val)
        self.row_indices.append(self.i_row)
        self.col_indices.append(index)
        if equality:
            self.data.append(-val)
            self.row_indices.append(self.i_row+1)
            self.col_indices.append(index)

    def commit_constraint(self, b_i, equality=False, description=''):
        self.b.append(b_i)
        if equality:
            self.b.append(-b_i)
        # debug(f"[Constraint] {description:<15}: {format_constraint(self.p, self.n, self.A, self.i_row)} {'==' if equality else '<='} {b_i}")
        self.i_row += 2 if equality else 1

    def get_A(self):
        # debug(f'Raw A:\n{self.A.toarray()}')
        return csr_matrix((self.data, (self.row_indices, self.col_indices)), shape=(len(self.b), self.p*self.n**2))
    
    def get_b(self):
        # debug(f'Raw b: {self.b}')
        return self.b
    
class ConstraintAdder:
    def __init__(self, cb: ConstraintBuilder, b_i, equality=False, description=''):
        self.p = cb.p
        self.n = cb.n
        self.cb = cb
        self.b_i = b_i
        self.equality = equality
        self.description = description

    def __enter__(self):
        return self
    
    def update(self, i, u, v, val):
        self.cb.update_row(i, u, v, val, equality=self.equality)

    def __exit__(self, exc_type, exc_value, traceback):
        self.cb.commit_constraint(self.b_i, equality=self.equality, description=self.description)
        return False

def make_constraints(capacity: dict, outgoing: dict, incoming: dict, factory: list, warehouse: list, demand: list, node_count, product_count):
    cb = ConstraintBuilder(product_count, node_count, len(capacity))

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
    outgoing = incoming = defaultdict(list)

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
        # debug(f' {src}--{cap}->{dst}')

    A, b = make_constraints(capacity, outgoing, incoming, factory, warehouse, demand, node_count, product_count)

    # The objective function doesn't matter - we're only interested in if the constraints can be met
    c = np.ones(product_count * node_count * node_count)

    result = linprog(c, A_ub=A, b_ub=b)
    # debug(format_linprog_result(result, node_count, product_count))
    return 'Yes' if result.success else 'No'

def main():
    print(get_answer())

import multiprocessing
import sys
import io

def worker(input_data, conn):
    """ Runs get_answer() with piped input and sends the result back. """
    sys.stdin = io.StringIO(input_data)  # Redirect stdin to use the piped input
    try:
        from min import get_answer  # Import get_answer from your script
        conn.send(get_answer())  # Send result back to the parent process
    except Exception as e:
        conn.send(f"Error: {e}")
    finally:
        conn.close()

def run_with_timeout():
    input_data = sys.stdin.read()  # Read all input before forking
    parent_conn, child_conn = multiprocessing.Pipe()  # Create a communication pipe

    process = multiprocessing.Process(target=worker, args=(input_data, child_conn))
    process.start()
    process.join(timeout=50)  # Wait up to 50 seconds

    if process.is_alive():
        process.terminate()
        process.join()
        print("No")
    else:
        if parent_conn.poll():  # Check if there's data in the pipe
            print(parent_conn.recv())  # Print the output from get_answer()
        else:
            print("Error: No response from process")

if __name__ == "__main__":
    run_with_timeout()


# import multiprocessing
# import sys

# def run_with_timeout():
#     input_data = sys.stdin.read()  # Read all input before forking

#     process = multiprocessing.Process(target=main, args=(input_data,))
#     process.start()
#     process.join(timeout=50)  # Wait up to 50 seconds
    
#     if process.is_alive():
#         process.terminate()
#         process.join()
#         print("No")

# if __name__ == '__main__':
#     run_with_timeout()
