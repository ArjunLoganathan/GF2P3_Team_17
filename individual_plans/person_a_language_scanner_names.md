# Person A Interim Plan: Language, Scanner, and Names

This plan is for the first interim report only. Your job is to make the logic description language precise enough that the team can build the parser and examples from it later.

You own the EBNF syntax, scanner-facing language decisions, and the report text for syntax/comments. You are not writing the full implementation yet, but your output must be detailed enough that implementation can start immediately after the interim report.

## Main Responsibility

You are responsible for answering this question:

> What exactly can be written in a valid logic definition file?

Your work defines the input format for the whole project. Person B will use your grammar to design the parser and semantic checks. Person C will use your grammar to write example definition files and circuit diagrams.

## Inputs You Need

From the group plan:
- Use the simple section-based language with `DEVICES`, `CONNECT`, `MONITOR`, and `END`.
- Use semicolons to end statements.
- Use free-format whitespace, meaning spaces and line breaks do not matter.
- Use comments handled by the scanner, not the parser.

From Person B:
- Confirm what syntax makes parser recovery easiest.
- Confirm that every grammar choice is suitable for a top-down parser with one-symbol lookahead.
- Confirm the exact punctuation needed for semantic checks, especially signal names like `G1.I1`.

From Person C:
- Get the two example circuits they want to include in the report.
- Check that both example circuits can be written clearly using your grammar.
- Ask Person C to test your grammar by writing example definition files without your help.

## Outputs You Must Produce

By the end of this interim work, you must provide:

1. A final EBNF grammar for the logic description language.
2. A short explanation of the language layout.
3. A scanner token list.
4. A comment syntax rule.
5. A whitespace rule.
6. A list of syntax errors the parser should detect.
7. A short report-ready section explaining why the syntax is readable and easy to parse.

These outputs should be given to the team before the first interim report is assembled.

## Recommended Definition File Format

Use this exact overall format unless the whole team agrees to change it:

```text
DEVICES:
  SW1 = SWITCH(0);
  SW2 = SWITCH(0);
  G1 = NAND(2);
  G2 = NAND(2);

CONNECT:
  SW1 -> G1.I1;
  SW2 -> G2.I2;
  G1 -> G2.I1;
  G2 -> G1.I2;

MONITOR:
  G1;
  G2;
END;
```

The important design choices are:
- Each major section starts with a keyword and colon.
- Each declaration ends with a semicolon.
- Connections use `->`, which makes direction obvious.
- Inputs and named outputs use dot notation, for example `G1.I1` or `D1.Q`.
- Single-output devices can be referred to by device name alone, for example `G1`.

## EBNF You Should Write

Start from this grammar and refine only if necessary:

```text
definition = devices_section , connections_section , monitors_section , "END" , ";" ;

devices_section = "DEVICES" , ":" , device_decl , { device_decl } ;
device_decl = name , "=" , device_kind , [ "(" , number , ")" ] , ";" ;

connections_section = "CONNECT" , ":" , connection , { connection } ;
connection = signal , "->" , signal , ";" ;

monitors_section = "MONITOR" , ":" , monitor , { monitor } ;
monitor = signal , ";" ;

signal = name , [ "." , name ] ;
device_kind = "CLOCK" | "SWITCH" | "AND" | "NAND" | "OR" | "NOR" | "DTYPE" | "XOR" ;
name = letter , { letter | digit } ;
number = digit , { digit } ;
letter = "A" | ... | "Z" | "a" | ... | "z" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
```

Keep the grammar simple. Do not add optional section ordering, nested blocks, or complex syntax. The parser will be easier if the sections always appear in this order:

1. `DEVICES`
2. `CONNECT`
3. `MONITOR`
4. `END;`

## Scanner Token List

Define the scanner tokens Person B will expect from the parser side.

Recommended token types:
- `KEYWORD`
- `NAME`
- `NUMBER`
- `COLON`
- `SEMICOLON`
- `EQUALS`
- `DOT`
- `ARROW`
- `LEFT_PAREN`
- `RIGHT_PAREN`
- `EOF`
- `INVALID`

Recommended keywords:
- `DEVICES`
- `CONNECT`
- `MONITOR`
- `END`
- `CLOCK`
- `SWITCH`
- `AND`
- `NAND`
- `OR`
- `NOR`
- `DTYPE`
- `XOR`

Explain in the report that keywords are reserved and cannot be used as user device names.

## Comment Rule

Choose one simple comment style:

```text
# This is a comment
```

Recommended rule:
- A comment starts with `#`.
- The scanner ignores every character from `#` to the end of the current line.
- Comments are not part of the EBNF grammar because the scanner removes them before parsing.

Example:

```text
DEVICES:
  SW1 = SWITCH(0); # initial switch value is low
END;
```

Do not add block comments for the interim version. Line comments are enough.

## Whitespace Rule

Write this clearly in the report:

> The language is free-format. Spaces, tabs, and line breaks may be inserted between symbols without changing the meaning of the file, except inside names, numbers, keywords, and punctuation symbols such as `->`.

Valid:

```text
SW1 = SWITCH(0);
```

Also valid:

```text
SW1
=
SWITCH
(
0
)
;
```

Invalid:

```text
SW 1 = SWITCH(0);
```

because `SW1` is one name and cannot contain a space.

## Syntax Errors To Identify

You should list syntax errors separately from semantic errors. Syntax errors are about malformed text, not whether the circuit makes sense.

Include at least these:
- Missing `DEVICES` section.
- Missing `CONNECT` section.
- Missing `MONITOR` section.
- Missing `END;`.
- Missing colon after a section keyword.
- Missing semicolon after a device declaration, connection, monitor, or `END`.
- Missing equals sign in a device declaration.
- Missing opening or closing parenthesis around a device qualifier.
- Missing arrow in a connection.
- Missing dot in a ported signal where the parser expects one.
- Invalid punctuation character.
- Invalid name, for example starting with a digit.
- Invalid number, for example a non-digit inside a number.
- Unexpected keyword or name in the wrong section.
- Unexpected end of file before `END;`.

Do not include semantic errors here. For example, `G1 -> G2;` is syntactically valid even if it is semantically wrong because the right side may not be an input.

## Error Recovery Guidance For Person B

Your syntax should make error recovery easy. Tell Person B to recover at:

- A semicolon, when an individual statement is wrong.
- A section keyword, when a whole section has gone wrong.
- `END`, when the parser needs to stop safely.
- `EOF`, as the final fallback.

This is why every declaration, connection, and monitor line should end with `;`.

## Report Section You Should Write

Write a report-ready section called something like:

### Syntax of the Logic Description Language

Include:
- One short paragraph explaining the language.
- The EBNF grammar.
- The comment rule.
- The whitespace rule.
- One short paragraph explaining why the grammar is readable and suitable for a top-down parser.

Suggested wording:

```text
The definition file is divided into three compulsory sections: DEVICES, CONNECT, and MONITOR, followed by END;. The DEVICES section declares every device in the network, the CONNECT section declares directed connections from outputs to inputs, and the MONITOR section lists the output signals to be monitored when simulation begins. The language is free-format, so whitespace and line breaks do not affect the meaning of the file.
```

## Coordination Checklist

Before the team freezes the interim report, confirm:

- Person B can parse every rule using one-symbol lookahead.
- Person B has enough punctuation to recover from errors.
- Person C has written both example files using the final grammar.
- Every keyword in your scanner token list appears in the grammar.
- Every punctuation symbol in the grammar appears in the scanner token list.
- The report does not describe syntax that the parser team is not planning to support.

## Timeline

### Friday 15 May to Sunday 17 May

- Read the project brief sections on syntax and scanner requirements.
- Draft the EBNF grammar.
- Draft the scanner token list.
- Choose the comment syntax.
- Give Person C the grammar so they can start example files.

### Monday 18 May

- Meet with Person B for 30 minutes.
- Check that the grammar is simple enough for recursive descent parsing.
- Remove any grammar feature that makes parsing complicated.

### Tuesday 19 May

- Update the grammar based on feedback.
- Write the syntax explanation in report-ready prose.
- Write the syntax error list.

### Wednesday 20 May

- Review Person C's example definition files.
- Confirm that both examples follow your grammar.
- If the examples are awkward to write, simplify the grammar rather than adding special cases.

### Thursday 21 May

- Freeze the grammar.
- Send the final EBNF, token list, comment rule, and syntax error list to the team.

### Friday 22 May to Sunday 24 May

- Help proofread the first interim report.
- Check that the EBNF and examples match exactly.
- Check that no semantic rules are accidentally written as syntax rules.

## Definition Of Done

Your interim work is done when:

- The EBNF grammar is complete.
- The comment and whitespace rules are written clearly.
- The scanner token list is complete.
- Syntax errors are listed.
- Person B confirms the grammar is parseable.
- Person C confirms the example files use the grammar.
- Your report section is ready to paste into the group PDF.
