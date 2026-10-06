"""Discovery of the per-subject question modules.

Every module in this package (other than the infrastructure ones below) must
export ``QUESTION_SET``. Discovery by scanning the package means several authors
can add subjects in parallel without editing a shared registry.
"""

import importlib
import pkgutil

from app.seeds.questions import types as _types
from app.seeds.questions.types import SubjectQuestionSet

_INFRASTRUCTURE_MODULES = {"types", "loader", "validate"}
_PACKAGE = __name__.rsplit(".", 1)[0]  # "app.seeds.questions"


def load_question_sets() -> list[SubjectQuestionSet]:
    package = importlib.import_module(_PACKAGE)
    sets: list[SubjectQuestionSet] = []
    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if module_info.name in _INFRASTRUCTURE_MODULES:
            continue
        module = importlib.import_module(f"{_PACKAGE}.{module_info.name}")
        question_set = getattr(module, "QUESTION_SET", None)
        if not isinstance(question_set, _types.SubjectQuestionSet):
            raise TypeError(f"{module.__name__} must export QUESTION_SET: SubjectQuestionSet")
        sets.append(question_set)
    return sets
