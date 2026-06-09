"""Waveform drawing canvas for the Logic Simulator GUI."""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle waveform drawing operations."""

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)
        self.devices = devices
        self.monitors = monitors
        self.visible_monitors = None
        self.status_text = "Load a circuit, then run the simulation."

        # Initialise variables for panning
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0  # previous mouse x position
        self.last_mouse_y = 0  # previous mouse y position

        # Initialise variables for zooming
        self.zoom = 1

        # Bind events to the canvas
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

    def render(self, text=None):
        """Handle all drawing operations."""
        if not self.IsShownOnScreen():
            return
        self.SetCurrent(self.context)
        self.status_text = text or self.status_text
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        # Clear everything
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        size = self.GetClientSize()
        self.render_text(self.status_text, 10, size.height - 20)
        self.draw_monitor_traces(size.width, size.height)

        # We have been drawing to the back buffer, flush the graphics pipeline
        # and swap the back buffer to the front
        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle the paint event."""
        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        needs_render = False
        # Calculate object coordinates of the mouse position
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            needs_render = True
        if event.ButtonUp() or event.Leaving():
            needs_render = True
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            needs_render = True
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            needs_render = True
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            needs_render = True
        if needs_render:
            self.render(self.status_text)
        else:
            self.Refresh()  # triggers the paint event

    def draw_monitor_traces(self, canvas_width, canvas_height):
        """Draw the recorded signal traces for all current monitors."""
        monitor_items = list(self.monitors.monitors_dictionary.items())
        if self.visible_monitors is not None:
            monitor_items = [
                item for item in monitor_items
                if item[0] in self.visible_monitors
            ]

        if not monitor_items:
            self.render_text("No monitor points selected.", 10,
                             canvas_height - 55)
            return

        left_margin = 130
        right_margin = 20
        row_height = 55
        first_row_y = canvas_height - 95
        longest_trace = max(
            len(signal_list)
            for _, signal_list in monitor_items)
        drawable_width = max(1, canvas_width - left_margin - right_margin)
        cycle_width = min(20, max(8, drawable_width / max(1, longest_trace)))
        visible_rows = min(
            len(monitor_items),
            max(1, int((first_row_y - 25) / row_height) + 1)
        )

        self.draw_cycle_grid(left_margin, first_row_y, row_height,
                             visible_rows, longest_trace, cycle_width)

        for row, ((device_id, output_id), signal_list) in enumerate(
                monitor_items):
            base_y = first_row_y - row * row_height
            if base_y < 25:
                self.render_text("More monitors below...", 10, 10)
                break
            low_y = base_y
            high_y = base_y + 22
            label = self.devices.get_signal_name(device_id, output_id)

            self.render_text(label, 10, low_y + 6)
            GL.glColor3f(0.85, 0.85, 0.85)
            self.draw_line(left_margin, low_y, left_margin +
                           max(1, len(signal_list)) * cycle_width, low_y)
            self.draw_line(left_margin, high_y, left_margin +
                           max(1, len(signal_list)) * cycle_width, high_y)

            GL.glColor3f(0.0, 0.0, 1.0)
            previous_y = None
            for index, signal in enumerate(signal_list):
                x_start = left_margin + index * cycle_width
                x_end = x_start + cycle_width

                if signal in [self.devices.HIGH, self.devices.RISING]:
                    current_y = high_y
                elif signal in [self.devices.LOW, self.devices.FALLING]:
                    current_y = low_y
                elif signal == self.devices.BLANK:
                    GL.glColor3f(0.6, 0.6, 0.6)
                    self.draw_line(x_start, low_y + 11, x_end, low_y + 11)
                    GL.glColor3f(0.0, 0.0, 1.0)
                    previous_y = None
                    continue
                else:
                    continue

                if previous_y is not None and previous_y != current_y:
                    self.draw_line(x_start, previous_y, x_start, current_y)
                self.draw_line(x_start, current_y, x_end, current_y)
                previous_y = current_y

    def draw_cycle_grid(self, left_margin, first_row_y, row_height,
                        visible_rows, longest_trace, cycle_width):
        """Draw vertical guide lines for each simulation cycle."""
        top_y = first_row_y + 30
        bottom_y = first_row_y - (visible_rows - 1) * row_height - 10

        GL.glColor3f(0.9, 0.9, 0.9)
        for cycle in range(longest_trace + 1):
            x_pos = left_margin + cycle * cycle_width
            self.draw_line(x_pos, bottom_y, x_pos, top_y)

            if cycle_width >= 14 or cycle % 5 == 0:
                self.render_text(str(cycle), x_pos - 3, top_y + 12)
                GL.glColor3f(0.9, 0.9, 0.9)

    def draw_line(self, x_start, y_start, x_end, y_end):
        """Draw a single straight line."""
        GL.glBegin(GL.GL_LINES)
        GL.glVertex2f(x_start, y_start)
        GL.glVertex2f(x_end, y_end)
        GL.glEnd()

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)  # text is black
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == '\n':
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))
