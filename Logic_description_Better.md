CircuitDefinition =
    [ ImportsBlock ],
    DevicesBlock,
    ConnectionsBlock,
    MonitorsBlock,
    "END", ";" ;

ImportsBlock =
    "IMPORT", ":", ImportRule, { ImportRule }, "END", "IMPORT", ";" ;

ImportRule =
    CustomTypeName, "FROM", QuotedString, ";" ;

DevicesBlock =
    "DEVICES", ":", DeviceDeclaration, { DeviceDeclaration },
    "END", "DEVICES", ";" ;

DeviceDeclaration =
    DeviceName, "=", DeviceType, [ "(", ParameterList, ")" ], ";" ;

DeviceType =
    PrimitiveType | CustomTypeName ;

PrimitiveType =
    "SWITCH" | "CLOCK" | "AND" | "OR" | "NAND" | "NOR" | "XOR" | "NOT" | "DTYPE" ;

ParameterList =
    Number, { ",", Number } ;

ConnectionsBlock =
    "CONNECT", ":", ConnectionRule, { ConnectionRule },
    "END", "CONNECT", ";" ;

ConnectionRule =
    OutputSignal, "=", InputSignal, ";" ;

MonitorsBlock =
    "MONITOR", ":", { MonitorRule }, "END", "MONITOR", ";" ;

MonitorRule =
    OutputSignal, ";" ;

OutputSignal =
    DeviceName, [ "." , PinName ] ;

InputSignal =
    DeviceName, "." , PinName ;

DeviceName =
    Identifier ;

CustomTypeName =
    Identifier ;

PinName =
    Identifier ;

Identifier =
    Letter, { Letter | Digit | "_" } ;

Number =
    Digit, { Digit } ;

QuotedString =
    '"', { Character }, '"' ;

Letter =
    "A" | "B" | ... | "Z" | "a" | ... | "z" ;

Digit =
    "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
