"""Implement the main graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation
or adjust the network properties.

Classes:
--------
Gui - configures the main window and all the widgets.
"""
import io
import os
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
from GUI.waveform_canvas_3d import WaveformCanvas3D


SPANISH_TRANSLATIONS = {
    "Logic Simulator": "Simulador Lógico",
    "File": "Archivo",
    "Help": "Ayuda",
    "About": "Acerca de",
    "Exit": "Salir",
    "Language": "Idioma",
    "English": "Inglés",
    "Spanish": "Español",
    "Chinese": "Chino",
    "Waveforms 2D": "Ondas 2D",
    "Waveforms 3D": "Ondas 3D",
    "Circuit": "Circuito",
    "Compiler": "Compilador",
    "Cycles": "Ciclos",
    "Completed cycles: ": "Ciclos completados: ",
    "Run": "Ejecutar",
    "Continue": "Continuar",
    "Switches": "Interruptores",
    "Monitors": "Monitores",
    "Ready.": "Listo.",
    "Circuit definition:": "Definicion del circuito:",
    "Compile": "Compilar",
    "Result:": "Resultado:",
    "Compilation successful.": "Compilacion exitosa.",
    "Compilation failed. See the Compiler tab.": "Compilacion fallida. Ver pestaña del Compilador.",
    "Nothing to continue. Run first.": "Nada que continuar. Ejecute primero.",
    "Error: network oscillating.": "Error: oscilacion de red.",
    "On": "Encendido",
    "Off": "Apagado",
    "Showing monitor {}": "Mostrando monitor {}",
    "Hid monitor {}": "Oculto monitor {}",
    "Set {} to {}": "Configurado {} a {}",
    "Opened file: ": "Archivo abierto: ",
    "Saved file: ": "Archivo guardado: ", 
    "Open": "Abrir", 
    "Save": "Guardar", 
    "Save As": "Guardar como",
    "Circuit visualiser": "Visualizador de circuitos",
    "Load a circuit, then run the simulation.": "Cargue un circuito y ejecute la simulación.",
    "No monitor points selected.": "No hay puntos de monitorización seleccionados.",
    "More monitors below...": "Más monitores abajo...",
    "3D waveform view.": "Vista de ondas 3D.",
    "Ran for {} cycles.": "Se ejecutó por {} ciclos.",
    "Continued for {} cycles. Total: {}.": "Se continuó por {} ciclos. Total: {}.",
    "Could not set switch {}.": "No se pudo configurar el interruptor {}.",
    "Could not add monitor {}.": "No se pudo agregar el monitor {}."
}

CHINESE_TRANSLATIONS = {
    "Logic Simulator": "逻辑模拟器",
    "File": "文件",
    "Help": "帮助",
    "About": "关于",
    "Exit": "退出",
    "Language": "语言",
    "English": "英语",
    "Spanish": "西班牙语",
    "Chinese": "中文",
    "Waveforms 2D": "二维波形",
    "Waveforms 3D": "三维波形",
    "Circuit": "电路",
    "Compiler": "编译器",
    "Cycles": "周期",
    "Completed cycles: ": "已完成周期: ",
    "Run": "运行",
    "Continue": "继续",
    "Switches": "开关",
    "Monitors": "监视器",
    "Ready.": "就绪。",
    "Circuit definition:": "电路定义:",
    "Compile": "编译",
    "Result:": "结果:",
    "Compilation successful.": "编译成功。",
    "Compilation failed. See the Compiler tab.": "编译失败。请参阅编译器选项卡。",
    "Nothing to continue. Run first.": "没有可以继续的内容。请先运行。",
    "Error: network oscillating.": "错误：网络振荡。",
    "On": "开",
    "Off": "关",
    "Showing monitor {}": "显示监视器 {}",
    "Hid monitor {}": "隐藏监视器 {}",
    "Set {} to {}": "设置 {} 为 {}",
    "Open": "打开",
    "Save": "保存",
    "Save As": "另存为",
    "Opened file: ": "已打开文件: ", 
    "Saved file: ": "已保存文件: ", 
    "Cannot open file '%s'.": "无法打开文件 '%s'.", 
    "Cannot save current data in file '%s'.": "无法将当前数据保存到文件 '%s'.",
    "Circuit visualiser": "电路可视化器",
    "Load a circuit, then run the simulation.": "加载电路，然后运行模拟。",
    "No monitor points selected.": "未选择监视点。",
    "More monitors below...": "下面有更多监视器...",
    "3D waveform view.": "3D 波形视图。",
    "Ran for {} cycles.": "运行了 {} 个周期。",
    "Continued for {} cycles. Total: {}.": "继续了 {} 个周期。总计: {}。",
    "Could not set switch {}.": "无法设置开关 {}。",
    "Could not add monitor {}.": "无法添加监视器 {}。"
}

def empty_model():
    """Build a fresh, empty simulator model."""
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    return names, devices, network, monitors


def compile_source(text):
    """Build a model from source text, capturing any parser error output."""
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
    """Configure the main window and all the widgets."""

    def __init__(self, title, path, source_text=""):
        """Initialise widgets and layout, then compile the initial source."""
        super().__init__(parent=None, title=title, size=(1000, 650))
        self.path = path
        self.names, self.devices, self.network, self.monitors = empty_model()
        self.cycles_completed = 0
        self.switch_buttons = {}
        self.monitor_buttons = {}
        self.visible_monitors = set()

        # Detect language from the Command Line (LANG=...) or Desktop Settings
        self.current_language = "English"
        lang_env = os.environ.get('LANG', '').lower()
        wx_loc = wx.GetLocale()
        sys_lang = wx_loc.GetCanonicalName().lower() if wx_loc else ""

        if 'es' in lang_env or 'es' in sys_lang:
            self.current_language = "Spanish"
        elif 'zh' in lang_env or 'zh' in sys_lang:
            self.current_language = "Chinese"

        # Apply translated title if necessary
        self.SetTitle(self.tr("Logic Simulator"))

        # Configure the file and language menu
        self.file_menu = wx.Menu()
        self.menu_bar = wx.MenuBar()
        
        self.file_menu.Append(wx.ID_OPEN, self.tr("Open"))
        self.file_menu.Append(wx.ID_SAVE, self.tr("Save"))
        self.file_menu.Append(wx.ID_SAVEAS, self.tr("Save As"))
        self.file_menu.AppendSeparator()
        
        self.file_menu.Append(wx.ID_HELP, self.tr("Help"))
        self.file_menu.Append(wx.ID_ABOUT, self.tr("About"))
        self.file_menu.AppendSeparator()       
        self.file_menu.Append(wx.ID_EXIT, self.tr("Exit"))

        self.menu_bar.Append(self.file_menu, self.tr("File"))

        self.lang_menu = wx.Menu()
        self.id_lang_en = wx.NewIdRef()
        self.id_lang_es = wx.NewIdRef()
        self.id_lang_zh = wx.NewIdRef()
        self.lang_menu.Append(self.id_lang_en, self.tr("English"))
        self.lang_menu.Append(self.id_lang_es, self.tr("Spanish"))
        self.lang_menu.Append(self.id_lang_zh, self.tr("Chinese"))

        self.menu_bar.Append(self.lang_menu, self.tr("Language"))

        self.SetMenuBar(self.menu_bar)

        # Canvas tabs for drawing signals and the circuit structure
        self.notebook = wx.Notebook(self)
        self.canvas_2d = MyGLCanvas(self.notebook, self.devices, self.monitors)
        self.canvas_2d.visible_monitors = self.visible_monitors
        self.canvas_3d = WaveformCanvas3D(self.notebook, self.devices,
                                          self.monitors)
        self.canvas_3d.visible_monitors = self.visible_monitors
        self.circuit_canvas = CircuitCanvas(self.notebook, self.names,
                                            self.devices)
        self.compiler_panel = self.build_compiler_panel(self.notebook)

        self.notebook.AddPage(self.canvas_2d, self.tr("Waveforms 2D"))
        self.notebook.AddPage(self.canvas_3d, self.tr("Waveforms 3D"))
        self.notebook.AddPage(self.circuit_canvas, self.tr("Circuit"))
        self.notebook.AddPage(self.compiler_panel, self.tr("Compiler"))

        # Configure the widgets
        self.cycle_text = wx.StaticText(self, wx.ID_ANY, self.tr("Cycles"))
        self.spin = wx.SpinCtrl(self, wx.ID_ANY, "10", min=0, max=100000)
        self.completed_text = wx.StaticText(self, wx.ID_ANY,
                                            self.tr("Completed cycles: ") + "0")
        self.run_button = wx.Button(self, wx.ID_ANY, self.tr("Run"))
        self.continue_button = wx.Button(self, wx.ID_ANY, self.tr("Continue"))
        self.switch_text = wx.StaticText(self, wx.ID_ANY, self.tr("Switches"))
        self.switch_panel = wx.ScrolledWindow(
            self, wx.ID_ANY, style=wx.VSCROLL | wx.BORDER_SIMPLE)
        self.switch_panel.SetScrollRate(0, 10)
        self.switch_panel.SetMinSize((-1, 160))
        self.switch_sizer = wx.BoxSizer(wx.VERTICAL)
        self.switch_panel.SetSizer(self.switch_sizer)
        self.monitor_text = wx.StaticText(self, wx.ID_ANY, self.tr("Monitors"))
        self.monitor_panel = wx.ScrolledWindow(
            self, wx.ID_ANY, style=wx.VSCROLL | wx.BORDER_SIMPLE)
        self.monitor_panel.SetScrollRate(0, 10)
        self.monitor_panel.SetMinSize((-1, 160))
        self.monitor_sizer = wx.BoxSizer(wx.VERTICAL)
        self.monitor_panel.SetSizer(self.monitor_sizer)
        self.status = wx.StaticText(self, wx.ID_ANY, self.tr("Ready."))

        # Bind events to widgets
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.Bind(wx.EVT_MENU, self.set_lang_en, id=self.id_lang_en)
        self.Bind(wx.EVT_MENU, self.set_lang_es, id=self.id_lang_es)
        self.Bind(wx.EVT_MENU, self.set_lang_zh, id=self.id_lang_zh)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)

        # Configure sizers for layout
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.notebook, 5, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(side_sizer, 1, wx.ALL, 5)

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
            wx.CallAfter(self.canvas_2d.render, self.tr("Ready."))
            wx.CallAfter(self.canvas_3d.render, self.tr("Ready."))
            wx.CallAfter(self.circuit_canvas.render)

    def tr(self, text):
        """Translate text based on the current active language."""
        if self.current_language == "Spanish":
            return SPANISH_TRANSLATIONS.get(text, text)
        elif self.current_language == "Chinese":
            return CHINESE_TRANSLATIONS.get(text, text)
        return text

    def set_lang_en(self, event):
        """Switch language to English and update GUI."""
        self.current_language = "English"
        self.refresh_labels()

    def set_lang_es(self, event):
        """Switch language to Spanish and update GUI."""
        self.current_language = "Spanish"
        self.refresh_labels()

    def set_lang_zh(self, event):
        """Switch language to Chinese and update GUI."""
        self.current_language = "Chinese"
        self.refresh_labels()

    def refresh_labels(self):
        """Update all text strings dynamically across the interface."""
        self.SetTitle(self.tr("Logic Simulator"))
        
        # Update Menu
        self.file_menu.SetLabel(wx.ID_HELP, self.tr("Help"))
        self.file_menu.SetLabel(wx.ID_ABOUT, self.tr("About"))
        self.file_menu.SetLabel(wx.ID_EXIT, self.tr("Exit"))
        self.menu_bar.SetMenuLabel(0, self.tr("File"))

        self.lang_menu.SetLabel(self.id_lang_en, self.tr("English"))
        self.lang_menu.SetLabel(self.id_lang_es, self.tr("Spanish"))
        self.lang_menu.SetLabel(self.id_lang_zh, self.tr("Chinese"))
        self.menu_bar.SetMenuLabel(1, self.tr("Language"))

        self.file_menu.SetLabel(wx.ID_OPEN, self.tr("Open"))
        self.file_menu.SetLabel(wx.ID_SAVE, self.tr("Save"))
        self.file_menu.SetLabel(wx.ID_SAVEAS, self.tr("Save As"))

        # Update Notebook tabs
        self.notebook.SetPageText(0, self.tr("Waveforms 2D"))
        self.notebook.SetPageText(1, self.tr("Waveforms 3D"))
        self.notebook.SetPageText(2, self.tr("Circuit"))
        self.notebook.SetPageText(3, self.tr("Compiler"))

        # Update Sidebar Controls
        self.cycle_text.SetLabel(self.tr("Cycles"))
        self.run_button.SetLabel(self.tr("Run"))
        self.continue_button.SetLabel(self.tr("Continue"))
        self.switch_text.SetLabel(self.tr("Switches"))
        self.monitor_text.SetLabel(self.tr("Monitors"))

        # Preserve errors or custom messages if possible, otherwise reset standard text
        if "Ready" in self.status.GetLabel() or "Listo" in self.status.GetLabel() or "就绪" in self.status.GetLabel():
            self.show_status(self.tr("Ready."))

        # Update Compiler texts
        self.def_text.SetLabel(self.tr("Circuit definition:"))
        self.compile_button.SetLabel(self.tr("Compile"))
        self.res_text.SetLabel(self.tr("Result:"))

        # Call generic updates to re-render dynamic items
        self.update_cycle_text()
        self.update_controls()
        self.Layout()

        if hasattr(self, 'circuit_canvas') and self.circuit_canvas:
            self.circuit_canvas.render()
        if hasattr(self, 'canvas_2d') and self.canvas_2d:
            self.canvas_2d.render()
        if hasattr(self, 'canvas_3d') and self.canvas_3d:
            self.canvas_3d.render()
        self.Refresh()


    def on_menu(self, event):
        """Handle the event when the user selects a file menu item."""
        menu_id = event.GetId()
        if menu_id == wx.ID_EXIT:
            self.Close(True)
        elif menu_id == wx.ID_OPEN:
            self.on_open_file()
        elif menu_id == wx.ID_SAVE:
            self.on_save_file()
        elif menu_id == wx.ID_SAVEAS:
            self.on_save_as_file()
        elif menu_id == wx.ID_HELP:
            wx.MessageBox(
                self.tr("Run: start from cycle 0 with cleared traces.\n"
                        "Continue: add more cycles to the current run.\n"
                        "Switches: click a switch's toggle to flip it 0/1.\n"
                        "Monitors: toggle each output On/Off to show it."),
                self.tr("Logsim Help"), wx.ICON_INFORMATION | wx.OK)
        elif menu_id == wx.ID_ABOUT:
            wx.MessageBox(
                self.tr("Logic Simulator\nGraphical user interface"),
                self.tr("About Logsim"), wx.ICON_INFORMATION | wx.OK)
            
    def on_open_file(self):
        """Open a file and load its contents into the compiler editor."""
        with wx.FileDialog(self, self.tr("Open"), wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'r', encoding='utf-8') as file:
                    self.editor.SetValue(file.read())
                self.path = pathname
                self.show_status(self.tr("Opened file: ") + pathname)
            except IOError:
                wx.LogError(self.tr("Cannot open file '%s'.") % pathname)

    def on_save_file(self):
        """Save the compiler editor contents to the current file path."""
        if self.path:
            try:
                with open(self.path, 'w', encoding='utf-8') as file:
                    file.write(self.editor.GetValue())
                self.show_status(self.tr("Saved file: ") + self.path)
            except IOError:
                wx.LogError(self.tr("Cannot save current data in file '%s'.") % self.path)
        else:
            self.on_save_as_file()

    def on_save_as_file(self):
        """Save the compiler editor contents to a new file location."""
        with wx.FileDialog(self, self.tr("Save As"), wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w', encoding='utf-8') as file:
                    file.write(self.editor.GetValue())
                self.path = pathname
                self.show_status(self.tr("Saved file: ") + pathname)
            except IOError:
                wx.LogError(self.tr("Cannot save current data in file '%s'.") % pathname)

    def build_compiler_panel(self, parent):
        """Build the Compiler tab: an editor, a Compile button, and results."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        code_font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL)

        self.editor = wx.TextCtrl(panel, wx.ID_ANY,
                                  style=wx.TE_MULTILINE | wx.HSCROLL)
        self.editor.SetFont(code_font)
        self.compile_button = wx.Button(panel, wx.ID_ANY, self.tr("Compile"))
        self.compile_button.Bind(wx.EVT_BUTTON, self.on_compile)
        self.compiler_output = wx.TextCtrl(
            panel, wx.ID_ANY,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.compiler_output.SetFont(code_font)

        self.def_text = wx.StaticText(panel, wx.ID_ANY, self.tr("Circuit definition:"))
        sizer.Add(self.def_text, 0, wx.ALL, 5)
        sizer.Add(self.editor, 3, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.compile_button, 0, wx.ALL, 5)
        
        self.res_text = wx.StaticText(panel, wx.ID_ANY, self.tr("Result:"))
        sizer.Add(self.res_text, 0, wx.ALL, 5)
        sizer.Add(self.compiler_output, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        return panel

    def on_compile(self, event=None):
        """Compile the editor text and refresh everything on success."""
        ok, model, output = compile_source(self.editor.GetValue())
        if ok and model is not None:
            self.load_model(model)
            message = self.tr("Compilation successful.")
            if output.strip():
                message += "\n\n" + output
            self.compiler_output.SetValue(message)
            self.show_status(self.tr("Compilation successful."))
        else:
            self.compiler_output.SetValue(
                output.strip() or self.tr("Compilation failed. See the Compiler tab."))
            self.show_status(self.tr("Compilation failed. See the Compiler tab."))

    def load_model(self, model):
        """Point the GUI and canvases at a freshly compiled model."""
        self.names, self.devices, self.network, self.monitors = model
        self.canvas_2d.devices = self.devices
        self.canvas_2d.monitors = self.monitors
        self.canvas_3d.devices = self.devices
        self.canvas_3d.monitors = self.monitors
        self.visible_monitors = set(self.monitors.monitors_dictionary)
        self.canvas_2d.visible_monitors = self.visible_monitors
        self.canvas_3d.visible_monitors = self.visible_monitors
        self.circuit_canvas.names = self.names
        self.circuit_canvas.devices = self.devices
        self.cycles_completed = 0
        self.update_controls()
        self.circuit_canvas.init = False
        self.canvas_2d.init = False
        self.canvas_3d.init = False
        wx.CallAfter(self.canvas_2d.render, self.tr("Ready."))
        wx.CallAfter(self.canvas_3d.render, self.tr("Ready."))
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
            self.show_status(self.tr("Ran for {} cycles.").format(cycles))

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
        cycles = self.spin.GetValue()
        if self.cycles_completed == 0:
            self.show_status(self.tr("Nothing to continue. Run first."))
            return
        if self.run_network(cycles):
            self.cycles_completed += cycles
            self.update_controls()
            self.show_status(self.tr("Continued for {} cycles. Total: {}.").format(
                cycles, self.cycles_completed))

    def on_toggle_switch(self, event):
        """Handle a switch toggle, applying the new state immediately."""
        toggle = event.GetEventObject()
        switch_id = self.switch_buttons[toggle]
        switch_name = self.names.get_name_string(switch_id)
        switch_state = 1 if toggle.GetValue() else 0
        if self.devices.set_switch(switch_id, switch_state):
            self.style_switch_toggle(toggle, switch_state)
            self.show_status(self.tr("Set {} to {}").format(switch_name, switch_state))
        else:
            toggle.SetValue(switch_state == 0)
            self.style_switch_toggle(toggle, 1 - switch_state)
            self.show_status(self.tr("Could not set switch {}.").format(switch_name))

    def style_switch_toggle(self, toggle, state):
        toggle.SetLabel(self.tr("On") if state == 1 else self.tr("Off"))

    def on_toggle_monitor(self, event):
        """Show or hide a monitor without deleting its saved waveform trace."""
        toggle = event.GetEventObject()
        device_id, output_id = self.monitor_buttons[toggle]
        monitor_key = (device_id, output_id)
        name = self.devices.get_signal_name(device_id, output_id)
        if toggle.GetValue():
            if monitor_key not in self.monitors.monitors_dictionary:
                error_type = self.monitors.make_monitor(device_id, output_id,
                                                        self.cycles_completed)
            else:
                error_type = self.monitors.NO_ERROR
            if error_type == self.monitors.NO_ERROR:
                self.visible_monitors.add(monitor_key)
                toggle.SetLabel(self.tr("On"))
                self.show_status(self.tr("Showing monitor {}").format(name))
            else:
                toggle.SetValue(False)
                self.show_status(self.tr("Could not add monitor {}.").format(name))
        else:
            self.visible_monitors.discard(monitor_key)
            toggle.SetLabel(self.tr("Off"))
            self.show_status(self.tr("Hid monitor {}").format(name))

    def run_network(self, cycles):
        """Run the network for the specified number of cycles."""
        for _ in range(cycles):
            if self.network.execute_network():
                self.monitors.record_signals()
            else:
                self.show_status(self.tr("Error: network oscillating."))
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
                                     self.tr("On") if state == 1 else self.tr("Off"), size=(40, -1))
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
                monitored = (device_id, output_id) in self.visible_monitors
                row = wx.BoxSizer(wx.HORIZONTAL)
                label = wx.StaticText(self.monitor_panel, wx.ID_ANY, name)
                toggle = wx.ToggleButton(self.monitor_panel, wx.ID_ANY,
                                         self.tr("On") if monitored else self.tr("Off"),
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
        self.completed_text.SetLabel(self.tr("Completed cycles: ") +
                                     str(self.cycles_completed))

    def show_status(self, message):
        """Display a status message and redraw the canvas."""
        self.status.SetLabel(message)
        self.canvas_2d.render(message)
        self.canvas_3d.render(message)