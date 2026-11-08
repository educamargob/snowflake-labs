# Shared knowledge-check engine. Exactly two data files, always: logic.json (grading, language-
# independent) + text.json (localizable, resolved for one language at build time -- the build
# step flattens quiz/{lang}/text.json to resources/text.json, so this module never deals with a
# language subfolder). Both are nested by persona key -- lab shape (flat vs
# persona-specific) is detected from CONTENT, not filenames:
#
#   Flat/shared quiz (one quiz for the whole lab, e.g. shared across personas):
#     logic.json = {"shared": {"q1": {...}, ...}}  -- single sentinel key "shared"
#     Usage:  from <folder>.knowledgecheck import quiz
#             quiz.display_question("q1")
#
#   Persona-specific quizzes (each persona has its own questions):
#     logic.json = {"data_analyst": {"q1": {...}, ...}, "data_engineer": {...}, ...}
#     (persona token uses underscores, e.g. "data_analyst", so readable names generate cleanly)
#     Usage:  from <folder>.knowledgecheck import data_analyst_quiz as quiz
#             quiz.display_question("q1")
#
# In both shapes, every quiz cell after the import looks the same: quiz.display_question(id).
# Binding the persona to a notebook-local variable (quiz) means a quiz cell copy-pasted into
# the wrong notebook fails loudly (NameError on `quiz`) instead of silently rendering the
# wrong questions.
#
# Nothing here is hand-maintained: the set of exported names (quiz, or <persona>_quiz /
# <PERSONA> per discovered persona) is generated entirely from logic.json's top-level keys at
# import time. To add a persona: add its key to both logic.json and en/text.json -- no code
# change needed. To add a question: add a matching "qN" entry to both files, under the same key.
#
# This is the ONE canonical, authored copy of this module (utils/quiz/knowledgecheck.py).
# It gets physically copied alongside each notebook at build time -- Workspace Notebooks can
# only import from subfolders of the notebook's own directory, so a single shared copy can't be
# imported directly across labs. Never edit a copy; edit this file and re-run the build.

import json
from pathlib import Path
from random import randint, shuffle

from IPython.display import HTML, display

_RESOURCES_DIR = Path(__file__).parent
_cache = {}

css_template = '''
<style>
.question {
    font-family: Arial, sans-serif;
    margin: 20px 0; 
    padding: 16px; 
    border: 1px solid #d0d0d0; 
    border-radius: 10px; 
    background: #fafafa;
}

.choice {
    position: relative;
    margin-bottom: 3px;
}
.choice-input {
    position: absolute;
    top: 10px;
}

.choice-text {
    display: block;
    padding: 10px;
    padding-left: 30px;
}

.choice-text:hover {
    background-color: #e8f0fe;
}

.choice-feedback {
    display: none;
    padding: 10px;
}

/* CORRECT_SELECTOR */ {
    .choice-input:checked ~ .choice-text {
        background-color: #e6f4ea; 
    }
    .choice-feedback {
        color: #1e7e34;
    }
    .choice-feedback::before {
        content: "✅ ";
    }
}

/* INCORRECT_SELECTOR */  { 
    .choice-input:checked ~ .choice-text {
        background-color: #fce8e6;
    }
    .choice-feedback {
        color: #c62828;
    }
    .choice-feedback::before {
        content: "❌ ";
    }
}

.choice-input:checked ~ .choice-text .choice-feedback {
    display: block;
}
</style>
'''


def _validate(persona, logic, text):
    logic_ids = set(logic.keys())
    text_ids = set(text.keys())
    if logic_ids != text_ids:
        only_logic = sorted(logic_ids - text_ids)
        only_text = sorted(text_ids - logic_ids)
        raise ValueError(
            f"{persona}: logic.json and text.json question ids don't match. "
            f"Only in logic: {only_logic or 'none'}. Only in text: {only_text or 'none'}."
        )
    for qid in logic_ids:
        choice_ids = set(text[qid]["choices"].keys())
        correct_ids = set(logic[qid]["correct"])
        missing = correct_ids - choice_ids
        if missing:
            raise ValueError(
                f"{persona} {qid}: logic.json marks {sorted(missing)} as correct, "
                f"but text.json has no such choice id (choices: {sorted(choice_ids)})."
            )


def _all_logic():
    if "_logic" not in _cache:
        _cache["_logic"] = json.loads((_RESOURCES_DIR / "logic.json").read_text())
    return _cache["_logic"]


def _all_text():
    if "_text" not in _cache:
        _cache["_text"] = json.loads((_RESOURCES_DIR / "text.json").read_text())
    return _cache["_text"]


def _load(persona):
    key = persona or "shared"
    cache_key = f"_merged_{key}"
    if cache_key not in _cache:
        logic = _all_logic()[key]
        text = _all_text()[key]
        _validate(key, logic, text)
        merged = {}
        for qid, meta in logic.items():
            merged[qid] = {**meta, **text[qid]}
        _cache[cache_key] = merged
    return _cache[cache_key]


def display_question(persona, question_id):
    data = _load(persona)
    if question_id not in data:
        return

    q = data[question_id]
    choice_items = list(q["choices"].items())  # [(choice_id, {"text":..., "feedback":...}), ...]
    if q["shuffle_choices"]:
        shuffle(choice_items)

    html = f'<div class="question"><h4 class="stem">{q["prompt"]}</h4>'

    correct_selectors = []
    incorrect_selectors = []
    for choice_id, choice in choice_items:
        dom_id = f"{question_id}-{randint(0, 999999999999999999)}"
        input_type = "checkbox" if q["multiselect"] else "radio"
        if choice_id in q["correct"]:
            correct_selectors.append(f".choice.{dom_id}")
        else:
            incorrect_selectors.append(f".choice.{dom_id}")
        html += f'''
            <div class="choice {dom_id}">
                <input type="{input_type}" name="{question_id}" id="input-{dom_id}" class="choice-input" />
                <label class="choice-text" for="input-{dom_id}">{choice["text"]}<div class="choice-feedback">{choice["feedback"]}</div></label>
            </div>
        '''
    html += "</div>"

    if len(correct_selectors) == 0:
        correct_selectors.append(".choice.null")
    if len(incorrect_selectors) == 0:
        incorrect_selectors.append(".choice.null")
    css = css_template.replace("/* CORRECT_SELECTOR */", ", ".join(correct_selectors))
    css = css.replace("/* INCORRECT_SELECTOR */", ", ".join(incorrect_selectors))

    display(HTML(css + html))


def display_all_questions(persona):
    for question_id in _load(persona):
        display_question(persona, question_id)


class KnowledgeCheck:
    def __init__(self, persona):
        self._persona = persona  # None => flat/shared quiz (shape A)

    def display_question(self, question_id):
        display_question(self._persona, question_id)

    def display_all_questions(self):
        display_all_questions(self._persona)


_keys = sorted(_all_logic().keys())
if _keys == ["shared"]:
    quiz = KnowledgeCheck(None)
else:
    for _persona in _keys:
        globals()[_persona.upper()] = _persona
        globals()[f"{_persona}_quiz"] = KnowledgeCheck(_persona)
