# Intent: an Earth and space diagram set, with the critique checked

## Goal

Generate five labeled science diagrams for Team Project 1's audience (K-12 teachers) from one prompt family, and know which ones are usable without trusting the model that judges them. Each diagram gets a yes/no checklist made from its prompt's requirements, a vision model answers the checklist, and plain code decides what the answers mean.

## Who it is for

A teacher who needs a correct diagram for a lesson, and me, deciding what Team Project 1's critique path should keep. A wrong label in a science diagram teaches the wrong thing, so a diagram that "looks fine" is not enough.

## The prompt family

Earth and space, one diagram per subject: The Solar System, Layers of the Earth, Volcano Cross-Section, Phases of the Moon, The Rock Cycle. Fixed for all five: a flat-color 2D textbook style on a white background, labels in clear text, and the subject's name as a large title at the top. Only the subject changes. Each prompt has a fixed seed.

## Constraints

- The critique is model output and may be wrong in either direction: it can call a correct diagram wrong, or a wrong one correct. The program makes that visible instead of hiding it.
- A critique that is not JSON is a failed critique, not a crash.
- A requirement the critic did not answer is a problem, and so is one it made up.
- The title is compared with the expected text in code. The critic reads the title; it does not get to judge whether its own reading is right.
- One generation per prompt and one critique per image. No model call runs inside a loop of tests.
- No API key in the repository.

## Not in scope

- Fixing bad images automatically. This lab finds them; Team Project 1 decides what to do with them.
- More than one style, or more than five subjects.

## How success is checked

No-key tests for the checker on hand-written critiques. Five real images and their critiques on two vision models, with every disagreement looked at by me. A seed re-run and one comparison image model. Results in `week06/CHECKS.md`.

**Approved by:** Ralston Raphael, November 9, 2026
