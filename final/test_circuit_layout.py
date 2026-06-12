"""Headless checks for the circuit visualiser routing.

Paste sample circuit paths into SAMPLE_PATHS and run this file directly.
It verifies that every wire route avoids passing through device boxes.
"""
from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
from GUI.circuit_canvas import CircuitCanvas


SAMPLE_PATHS = [
    "sample/and_test.txt",
    "sample/main.txt",
    "sample/divide_three_counter.txt",
]

CANVAS_HEIGHT = 600
BOX_PADDING = 1.0


def make_canvas(path):
    """Parse a circuit and return a GL-free CircuitCanvas with layout done."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    parser = Parser(names, devices, network, monitors, Scanner(path, names))
    if not parser.parse_network():
        raise AssertionError("Parsing failed for " + path)

    canvas = CircuitCanvas.__new__(CircuitCanvas)
    canvas.names = names
    canvas.devices = devices
    canvas.layout_origin_x = 90
    canvas.column_width = 330
    canvas.box_width = 160
    canvas.max_layer = 0
    canvas.gutter_lane_used = {}
    canvas.top_bus_used = 0
    canvas.bottom_bus_used = 0
    canvas.device_positions = {}
    canvas.input_pin_positions = {}
    canvas.output_pin_positions = {}
    canvas.input_wire_positions = {}
    canvas.output_wire_positions = {}
    canvas.layout_nodes = {}
    canvas.layout_edges = []
    canvas.feedback_edges = []
    canvas.edge_routes = []
    canvas.junction_points = []
    canvas.diagram_bounds = (0, 0, 0, 0)
    canvas.calculate_layout(CANVAS_HEIGHT)
    return canvas


def segment_hits_box(p_start, p_end, box):
    """Return True if an axis-aligned segment crosses the padded box."""
    bx0, by0, width, height = box
    left = bx0 + BOX_PADDING
    right = bx0 + width - BOX_PADDING
    bottom = by0 + BOX_PADDING
    top = by0 + height - BOX_PADDING

    x0, y0 = p_start
    x1, y1 = p_end

    if abs(x0 - x1) < 1e-6:  # vertical segment
        seg_low, seg_high = sorted([y0, y1])
        return left < x0 < right and seg_low < top and seg_high > bottom

    if abs(y0 - y1) < 1e-6:  # horizontal segment
        seg_low, seg_high = sorted([x0, x1])
        return bottom < y0 < top and seg_low < right and seg_high > left

    return False


def check_layout(path):
    """Assert routing covers every edge and never crosses a device box."""
    canvas = make_canvas(path)

    assert len(canvas.edge_routes) >= len(canvas.layout_edges), (
        path + ": some edges were not routed")

    boxes = list(canvas.device_positions.values())
    crossings = 0
    for route in canvas.edge_routes:
        points = route["points"]
        for index in range(len(points) - 1):
            for box in boxes:
                if segment_hits_box(points[index], points[index + 1], box):
                    crossings += 1

    assert crossings == 0, (
        path + ": " + str(crossings) + " wire segments cross a device box")
    print(path, "OK -", len(canvas.device_positions), "devices,",
          len(canvas.edge_routes), "routes,",
          len(canvas.feedback_edges), "feedback wires")


if __name__ == "__main__":
    for sample in SAMPLE_PATHS:
        check_layout(sample)
    print("All circuit layout checks passed.")
