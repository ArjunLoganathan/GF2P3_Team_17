CircuitDefinition = DevicesBlock, ConnectionsBlock, MonitorsBlock, "END" ;

ImportsBlock      = "IMPORT", ";", { ImportRule }, "IMPORT", "END", ";" ;
ImportRule        = CustomTypeName, "FROM", QuotedString, ";" ;

DevicesBlock      = "DEVICES", ":", { DeviceDeclaration }, "DEVICES", "END", ";" ;
DeviceDeclaration = DeviceName, "=", DeviceType, [ DeviceParameter ], ";" ;
DeviceType        = "SWITCH" | "CLOCK" | "AND" | "OR" | "NAND" | "NOR" | "XOR" | "NOT" | "DTYPE" ;
DeviceParameter   = Number ;

ConnectionsBlock  = "CONNECT", ":", { ConnectionRule }, "CONNECT", "END", ";" ;
ConnectionRule    = OutputSignal, "=", InputSignal, ";" ;
OutputSignal      = DeviceName, [ "." , PinName ] ;
InputSignal       = DeviceName, "." , PinName ;

MonitorsBlock     = "MONITOR", ";", { MonitorRule }, "MONITOR", "END", ";" ;
MonitorRule       = OutputSignal, ";" ;

DeviceName        = Letter, { Letter | Digit } ;
PinName           = Letter | Digit, { Letter | Digit } ;
Number            = Digit, { Digit } ;
QuotedString      = '"', { Character }, '"' ;

Letter            = "A" | "B" | ... | "Z" | "a" | ... | "z" ;
Digit             = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;