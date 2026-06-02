"""Circuit visualiser canvas for the Logic Simulator GUI."""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT


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
        if not self.IsShownOnScreen():
            return
        self.SetCurrent(self.context)
        if not self.init:
            self.init_gl()
            self.init = True
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

    def calculate_layout(self, canvas_height):
        """Calculate device and pin positions for the circuit view."""
        columns = {0: [], 1: [], 2: []}
        for device in self.devices.devices_list:
            columns[self.get_device_column(device)].append(device)

        box_width = 160
        box_height = 90
        column_width = 320
        row_height = 140
        pin_stub = 14
        self.device_positions = {}
        self.input_pin_positions = {}
        self.output_pin_positions = {}
        self.input_wire_positions = {}
        self.output_wire_positions = {}

        for column, column_devices in columns.items():
            for row, device in enumerate(column_devices):
                x_pos = 90 + column * column_width
                y_pos = canvas_height - 150 - row * row_height
                self.device_positions[device.device_id] = (
                    x_pos, y_pos, box_width, box_height)
                self.store_pin_positions(device, x_pos, y_pos,
                                         box_width, box_height, pin_stub)

    def get_device_column(self, device):
        """Return a simple layout column for the device."""
        if device.device_kind in [self.devices.SWITCH, self.devices.CLOCK]:
            return 0
        if device.device_kind in self.devices.gate_types:
            return 1
        return 2

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
                    self.render_text(label, pin_x + 8, pin_y - 4)

            for output_id in device.outputs:
                pin_x, pin_y = self.output_pin_positions[
                    (device.device_id, output_id)]
                wire_x, wire_y = self.output_wire_positions[
                    (device.device_id, output_id)]
                self.draw_line(pin_x, pin_y, wire_x, wire_y)
                label = self.get_pin_label(output_id, device)
                if label:
                    self.render_text(label, pin_x - 36, pin_y - 4)

    def draw_connections(self):
        """Draw orthogonal lines for all connected inputs."""
        connections = []
        for device in self.devices.devices_list:
            for input_id, connected_output in device.inputs.items():
                if connected_output is None:
                    continue
                output_device_id, output_id = connected_output
                source = self.output_wire_positions.get((output_device_id,
                                                         output_id))
                target = self.input_wire_positions.get((device.device_id,
                                                        input_id))
                if source is None or target is None:
                    continue
                connections.append((connected_output, source, target))

        source_routes = {}
        for source_key, source, target in connections:
            if source_key not in source_routes:
                source_routes[source_key] = len(source_routes)

            route_index = source_routes[source_key]
            GL.glColor3f(*self.get_wire_colour(route_index))
            source_x, source_y = source
            target_x, target_y = target
            mid_x = self.get_route_x(source_x, target_x, route_index)
            self.draw_line(source_x, source_y, mid_x, source_y)
            self.draw_line(mid_x, source_y, mid_x, target_y)
            self.draw_line(mid_x, target_y, target_x, target_y)

    def get_route_x(self, source_x, target_x, route_index):
        """Return a vertical route x-position for a source output."""
        route_gap = 28
        first_gap = 35
        if source_x <= target_x:
            max_gap = max(20, target_x - source_x - 20)
            route_gap_x = min(first_gap + route_index * route_gap, max_gap)
            return source_x + route_gap_x

        max_gap = max(20, source_x - target_x - 20)
        route_gap_x = min(first_gap + route_index * route_gap, max_gap)
        return source_x - route_gap_x

    def get_wire_colour(self, route_index):
        """Return a repeatable colour for a wire route."""
        colours = [
            (0.0, 0.0, 1.0),
            (0.0, 0.55, 0.0),
            (0.8, 0.0, 0.0),
            (0.65, 0.0, 0.75),
            (0.0, 0.55, 0.65),
            (0.9, 0.45, 0.0),
        ]
        return colours[route_index % len(colours)]

    def get_pin_label(self, pin_id, device):
        """Return a display label for a pin ID."""
        if pin_id is None:
            return ""
        if device.device_kind in self.devices.gate_types:
            return ""
        return self.names.get_name_string(pin_id)

    def draw_rectangle(self, x_pos, y_pos, width, height):
        """Draw a rectangle outline."""
        GL.glBegin(GL.GL_LINE_LOOP)
        GL.glVertex2f(x_pos, y_pos)
        GL.glVertex2f(x_pos + width, y_pos)
        GL.glVertex2f(x_pos + width, y_pos + height)
        GL.glVertex2f(x_pos, y_pos + height)
        GL.glEnd()

    def draw_line(self, x_start, y_start, x_end, y_end):
        """Draw a single straight line."""
        GL.glBegin(GL.GL_LINES)
        GL.glVertex2f(x_start, y_start)
        GL.glVertex2f(x_end, y_end)
        GL.glEnd()

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12
        for character in str(text):
            GLUT.glutBitmapCharacter(font, ord(character))
