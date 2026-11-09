# Week 6 checks: Earth and space image set

Run November 9, 2026, on the OpenRouter key from Team Project 1 (`.env`, never committed). Everything billed below together cost about **$0.14**.

The "what I saw" columns are from looking at each image before reading any critique (titles read letter by letter). The images are in `images/`, `images-seed/` and `images-nb/`. **Ralston: confirm each "what I saw" entry against the image before the tag.**

## Per image (FLUX.2 klein, seeds 501–505)

Cost is `usage.cost` from the Image API reply (also in `images/manifest.json`). The verdict is the code's check of each critic (`critique.json` = minimax/minimax-m3, `critique-mimo.json` = xiaomi/mimo-v2.6-flash). The title is the narrow read compared in code with `expected_text`.

| Image | Cost | Gen s | minimax verdict | mimo verdict | Title read (both) | What I saw |
|---|---|---|---|---|---|---|
| solar-system | $0.014 | 3.0 | unmet: eight planets | unmet: eight planets | "The Solar System": match | Title right. 4 planets, not 8. Every label is gibberish ("Eedmirt", "Satulh", "Glatnist", "Mecunicr"). Three planets have rings. |
| earth-layers | $0.014 | 3.7 | **failed critique**: not JSON (hit `max_tokens`=1500 on hidden reasoning; all 4 counted unanswered) | unmet: layer labels | "Layers of the Earth": match | Title right. Wedge cut-away, four colored bands. Labels misspelled ("Mantue" twice, "Outhr Core", "Inter Core", "ucrust"). |
| volcano | $0.014 | 3.7 | unmet: magma chamber, vent | unmet: all 4 | **"Volacno Cros-Sectom": MISMATCH** | Title misspelled. An outside view of a cone with a lava channel down the front, not a cut-away. No magma chamber. All labels gibberish. |
| moon-phases | $0.014 | 3.8 | unmet: eight shapes | unmet: all 4 | "Phases of the Moon": match | Title right. 4 shapes, not 8, labeled "first quatter", "waking gibbous", "waning gibbous", "waning cresnint". The dark disc is labeled waning gibbous and the full green disc waning crescent. |
| rock-cycle | $0.014 | 3.1 | unmet: rock labels | unmet: rock labels | "The Rock Cycle": match | Title right. Three rocks, arrows around them, one small gap on the right. Labels "Ignous", "Mgimartcary", "Metamrhcan", "Selidenalry". |

**0 of 5 images pass the code's check on either critic.** The checker found something wrong with every image, and the critics agreed on all five titles. Only one title (the volcano) was actually wrong.

## Seed check

`volcano` again with seed 503 (`images-seed/`, $0.014, 3.4 s). **By eye: the same picture**, including the same misspelled title and the same nonsense labels. **`cmp`: the bytes differ** ("differ: char 113, line 1"); both files are 207,459 bytes. So the seed fixes the picture, not the JPEG bytes, and comparing hashes would wrongly say "different image". This matches the course's October 20 finding.

## Comparison image model

`volcano` on `google/gemini-3.1-flash-lite-image` (`images-nb/`): **$0.03362** from `usage.cost` (2.4× FLUX), 4.3 s. The title came out right ("VOLCANO CROSS-SECTION"), with a real cut-away, a magma chamber, a conduit and a lava flow. minimax's checklist: **all 4 met, title match** (`critique-nb.json`). **What I saw:** it passes the checklist, but the "Vent" arrow points at the magma chamber, "Throat" appears twice, and "Crust" points at the ground surface. None of those were on the checklist, so the code could not see them. A teacher would.

## Step 5: the critic checked

### Where the two critics disagreed (`python3 critique.py --compare critique.json critique-mimo.json`: 3 images)

| Image | Requirement | minimax | mimo | What I saw | Who was right |
|---|---|---|---|---|---|
| earth-layers | all four | no answer (failed critique) | cross-section ✓, four layers ✓, labels ✗, no people ✓ | as mimo said | mimo |
| volcano | cut in half as a cross-section | true | false | outside view, not a cut-away | mimo |
| volcano | lava coming out | true | false | lava runs from the crater down the front | minimax (met) |
| moon-phases | a full moon is shown | true | false | a full disc is there, but labeled "waning cresnint" | mimo, for teaching use |
| moon-phases | a new moon is shown | true | false | a dark disc is there, but labeled "waning gibbous" | mimo, for teaching use |
| moon-phases | every shape has a label | true | false | all four have one; mimo marked it false "since there are only four" | minimax (mimo answered a different question) |

### Where they agreed and were both wrong, or both loose

- **solar-system, "Every planet has a text label":** both said true. Each planet has *a* label, but every label is gibberish. The requirement was too weak; "labeled with its correct name" would have caught it.
- **solar-system, "Saturn is drawn with rings":** both said true, because of the planet whose label they read as "Saturlh" (minimax) and "Satwlth" (mimo). The image prints "Satulh". Both misread the same label, each in a different way, and three planets have rings. No planet is actually named Saturn.
- **rock-cycle evidence:** minimax wrote that only "Igneous" was labeled clearly. The image says "Ignous", so it silently corrected the spelling in its own evidence. mimo quoted "Ignous" correctly.

### The open-ended critique (`open-ended-volcano.txt`)

minimax-m3 on `images/volcano.jpg`: "Critique this science diagram. What is wrong with it?" The first try at `max_tokens`=2000 returned **no text at all** (finish `length`, $0.00283, all hidden reasoning). The second try at 8000 answered (4,503 tokens out, $0.00583). This ran in a plain Python script outside the repository's Claude Code session, so the hook and spec were not involved. Ralston did not type it himself.

Claims, against the image:

- True: the labels are "nonsensical pseudo-text". It quoted "Roabcionncre Fiemclone", "Dinable", and "Chgisfacans" (printed "Chglsfacans"). "Erampeloom" is printed "Erimpeloom".
- True: one leader line at upper left has no label.
- True: no magma chamber under the conduit.
- True: it is not a real cut-away ("the cut face is not defined").
- Plausible but not checkable from the prompt: no lava/ash layers, no legend, and "stratovolcano" would be the better name.
- **Missed:** the title. It wrote "The title says 'Volcano'", but the title says **"Volacno Cros-Sectom"**. It corrected the spelling in its head, which is the October 19 story run backwards. The narrow title read, compared in code, is the only check here that caught it.

### Which check caught what

The narrow title question, compared in code, was the only check that caught the misspelled volcano title. The open-ended critique read straight past it, and the checklist never asks about spelling. The second model was what exposed the critic's own failures: minimax's empty earth-layers critique and its looser "cross-section" call. A person looking was the only check that caught what no requirement asked: the gibberish planet labels both models accepted, the mislabeled moon phases, and Gemini's "Vent" arrow pointing at the magma chamber. For Team Project 1's critique path I would keep the narrow text read compared in code as the hard gate, add a second critic only to flag images for a person, and make every label a requirement, so the checklist asks "labeled X" rather than "has a label".

## Linter

`uvx ruff check week06`: all checks passed.

**Guard finding:** the lab says `pip install openrouter` must be blocked until `spec.md` names it. It was not blocked, even before the Week 6 spec section existed. The Week 5 spec already contained `OPENROUTER_API_KEY`, and `guard.py` matches the package name as a case-insensitive substring of `spec.md`. The guard passes for the wrong reason. It should match a package listed under Dependencies, not any mention of the word.

## Tests

`.venv/bin/python -m pytest week06/tests -v`: 10 passed, no key. They cover all met, one unmet by name, a truthy string that is not `true`, one unanswered, one invented, loose requirement matching, not JSON (prose, empty, `None`, wrong shape, a JSON array), JSON in prose and fences, the title comparison ("Volcano Cross-Section" vs "Volcano Cross-Sectoin"), and two critics disagreeing vs identical files. The red run is commit "Test: image-set checker (red)" and the green run is the next commit.

## Review

_Pending: the Team Project 1 pull request (branch `week06-ralston`)._
