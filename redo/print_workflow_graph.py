import matplotlib.pyplot as plt
from PIL import Image
import io
from main_workflow import DocumentProcessingWorkflow

try:
    from IPython.display import Image, display
except ImportError:
    Image = None
    display = None

def print_workflow_structure():
    app = DocumentProcessingWorkflow()
    graph = getattr(app, 'graph', None)
    if not graph:
        print("No graph found in workflow.")
        return
    print("Workflow Nodes:")
    for node in graph.nodes:
        print(f"  - {node}")
    print("\nWorkflow Edges (Transitions):")
    # Try to use _edges if available
    edges = getattr(graph, '_edges', None)
    if edges and hasattr(edges, 'items'):
        for src, targets in edges.items():
            for tgt in targets:
                print(f"  {src} -> {tgt}")
    else:
        print("  (Could not introspect edges. Only nodes are shown.)")

if __name__ == "__main__":
    print_workflow_structure() 