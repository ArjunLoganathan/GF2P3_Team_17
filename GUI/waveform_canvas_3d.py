"""3D waveform drawing canvas for the Logic Simulator GUI."""
import math

import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLU, GLUT


class WaveformCanvas3D(wxcanvas.GLCanvas):
    """Draw monitored signal traces as simple 3D blocks."""

    def __init__(self, parent, devices, monitors):
        """Initialise canvas state."""
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
        self.status_text = "3D waveform view."
        self.pan_x = 0
        self.pan_y = 0
        self.zoom = 1
        self.depth_offset = 900
        self.rotate_x = 25
        self.rotate_y = -35
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def init_gl(self):
        """Configure the OpenGL perspective view."""
        size = self.GetClientSize()
        width = max(size.width, 1)
        height = max(size.height, 1)
        self.SetCurrent(self.context)
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(45, width / height, 10, 10000)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glClearColor(0.02, 0.02, 0.03, 0.0)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LEQUAL)

    def render(self, text=None):
        """Draw the 3D waveform scene."""
        if not self.IsShownOnScreen():
            return
        self.SetCurrent(self.context)
        self.status_text = text or self.status_text
        if not self.init:
            self.init_gl()
            self.init = True

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslatef(self.pan_x, self.pan_y, -self.depth_offset)
        GL.glScalef(self.zoom, self.zoom, self.zoom)
        GL.glRotatef(self.rotate_x, 1, 0, 0)
        GL.glRotatef(self.rotate_y, 0, 1, 0)

        self.draw_monitor_traces()
        GL.glColor3f(1.0, 1.0, 1.0)
        self.render_text(self.status_text, -320, 220, 0)

        GL.glFlush()
        self.SwapBuffers()

    def on_paint(self, event):
        """Handle redraw events."""
        self.render()

    def on_size(self, event):
        """Reinitialise projection after resize."""
        self.init = False
        self.Refresh()

    def on_mouse(self, event):
        """Rotate, pan and zoom the 3D scene."""
        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
        if event.Dragging():
            dx = event.GetX() - self.last_mouse_x
            dy = event.GetY() - self.last_mouse_y
            if event.LeftIsDown():
                self.rotate_y += dx * 0.5
                self.rotate_x += dy * 0.5
            elif event.RightIsDown():
                self.pan_x += dx
                self.pan_y -= dy
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.Refresh()
        if event.GetWheelRotation() < 0:
            self.zoom *= 0.9
            self.Refresh()
        if event.GetWheelRotation() > 0:
            self.zoom *= 1.1
            self.Refresh()

    def draw_monitor_traces(self):
        """Draw every visible monitor trace as a row of cuboids."""
        monitor_items = list(self.monitors.monitors_dictionary.items())
        if self.visible_monitors is not None:
            monitor_items = [
                item for item in monitor_items if item[0] in self.visible_monitors
            ]

        if not monitor_items:
            GL.glColor3f(1.0, 1.0, 1.0)
            self.render_text("No monitor points selected.", -220, 0, 0)
            return

        cycle_width = 20
        row_spacing = 55
        start_x = -240
        start_z = -120

        for row, ((device_id, output_id), signal_list) in enumerate(
                monitor_items):
            z_pos = start_z + row * row_spacing
            label = self.devices.get_signal_name(device_id, output_id)
            GL.glColor3f(1.0, 1.0, 1.0)
            self.render_text(label, start_x - 95, 0, z_pos)

            for index, signal in enumerate(signal_list):
                x_pos = start_x + index * cycle_width
                height = self.signal_height(signal)
                GL.glColor3f(*self.signal_colour(signal))
                self.draw_cuboid(x_pos, z_pos, 8, 8, height)

    def signal_height(self, signal):
        """Return a cuboid height for a signal level."""
        if signal == self.devices.HIGH:
            return 36
        if signal == self.devices.RISING:
            return 28
        if signal == self.devices.FALLING:
            return 18
        if signal == self.devices.BLANK:
            return 6
        return 10

    def signal_colour(self, signal):
        """Return a colour for a signal level."""
        if signal == self.devices.HIGH:
            return 0.2, 0.8, 1.0
        if signal == self.devices.LOW:
            return 0.1, 0.25, 0.8
        if signal == self.devices.RISING:
            return 0.1, 0.9, 0.25
        if signal == self.devices.FALLING:
            return 1.0, 0.4, 0.1
        return 0.45, 0.45, 0.45

    def draw_cuboid(self, x_pos, z_pos, half_width, half_depth, height):
        """Draw a cuboid standing on the y=0 plane."""
        y_low = 0
        y_high = height
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, y_low, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, y_high, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, y_low, z_pos + half_depth)
        GL.glEnd()

    def render_text(self, text, x_pos, y_pos, z_pos):
        """Draw bitmap text in 3D space."""
        GL.glRasterPos3f(x_pos, y_pos, z_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12
        for character in str(text):
            GLUT.glutBitmapCharacter(font, ord(character))
