"""Question bank for the AI Engineering subject (llm-fundamentals,
context-engineering, rag-architecture, ai-agents-tool-use, ai-evaluation;
ten questions each, English + Brazilian Portuguese).

Written by Claude (``source=ai_generated``) and awaiting the owner's review,
as decided in docs/PROPOSAL_TRACK_I.md (D6). Rules: ``validate.py``.

Deliberately conceptual: no product/model names, versions or prices, so the
bank does not go stale.
"""

from app.models.assessment import (
    AssessmentKind,
    QuestionDifficulty,
    QuestionSource,
    QuestionType,
)
from app.models.user import Language
from app.seeds.questions.types import (
    AssessmentSeed,
    OptionSeed,
    QuestionSeed,
    QuestionText,
    SubjectQuestionSet,
)

EASY = QuestionDifficulty.EASY
MEDIUM = QuestionDifficulty.MEDIUM
HARD = QuestionDifficulty.HARD
MC = QuestionType.MULTIPLE_CHOICE
MS = QuestionType.MULTI_SELECT
CODE = QuestionType.CODE_READING
SHORT = QuestionType.SHORT_ANSWER
AI = QuestionSource.AI_GENERATED


def _options(*texts: str) -> tuple[OptionSeed, ...]:
    """_options("text a", "text b", ...) -> options with ids a, b, c..."""
    return tuple(OptionSeed(id=chr(ord("a") + i), text=text) for i, text in enumerate(texts))


def _q(
    code: str,
    competency: str,
    type_: QuestionType,
    difficulty: QuestionDifficulty,
    correct: tuple[str, ...] | None,
    tags: tuple[str, ...],
    en: QuestionText,
    pt: QuestionText,
) -> QuestionSeed:
    return QuestionSeed(
        code=code,
        competency_slug=competency,
        type=type_,
        difficulty=difficulty,
        correct=correct,
        tags=tags,
        source=AI,
        text={Language.EN: en, Language.PT_BR: pt},
    )


def _t(
    prompt: str,
    explanation: str,
    options: tuple[OptionSeed, ...] | None = None,
    model_answer: str | None = None,
) -> QuestionText:
    return QuestionText(
        prompt=prompt, explanation=explanation, options=options, model_answer=model_answer
    )


_COSINE_CODE = """```python
import math

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

print(round(cosine([1, 0], [3, 0]), 2),
      round(cosine([1, 0], [0, 2]), 2),
      round(cosine([1, 1], [-1, -1]), 2))
```"""

# ----------------------------------------------------------------------
# llm-fundamentals
# ----------------------------------------------------------------------
_LLM = "llm-fundamentals"

LLM_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "llm-fundamentals-q01",
        _LLM,
        MC,
        EASY,
        ("c",),
        ("tokens", "tokenization"),
        _t(
            "Which description of a **token** is the most accurate?",
            "A tokenizer splits text into pieces from a fixed vocabulary; a common word may be "
            "a single token while a rare word is split into several subword pieces. That is why "
            "word count and token count differ. Options A and B describe special cases at best, "
            "and D (a whole sentence) is not how tokenizers work.",
            _options(
                "Exactly one word of the input text.",
                "Exactly one character of the input text.",
                "A unit of text produced by the model's tokenizer, often a word or a piece of a "
                "word.",
                "One whole sentence of the input text.",
            ),
        ),
        _t(
            "Qual descrição de **token** é a mais precisa?",
            "Um tokenizer divide o texto em pedaços de um vocabulário fixo; uma palavra comum "
            "pode ser um único token, enquanto uma palavra rara é dividida em vários pedaços "
            "(subwords). Por isso o número de palavras difere do número de tokens. As opções A "
            "e B descrevem, no máximo, casos particulares, e a D (uma frase inteira) não "
            "corresponde ao funcionamento de um tokenizer.",
            _options(
                "Exatamente uma palavra do texto de entrada.",
                "Exatamente um caractere do texto de entrada.",
                "Uma unidade de texto produzida pelo tokenizer do modelo, geralmente uma "
                "palavra ou um pedaço de palavra.",
                "Uma frase inteira do texto de entrada.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q02",
        _LLM,
        MC,
        EASY,
        ("b",),
        ("sampling", "temperature"),
        _t(
            "What does lowering the sampling temperature toward 0 do?",
            "Temperature reshapes the next-token distribution before sampling. Low values "
            "concentrate probability on the top-ranked tokens, so generation approaches greedy "
            "decoding and becomes more repeatable. A describes the opposite (high temperature). "
            "C is false: determinism says nothing about correctness, and a model can "
            "consistently repeat a wrong answer. D confuses sampling with the context window.",
            _options(
                "It flattens the distribution so the model becomes more creative.",
                "It concentrates probability on the highest-ranked tokens, so output approaches "
                "greedy decoding and becomes more repeatable.",
                "It guarantees that the answer is factually correct.",
                "It reduces the number of tokens that fit in the context window.",
            ),
        ),
        _t(
            "O que acontece ao reduzir a temperatura de amostragem (sampling temperature) "
            "para perto de 0?",
            "A temperatura remodela a distribuição do próximo token antes da amostragem. "
            "Valores baixos concentram a probabilidade nos tokens mais bem ranqueados, então a "
            "geração se aproxima do greedy decoding e fica mais repetível. A descreve o oposto "
            "(temperatura alta). A C é falsa: determinismo não diz nada sobre correção, e um "
            "modelo pode repetir consistentemente uma resposta errada. A D confunde amostragem "
            "com janela de contexto.",
            _options(
                "A distribuição fica mais plana e o modelo se torna mais criativo.",
                "A probabilidade se concentra nos tokens mais bem ranqueados, então a saída se "
                "aproxima do greedy decoding e fica mais repetível.",
                "Garante que a resposta seja factualmente correta.",
                "Reduz o número de tokens que cabem na janela de contexto.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q03",
        _LLM,
        MC,
        EASY,
        ("d",),
        ("context-window",),
        _t(
            "What does the **context window** of a model limit?",
            "The context window is the maximum number of tokens the model can handle in one "
            "request, covering the input and the generated output together. A refers to "
            "training data size, B to model size, and C to API rate limits; none of these is "
            "the context window.",
            _options(
                "How many tokens the model saw during training.",
                "How many parameters the model has.",
                "How many requests per minute you may send.",
                "The maximum number of tokens the model can handle in a single request, "
                "counting both the input and the generated output.",
            ),
        ),
        _t(
            "O que a **janela de contexto** (context window) de um modelo limita?",
            "A janela de contexto é o número máximo de tokens que o modelo consegue processar "
            "em uma requisição, contando entrada e saída gerada em conjunto. A se refere ao "
            "tamanho dos dados de treinamento, B ao tamanho do modelo e C aos limites de taxa "
            "da API; nenhuma delas é a janela de contexto.",
            _options(
                "Quantos tokens o modelo viu durante o treinamento.",
                "Quantos parâmetros o modelo possui.",
                "Quantas requisições por minuto você pode enviar.",
                "O número máximo de tokens que o modelo consegue processar em uma única "
                "requisição, contando a entrada e a saída gerada.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q04",
        _LLM,
        MS,
        MEDIUM,
        ("a", "c", "e"),
        ("hallucination", "mitigation"),
        _t(
            "Which statements about hallucination are **true**? Select all that apply.",
            "A is true: training rewards plausible continuations and has no built-in "
            "'I don't know' outcome. C is true: retrieval grounding constrains the answer but "
            "the model can still misread or ignore the context. E is true: external checks "
            "(a database, a schema validator, a tool) are more dependable than only "
            "instructing the model to be careful. B is false: temperature 0 only makes output "
            "repeatable, not correct. D is false: fluent, confident wording is not evidence of "
            "accuracy.",
            _options(
                "The training objective rewards plausible continuations and has no built-in "
                "notion of 'I don't know'.",
                "Setting the temperature to 0 eliminates hallucination.",
                "Grounding answers in retrieved documents reduces hallucination but does not "
                "eliminate it.",
                "A fluent, confident tone is a reliable sign that an answer is correct.",
                "Checking outputs against an authoritative source (a database, a validator, a "
                "tool) is more dependable than only telling the model not to make things up.",
            ),
        ),
        _t(
            "Quais afirmações sobre alucinação são **verdadeiras**? Selecione todas que se "
            "aplicam.",
            "A é verdadeira: o treinamento recompensa continuações plausíveis e não tem um "
            "resultado embutido do tipo 'não sei'. C é verdadeira: o grounding por recuperação "
            "restringe a resposta, mas o modelo ainda pode interpretar mal ou ignorar o "
            "contexto. E é verdadeira: verificações externas (um banco de dados, um validador "
            "de schema, uma ferramenta) são mais confiáveis do que apenas instruir o modelo a "
            "tomar cuidado. B é falsa: temperatura 0 só torna a saída repetível, não correta. "
            "D é falsa: um texto fluente e confiante não é evidência de precisão.",
            _options(
                "O objetivo de treinamento recompensa continuações plausíveis e não tem uma "
                "noção embutida de 'não sei'.",
                "Definir a temperatura como 0 elimina a alucinação.",
                "Ancorar (grounding) as respostas em documentos recuperados reduz a alucinação, "
                "mas não a elimina.",
                "Um tom fluente e confiante é um sinal confiável de que a resposta está correta.",
                "Verificar as saídas contra uma fonte autoritativa (um banco de dados, um "
                "validador, uma ferramenta) é mais confiável do que apenas dizer ao modelo para "
                "não inventar.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q05",
        _LLM,
        MC,
        MEDIUM,
        ("c",),
        ("sampling", "top-p"),
        _t(
            "With top-p (nucleus) sampling set to 0.9, which candidates does the model sample "
            "from at each step?",
            "Top-p keeps the smallest set of most likely tokens whose cumulative probability "
            "reaches at least 0.9, so the pool size adapts to how confident the model is. A "
            "describes top-k (a fixed count of candidates). B would usually select nothing, "
            "since a single token rarely exceeds 0.9. D is wrong: the pool is chosen by "
            "probability, not at random.",
            _options(
                "The 90 most likely tokens.",
                "Only tokens whose individual probability exceeds 0.9.",
                "The smallest set of most likely tokens whose cumulative probability reaches "
                "at least 0.9.",
                "A random 90% of the vocabulary.",
            ),
        ),
        _t(
            "Com top-p (nucleus sampling) definido como 0,9, de quais candidatos o modelo "
            "amostra a cada passo?",
            "O top-p mantém o menor conjunto de tokens mais prováveis cuja probabilidade "
            "acumulada atinge pelo menos 0,9, então o tamanho do conjunto se adapta à confiança "
            "do modelo. A descreve o top-k (um número fixo de candidatos). B normalmente não "
            "selecionaria nada, pois um único token raramente passa de 0,9. D está errada: o "
            "conjunto é escolhido por probabilidade, não ao acaso.",
            _options(
                "Os 90 tokens mais prováveis.",
                "Apenas os tokens cuja probabilidade individual excede 0,9.",
                "O menor conjunto de tokens mais prováveis cuja probabilidade acumulada atinge "
                "pelo menos 0,9.",
                "Uma seleção aleatória de 90% do vocabulário.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q06",
        _LLM,
        CODE,
        MEDIUM,
        ("c",),
        ("embeddings", "cosine-similarity"),
        _t(
            "What does this code print?\n\n" + _COSINE_CODE,
            "Cosine similarity compares direction, not magnitude. `[1, 0]` and `[3, 0]` point "
            "the same way (1.0), `[1, 0]` and `[0, 2]` are orthogonal (0.0), and `[1, 1]` and "
            "`[-1, -1]` point in opposite directions (-1.0). A would be the result if the "
            "vector length mattered (a raw dot product gives 3, 0, -2), and B ignores the sign "
            "of the last pair.",
            _options(
                "`3.0 0.0 -2.0`",
                "`1.0 0.0 1.0`",
                "`1.0 0.0 -1.0`",
                "`0.5 0.0 -0.5`",
            ),
        ),
        _t(
            "O que este código imprime?\n\n" + _COSINE_CODE,
            "A similaridade de cosseno compara direção, não magnitude. `[1, 0]` e `[3, 0]` "
            "apontam para o mesmo lado (1.0), `[1, 0]` e `[0, 2]` são ortogonais (0.0) e "
            "`[1, 1]` e `[-1, -1]` apontam em sentidos opostos (-1.0). A seria o resultado se o "
            "comprimento dos vetores importasse (o produto escalar bruto dá 3, 0, -2), e B "
            "ignora o sinal do último par.",
            _options(
                "`3.0 0.0 -2.0`",
                "`1.0 0.0 1.0`",
                "`1.0 0.0 -1.0`",
                "`0.5 0.0 -0.5`",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q07",
        _LLM,
        MC,
        MEDIUM,
        ("a",),
        ("sampling", "extraction"),
        _t(
            "You use an LLM to extract the date, amount and vendor from invoices, and you want "
            "results to be as consistent as possible from run to run. Which setup fits best?",
            "Extraction rewards consistency, so low temperature is the right default, and "
            "because even low-temperature output can be wrong or malformed you should still "
            "validate it (for example against a schema). B and C add randomness that "
            "extraction does not need. D is false: sampling settings directly affect how much "
            "outputs vary.",
            _options(
                "A low temperature (near 0), plus validation of the output against a schema.",
                "A high temperature with top-p 1.0 so the model explores every phrasing.",
                "A temperature well above 1 with a large top-k to avoid repetitive output.",
                "Any setting works, because sampling parameters never affect extraction.",
            ),
        ),
        _t(
            "Você usa um LLM para extrair data, valor e fornecedor de notas fiscais e quer "
            "resultados o mais consistentes possível entre execuções. Qual configuração é a "
            "mais adequada?",
            "Extração valoriza consistência, então temperatura baixa é o padrão correto, e como "
            "até uma saída com temperatura baixa pode estar errada ou malformada, ainda assim "
            "convém validá-la (por exemplo, contra um schema). B e C adicionam aleatoriedade "
            "de que a extração não precisa. D é falsa: os parâmetros de amostragem afetam "
            "diretamente o quanto as saídas variam.",
            _options(
                "Temperatura baixa (perto de 0), mais validação da saída contra um schema.",
                "Temperatura alta com top-p 1,0 para o modelo explorar todas as formulações.",
                "Temperatura bem acima de 1 com top-k grande para evitar saídas repetitivas.",
                "Qualquer configuração serve, pois parâmetros de amostragem nunca afetam a "
                "extração.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q08",
        _LLM,
        MC,
        MEDIUM,
        ("d",),
        ("embeddings", "semantic-similarity"),
        _t(
            "The texts 'How do I get my money back?' and 'Refund policy' share no words, yet "
            "their embeddings are close together. Why?",
            "Embedding models are trained so that texts with similar meaning land near each "
            "other in vector space, so closeness reflects semantics rather than shared words. "
            "A and B describe lexical matching, which is what sparse methods such as BM25 do. "
            "C is invented: text length does not decide where a vector lands.",
            _options(
                "Embedding models match on shared letters, and both strings contain similar "
                "letters.",
                "Embeddings store the exact words, and a synonym dictionary links them at "
                "query time.",
                "Short texts always map to the same region of the vector space.",
                "The model learns to place texts with similar meaning near each other, so "
                "distance reflects semantics rather than word overlap.",
            ),
        ),
        _t(
            "Os textos 'Como faço para ter meu dinheiro de volta?' e 'Política de reembolso' "
            "não compartilham palavras, mas seus embeddings ficam próximos. Por quê?",
            "Modelos de embedding são treinados para que textos de significado parecido fiquem "
            "próximos no espaço vetorial, então a proximidade reflete semântica, não palavras "
            "em comum. A e B descrevem casamento lexical, que é o que métodos esparsos como o "
            "BM25 fazem. C é inventada: o tamanho do texto não define onde o vetor cai.",
            _options(
                "Modelos de embedding casam por letras em comum, e as duas frases têm letras "
                "parecidas.",
                "Embeddings guardam as palavras exatas, e um dicionário de sinônimos as liga "
                "no momento da consulta.",
                "Textos curtos sempre caem na mesma região do espaço vetorial.",
                "O modelo aprende a posicionar textos de significado parecido perto uns dos "
                "outros, então a distância reflete semântica e não sobreposição de palavras.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q09",
        _LLM,
        MC,
        HARD,
        ("b",),
        ("tokenization", "limitations"),
        _t(
            "Why do LLMs often stumble on tasks like counting the letters in a word, even "
            "though they handle much harder language tasks well?",
            "The model reads and writes tokens, not characters, so the letter-by-letter "
            "structure of a word is not directly visible to it; a word may be one token or an "
            "arbitrary split of pieces. A is too strong: models can do arithmetic, just not "
            "reliably, which is why tools help. C and D are unrelated: short words fit any "
            "context window, and temperature is not the cause.",
            _options(
                "They cannot do any arithmetic at all.",
                "They operate on tokens rather than characters, so the character-level "
                "structure of a word is not directly visible to them.",
                "The context window is too small to hold short words.",
                "The temperature is always too high for counting tasks.",
            ),
        ),
        _t(
            "Por que LLMs costumam tropeçar em tarefas como contar as letras de uma palavra, "
            "mesmo lidando bem com tarefas de linguagem muito mais difíceis?",
            "O modelo lê e escreve tokens, não caracteres, então a estrutura letra a letra de "
            "uma palavra não é diretamente visível para ele; uma palavra pode ser um token ou "
            "uma divisão arbitrária em pedaços. A é forte demais: modelos fazem aritmética, "
            "só que sem confiabilidade, por isso ferramentas ajudam. C e D não têm relação: "
            "palavras curtas cabem em qualquer janela de contexto, e a temperatura não é a "
            "causa.",
            _options(
                "Eles não conseguem fazer nenhuma aritmética.",
                "Eles operam sobre tokens e não sobre caracteres, então a estrutura em nível "
                "de caractere de uma palavra não é diretamente visível para eles.",
                "A janela de contexto é pequena demais para caber palavras curtas.",
                "A temperatura é sempre alta demais para tarefas de contagem.",
            ),
        ),
    ),
    _q(
        "llm-fundamentals-q10",
        _LLM,
        SHORT,
        HARD,
        None,
        ("hallucination", "grounding"),
        _t(
            "Explain in a few sentences why LLMs hallucinate, and name one architectural "
            "mitigation together with its limitation.",
            "Self-check: did you mention (1) that the model is trained to produce plausible "
            "continuations and has no built-in way to abstain, (2) one mitigation such as "
            "retrieval grounding, tool use or output validation, and (3) why it is not a "
            "complete fix?",
            model_answer="An LLM is trained to predict plausible next tokens, and the training "
            "objective has no 'I don't know' outcome, so when it lacks knowledge it still "
            "produces fluent text that sounds right. One architectural mitigation is retrieval "
            "grounding (RAG): fetch relevant documents and instruct the model to answer only "
            "from them, ideally with citations. The limitation is that it constrains rather "
            "than eliminates the problem: retrieval can miss the right passage, and the model "
            "can still misread or ignore the context, so answers should also be evaluated and "
            "verified.",
        ),
        _t(
            "Explique em poucas frases por que LLMs alucinam e cite uma mitigação "
            "arquitetural junto com sua limitação.",
            "Autoavaliação: você mencionou (1) que o modelo é treinado para produzir "
            "continuações plausíveis e não tem como se abster, (2) uma mitigação como grounding "
            "por recuperação, uso de ferramentas ou validação da saída, e (3) por que ela não "
            "é uma solução completa?",
            model_answer="Um LLM é treinado para prever os próximos tokens mais plausíveis, e o "
            "objetivo de treinamento não tem um resultado 'não sei'; por isso, quando falta "
            "conhecimento, ele ainda produz um texto fluente que soa correto. Uma mitigação "
            "arquitetural é o grounding por recuperação (RAG): buscar documentos relevantes e "
            "instruir o modelo a responder apenas com base neles, de preferência com citações. "
            "A limitação é que isso restringe o problema em vez de eliminá-lo: a recuperação "
            "pode não trazer a passagem certa, e o modelo ainda pode interpretar mal ou "
            "ignorar o contexto, então as respostas também devem ser avaliadas e verificadas.",
        ),
    ),
)

# @@NEXT-COMPETENCY@@

QUESTIONS: tuple[QuestionSeed, ...] = (*LLM_QUESTIONS,)

ASSESSMENTS: tuple[AssessmentSeed, ...] = (
    AssessmentSeed(
        code="ai-engineering-llm-fundamentals-quiz",
        title="LLM Fundamentals Quiz",
        description="Tokens, sampling, embeddings, context windows and why models hallucinate.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="llm-fundamentals",
        translations={
            "pt-BR": {
                "title": "Quiz de Fundamentos de LLMs",
                "description": "Tokens, amostragem, embeddings, janelas de contexto e por que "
                "os modelos alucinam.",
            }
        },
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="ai-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
