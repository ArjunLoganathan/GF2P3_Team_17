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
        if not self.IsShownOnScreen():
            return
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices
            self.init_gl()
            self.init = True

        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event
        self.init = False

    def on_mouse(self, event):
        """Handle mouse events."""
        text = ""
        # Calculate object coordinates of the mouse position
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])
        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])
        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])
        if text:
            self.render(self.status_text)
        else:
            self.Refresh()  # triggers the paint event

    def draw_monitor_traces(self, canvas_width, canvas_height):
        """Draw the recorded signal traces for all current monitors."""
        if not self.monitors.monitors_dictionary:
            self.render_text("No monitor points selected.", 10,
                             canvas_height - 55)
            return

        left_margin = 130
        right_margin = 20
        row_height = 55
        first_row_y = canvas_height - 95
        longest_trace = max(
            len(signal_list)
            for signal_list in self.monitors.monitors_dictionary.values())
        drawable_width = max(1, canvas_width - left_margin - right_margin)
        cycle_width = min(20, max(8, drawable_width / max(1, longest_trace)))

        for row, ((device_id, output_id), signal_list) in enumerate(
                self.monitors.monitors_dictionary.items()):
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
            for index, signal in enumerate(signal_list):
                x_start = left_margin + index * cycle_width
                x_end = x_start + cycle_width
                if signal == self.devices.HIGH:
                    self.draw_line(x_start, high_y, x_end, high_y)
                elif signal == self.devices.LOW:
                    self.draw_line(x_start, low_y, x_end, low_y)
                elif signal == self.devices.RISING:
                    self.draw_line(x_start, low_y, x_end, high_y)
                elif signal == self.devices.FALLING:
                    self.draw_line(x_start, high_y, x_end, low_y)
                elif signal == self.devices.BLANK:
                    GL.glColor3f(0.6, 0.6, 0.6)
                    self.draw_line(x_start, low_y + 11, x_end, low_y + 11)
                    GL.glColor3f(0.0, 0.0, 1.0)

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
