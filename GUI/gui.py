"""Implement the main graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
Gui - configures the main window and all the widgets.
"""
import io
from contextlib import redirect_stdout

import wx

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
from GUI.circuit_canvas import CircuitCanvas
from GUI.waveform_canvas import MyGLCanvas


def empty_model():
    """Build a fresh, empty simulator model."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    return names, devices, network, monitors


def compile_source(text):
    """Build a model from source text, capturing any parser error output.

    Return a tuple (ok, model, output) where model is the four-tuple of
    simulator objects on success or None on failure, and output is the
    captured parser messages.
    """
    names, devices, network, monitors = empty_model()
    buffer = io.StringIO()
    try:
        scanner = Scanner(None, names, source_text=text)
        parser = Parser(names, devices, network, monitors, scanner)
        with redirect_stdout(buffer):
            ok = parser.parse_network()
    except Exception as exc:
        return False, None, buffer.getvalue() + "\n" + str(exc)
    return ok, (names, devices, network, monitors), buffer.getvalue()


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

    def __init__(self, title, path, source_text=""):
        """Initialise widgets and layout, then compile the initial source."""
        super().__init__(parent=None, title=title, size=(1000, 650))
        self.path = path
        self.names, self.devices, self.network, self.monitors = empty_model()
        self.cycles_completed = 0
        self.switch_buttons = {}
        self.monitor_buttons = {}

        # Configure the file menu
        file_menu = wx.Menu()
        menu_bar = wx.MenuBar()
        file_menu.Append(wx.ID_HELP, "&Help")
        file_menu.Append(wx.ID_ABOUT, "&About")
        file_menu.Append(wx.ID_EXIT, "&Exit")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        # Canvas tabs for drawing signals and the circuit structure
        self.notebook = wx.Notebook(self)
        self.canvas = MyGLCanvas(self.notebook, self.devices, self.monitors)
        self.circuit_canvas = CircuitCanvas(self.notebook, self.names,
                                            self.devices)
        self.compiler_panel = self.build_compiler_panel(self.notebook)
        self.notebook.AddPage(self.canvas, "Waveforms")
        self.notebook.AddPage(self.circuit_canvas, "Circuit")
        self.notebook.AddPage(self.compiler_panel, "Compiler")

        # Configure the widgets
        self.file_text = wx.StaticText(self, wx.ID_ANY,
                                       "File: " + (path or "(none)"))
        self.cycle_text = wx.StaticText(self, wx.ID_ANY, "Cycles")
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", min=0, max=100000)
        self.completed_text = wx.StaticText(self, wx.ID_ANY,
                                            "Completed cycles: 0")
        self.run_button = wx.Button(self, wx.ID_ANY, "Run")
        self.continue_button = wx.Button(self, wx.ID_ANY, "Continue")
        self.switch_text = wx.StaticText(self, wx.ID_ANY, "Switches")
        self.switch_panel = wx.ScrolledWindow(self, wx.ID_ANY,
                                              style=wx.VSCROLL | wx.BORDER_SIMPLE)
        self.switch_panel.SetScrollRate(0, 10)
        self.switch_panel.SetMinSize((-1, 160))
        self.switch_sizer = wx.BoxSizer(wx.VERTICAL)
        self.switch_panel.SetSizer(self.switch_sizer)
        self.monitor_text = wx.StaticText(self, wx.ID_ANY, "Monitors")
        self.monitor_panel = wx.ScrolledWindow(self, wx.ID_ANY,
                                               style=wx.VSCROLL | wx.BORDER_SIMPLE)
        self.monitor_panel.SetScrollRate(0, 10)
        self.monitor_panel.SetMinSize((-1, 160))
        self.monitor_sizer = wx.BoxSizer(wx.VERTICAL)
        self.monitor_panel.SetSizer(self.monitor_sizer)
        self.status = wx.StaticText(self, wx.ID_ANY, "Ready.")

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.notebook, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

        side_sizer.Add(self.file_text, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.cycle_text, 0, wx.ALL, 5)
        side_sizer.Add(self.spin, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.completed_text, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.run_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.Add(self.continue_button, 0, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.switch_text, 0, wx.ALL, 5)
        side_sizer.Add(self.switch_panel, 1, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.monitor_text, 0, wx.ALL, 5)
        side_sizer.Add(self.monitor_panel, 1, wx.ALL | wx.EXPAND, 5)
        side_sizer.AddSpacer(15)
        side_sizer.Add(self.status, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
        self.editor.SetValue(source_text)
        self.update_controls()
        if source_text.strip():
            self.on_compile()
        else:
            wx.CallAfter(self.canvas.render, "Ready.")
            wx.CallAfter(self.circuit_canvas.render)

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.Close(True)
        if menu_id == wx.ID_HELP:
            wx.MessageBox("Run: start from cycle 0 with cleared traces.\n"
                          "Continue: add more cycles to the current run.\n"
                          "Switches: click a switch's toggle to flip it 0/1.\n"
                          "Monitors: toggle each output On/Off to show it.",
                          "Logsim Help", wx.ICON_INFORMATION | wx.OK)
        if menu_id == wx.ID_ABOUT:
            wx.MessageBox("Logic Simulator\nGraphical user interface",
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def build_compiler_panel(self, parent):
        """Build the Compiler tab: an editor, a Compile button, and results."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        code_font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL)

        self.editor = wx.TextCtrl(panel, wx.ID_ANY,
                                  style=wx.TE_MULTILINE | wx.HSCROLL)
        self.editor.SetFont(code_font)
        self.compile_button = wx.Button(panel, wx.ID_ANY, "Compile")
        self.compile_button.Bind(wx.EVT_BUTTON, self.on_compile)
        self.compiler_output = wx.TextCtrl(
            panel, wx.ID_ANY,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.compiler_output.SetFont(code_font)

        sizer.Add(wx.StaticText(panel, wx.ID_ANY, "Circuit definition:"),
                  0, wx.ALL, 5)
        sizer.Add(self.editor, 3, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.compile_button, 0, wx.ALL, 5)
        sizer.Add(wx.StaticText(panel, wx.ID_ANY, "Result:"), 0, wx.ALL, 5)
        sizer.Add(self.compiler_output, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel

    def on_compile(self, event=None):
        """Compile the editor text and refresh everything on success."""
        ok, model, output = compile_source(self.editor.GetValue())
        if ok and model is not None:
            self.load_model(model)
            message = "Compilation successful."
            if output.strip():
                message += "\n\n" + output
            self.compiler_output.SetValue(message)
            self.show_status("Compilation successful.")
        else:
            self.compiler_output.SetValue(
                output.strip() or "Compilation failed.")
            self.show_status("Compilation failed. See the Compiler tab.")

    def load_model(self, model):
        """Point the GUI and canvases at a freshly compiled model."""
        self.names, self.devices, self.network, self.monitors = model
        self.canvas.devices = self.devices
        self.canvas.monitors = self.monitors
        self.circuit_canvas.names = self.names
        self.circuit_canvas.devices = self.devices
        self.cycles_completed = 0
        self.update_controls()
        self.circuit_canvas.init = False
        wx.CallAfter(self.canvas.render, "Ready.")
        wx.CallAfter(self.circuit_canvas.render)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        cycles = self.spin.GetValue()
        self.cycles_completed = 0
        self.monitors.reset_monitors()
        self.devices.cold_startup()
        if self.run_network(cycles):
            self.cycles_completed = cycles
            self.update_controls()
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
            self.show_status("Continued for " + str(cycles) +
                             " cycles. Total: " +
                             str(self.cycles_completed) + ".")

    def on_toggle_switch(self, event):
        """Handle a switch toggle, applying the new state immediately."""
        toggle = event.GetEventObject()
        switch_id = self.switch_buttons[toggle]
        switch_name = self.names.get_name_string(switch_id)
        switch_state = 1 if toggle.GetValue() else 0
        if self.devices.set_switch(switch_id, switch_state):
            self.style_switch_toggle(toggle, switch_state)
            self.show_status("Set " + switch_name + " to " +
                             str(switch_state) + ".")
        else:
            toggle.SetValue(switch_state == 0)
            self.style_switch_toggle(toggle, 1 - switch_state)
            self.show_status("Could not set switch " + switch_name + ".")

    def style_switch_toggle(self, toggle, state):
        """Update a switch toggle's label to show its 0/1 state."""
        toggle.SetLabel(str(state))

    def on_toggle_monitor(self, event):
        """Handle a monitor toggle, adding or removing it immediately."""
        toggle = event.GetEventObject()
        device_id, output_id = self.monitor_buttons[toggle]
        monitor_name = self.devices.get_signal_name(device_id, output_id)
        if toggle.GetValue():
            error_type = self.monitors.make_monitor(device_id, output_id,
                                                    self.cycles_completed)
            if error_type == self.monitors.NO_ERROR:
                toggle.SetLabel("On")
                self.show_status("Added monitor " + monitor_name + ".")
            else:
                toggle.SetValue(False)
                self.show_status("Could not add monitor " + monitor_name + ".")
        else:
            if self.monitors.remove_monitor(device_id, output_id):
                toggle.SetLabel("Off")
                self.show_status("Removed monitor " + monitor_name + ".")
            else:
                toggle.SetValue(True)
                self.show_status("Could not remove monitor " +
                                 monitor_name + ".")

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
        """Rebuild one toggle button per switch, reflecting its current state."""
        self.switch_sizer.Clear(delete_windows=True)
        self.switch_buttons = {}
        for switch_id in self.devices.find_devices(self.devices.SWITCH):
            switch_name = self.names.get_name_string(switch_id)
            if switch_name is None:
                continue
            state = self.devices.get_device(switch_id).switch_state
            row = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self.switch_panel, wx.ID_ANY, switch_name)
            toggle = wx.ToggleButton(self.switch_panel, wx.ID_ANY,
                                     str(state), size=(40, -1))
            toggle.SetValue(state == 1)
            toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_switch)
            self.switch_buttons[toggle] = switch_id
            row.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
            row.Add(toggle, 0, wx.ALL, 2)
            self.switch_sizer.Add(row, 0, wx.EXPAND)
        self.switch_panel.Layout()
        self.switch_panel.FitInside()

    def update_monitor_choices(self):
        """Rebuild one toggle per output, reflecting whether it is monitored."""
        self.monitor_sizer.Clear(delete_windows=True)
        self.monitor_buttons = {}
        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)
            for output_id in device.outputs:
                name = self.devices.get_signal_name(device_id, output_id)
                monitored = (device_id, output_id) in \
                    self.monitors.monitors_dictionary
                row = wx.BoxSizer(wx.HORIZONTAL)
                label = wx.StaticText(self.monitor_panel, wx.ID_ANY, name)
                toggle = wx.ToggleButton(self.monitor_panel, wx.ID_ANY,
                                         "On" if monitored else "Off",
                                         size=(50, -1))
                toggle.SetValue(monitored)
                toggle.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_monitor)
                self.monitor_buttons[toggle] = (device_id, output_id)
                row.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
                row.Add(toggle, 0, wx.ALL, 2)
                self.monitor_sizer.Add(row, 0, wx.EXPAND)
        self.monitor_panel.Layout()
        self.monitor_panel.FitInside()

    def update_button_states(self):
        """Enable controls only when the related action is available."""
        self.continue_button.Enable(self.cycles_completed > 0)

    def update_cycle_text(self):
        """Display the number of completed simulation cycles."""
        self.completed_text.SetLabel("Completed cycles: " +
                                     str(self.cycles_completed))

    def show_status(self, message):
        """Display a status message and redraw the canvas."""
        self.status.SetLabel(message)
        self.canvas.render(message)

