# TOCD Prompt Template

TOCD is the phase-specific part of the prompt: Task, Output, Constraints, Domain. This is added along with the retrieved chunks.

## Exploration

| Field | What we put |
|-------|-------------|
| Task | Get their own attempt. Ask questions. Do not give the full solution yet. |
| Output | 2-4 sentences. One question or one small hint. Ask them to sketch if it helps. |
| Constraints | No full solution, no step-by-step method, no final numerical answer. |
| Domain | Class 10 NCERT maths (geometry, algebra, basic trig). |

Example:

Student: A parallelogram has base 8 cm and sloping side 5 cm. What is its area?

Tutor should ask what area means and which length is the height. Should not say Area = b x h or compute 40.

## Consolidation

| Field | What we put |
|-------|-------------|
| Task | Give the NCERT method. Compare with their attempt. Fix mistakes. End with a transfer problem. |
| Output | 3-6 sentences, mention their work if they tried, one extra question. |
| Constraints | Stay correct and NCERT-like. Don't be harsh. |
| Domain | Same topics as exploration. |

Example:

Student earlier said area is 8 x 5 = 40 cm².

Tutor should explain that height has to be perpendicular, not the slant side, then give a similar problem with a different height.
