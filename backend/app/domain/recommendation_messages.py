"""Localised "why" sentences for recommendations: a plain template dictionary
(no i18n library). Keys come from `Candidate.reason_key`; unknown languages
fall back to English. Plural forms are separate keys (`*_one`, `*_other`).
"""

from collections.abc import Mapping

_EN: dict[str, str] = {
    "review_due_today": "Your spaced-repetition review is due today.",
    "review_due_one": "Your review is 1 day overdue; recalling it now keeps it from fading.",
    "review_due_other": (
        "Your review is {days} days overdue; recalling it now keeps it from fading."
    ),
    "goal_deadline_overdue": 'Your goal "{goal}" is past its target date.',
    "goal_deadline_today": 'Your goal "{goal}" is due today.',
    "goal_deadline_one": 'Your goal "{goal}" is due in 1 day.',
    "goal_deadline_other": 'Your goal "{goal}" is due in {days} days.',
    "strengthen_weak": "Mastery is only {mastery}%; a bit more practice will make it stick.",
    "strengthen_weak_lapse": (
        "You struggled to recall this last time (mastery {mastery}%); reinforce it."
    ),
    "take_quiz": "Only {coverage}% of its quiz questions are answered correctly; test yourself.",
    "continue_learning": "You are part way there (mastery {mastery}%); keep going.",
    "next_in_path": "Next unlocked step of your path {path}.",
    "starting_point_path": "A good place to start: the first step of {path}.",
    "starting_point": "A good place to start your learning.",
}

_PT_BR: dict[str, str] = {
    "review_due_today": "Sua revisão espaçada vence hoje.",
    "review_due_one": "Sua revisão está 1 dia atrasada; relembrar agora evita que ela se perca.",
    "review_due_other": (
        "Sua revisão está {days} dias atrasada; relembrar agora evita que ela se perca."
    ),
    "goal_deadline_overdue": 'Sua meta "{goal}" passou da data-alvo.',
    "goal_deadline_today": 'Sua meta "{goal}" vence hoje.',
    "goal_deadline_one": 'Sua meta "{goal}" vence em 1 dia.',
    "goal_deadline_other": 'Sua meta "{goal}" vence em {days} dias.',
    "strengthen_weak": "O domínio está em apenas {mastery}%; mais prática vai fixar o conteúdo.",
    "strengthen_weak_lapse": (
        "Você teve dificuldade de lembrar disto da última vez (domínio {mastery}%); reforce."
    ),
    "take_quiz": "Você acertou só {coverage}% das questões do quiz; teste-se.",
    "continue_learning": "Você está no meio do caminho (domínio {mastery}%); continue.",
    "next_in_path": "Próxima etapa liberada da sua trilha {path}.",
    "starting_point_path": "Um bom ponto de partida: a primeira etapa de {path}.",
    "starting_point": "Um bom ponto de partida para começar a aprender.",
}

TEMPLATES: Mapping[str, Mapping[str, str]] = {"en": _EN, "pt-BR": _PT_BR}


def _template_key(reason_key: str, params: Mapping[str, str | int]) -> str:
    days = params.get("days")
    if reason_key == "review_due":
        if days == 0:
            return "review_due_today"
        return "review_due_one" if days == 1 else "review_due_other"
    if reason_key == "goal_deadline" and isinstance(days, int):
        if days < 0:
            return "goal_deadline_overdue"
        if days == 0:
            return "goal_deadline_today"
        return "goal_deadline_one" if days == 1 else "goal_deadline_other"
    return reason_key


def render_reason(reason_key: str, params: Mapping[str, str | int], language: str) -> str:
    templates = TEMPLATES.get(language, _EN)
    key = _template_key(reason_key, params)
    return templates.get(key, _EN[key]).format(**params)
