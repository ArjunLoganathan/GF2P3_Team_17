"""Implement the main graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
Gui - configures the main window and all the widgets.
"""
import wx
from GUI.circuit_canvas import CircuitCanvas
from GUI.waveform_canvas import MyGLCanvas


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
        file_menu.Append(wx.ID_HELP, "&Help")
        file_menu.Append(wx.ID_ABOUT, "&About")
        file_menu.Append(wx.ID_EXIT, "&Exit")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        # Canvas tabs for drawing signals and the circuit structure
        self.notebook = wx.Notebook(self)
        self.canvas = MyGLCanvas(self.notebook, devices, monitors)
        self.circuit_canvas = CircuitCanvas(self.notebook, names, devices)
        self.notebook.AddPage(self.canvas, "Waveforms")
        self.notebook.AddPage(self.circuit_canvas, "Circuit")

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
        wx.CallAfter(self.circuit_canvas.render)

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.Close(True)
        if menu_id == wx.ID_HELP:
            wx.MessageBox("Run: start from cycle 0 with cleared traces.\n"
                          "Continue: add more cycles to the current run.\n"
                          "Set Switch: choose a switch and set it to 0 or 1.\n"
                          "Add/Remove Monitor: choose which outputs to show.",
                          "Logsim Help", wx.ICON_INFORMATION | wx.OK)
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
        self.set_choice_items(self.switch_choice, switch_names)

    def update_monitor_choices(self):
        """Refresh the monitor selectors."""
        self.monitor_choices = {}
        self.available_monitor_choices = {}
        monitored_names = []
        available_names = []

        for device_id, output_id in self.monitors.monitors_dictionary:
            name = self.devices.get_signal_name(device_id, output_id)
            monitored_names.append(name)
            self.monitor_choices[name] = (device_id, output_id)

        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)
            for output_id in device.outputs:
                if (device_id, output_id) not in self.monitors.monitors_dictionary:
                    name = self.devices.get_signal_name(device_id, output_id)
                    available_names.append(name)
                    self.available_monitor_choices[name] = (device_id,
                                                            output_id)

        self.set_choice_items(self.remove_monitor_choice, monitored_names)
        self.set_choice_items(self.add_monitor_choice, available_names)

    def set_choice_items(self, choice, items):
        """Refresh a choice control while preserving its selection."""
        previous_selection = choice.GetStringSelection()
        choice.Set(items)
        if previous_selection in items:
            choice.SetStringSelection(previous_selection)
        elif items:
            choice.SetSelection(0)

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

