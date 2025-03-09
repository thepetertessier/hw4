import random
import sys

def generate_input(node_count, edge_count, product_count, seed=42):
    random.seed(seed)
    
    # First line: node_count, edge_count, product_count
    lines = [f"{node_count} {edge_count} {product_count}"]
    
    # Generate product lines: factory, warehouse, demand.
    # Ensure factory and warehouse are different.
    for _ in range(product_count):
        factory = random.randint(0, node_count - 1)
        warehouse = random.randint(0, node_count - 1)
        while warehouse == factory:
            warehouse = random.randint(0, node_count - 1)
        demand = random.randint(1, 10)  # demand between 1 and 10
        lines.append(f"{factory} {warehouse} {demand}")
    
    # Maximum possible directed edges (no self-loops)
    max_possible_edges = node_count * (node_count - 1)
    if edge_count > max_possible_edges:
        sys.exit(f"Error: edge_count {edge_count} exceeds maximum possible unique edges {max_possible_edges}.")

    # Generate unique edges: src, dst, capacity.
    edges = set()
    while len(edges) < edge_count:
        src = random.randint(0, node_count - 1)
        dst = random.randint(0, node_count - 1)
        if src == dst:
            continue
        if (src, dst) in edges:
            continue
        edges.add((src, dst))
        capacity = random.randint(1, 20)  # capacity between 1 and 20
        lines.append(f"{src} {dst} {capacity}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_input.py <node_count> <edge_count> <product_count> [seed]")
        sys.exit(1)
    
    node_count = int(sys.argv[1])
    edge_count = int(sys.argv[2])
    product_count = int(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    huge_input = generate_input(node_count, edge_count, product_count, seed)
    print(huge_input)
