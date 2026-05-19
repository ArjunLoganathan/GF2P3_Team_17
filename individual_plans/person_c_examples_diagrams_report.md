# Person C Interim Plan: Examples, Diagrams, and Report Assembly

This plan is for the first interim report only. Your job is to make the report concrete, readable, and complete. You own the example definition files, circuit diagrams, teamwork planning section, and final assembly of the group PDF.

You are not responsible for inventing the grammar or all semantic rules, but you must test them by using them. If the examples are hard to write or explain, tell Person A and Person B early.

## Main Responsibility

You are responsible for answering this question:

> Can a reader understand the proposed language and see two complete circuits written in it?

Your work turns the technical specification into a report that is clear enough for assessment.

## Inputs You Need

From Person A:
- Final EBNF grammar.
- Comment rule.
- Whitespace rule.
- Exact syntax for devices, connections, monitors, and `END;`.

From Person B:
- Semantic constraints.
- Semantic error list.
- Confirmation that your example files are valid.
- Any rules about ports, especially `DTYPE.Q`, `DTYPE.QBAR`, gate inputs, and monitor outputs.

From the group:
- Team member names.
- Team number, if known.
- Agreed role split.
- Planned meeting/checkpoint times.
- Any repository/tooling decisions, for example GitHub/GitLab and issue tracking.

## Outputs You Must Produce

By the end of this interim work, you must provide:

1. Two valid example definition files.
2. Two circuit diagrams matching those files.
3. A teamwork planning section.
4. An introduction/general approach section.
5. A report assembly checklist.
6. A final proofread pass before submission.

You should also keep a short list of any questions or inconsistencies found while writing the examples.

## Example File 1: NAND Latch

Use the NAND latch described in the project brief because it is familiar and directly relevant.

Draft definition file:

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

Diagram requirements:
- Show `SW1` connected to `G1.I1`.
- Show `SW2` connected to `G2.I2`.
- Show feedback from `G1` to `G2.I1`.
- Show feedback from `G2` to `G1.I2`.
- Mark monitor points on `G1` and `G2`.

Simple diagram layout:

```text
        +--------+             +--------+
SW1 --->| G1 NAND|---- G1 ---->| G2 I1  |
        | I1  I2 |             | NAND   |---- G2
G2  --->|        |             | I2     |
        +--------+             +--------+
                                  ^
                                  |
                                 SW2
```

You can redraw this neatly in Word, PowerPoint, draw.io, diagrams.net, LaTeX/TikZ, or any simple drawing tool.

## Example File 2: Clocked D-Type Circuit

Use a second example that exercises different device types. A simple DTYPE circuit is useful because it tests named inputs and named outputs.

Draft definition file:

```text
DEVICES:
  DATA_SW = SWITCH(0);
  SET_SW = SWITCH(0);
  CLEAR_SW = SWITCH(0);
  CLK1 = CLOCK(2);
  D1 = DTYPE;

CONNECT:
  DATA_SW -> D1.DATA;
  CLK1 -> D1.CLK;
  SET_SW -> D1.SET;
  CLEAR_SW -> D1.CLEAR;

MONITOR:
  D1.Q;
  D1.QBAR;
  CLK1;
END;
```

Diagram requirements:
- Show four inputs going into the DTYPE: `DATA`, `CLK`, `SET`, `CLEAR`.
- Show `D1.Q` and `D1.QBAR` as outputs.
- Mark monitors on `D1.Q`, `D1.QBAR`, and `CLK1`.
- Label `CLK1` as a clock with half-period 2.
- Label switches with initial value 0.

Simple diagram layout:

```text
DATA_SW ----> DATA       Q ----> monitor D1.Q
CLK1 -------> CLK    +-------+
SET_SW -----> SET    | DTYPE |
CLEAR_SW ---> CLEAR  +-------+
                     QBAR --> monitor D1.QBAR

CLK1 is also monitored.
```

Before finalising this example, check with Person B that `DTYPE` with no qualifier is the team's chosen syntax.

## Optional Invalid Examples

The first interim report requires two example definition files with diagrams, not necessarily invalid files. However, it is useful to include short error examples in the error handling section if there is space.

Possible one-line invalid examples:

```text
G1 = NAND(20);
```

Meaning: invalid gate input count.

```text
SW1 -> G1;
```

Meaning: connection target is an output, not an input.

```text
MONITOR:
  G1.I1;
```

Meaning: monitor point is an input, not an output.

Only include these if the final report remains concise.

## Teamwork Planning Section

Write this section in clear prose. It should explain who does what and when.

Include:
- Person A owns language syntax, EBNF, scanner token decisions, comments, whitespace, and syntax errors.
- Person B owns semantic constraints, parser design, error handling, and semantic errors.
- Person C owns examples, diagrams, report assembly, timeline, and final checks.
- All three people review the language before freezing it.
- All three people contribute to checking the examples and report.
- Later implementation will rotate testing so nobody is the only tester of their own work.

Suggested wording:

```text
The team divided the first interim work into three parallel tracks. One member focused on the syntax of the definition language and scanner-level decisions, one member focused on semantic constraints and parser error handling, and one member focused on example circuits, diagrams, report assembly, and schedule coordination. The three tracks were deliberately linked by clear inputs and outputs: the examples had to conform to the grammar, the semantic rules had to validate the examples, and all members reviewed the final language before submission.
```

## Introduction And General Approach Section

Write a short introduction. Keep it simple.

Include:
- The project is a Python logic simulator.
- The simulator first reads a text definition file describing devices, connections, and monitor points.
- It then lets the user run the network and inspect signal traces.
- The first interim report specifies the definition language before implementation.
- The team chose a readable section-based language to make both user writing and parser error recovery easier.

Suggested wording:

```text
The aim of the project is to develop a Python logic simulator for combinational and clocked logic circuits. The simulator will operate in two phases. First, it will read a definition file describing the devices, their connections, and the initial monitor points. Second, it will allow the user to run the simulation, change switch states, and inspect monitored signals. This interim report focuses on the first phase by specifying the syntax and semantics of the definition language.
```

## Report Assembly Structure

Assemble the first interim report in this order:

1. Title page
2. Introduction and general approach
3. Teamwork planning
4. Syntax and EBNF
5. Comment and whitespace rules
6. Semantic constraints
7. Error handling
8. Example definition file 1 with diagram
9. Example definition file 2 with diagram

Check the project brief requires:
- Introduction and general approach.
- Teamwork planning: who will do what, and when.
- EBNF syntax.
- Identification of all possible semantic errors.
- Description of error handling.
- Two example definition files with diagrams.

## Formatting Rules For The Report

Use a clean format:
- Keep headings short.
- Use monospace formatting for keywords and example definition files.
- Keep grammar in a code block or equivalent fixed-width style.
- Put each example file near its diagram.
- Make diagrams readable in black and white.
- Keep the report professional and concise.

Do not let the examples drift from the grammar. If the grammar says `MONITOR:` then do not write `MONITORS:` in the examples.

## Cross-Checks You Must Perform

Before submission, check:

- Every keyword in the examples appears in Person A's grammar.
- Every punctuation symbol in the examples appears in Person A's scanner token list.
- Every device and port in the examples obeys Person B's semantic constraints.
- Every connection in each diagram appears in the matching definition file.
- Every connection in each definition file appears in the matching diagram.
- Every monitor point in the examples is shown or labelled in the diagrams.
- The introduction does not promise functionality outside the brief.
- The teamwork plan matches the actual split.

## Timeline

### Friday 15 May to Sunday 17 May

- Draft the teamwork planning section.
- Draft the introduction.
- Create first versions of both example files.
- Sketch both circuit diagrams roughly.
- Ask Person A whether the example syntax is valid.
- Ask Person B whether the examples are semantically valid.

### Monday 18 May

- Update examples after the grammar meeting.
- Start the clean diagrams.
- Add the project deadline timeline to the teamwork section.

### Tuesday 19 May

- Finish clean diagram for Example 1.
- Finish clean diagram for Example 2.
- Check both diagrams against the definition files line by line.

### Wednesday 20 May

- Send the example files and diagrams to Person A and Person B.
- Fix any syntax or semantic problems they find.
- Start assembling the report document.

### Thursday 21 May

- Insert Person A's EBNF section.
- Insert Person B's semantic constraints and error handling section.
- Check that formatting is consistent.
- Make sure the report contains every required item from the brief.

### Friday 22 May

- Do a full proofread.
- Check all examples against the final grammar.
- Check diagrams are legible.
- Confirm all three team members agree with the report contents.

### Saturday 23 May

- Produce a near-final PDF.
- Ask the team to read the PDF, not just the source document.
- Fix layout, typos, and inconsistencies.

### Sunday 24 May

- Final check before 4pm.
- Submit the group PDF early if possible.
- Keep a copy of the submitted PDF in the repository or shared drive.

## Definition Of Done

Your interim work is done when:

- The report has an introduction.
- The report has a clear teamwork planning section.
- Two valid example definition files are included.
- Two matching diagrams are included.
- Person A confirms the examples match the grammar.
- Person B confirms the examples obey the semantic rules.
- The full report includes every required item from the brief.
- The final PDF is ready before the deadline.
