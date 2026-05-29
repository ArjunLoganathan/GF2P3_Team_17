"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It
    also contains handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing
                                           operations.
    """

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


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to change the circuit properties and run simulations.

    Parameters
    ----------
    title: title of the window.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_spin(self, event): Event handler for when the user changes the spin
                           control value.

    on_run_button(self, event): Event handler for when the user clicks the run
                                button.

    on_text_box(self, event): Event handler for when the user enters text.
    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(1000, 650))
        self.path = path
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.cycles_completed = 0
        self.switch_choices = {}
        self.monitor_choices = {}
        self.available_monitor_choices = {}

        # Configure the file menu
        file_menu = wx.Menu()
        menu_bar = wx.MenuBar()
        file_menu.Append(wx.ID_ABOUT, "&About")
        file_menu.Append(wx.ID_EXIT, "&Exit")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        # Canvas for drawing signals
        self.canvas = MyGLCanvas(self, devices, monitors)

        # Configure the widgets
        self.file_text = wx.StaticText(self, wx.ID_ANY, "File: " + path)
        self.cycle_text = wx.StaticText(self, wx.ID_ANY, "Cycles")
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", min=0, max=100000)
        self.completed_text = wx.StaticText(self, wx.ID_ANY,
                                            "Completed cycles: 0")
        self.run_button = wx.Button(self, wx.ID_ANY, "Run")
        self.continue_button = wx.Button(self, wx.ID_ANY, "Continue")
        self.switch_text = wx.StaticText(self, wx.ID_ANY, "Switch")
        self.switch_choice = wx.Choice(self, wx.ID_ANY)
        self.switch_state = wx.Choice(self, wx.ID_ANY, choices=["0", "1"])
        self.switch_state.SetSelection(0)
        self.set_switch_button = wx.Button(self, wx.ID_ANY, "Set Switch")
        self.add_monitor_text = wx.StaticText(self, wx.ID_ANY, "Add Monitor")
        self.add_monitor_choice = wx.Choice(self, wx.ID_ANY)
        self.add_monitor_button = wx.Button(self, wx.ID_ANY, "Add")
        self.remove_monitor_text = wx.StaticText(self, wx.ID_ANY,
                                                "Remove Monitor")
        self.remove_monitor_choice = wx.Choice(self, wx.ID_ANY)
        self.remove_monitor_button = wx.Button(self, wx.ID_ANY, "Remove")
        self.status = wx.StaticText(self, wx.ID_ANY, "Ready.")

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.set_switch_button.Bind(wx.EVT_BUTTON, self.on_set_switch_button)
        self.add_monitor_button.Bind(wx.EVT_BUTTON, self.on_add_monitor_button)
        self.remove_monitor_button.Bind(wx.EVT_BUTTON,
                                        self.on_remove_monitor_button)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.canvas, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

        side_sizer.Add(self.file_text, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.cycle_text, 0, wx.ALL, 5)
        side_sizer.Add(self.spin, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.completed_text, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.run_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.continue_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.switch_text, 0, wx.ALL, 5)
        side_sizer.Add(self.switch_choice, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.switch_state, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.set_switch_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.add_monitor_text, 0, wx.ALL, 5)
        side_sizer.Add(self.add_monitor_choice, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.add_monitor_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.remove_monitor_text, 0, wx.ALL, 5)
        side_sizer.Add(self.remove_monitor_choice, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.remove_monitor_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.status, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
        self.update_controls()
        wx.CallAfter(self.canvas.render, "Ready.")

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.Close(True)
        if menu_id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nGraphical user interface",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        cycles = self.spin.GetValue()
        self.cycles_completed = 0
        self.monitors.reset_monitors()
        self.devices.cold_startup()
        if self.run_network(cycles):
            self.cycles_completed = cycles
            self.update_controls()
            self.update_cycle_text()
            self.show_status("Ran for " + str(cycles) + " cycles.")

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        cycles = self.spin.GetValue()
        if self.cycles_completed == 0:
            self.show_status("Nothing to continue. Run first.")
            return
        if self.run_network(cycles):
            self.cycles_completed += cycles
            self.update_controls()
            self.update_cycle_text()
            self.show_status("Continued for " + str(cycles) +
                             " cycles. Total: " +
                             str(self.cycles_completed) + ".")

    def on_set_switch_button(self, event):
        """Handle the event when the user sets a switch."""
        switch_name = self.switch_choice.GetStringSelection()
        if not switch_name:
            self.show_status("No switch selected.")
            return
        switch_id = self.switch_choices[switch_name]
        switch_state = int(self.switch_state.GetStringSelection())
        if self.devices.set_switch(switch_id, switch_state):
            self.show_status("Set " + switch_name + " to " +
                             str(switch_state) + ".")
        else:
            self.show_status("Could not set switch " + switch_name + ".")

    def on_add_monitor_button(self, event):
        """Handle the event when the user adds a monitor."""
        monitor_name = self.add_monitor_choice.GetStringSelection()
        if not monitor_name:
            self.show_status("No available monitor selected.")
            return
        device_id, output_id = self.available_monitor_choices[monitor_name]
        error_type = self.monitors.make_monitor(device_id, output_id,
                                                self.cycles_completed)
        if error_type == self.monitors.NO_ERROR:
            self.update_controls()
            self.show_status("Added monitor " + monitor_name + ".")
        else:
            self.show_status("Could not add monitor " + monitor_name + ".")

    def on_remove_monitor_button(self, event):
        """Handle the event when the user removes a monitor."""
        monitor_name = self.remove_monitor_choice.GetStringSelection()
        if not monitor_name:
            self.show_status("No monitor selected.")
            return
        device_id, output_id = self.monitor_choices[monitor_name]
        if self.monitors.remove_monitor(device_id, output_id):
            self.update_controls()
            self.show_status("Removed monitor " + monitor_name + ".")
        else:
            self.show_status("Could not remove monitor " + monitor_name + ".")

    def run_network(self, cycles):
        """Run the network for the specified number of cycles."""
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                self.show_status("Error: network oscillating.")
                return False
        return True

    def update_controls(self):
        """Refresh all switch and monitor choice controls."""
        self.update_switch_choices()
        self.update_monitor_choices()
        self.update_button_states()
        self.update_cycle_text()

    def update_switch_choices(self):
        """Refresh the switch selector."""
        self.switch_choices = {}
        switch_names = []
        for switch_id in self.devices.find_devices(self.devices.SWITCH):
            switch_name = self.names.get_name_string(switch_id)
            if switch_name is not None:
                switch_names.append(switch_name)
                self.switch_choices[switch_name] = switch_id
        self.switch_choice.Set(switch_names)
        if switch_names:
            self.switch_choice.SetSelection(0)

    def update_monitor_choices(self):
        """Refresh the monitor selectors."""
        self.monitor_choices = {}
        self.available_monitor_choices = {}
        monitored_names, available_names = self.monitors.get_signal_names()

        for name in monitored_names:
            self.monitor_choices[name] = tuple(self.devices.get_signal_ids(name))
        for name in available_names:
            self.available_monitor_choices[name] = tuple(
                self.devices.get_signal_ids(name))

        self.remove_monitor_choice.Set(monitored_names)
        if monitored_names:
            self.remove_monitor_choice.SetSelection(0)
        self.add_monitor_choice.Set(available_names)
        if available_names:
            self.add_monitor_choice.SetSelection(0)

    def update_button_states(self):
        """Enable controls only when the related action is available."""
        has_switches = bool(self.switch_choices)
        has_monitors = bool(self.monitor_choices)
        has_available_monitors = bool(self.available_monitor_choices)

        self.continue_button.Enable(self.cycles_completed > 0)
        self.switch_choice.Enable(has_switches)
        self.switch_state.Enable(has_switches)
        self.set_switch_button.Enable(has_switches)
        self.add_monitor_choice.Enable(has_available_monitors)
        self.add_monitor_button.Enable(has_available_monitors)
        self.remove_monitor_choice.Enable(has_monitors)
        self.remove_monitor_button.Enable(has_monitors)

    def update_cycle_text(self):
        """Display the number of completed simulation cycles."""
        self.completed_text.SetLabel("Completed cycles: " +
                                     str(self.cycles_completed))

    def show_status(self, message):
        """Display a status message and redraw the canvas."""
        self.status.SetLabel(message)
        self.canvas.render(message)

