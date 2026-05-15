---
name: GF2 Project Plan
overview: A simple 3-person project plan for the GF2 logic simulator, splitting implementation, testing, and reports evenly while respecting the course deadlines.
todos:
  - id: agree-grammar
    content: Agree and freeze the logic description language grammar as a team.
    status: pending
  - id: first-report
    content: Write and submit the first interim group report with EBNF, semantic errors, error handling, examples, and diagrams.
    status: pending
  - id: implement-core
    content: Implement names, scanner, parser, and GUI in parallel with cross-testing.
    status: pending
  - id: second-submission
    content: Prepare second interim code zip, pytest tests, git logs, example files, diagrams, and individual user guides.
    status: pending
  - id: maintenance
    content: Implement the maintenance memo changes after 5 June and update tests.
    status: pending
  - id: final-submission
    content: Create final folder, finish individual final reports, submit final zip/PDF, and prepare demo.
    status: pending
isProject: false
---

# GF2 Project Plan

## Goal
Build a Python logic simulator using the supplied skeleton code, submit the required reports, and keep the workload balanced across 3 people.

Key deadlines from [`gf2_python_p3.pdf`](gf2_python_p3.pdf):
- First interim report: Sunday 24 May 2026, 4pm, group, 15 marks.
- Second interim report/code: Friday 5 June 2026, 11am, individual/group split, 15 marks.
- Maintenance memo released: Friday 5 June 2026, 11am.
- Final report/code/demo: Friday 12 June 2026, 4pm report and 4-6pm demo slot, individual, 50 marks.

## Team Split
Use three main owners, but every module should be tested by someone other than its author.

Person A: Language, scanner, and names
- Own [`names.py`](names.py): implement name lookup/query and tests.
- Own [`scanner.py`](scanner.py): tokenisation, comments, line/column error reporting, tests.
- Lead the EBNF syntax section of the first interim report.
- Write scanner/names pytest tests.

Person B: Parser and network construction
- Own [`parse.py`](parse.py): syntax parser first, then semantic checks and calls to `Devices`, `Network`, and `Monitors`.
- Lead semantic error list and error handling section of the first interim report.
- Write parser tests using good and bad definition files.

Person C: GUI, integration, and release packaging
- Own [`gui.py`](gui.py): implement run, continue, switch setting, monitor add/remove, quit, and waveform display.
- Lead integration testing, definition examples, screenshots, and packaging.
- Write manual GUI test checklist and help prepare final folder/zip submissions.

Shared responsibilities:
- All 3 review the logic description language before coding.
- All 3 produce at least one valid definition file and one invalid/error-case file.
- All 3 keep individual git commits clean because each person must submit their own commit log.
- Rotate testing: A tests B's parser, B tests C's GUI flow, C tests A's scanner/names.

## Recommended Language Structure
Keep the definition language simple and readable. Use sections and semicolons so parser recovery is easier.

Example style:
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

Suggested EBNF shape for the first report:
```text
definition = devices_section , connections_section , monitors_section , "END" , ";" ;
devices_section = "DEVICES" , ":" , device_decl , { device_decl } ;
device_decl = name , "=" , device_kind , [ "(" , number , ")" ] , ";" ;
connections_section = "CONNECT" , ":" , connection , { connection } ;
connection = signal , "->" , signal , ";" ;
monitors_section = "MONITOR" , ":" , signal , { signal } ;
signal = name , [ "." , name ] ;
device_kind = "CLOCK" | "SWITCH" | "AND" | "NAND" | "OR" | "NOR" | "DTYPE" | "XOR" ;
name = letter , { letter | digit } ;
number = digit , { digit } ;
```

Agree this grammar as a team before coding. Once agreed, do not keep changing it unless absolutely necessary.

## First Interim Report Instructions
One group PDF. Suggested structure:

1. Introduction and general approach
- State that the project is a Python logic simulator.
- Briefly explain the two phases: read definition file, then run simulation.
- Explain the team split and timeline.

2. Teamwork planning
- Include who owns names/scanner, parser, GUI/integration.
- Include the rule that another person tests each module.
- Include planned meeting/checkpoint times.

3. EBNF syntax
- Write the full EBNF grammar.
- Define comments separately because the scanner removes them before parsing.
- Mention that whitespace and line breaks are free-format.

4. Semantic constraints
Include every rule the parser/network must enforce, such as:
- Device names must be unique.
- Device kind must be valid.
- SWITCH qualifier must be 0 or 1.
- CLOCK qualifier must be positive.
- Gate qualifier must be 1-16, except XOR fixed at 2 inputs and DTYPE fixed ports.
- Connections must go from output to input.
- Inputs cannot be connected more than once.
- Referenced devices and ports must exist.
- Every required input must be connected before simulation.
- Monitors must refer to valid outputs.

5. Error handling
- Syntax errors: print current line, caret marker, and clear message, then recover at the next semicolon/section keyword.
- Semantic errors: print clear message with the bad name/port/device and location if available.
- Parser returns failure if any error is found.
- Stop building the network after the first error, but continue parsing to report more errors where possible.

6. Example definition files and diagrams
- Example 1: simple NAND latch from the brief.
- Example 2: a different circuit, e.g. clocked DTYPE or XOR/AND combination.
- Each example must include a readable definition file and a circuit diagram.

## Second Interim Report Instructions
Each person submits individually.

Code zip must contain:
- Code written or modified by that person/group.
- Pytest tests.
- Any altered supplied code.
- A text file from `git log --author="Your Name"`.
- README only if code intentionally breaks PEP 8/257.

PDF must contain:
- Example definition files.
- Circuit diagrams for those files.
- A one-page user guide written individually.

One-page user guide should include:
- How to run command-line mode: `python logsim.py -c path/to/file.txt`.
- How to run GUI mode: `python logsim.py path/to/file.txt`.
- Definition language summary.
- Available commands/buttons: run, continue, set switch, add monitor, remove monitor, quit.
- Explanation of supplied example files.
- Common errors and what their messages mean.

## Final Report Instructions
Each person writes an individual report, max 5 pages excluding title page and appendices.

Required structure:
- Title page: name, team number, college, CRSID.
- Introduction, about 0.5 page.
- Logic simulator function and software structure, about 1 page.
- Teamwork and collaboration commentary, about 1 page.
- Software written or modified by you, about 1 page.
- Test procedures, about 0.5 page.
- Conclusions and future improvements, about 1 page.

Appendices:
- A: Example files, diagrams, and test results, can be shared.
- B: Logic description language specification, can be shared.
- C: Single-page user guide, must be individually written.
- D: Brief description of files in the final folder, can be shared.

Make sure the repository contains a [`final`](final) folder with final Python code and test definition files before submission.

## Timeline

Now to Sunday 17 May:
- Form team roles.
- Everyone completes Python preliminaries if needed.
- Read supplied code together.
- Agree the definition language grammar.
- Create two valid example definition files and start diagrams.

Monday 18 May to Thursday 21 May:
- A drafts EBNF and scanner token list.
- B drafts semantic constraints and parser function structure.
- C drafts example circuits, diagrams, and GUI plan.
- Team reviews the language and freezes it by Thursday evening.

Friday 22 May to Sunday 24 May:
- Finish first interim report.
- Check EBNF matches the parser plan.
- Proofread semantic error list.
- Submit group PDF before Sunday 24 May, 4pm.

Monday 25 May to Wednesday 27 May:
- A implements and tests `names.py` and main scanner basics.
- B writes parser skeleton using the agreed grammar.
- C builds GUI layout and studies `userint.py` for command behavior.
- Everyone starts committing regularly.

Thursday 28 May to Sunday 31 May:
- A finishes scanner with comments, numbers, names, keywords, punctuation, and error location output.
- B completes syntax parsing and parser tests using fake/simple valid files.
- C implements GUI controls for run/continue/switch/monitor/zap and starts waveform display.
- Cross-test another person's module.

Monday 1 June to Wednesday 3 June:
- B adds semantic checks and network construction.
- A fixes scanner/parser interface bugs and expands scanner tests.
- C performs integrated GUI and command-line testing.
- Team prepares example files, diagrams, and user guide drafts.

Thursday 4 June:
- Freeze second interim code.
- Run pytest and PEP 8/257 checks.
- Test on DPO Linux if possible.
- Prepare individual zips, git logs, and PDFs.

Friday 5 June before 11am:
- Submit second interim report/code.

Friday 5 June after 11am to Sunday 7 June:
- Read maintenance memo as a team.
- Split maintenance changes by affected area.
- Keep changes small and tested.

Monday 8 June to Wednesday 10 June:
- Finish maintenance implementation.
- Add/update pytest tests and definition files.
- Re-test command-line mode and GUI mode.
- Start final reports.

Thursday 11 June:
- Create and test the `final` folder.
- Run the project from a clean checkout/folder.
- Finish screenshots/test results.
- Final proofreading of individual reports.

Friday 12 June:
- Submit final zip and PDF before 4pm.
- Attend final DPO demo slot between 4pm and 6pm.

## Working Rules
- Keep the implementation simple.
- Use git branches or very small commits so work can be merged easily.
- Do not change the agreed grammar mid-project unless the whole team approves.
- Every bug found during integration should become a test where practical.
- Test regularly on Linux because assessment is under DPO Linux.
- Prioritise correct parser/scanner behavior over a fancy GUI.

## Minimum Definition of Done
Before second interim:
- Definition files parse correctly.
- Syntax and semantic errors are reported clearly.
- The network is built through supplied `Devices`, `Network`, and `Monitors` APIs.
- Command-line mode works.
- GUI supports the required user actions.
- Pytest tests pass.

Before final:
- Maintenance memo features are implemented.
- `final` folder exists and runs out of the box.
- Test definition files are included.
- Final reports explain individual contributions honestly and clearly.