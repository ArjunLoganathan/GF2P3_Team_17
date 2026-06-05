"""Circuit visualiser canvas for the Logic Simulator GUI."""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT
from OpenGL.arrays import vbo
import numpy as np
from OpenGL import GL


class CircuitCanvas(wxcanvas.GLCanvas):
    """Draw a static visual representation of the logic circuit."""

    def __init__(self, parent, names, devices):
        """Initialise circuit canvas properties."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)
        self.names = names
        self.devices = devices
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.zoom = 1
        self.device_positions = {}
        self.input_pin_positions = {}
        self.output_pin_positions = {}
        self.input_wire_positions = {}
        self.output_wire_positions = {}
        self.layout_nodes = {}
        self.layout_edges = []
        self.feedback_edges = []
        self.edge_routes = []
        self.junction_points = []
        self.diagram_bounds = (0, 0, 0, 0)

        # Layout geometry constants, set up in calculate_layout.
        self.layout_origin_x = 90
        self.column_width = 330
        self.box_width = 160
        self.max_layer = 0
        self.gutter_lane_used = {}
        self.top_bus_used = 0
        self.bottom_bus_used = 0

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def render(self):
        """Draw the circuit visualiser."""
        if not self.IsShownOnScreen():
            return
        self.SetCurrent(self.context)
        if not self.init:
            self.init_gl()
            self.init = True

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        size = self.GetClientSize()
        self.render_text("Circuit visualiser", 10, size.height - 20)
        self.draw_circuit(size.width, size.height)
        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        self.init = False

    def on_mouse(self, event):
        """Handle panning and zooming."""
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom

        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False

        self.Refresh()

    def draw_circuit(self, canvas_width, canvas_height):
        """Draw all devices and their interconnections."""
        self.calculate_layout(canvas_height)
        self.draw_connections()
        self.draw_devices()

    def build_graph(self):
        """Build device nodes and connection edges from the simulator data."""
        self.layout_nodes = {}
        self.layout_edges = []

        for index, device in enumerate(self.devices.devices_list):
            self.layout_nodes[device.device_id] = {
                "device": device,
                "order": index,
                "layer": 0,
                "width": 0,
                "height": 0,
            }

        for device in self.devices.devices_list:
            for input_id, connected_output in device.inputs.items():
                if connected_output is None:
                    continue
                output_device_id, output_id = connected_output
                if output_device_id not in self.layout_nodes:
                    continue
                self.layout_edges.append({
                    "source_device": output_device_id,
                    "source_port": output_id,
                    "target_device": device.device_id,
                    "target_port": input_id,
                })

    def assign_layers(self):
        """Assign readable left-to-right layers via feedback-aware layering.

        Feedback (back) edges are detected and excluded, so the remaining
        forward edges form a DAG. Devices are then placed by longest path
        from the inputs, which lets sequential chains (counters, shift
        registers) flow across columns while true feedback stays a short hop.
        """
        adjacency = {node_id: [] for node_id in self.layout_nodes}
        for edge in self.layout_edges:
            source = edge["source_device"]
            target = edge["target_device"]
            if target not in adjacency[source]:
                adjacency[source].append(target)

        back_edges = self.find_back_edges(adjacency)
        forward_pairs = [(u, v) for u, neighbours in adjacency.items()
                         for v in neighbours if (u, v) not in back_edges]

        for node in self.layout_nodes.values():
            node["layer"] = 0

        for _ in range(len(self.layout_nodes)):
            changed = False
            for source, target in forward_pairs:
                wanted_layer = self.layout_nodes[source]["layer"] + 1
                if wanted_layer > self.layout_nodes[target]["layer"]:
                    self.layout_nodes[target]["layer"] = wanted_layer
                    changed = True
            if not changed:
                break

        self.collapse_layers()

    def find_back_edges(self, adjacency):
        """Return the set of (source, target) edges that close a cycle.

        Uses an iterative depth-first search with white/grey/black colouring;
        an edge into a node still on the recursion stack (grey) is a back edge.
        """
        white, grey, black = 0, 1, 2
        colour = {node_id: white for node_id in self.layout_nodes}
        back_edges = set()

        for start in self.layout_nodes:
            if colour[start] != white:
                continue
            colour[start] = grey
            stack = [(start, iter(adjacency[start]))]
            while stack:
                node, neighbours = stack[-1]
                descended = False
                for neighbour in neighbours:
                    if colour[neighbour] == grey:
                        back_edges.add((node, neighbour))
                    elif colour[neighbour] == white:
                        colour[neighbour] = grey
                        stack.append((neighbour, iter(adjacency[neighbour])))
                        descended = True
                        break
                if not descended:
                    colour[node] = black
                    stack.pop()

        return back_edges

    def collapse_layers(self):
        """Renumber the used layers to contiguous integers (no empty columns)."""
        used = sorted({node["layer"] for node in self.layout_nodes.values()})
        remap = {layer: index for index, layer in enumerate(used)}
        for node in self.layout_nodes.values():
            node["layer"] = remap[node["layer"]]

    def order_layers(self, layers):
        """Order nodes within each layer to reduce wire crossings.

        Uses a light barycenter pass: each node is placed near the average
        rank of the devices that feed it in earlier layers.
        """
        predecessors = {}
        successors = {}
        for edge in self.layout_edges:
            predecessors.setdefault(edge["target_device"], []).append(
                edge["source_device"])
            successors.setdefault(edge["source_device"], []).append(
                edge["target_device"])

        order_index = {node_id: node["order"]
                       for node_id, node in self.layout_nodes.items()}

        ranks = {}
        for layer in sorted(layers):
            layer_nodes = layers[layer]
            if layer == min(layers):
                layer_nodes.sort(key=lambda item: item["order"])
            else:
                def barycenter(node):
                    device_id = node["device"].device_id
                    source_ranks = [ranks[s]
                                    for s in predecessors.get(device_id, [])
                                    if s in ranks]
                    if source_ranks:
                        return sum(source_ranks) / len(source_ranks)
                    # No ranked inputs: hint from where this node feeds.
                    target_orders = [order_index[t]
                                     for t in successors.get(device_id, [])
                                     if t in order_index]
                    if target_orders:
                        return sum(target_orders) / len(target_orders)
                    return node["order"]
                layer_nodes.sort(key=barycenter)
            for rank, node in enumerate(layer_nodes):
                ranks[node["device"].device_id] = rank

    def calculate_layout(self, canvas_height):
        """Calculate device and pin positions for the circuit view."""
        self.build_graph()
        self.assign_layers()
        box_width = self.box_width
        column_width = self.column_width
        vertical_gap = 40
        pin_stub = 14
        self.device_positions = {}
        self.input_pin_positions = {}
        self.output_pin_positions = {}
        self.input_wire_positions = {}
        self.output_wire_positions = {}
        self.feedback_edges = []
        self.edge_routes = []
        self.junction_points = []
        self.gutter_lane_used = {}
        self.top_bus_used = 0
        self.bottom_bus_used = 0

        self.max_layer = max(
            (node["layer"] for node in self.layout_nodes.values()), default=0)

        # Size the top and bottom bus bands from how many wires need them.
        feedback_count = 0
        multispan_count = 0
        for edge in self.layout_edges:
            cs = self.layout_nodes[edge["source_device"]]["layer"]
            ct = self.layout_nodes[edge["target_device"]]["layer"]
            if ct <= cs:
                feedback_count += 1
            elif ct > cs + 1:
                multispan_count += 1
        top_margin = 70 + feedback_count * 22
        bottom_margin = 45 + multispan_count * 22

        layers = {}
        for node in self.layout_nodes.values():
            device = node["device"]
            pin_count = max(len(device.inputs), len(device.outputs), 1)
            node["width"] = box_width
            node["height"] = max(90, 26 * pin_count + 35)
            layers.setdefault(node["layer"], []).append(node)

        self.order_layers(layers)

        available_height = max(120, canvas_height - top_margin - bottom_margin)
        min_x = self.layout_origin_x
        max_x = self.layout_origin_x
        min_y = canvas_height
        max_y = 0

        # Align every column to one shared top edge so columns line up and the
        # whole block is centred by the tallest column.
        tallest = 0
        for layer_nodes in layers.values():
            layer_height = sum(node["height"] for node in layer_nodes)
            layer_height += vertical_gap * max(0, len(layer_nodes) - 1)
            tallest = max(tallest, layer_height)
        shared_top_y = canvas_height - top_margin
        if tallest < available_height:
            shared_top_y -= (available_height - tallest) / 2

        for layer, layer_nodes in sorted(layers.items()):
            current_y = shared_top_y
            for node in layer_nodes:
                device = node["device"]
                x_pos = self.layout_origin_x + layer * column_width
                y_pos = current_y - node["height"]
                self.device_positions[device.device_id] = (
                    x_pos, y_pos, node["width"], node["height"])
                self.store_pin_positions(device, x_pos, y_pos,
                                         node["width"], node["height"],
                                         pin_stub)
                min_x = min(min_x, x_pos)
                max_x = max(max_x, x_pos + node["width"])
                min_y = min(min_y, y_pos)
                max_y = max(max_y, y_pos + node["height"])
                current_y = y_pos - vertical_gap

        self.diagram_bounds = (min_x, min_y, max_x, max_y)
        self.calculate_edge_routes()

    def next_gutter_x(self, gutter):
        """Return a free vertical lane x inside the given gutter.

        Gutter -1 is the outer-left margin and any gutter at or beyond the
        last layer is the outer-right margin. Real gutters sit in the empty
        space between two device columns.
        """
        spacing = 22
        count = self.gutter_lane_used.get(gutter, 0)
        self.gutter_lane_used[gutter] = count + 1
        _, _, max_x, _ = self.diagram_bounds

        if gutter <= -1:
            return self.layout_origin_x - 25 - count * spacing
        if gutter >= self.max_layer:
            return max_x + 25 + count * spacing

        left = self.layout_origin_x + gutter * self.column_width \
            + self.box_width
        right = self.layout_origin_x + (gutter + 1) * self.column_width
        return min(left + 25 + count * spacing, right - 12)

    def next_bus_y(self, side):
        """Return a free horizontal bus lane y above or below the boxes."""
        spacing = 22
        _, min_y, _, max_y = self.diagram_bounds
        if side == "top":
            count = self.top_bus_used
            self.top_bus_used += 1
            return max_y + 22 + count * spacing
        count = self.bottom_bus_used
        self.bottom_bus_used += 1
        return min_y - 22 - count * spacing

    def calculate_edge_routes(self):
        """Precompute orthogonal wire routes for all graph edges.

        Vertical segments live only in empty gutters between columns, and
        long horizontals live only in top/bottom bus bands above or below all
        boxes, so a wire can never cross a device rectangle. Edges sharing a
        source pin are merged onto one trunk with junction dots.
        """
        self.edge_routes = []
        self.feedback_edges = []
        self.junction_points = []

        groups = {}
        order = []
        for edge in self.layout_edges:
            source_key = (edge["source_device"], edge["source_port"])
            if source_key not in groups:
                groups[source_key] = []
                order.append(source_key)
            groups[source_key].append(edge)

        for colour_index, source_key in enumerate(order):
            source = self.output_wire_positions.get(source_key)
            if source is None:
                continue
            cs = self.layout_nodes[source_key[0]]["layer"]

            adjacent = []
            forward = []
            feedback = []
            for edge in groups[source_key]:
                target_key = (edge["target_device"], edge["target_port"])
                target = self.input_wire_positions.get(target_key)
                if target is None:
                    continue
                ct = self.layout_nodes[edge["target_device"]]["layer"]
                record = (edge, target, ct)
                if ct <= cs:
                    feedback.append(record)
                elif ct == cs + 1:
                    adjacent.append(record)
                else:
                    forward.append(record)

            self.route_adjacent_group(source, cs, adjacent, colour_index)
            self.route_bus_group(source, cs, forward, colour_index,
                                 "bottom")
            self.route_bus_group(source, cs, feedback, colour_index, "top")

    def route_adjacent_group(self, source, cs, records, colour_index):
        """Route edges to the next column as one trunk in the shared gutter."""
        if not records:
            return
        source_y = source[1]
        trunk_x = self.next_gutter_x(cs)
        for edge, target, _ in records:
            target_y = target[1]
            points = [
                source,
                (trunk_x, source_y),
                (trunk_x, target_y),
                target,
            ]
            self.edge_routes.append({
                "points": points,
                "index": colour_index,
            })
            self.junction_points.append((trunk_x, target_y, colour_index))
        self.junction_points.append((trunk_x, source_y, colour_index))

    def route_bus_group(self, source, cs, records, colour_index, side):
        """Route edges via a shared riser and a top or bottom bus band."""
        if not records:
            return
        source_y = source[1]
        rise_x = self.next_gutter_x(cs)
        bus_y = self.next_bus_y(side)
        is_feedback = side == "top"
        for edge, target, ct in records:
            target_y = target[1]
            drop_x = self.next_gutter_x(ct - 1)
            points = [
                source,
                (rise_x, source_y),
                (rise_x, bus_y),
                (drop_x, bus_y),
                (drop_x, target_y),
                target,
            ]
            self.edge_routes.append({
                "points": points,
                "index": colour_index,
            })
            if is_feedback:
                self.feedback_edges.append(edge)
            self.junction_points.append((drop_x, bus_y, colour_index))
        self.junction_points.append((rise_x, bus_y, colour_index))

    def store_pin_positions(self, device, x_pos, y_pos, box_width, box_height,
                            pin_stub):
        """Store input and output pin coordinates for one device."""
        input_ids = list(device.inputs.keys())
        output_ids = list(device.outputs.keys())

        for index, input_id in enumerate(input_ids):
            pin_y = y_pos + box_height * (index + 1) / (len(input_ids) + 1)
            self.input_pin_positions[(device.device_id, input_id)] = (
                x_pos, pin_y)
            self.input_wire_positions[(device.device_id, input_id)] = (
                x_pos - pin_stub, pin_y)

        for index, output_id in enumerate(output_ids):
            pin_y = y_pos + box_height * (index + 1) / (len(output_ids) + 1)
            self.output_pin_positions[(device.device_id, output_id)] = (
                x_pos + box_width, pin_y)
            self.output_wire_positions[(device.device_id, output_id)] = (
                x_pos + box_width + pin_stub, pin_y)

    def draw_devices(self):
        """Draw device boxes, names, and pin labels."""
        for device in self.devices.devices_list:
            x_pos, y_pos, box_width, box_height = self.device_positions[
                device.device_id]
            device_name = self.names.get_name_string(device.device_id)
            device_kind = self.names.get_name_string(device.device_kind)

            GL.glColor3f(0.0, 0.0, 0.0)
            self.draw_rectangle(x_pos, y_pos, box_width, box_height)
            self.render_text(device_kind, x_pos + 14, y_pos + box_height - 24)
            self.render_text(device_name, x_pos + 14, y_pos + box_height - 48)

            for input_id in device.inputs:
                pin_x, pin_y = self.input_pin_positions[
                    (device.device_id, input_id)]
                wire_x, wire_y = self.input_wire_positions[
                    (device.device_id, input_id)]
                self.draw_line(wire_x, wire_y, pin_x, pin_y)
                label = self.get_pin_label(input_id, device)
                if label:
                    label_x = pin_x - 6 - self.text_width(label)
                    self.render_text(label, label_x, pin_y + 6)

            for output_id in device.outputs:
                pin_x, pin_y = self.output_pin_positions[
                    (device.device_id, output_id)]
                wire_x, wire_y = self.output_wire_positions[
                    (device.device_id, output_id)]
                self.draw_line(pin_x, pin_y, wire_x, wire_y)
                label = self.get_pin_label(output_id, device)
                if label:
                    self.render_text(label, wire_x + 6, pin_y + 6)

    # def draw_connections(self):
    #     """Draw precomputed orthogonal wire routes and their junction dots."""
    #     for route in self.edge_routes:
    #         GL.glColor3f(*self.get_wire_colour(route["index"]))
    #         points = route["points"]
    #         for index in range(len(points) - 1):
    #             start_x, start_y = points[index]
    #             end_x, end_y = points[index + 1]
    #             self.draw_line(start_x, start_y, end_x, end_y)

    #     for x_pos, y_pos, colour_index in self.junction_points:
    #         GL.glColor3f(*self.get_wire_colour(colour_index))
    #         self.draw_junction(x_pos, y_pos)

    def draw_connections(self):
        """Draw all precomputed orthogonal wire routes in a single batched call."""
        all_vertices = []
        all_colors = []

        for route in self.edge_routes:
            color = self.get_wire_colour(route["index"])
            points = route["points"]
            for index in range(len(points) - 1):
                all_vertices.extend([points[index], points[index + 1]])
                all_colors.extend([color, color])

        if not all_vertices:
            return

        vertex_data = np.array(all_vertices, dtype=np.float32)
        color_data = np.array(all_colors, dtype=np.float32)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        GL.glVertexPointer(2, GL.GL_FLOAT, 0, vertex_data)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, color_data)

        GL.glDrawArrays(GL.GL_LINES, 0, len(vertex_data))

        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

        for x_pos, y_pos, colour_index in self.junction_points:
            GL.glColor3f(*self.get_wire_colour(colour_index))
            self.draw_junction(x_pos, y_pos)

    def get_wire_colour(self, route_index):
        colours = [
            (0.0, 0.0, 1.0),
            (0.0, 0.55, 0.0),
            (0.8, 0.0, 0.0),
            (0.65, 0.0, 0.75),
            (0.0, 0.55, 0.65),
            (0.9, 0.45, 0.0),
            (0.4, 0.2, 0.7),
            (0.6, 0.4, 0.0),
        ]
        return colours[route_index % len(colours)]

    def get_pin_label(self, pin_id, device):
        """Return a display label for a pin ID."""
        if pin_id is None:
            return ""
        return self.names.get_name_string(pin_id)

    # def draw_rectangle(self, x_pos, y_pos, width, height):
    #     """Draw a rectangle outline."""
    #     GL.glBegin(GL.GL_LINE_LOOP)
    #     GL.glVertex2f(x_pos, y_pos)
    #     GL.glVertex2f(x_pos + width, y_pos)
    #     GL.glVertex2f(x_pos + width, y_pos + height)
    #     GL.glVertex2f(x_pos, y_pos + height)
    #     GL.glEnd()

    def draw_rectangle(self, x_pos, y_pos, width, height):
        """Draw a rectangle outline using Vertex Arrays."""
        vertices = np.array([
            [x_pos, y_pos],
            [x_pos + width, y_pos],
            [x_pos + width, y_pos + height],
            [x_pos, y_pos + height]
        ], dtype=np.float32)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, vertices)
        GL.glDrawArrays(GL.GL_LINE_LOOP, 0, 4)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

    # def draw_line(self, x_start, y_start, x_end, y_end):
    #     """Draw a single straight line."""
    #     GL.glBegin(GL.GL_LINES)
    #     GL.glVertex2f(x_start, y_start)
    #     GL.glVertex2f(x_end, y_end)
    #     GL.glEnd()

    def draw_line(self, x_start, y_start, x_end, y_end):
        """Draw a single straight line using Vertex Arrays."""
        vertices = np.array([
            [x_start, y_start],
            [x_end, y_end]
        ], dtype=np.float32)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, vertices)
        GL.glDrawArrays(GL.GL_LINES, 0, 2)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

    # def draw_junction(self, x_pos, y_pos, radius=3):
    #     """Draw a small filled square marking a wire junction."""
    #     GL.glBegin(GL.GL_QUADS)
    #     GL.glVertex2f(x_pos - radius, y_pos - radius)
    #     GL.glVertex2f(x_pos + radius, y_pos - radius)
    #     GL.glVertex2f(x_pos + radius, y_pos + radius)
    #     GL.glVertex2f(x_pos - radius, y_pos + radius)
    #     GL.glEnd()

    def draw_junction(self, x_pos, y_pos, radius=3):
        """Draw a filled square marking a wire junction using Triangle Strips."""
        vertices = np.array([
            [x_pos - radius, y_pos - radius],
            [x_pos + radius, y_pos - radius],
            [x_pos - radius, y_pos + radius],
            [x_pos + radius, y_pos + radius]
        ], dtype=np.float32)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, vertices)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)

    def text_width(self, text):
        """Return the pixel width of text in the label font."""
        font = GLUT.GLUT_BITMAP_HELVETICA_12
        return sum(GLUT.glutBitmapWidth(font, ord(c)) for c in str(text))

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12
        for character in str(text):
            GLUT.glutBitmapCharacter(font, ord(character))
