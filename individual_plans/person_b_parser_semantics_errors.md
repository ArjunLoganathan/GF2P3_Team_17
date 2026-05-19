# Person B Interim Plan: Parser, Semantics, and Error Handling

This plan is for the first interim report only. Your job is to define what makes a syntactically valid definition file meaningful as a logic circuit, and to describe how the future parser should detect and report errors.

You are not implementing the parser yet, but you are designing its behaviour. Person A defines the syntax. You define the semantic constraints and parser error strategy. Person C uses your rules to create examples and diagrams that are valid and meaningful.

## Main Responsibility

You are responsible for answering this question:

> Once a file follows the grammar, what extra rules must it obey to describe a valid logic circuit?

Your work is the bridge between the language specification and the later code in `parse.py`.

## Inputs You Need

From Person A:
- Final EBNF grammar.
- Final scanner token list.
- Comment and whitespace rules.
- The punctuation available for parser recovery, especially semicolons and section keywords.

From Person C:
- The two example circuits intended for the first interim report.
- The exact device names, connections, and monitor points used in those examples.
- Draft diagrams, so you can check that the definition files and diagrams describe the same circuit.

From the project brief:
- Supported devices: `CLOCK`, `SWITCH`, `AND`, `NAND`, `OR`, `NOR`, `DTYPE`, `XOR`.
- Gate input limits: `AND`, `NAND`, `OR`, `NOR` have 1 to 16 inputs.
- `XOR` has exactly 2 inputs.
- `DTYPE` has inputs `DATA`, `CLK`, `SET`, `CLEAR` and outputs `Q`, `QBAR`.
- `CLOCK` and `SWITCH` have one output and no inputs.
- Connections must connect outputs to inputs.
- Monitor points must be output signals.

## Outputs You Must Produce

By the end of this interim work, you must provide:

1. A full list of semantic constraints.
2. A full list of semantic errors.
3. A syntax error handling strategy.
4. A semantic error handling strategy.
5. A parser recovery strategy.
6. A parser design outline showing which functions will correspond to the EBNF rules.
7. Report-ready text for the semantic constraints and error handling sections.

## Parser Design Outline

Use Person A's grammar and map each grammar rule to a parser method later.

Expected parser methods:
- `parse_network()`
- `parse_devices_section()`
- `parse_device_decl()`
- `parse_connections_section()`
- `parse_connection()`
- `parse_monitors_section()`
- `parse_monitor()`
- `parse_signal()`
- `parse_device_kind()`
- `expect_symbol()`
- `report_error()`
- `recover_to()`

Keep the parser design simple. The parser should:

1. Read tokens from the scanner.
2. Check syntax first.
3. Record enough information for semantic checks.
4. Build the network only if no errors have been found.

For the report, say that the implementation will use top-down parsing because the grammar has a clear first token for each section and statement type.

## Semantic Constraints

Write these in the interim report. This is one of your most important sections.

### Device Rules

- Every device name must be unique.
- A device name cannot be a reserved keyword.
- Every device kind must be one of `CLOCK`, `SWITCH`, `AND`, `NAND`, `OR`, `NOR`, `DTYPE`, or `XOR`.
- `SWITCH` must have one qualifier, either `0` or `1`, representing its initial output.
- `CLOCK` must have one positive integer qualifier, representing the number of simulation cycles in half a clock period.
- `AND`, `NAND`, `OR`, and `NOR` must have one integer qualifier from `1` to `16`, representing the number of inputs.
- `XOR` must not have a qualifier if the team chooses fixed syntax, because it always has two inputs.
- `DTYPE` must not have a qualifier because its ports are fixed.
- No device may be used in a connection or monitor before being declared in the `DEVICES` section.

### Port Rules

- `CLOCK`, `SWITCH`, `AND`, `NAND`, `OR`, `NOR`, and `XOR` have a single unnamed output, referenced using the device name alone.
- `DTYPE` outputs are referenced as `device.Q` and `device.QBAR`.
- Gate inputs are named `I1`, `I2`, etc., up to the declared number of inputs.
- `XOR` inputs are `I1` and `I2`.
- `DTYPE` inputs are `DATA`, `CLK`, `SET`, and `CLEAR`.
- A port name must exist for the declared device kind.
- A signal used as a monitor must refer to an output, not an input.
- The left side of a connection must refer to an output.
- The right side of a connection must refer to an input.

### Connection Rules

- Each connection must go from one output signal to one input signal.
- An input may only be connected once.
- Multiple inputs may be connected to the same output.
- All required inputs should be connected before the simulation can run.
- A connection cannot refer to an undeclared device.
- A connection cannot refer to a non-existent port.
- A connection cannot connect input to input.
- A connection cannot connect output to output.
- A connection cannot connect a signal to itself in a meaningless way.

### Monitor Rules

- Every monitor must refer to an existing output signal.
- A monitor cannot refer to an input signal.
- Repeated monitor declarations should either be rejected or ignored consistently. For simplicity, specify that duplicate monitors are reported as semantic errors.

## Semantic Error List

Include this list in the report. Keep the wording clear because it will later become parser error messages.

Device errors:
- Duplicate device name.
- Reserved keyword used as a device name.
- Unknown device kind.
- Missing required qualifier for `SWITCH`, `CLOCK`, or gates.
- Unexpected qualifier for `DTYPE` or `XOR`.
- Invalid switch initial value.
- Invalid clock period.
- Invalid gate input count.

Signal and port errors:
- Unknown device name.
- Unknown input port.
- Unknown output port.
- Input used where an output is required.
- Output used where an input is required.
- Single-output device incorrectly given an output port.
- Multi-output device output not specified where required.

Connection errors:
- Attempt to connect to an input that is already connected.
- Attempt to connect from an input.
- Attempt to connect to an output.
- Required input left unconnected.
- Connection uses undeclared device.

Monitor errors:
- Monitor uses undeclared device.
- Monitor refers to an input.
- Monitor refers to a non-existent output.
- Duplicate monitor point.

## Syntax Error Handling Strategy

For syntax errors, specify this behaviour:

- Print the current input line.
- Print a caret marker under the approximate error location.
- Print a clear message, for example `Expected semicolon`.
- Increment an error count.
- Skip tokens until a sensible recovery point is found.
- Continue parsing so that the user can see more than one error from the file.

Recommended recovery points:
- Semicolon, for errors inside one statement.
- `DEVICES`, `CONNECT`, `MONITOR`, or `END`, for errors near section boundaries.
- `EOF`, if no safe recovery point is found.

Example report wording:

```text
When a syntax error is detected, the parser will ask the scanner to print the current source line and a caret marker at the current token. A short error message will then be printed. The parser will skip input symbols until it reaches a semicolon, a section keyword, END, or end of file, depending on where the error occurred.
```

## Semantic Error Handling Strategy

For semantic errors, specify this behaviour:

- Print the current input line and caret marker where possible.
- Print a message naming the bad device, port, or signal.
- Increment an error count.
- Do not run the simulator if any semantic error is found.
- Avoid building or modifying the network after the first serious semantic error.
- Continue checking later declarations where possible so the user receives useful feedback.

Example messages:

```text
*** Error: Device name G1 has already been declared.
*** Error: G1.I3 is not a valid input for NAND gate G1, which has only 2 inputs.
*** Error: G2 is an output and cannot appear on the right side of a connection.
*** Error: Monitor point D1.DATA is an input, not an output.
```

## Parser/Network Construction Policy

For the interim report, describe the intended policy:

- The parser will first validate syntax and semantics.
- Calls to the supplied `Devices`, `Network`, and `Monitors` classes will only be made when the parser is confident the current statement is valid.
- If any error has already occurred, the parser will continue checking where possible but will not start simulation.
- `parse_network()` will return `True` only if the whole file is valid.
- `parse_network()` will return `False` if any syntax or semantic error is found.

This matches the project brief's guidance that network construction should stop after an error, while parsing can continue for better reporting.

## Report Section You Should Write

Write two report-ready sections:

### Semantic Constraints

Include:
- Device constraints.
- Port constraints.
- Connection constraints.
- Monitor constraints.
- A short explanation that these rules are checked after syntax is recognised.

### Error Handling

Include:
- Syntax error handling.
- Semantic error handling.
- Error recovery.
- Example error messages.
- A statement that the simulator will not run if parsing fails.

Suggested opening:

```text
A file may satisfy the grammar but still fail to describe a meaningful circuit. These cases are treated as semantic errors. The parser will therefore check not only that each statement is syntactically well formed, but also that devices are declared once, ports exist for the relevant device type, connections run from outputs to inputs, and monitor points refer to valid outputs.
```

## Coordination Checklist

Before the interim report is frozen, confirm:

- Person A's EBNF has no rule that is ambiguous for your parser design.
- Person A's token list includes everything your parser needs.
- Person C's example circuits obey every semantic rule.
- Every semantic error listed has a clear detection point.
- Error handling text does not promise something too complicated to implement later.
- The team agrees whether duplicate monitors are errors or ignored. Recommended: treat them as errors for simplicity.

## Timeline

### Friday 15 May to Sunday 17 May

- Read the project brief sections on semantics, parser, devices, network, and monitors.
- Draft the semantic constraints.
- Draft the semantic error list.
- Check the supplied device rules carefully.

### Monday 18 May

- Meet with Person A.
- Walk through the grammar one rule at a time.
- Check that parser functions can be written directly from the grammar.
- Ask for changes if any rule is difficult to parse simply.

### Tuesday 19 May

- Write the parser design outline.
- Write the syntax error recovery approach.
- Write the semantic error handling approach.

### Wednesday 20 May

- Review Person C's example definition files and diagrams.
- Mark any syntax or semantic mistakes.
- Make sure examples include at least one non-trivial connection pattern.

### Thursday 21 May

- Freeze the semantic constraints and error list.
- Send final report-ready text to the team.

### Friday 22 May to Sunday 24 May

- Help proofread the first interim report.
- Check that examples, diagrams, EBNF, and semantic constraints all agree.
- Check that the report clearly separates syntax errors from semantic errors.

## Definition Of Done

Your interim work is done when:

- The semantic constraints are complete.
- The semantic error list is complete.
- The parser design outline follows the EBNF.
- Syntax and semantic error handling are clearly described.
- Person A confirms the parser plan matches the grammar.
- Person C confirms both examples pass your semantic rules.
- Your report sections are ready to paste into the group PDF.
