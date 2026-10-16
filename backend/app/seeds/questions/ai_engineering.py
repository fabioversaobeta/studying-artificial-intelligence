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
                "Exactly one word of the input text, as separated by spaces and punctuation.",
                "Exactly one character of the input text, including spaces and punctuation "
                "marks.",
                "A unit of text from the model's tokenizer, often a word or part of a word.",
                "One whole sentence of the input text, up to the next full stop.",
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
                "Exatamente uma palavra do texto de entrada, separada por espaços e "
                "pontuação.",
                "Exatamente um caractere do texto de entrada, incluindo espaços e sinais de "
                "pontuação.",
                "Uma unidade de texto do tokenizer do modelo, em geral uma palavra ou parte "
                "dela.",
                "Uma frase inteira do texto de entrada, até o próximo ponto final.",
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
                "It flattens the distribution so the model becomes more creative and varied "
                "in its wording.",
                "It concentrates probability on the top-ranked tokens, so output becomes "
                "more repeatable.",
                "It guarantees that the answer is factually correct, since the model stops "
                "guessing.",
                "It reduces the number of tokens that fit in the context window and "
                "shortens each reply.",
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
                "A distribuição fica mais plana e o modelo se torna mais criativo e variado "
                "na redação.",
                "A probabilidade se concentra nos tokens mais bem ranqueados, então a saída "
                "fica mais repetível.",
                "Garante que a resposta seja factualmente correta, já que o modelo deixa de "
                "chutar.",
                "Reduz o número de tokens que cabem na janela de contexto e encurta cada "
                "resposta.",
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
                "How many tokens the model saw during training, which determines how much it "
                "can remember at once.",
                "How many parameters the model has, which sets how large its memory is.",
                "How many requests per minute you may send before the API throttles you.",
                "The maximum number of tokens the model can handle in one request, input and "
                "output together.",
            ),
        ),
        _t(
            "O que a **janela de contexto** (context window) de um modelo limita?",
            "A janela de contexto é o número máximo de tokens que o modelo consegue processar "
            "em uma requisição, contando entrada e saída gerada em conjunto. A se refere ao "
            "tamanho dos dados de treinamento, B ao tamanho do modelo e C aos limites de taxa "
            "da API; nenhuma delas é a janela de contexto.",
            _options(
                "Quantos tokens o modelo viu durante o treinamento, o que determina quanto "
                "ele consegue lembrar de uma vez.",
                "Quantos parâmetros o modelo possui, o que define o tamanho da sua memória.",
                "Quantas requisições por minuto você pode enviar antes de a API limitar o "
                "seu acesso.",
                "O número máximo de tokens que o modelo consegue processar em uma "
                "requisição, entrada e saída juntas.",
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
                "A high temperature with top-p 1.0 so the model explores every phrasing and "
                "never repeats itself.",
                "A temperature well above 1 with a large top-k to avoid repetitive output "
                "across runs.",
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
                "Temperatura alta com top-p 1,0 para o modelo explorar todas as formulações "
                "e nunca se repetir.",
                "Temperatura bem acima de 1 com top-k grande para evitar saídas repetitivas "
                "entre execuções.",
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
                "Embedding models match on shared letters, and both strings contain a "
                "similar mix of letters and spaces.",
                "Embeddings store the exact words, and a synonym dictionary links them at "
                "query time, as in lexical search.",
                "Short texts always map to the same region of the vector space.",
                "The model learns to place texts with similar meaning near each other, so "
                "distance reflects semantics.",
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
                "Modelos de embedding casam por letras em comum, e as duas frases têm uma "
                "mistura parecida de letras e espaços.",
                "Embeddings guardam as palavras exatas, e um dicionário de sinônimos as liga "
                "no momento da consulta, como em uma busca lexical.",
                "Textos curtos sempre caem na mesma região do espaço vetorial.",
                "O modelo aprende a posicionar textos de significado parecido perto uns dos "
                "outros, então a distância reflete semântica.",
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

_FIT_CODE = """```python
def fit(history, budget, count):
    kept = []
    used = 0
    for msg in reversed(history):
        cost = count(msg)
        if used + cost > budget:
            break
        kept.append(msg)
        used += cost
    return list(reversed(kept))

print(fit(["aa", "bbbb", "cc", "dd"], 6, len))
```"""

# ----------------------------------------------------------------------
# context-engineering
# ----------------------------------------------------------------------
_CTX = "context-engineering"

CONTEXT_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "context-engineering-q01",
        _CTX,
        MC,
        EASY,
        ("c",),
        ("definition",),
        _t(
            "Which best describes **context engineering**?",
            "Context engineering is deciding, for each model call, what information goes into "
            "the context (instructions, history, retrieved documents, tool results) and in "
            "what form. A covers only prompt wording, which is one part of it. B is about "
            "picking a model, not managing what it sees. D (fine-tuning) changes the model, "
            "not its inputs.",
            _options(
                "Writing the cleverest possible wording for a single prompt and polishing "
                "it until it works.",
                "Choosing the model with the largest context window and sending it as much "
                "text as it accepts.",
                "Deciding, for each model call, what information enters the context and in "
                "what form.",
                "Fine-tuning the model on the application's data so that it no longer needs "
                "instructions or retrieved documents.",
            ),
        ),
        _t(
            "Qual alternativa descreve melhor **context engineering**?",
            "Context engineering é decidir, a cada chamada ao modelo, quais informações entram "
            "no contexto (instruções, histórico, documentos recuperados, resultados de "
            "ferramentas) e em que forma. A cobre só a redação do prompt, que é apenas uma "
            "parte. B trata da escolha do modelo, não de gerenciar o que ele vê. D (fine-tuning) "
            "altera o modelo, não suas entradas.",
            _options(
                "Escrever a redação mais engenhosa possível para um único prompt e lapidá-la "
                "até funcionar.",
                "Escolher o modelo com a maior janela de contexto e enviar a ele todo o "
                "texto que ele aceitar.",
                "Decidir, a cada chamada ao modelo, quais informações entram no contexto e "
                "em que forma.",
                "Fazer fine-tuning do modelo com os dados da aplicação para que ele não "
                "precise mais de instruções nem de documentos recuperados.",
            ),
        ),
    ),
    _q(
        "context-engineering-q02",
        _CTX,
        MC,
        EASY,
        ("b",),
        ("cost", "context-pollution"),
        _t(
            "Why not simply fill the context window with everything that might be relevant?",
            "More input tokens mean more cost and latency, and irrelevant material can "
            "actively degrade answer quality even when it fits. A is false: models can use "
            "far more than the first thousand tokens. C and D invent restrictions that do not "
            "exist.",
            _options(
                "The model ignores everything after the first thousand tokens, however "
                "large the window is.",
                "More input raises cost and latency, and irrelevant material can degrade the "
                "answer.",
                "Users are not allowed to fill the context window beyond a fixed share of "
                "its size.",
                "Longer prompts disable sampling parameters such as temperature and top-p.",
            ),
        ),
        _t(
            "Por que não simplesmente encher a janela de contexto com tudo o que pode ser "
            "relevante?",
            "Mais tokens de entrada significam mais custo e latência, e material irrelevante "
            "pode piorar ativamente a qualidade da resposta mesmo quando cabe na janela. A é "
            "falsa: modelos usam muito mais do que os primeiros mil tokens. C e D inventam "
            "restrições que não existem.",
            _options(
                "O modelo ignora tudo depois dos primeiros mil tokens, por maior que seja a "
                "janela.",
                "Mais entrada aumenta custo e latência, e material irrelevante pode piorar a "
                "resposta.",
                "Usuários não têm permissão para encher a janela de contexto além de uma "
                "fração fixa do seu tamanho.",
                "Prompts mais longos desativam parâmetros de amostragem como temperatura e "
                "top-p.",
            ),
        ),
    ),
    _q(
        "context-engineering-q03",
        _CTX,
        MC,
        EASY,
        ("d",),
        ("prioritization", "on-demand-retrieval"),
        _t(
            "Which of these is the best candidate to fetch **on demand** instead of keeping in "
            "every request?",
            "A large reference manual that is only occasionally needed should be retrieved "
            "when a step requires it. The user's current question, the output-format rules and "
            "the safety/policy rules are small and needed on every call, so they belong "
            "permanently in context.",
            _options(
                "The user's current question, which the model needs to answer on this call.",
                "The output-format instructions that every response has to follow.",
                "The safety and policy rules the assistant must always follow, in every "
                "single response.",
                "A 500-page reference manual that is consulted only occasionally.",
            ),
        ),
        _t(
            "Qual destes é o melhor candidato a ser buscado **sob demanda** em vez de ficar em "
            "toda requisição?",
            "Um manual de referência grande, que só é necessário de vez em quando, deve ser "
            "recuperado quando uma etapa o exigir. A pergunta atual do usuário, as regras de "
            "formato de saída e as regras de segurança/política são pequenas e necessárias em "
            "toda chamada, então ficam permanentemente no contexto.",
            _options(
                "A pergunta atual do usuário, de que o modelo precisa para responder nesta "
                "chamada.",
                "As instruções de formato de saída que toda resposta precisa seguir.",
                "As regras de segurança e política que o assistente deve sempre seguir, em "
                "toda e qualquer resposta.",
                "Um manual de referência de 500 páginas, consultado apenas ocasionalmente.",
            ),
        ),
    ),
    _q(
        "context-engineering-q04",
        _CTX,
        MC,
        MEDIUM,
        ("a",),
        ("context-pollution", "rag"),
        _t(
            "A team raises the number of retrieved chunks from 5 to 50 'to be safe'. Everything "
            "still fits in the window, but answer quality drops. What is the most likely cause?",
            "Extra, mostly irrelevant chunks add noise that distracts the model and dilutes "
            "the passages that matter (context pollution). B contradicts the premise, since "
            "everything fits. C is backwards: a larger k usually lowers precision. D is "
            "nonsense: embeddings of stored chunks do not depend on how many are retrieved.",
            _options(
                "The extra, mostly irrelevant chunks add noise that distracts the model and "
                "dilutes the relevant passages.",
                "The model forgets chunks because the context window has been exceeded.",
                "Retrieval becomes more precise as the number of chunks grows.",
                "The embeddings of stored chunks change when more of them are retrieved.",
            ),
        ),
        _t(
            "Uma equipe aumenta o número de chunks recuperados de 5 para 50 'por segurança'. "
            "Tudo ainda cabe na janela, mas a qualidade das respostas cai. Qual é a causa mais "
            "provável?",
            "Chunks extras, em sua maioria irrelevantes, adicionam ruído que distrai o modelo e "
            "dilui as passagens que importam (context pollution). B contradiz a premissa, pois "
            "tudo cabe. C é o contrário: um k maior normalmente reduz a precisão. D não faz "
            "sentido: os embeddings dos chunks armazenados não dependem de quantos são "
            "recuperados.",
            _options(
                "Os chunks extras, em sua maioria irrelevantes, adicionam ruído que distrai o "
                "modelo e dilui as passagens relevantes.",
                "O modelo esquece chunks porque a janela de contexto foi excedida.",
                "A recuperação fica mais precisa conforme o número de chunks cresce.",
                "Os embeddings dos chunks armazenados mudam quando mais deles são recuperados.",
            ),
        ),
    ),
    _q(
        "context-engineering-q05",
        _CTX,
        CODE,
        MEDIUM,
        ("c",),
        ("context-budget", "history-trimming"),
        _t(
            "What does this code print?\n\n" + _FIT_CODE,
            "It walks the history from newest to oldest and stops at the first message that "
            "does not fit. `dd` (2) and `cc` (2) fit within 6; `bbbb` would bring the total to "
            "8, so the loop breaks, and the older `aa` is dropped too even though it alone "
            "would have fit. D is what you would get with `continue` instead of `break`. "
            "A and B ignore the budget check.",
            _options(
                "`['aa', 'bbbb', 'cc', 'dd']`",
                "`['bbbb', 'cc', 'dd']`",
                "`['cc', 'dd']`",
                "`['aa', 'cc', 'dd']`",
            ),
        ),
        _t(
            "O que este código imprime?\n\n" + _FIT_CODE,
            "Ele percorre o histórico do mais novo para o mais antigo e para na primeira "
            "mensagem que não cabe. `dd` (2) e `cc` (2) cabem em 6; `bbbb` levaria o total a 8, "
            "então o laço é interrompido, e o `aa`, mais antigo, também é descartado mesmo que "
            "sozinho coubesse. D seria o resultado com `continue` no lugar de `break`. A e B "
            "ignoram a verificação do orçamento.",
            _options(
                "`['aa', 'bbbb', 'cc', 'dd']`",
                "`['bbbb', 'cc', 'dd']`",
                "`['cc', 'dd']`",
                "`['aa', 'cc', 'dd']`",
            ),
        ),
    ),
    _q(
        "context-engineering-q06",
        _CTX,
        MS,
        MEDIUM,
        ("a", "b", "e"),
        ("compression", "tool-outputs"),
        _t(
            "Which techniques reduce context size **without** throwing away what the model "
            "needs? Select all that apply.",
            "A (summarizing older turns), B (trimming tool results to the relevant fields) and "
            "E (fetching documents through a tool when needed instead of preloading them) all "
            "shrink the context while keeping the essential information. C would remove the "
            "instructions the model must keep following, and D increases the context instead "
            "of shrinking it.",
            _options(
                "Summarize older conversation turns.",
                "Return only the relevant fields of a tool result instead of the full payload.",
                "Drop the system prompt after the first turn.",
                "Send the whole conversation twice so nothing is missed.",
                "Retrieve documents through a tool when needed instead of preloading them.",
            ),
        ),
        _t(
            "Quais técnicas reduzem o tamanho do contexto **sem** descartar o que o modelo "
            "precisa? Selecione todas que se aplicam.",
            "A (resumir turnos antigos), B (reduzir resultados de ferramentas aos campos "
            "relevantes) e E (buscar documentos por meio de uma ferramenta quando necessário, "
            "em vez de pré-carregá-los) encolhem o contexto mantendo a informação essencial. C "
            "removeria as instruções que o modelo precisa continuar seguindo, e D aumenta o "
            "contexto em vez de reduzi-lo.",
            _options(
                "Resumir turnos antigos da conversa.",
                "Devolver apenas os campos relevantes de um resultado de ferramenta, em vez do "
                "payload completo.",
                "Descartar o system prompt depois do primeiro turno.",
                "Enviar a conversa inteira duas vezes para não perder nada.",
                "Recuperar documentos por meio de uma ferramenta quando necessário, em vez de "
                "pré-carregá-los.",
            ),
        ),
    ),
    _q(
        "context-engineering-q07",
        _CTX,
        MC,
        MEDIUM,
        ("d",),
        ("cost", "conversation-history"),
        _t(
            "A chatbot resends the full conversation history on every turn. Ignoring any "
            "caching, how does the total number of input tokens processed over a conversation "
            "of N turns grow?",
            "Turn k sends roughly k messages, so the total is about 1 + 2 + ... + N, which "
            "grows roughly quadratically with N. That is why long conversations need trimming "
            "or summarization. A, B and C all understate the growth, because each turn "
            "re-reads everything that came before it.",
            _options(
                "It stays constant, because only the newest message counts.",
                "It grows linearly, because each turn adds the same fixed cost.",
                "It grows logarithmically, because older turns are compressed automatically.",
                "It grows roughly quadratically, because each turn re-reads all previous turns.",
            ),
        ),
        _t(
            "Um chatbot reenvia o histórico completo da conversa a cada turno. Ignorando "
            "qualquer cache, como cresce o total de tokens de entrada processados em uma "
            "conversa de N turnos?",
            "O turno k envia cerca de k mensagens, então o total é aproximadamente "
            "1 + 2 + ... + N, que cresce de forma aproximadamente quadrática em N. Por isso "
            "conversas longas exigem corte ou sumarização. A, B e C subestimam o crescimento, "
            "pois cada turno relê tudo o que veio antes.",
            _options(
                "Permanece constante, pois só a mensagem mais recente conta.",
                "Cresce linearmente, pois cada turno acrescenta o mesmo custo fixo.",
                "Cresce logaritmicamente, pois os turnos antigos são comprimidos automaticamente.",
                "Cresce de forma aproximadamente quadrática, pois cada turno relê todos os "
                "turnos anteriores.",
            ),
        ),
    ),
    _q(
        "context-engineering-q08",
        _CTX,
        MC,
        MEDIUM,
        ("a",),
        ("summarization", "state"),
        _t(
            "A rolling summary of a long support conversation keeps losing the customer's order "
            "number and an explicit constraint they stated. What is the best fix?",
            "Summaries are lossy by nature, so exact facts that must survive (identifiers, "
            "hard constraints) should be kept verbatim in a structured note carried alongside "
            "the summary. B makes the loss worse. C is irrelevant: temperature does not decide "
            "what a summary keeps. D throws away far more than it saves.",
            _options(
                "Keep exact critical facts (IDs, constraints) verbatim in a structured note "
                "next to the summary.",
                "Summarize more aggressively, compressing the whole history into a single "
                "sentence so less can go missing.",
                "Raise the temperature when generating the summary so it explores more "
                "details.",
                "Drop the summary and keep only the last user message plus the system prompt.",
            ),
        ),
        _t(
            "Um resumo contínuo (rolling summary) de uma longa conversa de suporte perde o "
            "tempo todo o número do pedido do cliente e uma restrição explícita que ele "
            "informou. Qual é a melhor correção?",
            "Resumos são com perda por natureza, então fatos exatos que precisam sobreviver "
            "(identificadores, restrições rígidas) devem ser mantidos literalmente em uma nota "
            "estruturada, ao lado do resumo. B piora a perda. C é irrelevante: a temperatura "
            "não define o que um resumo preserva. D descarta muito mais do que economiza.",
            _options(
                "Manter os fatos críticos exatos (IDs, restrições) literalmente em uma nota "
                "estruturada ao lado do resumo.",
                "Resumir de forma mais agressiva, comprimindo todo o histórico em uma só "
                "frase para haver menos a perder.",
                "Aumentar a temperatura ao gerar o resumo para que ele explore mais "
                "detalhes.",
                "Descartar o resumo e manter apenas a última mensagem do usuário e o system "
                "prompt.",
            ),
        ),
    ),
    _q(
        "context-engineering-q09",
        _CTX,
        MC,
        HARD,
        ("b",),
        ("lost-in-the-middle", "ordering"),
        _t(
            "You are assembling a very long prompt that contains one critical instruction. "
            "Where should that instruction go?",
            "Models tend to use information in the middle of a very long context less reliably "
            "than information at the beginning or end (the 'lost in the middle' effect), so "
            "critical instructions belong at the start and, if needed, are restated near the "
            "end. A is the weakest position. C is wrong: position matters. D confuses format "
            "with placement: markup does not fix a position problem.",
            _options(
                "In the exact middle, because that is the most protected position.",
                "At the beginning, and restated near the end if the prompt is very long.",
                "Anywhere; position never affects how well the model follows it.",
                "Inside a deeply nested markup block, which makes the model prioritize it.",
            ),
        ),
        _t(
            "Você está montando um prompt muito longo que contém uma instrução crítica. Onde "
            "ela deve ficar?",
            "Modelos tendem a usar informações no meio de um contexto muito longo com menos "
            "confiabilidade do que as do início ou do fim (o efeito 'lost in the middle'), "
            "então instruções críticas ficam no início e, se necessário, são repetidas perto "
            "do fim. A é a pior posição. C está errada: a posição importa. D confunde formato "
            "com posicionamento: marcação não resolve um problema de posição.",
            _options(
                "Exatamente no meio, pois é a posição mais protegida.",
                "No início, e repetida perto do fim se o prompt for muito longo.",
                "Em qualquer lugar; a posição nunca afeta o quanto o modelo a segue.",
                "Dentro de um bloco de marcação bem aninhado, o que faz o modelo priorizá-la.",
            ),
        ),
    ),
    _q(
        "context-engineering-q10",
        _CTX,
        SHORT,
        HARD,
        None,
        ("context-budget", "agents"),
        _t(
            "A coding agent works on a large codebase with a limited context window. Describe a "
            "policy for what stays in context, what is retrieved on demand, and what is "
            "summarized or dropped.",
            "Self-check: did you cover (1) a fixed core that always stays (instructions, task, "
            "tool definitions), (2) on-demand retrieval of files instead of preloading, "
            "(3) summarizing or trimming old history and tool output, and (4) a reserved "
            "budget for the model's output?",
            model_answer="Keep a small fixed core in every call: the system instructions, the "
            "current task and the tool definitions. Do not preload the codebase; give the agent "
            "search and read tools so it pulls in only the files or snippets a step needs, and "
            "trim large tool outputs to the relevant lines. Summarize older history into a "
            "compact state note (decisions made, files touched, open questions) while keeping "
            "exact identifiers and constraints verbatim, and drop stale material such as files "
            "no longer relevant. Reserve part of the window for the model's output and monitor "
            "token usage so compaction happens before the limit is hit.",
        ),
        _t(
            "Um agente de programação trabalha em uma base de código grande com uma janela de "
            "contexto limitada. Descreva uma política para o que fica no contexto, o que é "
            "recuperado sob demanda e o que é resumido ou descartado.",
            "Autoavaliação: você cobriu (1) um núcleo fixo que sempre permanece (instruções, "
            "tarefa, definições de ferramentas), (2) recuperação de arquivos sob demanda em vez "
            "de pré-carregar, (3) resumo ou corte de histórico antigo e de saídas de "
            "ferramentas, e (4) um orçamento reservado para a saída do modelo?",
            model_answer="Manter um núcleo fixo e pequeno em toda chamada: as instruções do "
            "sistema, a tarefa atual e as definições das ferramentas. Não pré-carregar a base de "
            "código; dar ao agente ferramentas de busca e leitura para trazer apenas os "
            "arquivos ou trechos de que cada etapa precisa, e reduzir saídas grandes de "
            "ferramentas às linhas relevantes. Resumir o histórico antigo em uma nota de estado "
            "compacta (decisões tomadas, arquivos alterados, dúvidas em aberto), mantendo "
            "identificadores e restrições exatos de forma literal, e descartar material obsoleto, "
            "como arquivos que deixaram de ser relevantes. Reservar parte da janela para a "
            "saída do modelo e monitorar o uso de tokens, para que a compactação ocorra antes de "
            "o limite ser atingido.",
        ),
    ),
)

_CHUNK_CODE = """```python
def chunk(words, size, overlap):
    step = size - overlap
    return [words[i:i + size] for i in range(0, len(words), step)]

pieces = chunk(list(range(10)), 4, 1)
print(len(pieces), pieces[-1])
```"""

# ----------------------------------------------------------------------
# rag-architecture
# ----------------------------------------------------------------------
_RAG = "rag-architecture"

RAG_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "rag-architecture-q01",
        _RAG,
        MC,
        EASY,
        ("b",),
        ("rag", "motivation"),
        _t(
            "What core problem does retrieval-augmented generation (RAG) address?",
            "RAG fetches relevant documents at query time and puts them in the prompt, so the "
            "model can answer from current or private knowledge without being retrained. A is "
            "unrelated to RAG. C is backwards: retrieved text consumes context window. D "
            "overstates it: grounding reduces hallucination but does not guarantee its absence.",
            _options(
                "It makes the model train faster by shrinking the training set it needs to "
                "see.",
                "It lets the model answer from current or private knowledge supplied at "
                "query time.",
                "It removes the context window limit by moving the prompt into an external "
                "index.",
                "It guarantees that the model never hallucinates, because every answer is "
                "checked against sources.",
            ),
        ),
        _t(
            "Que problema central a geração aumentada por recuperação (RAG) resolve?",
            "O RAG busca documentos relevantes no momento da consulta e os coloca no prompt, "
            "de modo que o modelo responda com conhecimento atual ou privado sem ser "
            "retreinado. A não tem relação com RAG. C é o oposto: o texto recuperado consome "
            "janela de contexto. D exagera: o grounding reduz a alucinação, mas não garante "
            "sua ausência.",
            _options(
                "Faz o modelo treinar mais rápido ao reduzir o conjunto de treino que ele "
                "precisa ver.",
                "Permite que o modelo responda com conhecimento atual ou privado fornecido "
                "na consulta.",
                "Remove o limite da janela de contexto ao mover o prompt para um índice "
                "externo.",
                "Garante que o modelo nunca alucine, pois toda resposta é conferida contra "
                "as fontes recuperadas.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q02",
        _RAG,
        MC,
        EASY,
        ("d",),
        ("ingestion", "pipeline"),
        _t(
            "Which sequence describes the ingestion side of a typical RAG pipeline?",
            "Documents are first loaded and parsed into text, then split into chunks, each "
            "chunk is embedded, and the vectors are stored together with metadata. The other "
            "orders are impossible: you cannot embed before you have chunks, nor chunk text "
            "that has not been parsed yet.",
            _options(
                "Embed each document, then chunk the embeddings, then parse them into text, "
                "then store the results.",
                "Store the raw files, then chunk them, then embed each chunk, then finally "
                "parse the vectors into text.",
                "Chunk the raw files, then store the chunks, then parse them into text, then "
                "embed each chunk.",
                "Load and parse documents, split into chunks, embed each chunk, store the "
                "vectors with metadata.",
            ),
        ),
        _t(
            "Qual sequência descreve a etapa de ingestão de um pipeline RAG típico?",
            "Os documentos são primeiro carregados e convertidos em texto, depois divididos em "
            "chunks, cada chunk recebe um embedding e os vetores são armazenados junto com "
            "metadados. As outras ordens são impossíveis: não dá para gerar embeddings antes de "
            "ter chunks, nem dividir um texto que ainda não foi extraído.",
            _options(
                "Gerar o embedding de cada documento, dividir os embeddings em chunks, "
                "extrair o texto deles e por fim armazenar o resultado.",
                "Armazenar os arquivos brutos, dividi-los em chunks, gerar o embedding de "
                "cada chunk e só então extrair o texto dos vetores.",
                "Dividir os arquivos brutos em chunks, armazenar os chunks, extrair o texto "
                "deles e depois gerar o embedding de cada chunk.",
                "Carregar e extrair o texto dos documentos, dividir em chunks, gerar o "
                "embedding de cada chunk e armazenar os vetores com metadados.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q03",
        _RAG,
        MC,
        EASY,
        ("a",),
        ("sparse-retrieval", "bm25"),
        _t(
            "Users often search a support knowledge base for exact error codes such as "
            "`ERR_4021`. Which retrieval approach is most reliable for these queries?",
            "Keyword (sparse) retrieval such as BM25 matches exact terms, so it finds the "
            "literal code. Dense retrieval encodes meaning and can miss rare identifiers that "
            "have no semantic content, which is why hybrid retrieval combines both. C and D "
            "do not retrieve anything on their own.",
            _options(
                "Keyword (sparse) retrieval such as BM25, which matches exact terms.",
                "Dense retrieval only, because embeddings always capture exact strings.",
                "Raising the temperature of the generation model.",
                "Increasing the context window of the generation model.",
            ),
        ),
        _t(
            "Usuários costumam buscar em uma base de conhecimento de suporte por códigos de "
            "erro exatos, como `ERR_4021`. Qual abordagem de recuperação é a mais confiável "
            "para essas consultas?",
            "A recuperação por palavras-chave (esparsa), como o BM25, casa termos exatos e "
            "encontra o código literal. A recuperação densa codifica significado e pode "
            "perder identificadores raros sem conteúdo semântico, por isso a recuperação "
            "híbrida combina as duas. C e D não recuperam nada por si só.",
            _options(
                "Recuperação por palavras-chave (esparsa), como o BM25, que casa termos exatos.",
                "Somente recuperação densa, pois embeddings sempre capturam strings exatas.",
                "Aumentar a temperatura do modelo de geração.",
                "Aumentar a janela de contexto do modelo de geração.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q04",
        _RAG,
        CODE,
        MEDIUM,
        ("c",),
        ("chunking", "overlap"),
        _t(
            "What does this code print?\n\n" + _CHUNK_CODE,
            "The window starts at 0, 3, 6 and 9 (step = 4 - 1 = 3), giving four chunks. The "
            "last window contains only `[9]`, which is already inside the overlap of the "
            "previous chunk, a common redundancy in naive sliding-window chunkers. A and B get "
            "the chunk count or sizes wrong, and D would require a step of 2.",
            _options(
                "`3 [6, 7, 8, 9]`",
                "`4 [6, 7, 8, 9]`",
                "`4 [9]`",
                "`5 [8, 9]`",
            ),
        ),
        _t(
            "O que este código imprime?\n\n" + _CHUNK_CODE,
            "A janela começa em 0, 3, 6 e 9 (passo = 4 - 1 = 3), gerando quatro chunks. A "
            "última janela contém apenas `[9]`, que já está na sobreposição do chunk anterior, "
            "uma redundância comum em chunkers ingênuos de janela deslizante. A e B erram a "
            "quantidade ou o tamanho dos chunks, e D exigiria um passo de 2.",
            _options(
                "`3 [6, 7, 8, 9]`",
                "`4 [6, 7, 8, 9]`",
                "`4 [9]`",
                "`5 [8, 9]`",
            ),
        ),
    ),
    _q(
        "rag-architecture-q05",
        _RAG,
        MC,
        MEDIUM,
        ("b",),
        ("chunking", "tradeoffs"),
        _t(
            "Evaluating a RAG system, you see that the retrieved chunks are on-topic, but the "
            "answers keep missing details that sit just before or after the retrieved text. "
            "What is the most likely problem and fix?",
            "Chunks that are too small cut related information apart, so each hit is on-topic "
            "but incomplete. Larger chunks, more overlap, or expanding hits with neighboring "
            "(parent) text address this. A describes the opposite problem: oversized chunks "
            "produce diluted embeddings and waste context, not missing neighbors. C and D do "
            "not affect which text is retrieved.",
            _options(
                "Chunks are too large and dilute each embedding; make them smaller so each "
                "one is more focused.",
                "Chunks are too small and split related information; use larger chunks or "
                "more overlap.",
                "The embedding vectors have too many dimensions; reduce them to speed up the "
                "search.",
                "The generation temperature is too low; raise it so the answer includes more "
                "details.",
            ),
        ),
        _t(
            "Ao avaliar um sistema RAG, você nota que os chunks recuperados são do assunto "
            "certo, mas as respostas perdem detalhes que estão logo antes ou depois do texto "
            "recuperado. Qual é o problema mais provável e a correção?",
            "Chunks pequenos demais separam informações relacionadas, então cada resultado é "
            "do assunto certo, porém incompleto. Chunks maiores, mais sobreposição ou "
            "expandir os resultados com o texto vizinho (parent) resolvem. A descreve o "
            "problema oposto: chunks grandes demais geram embeddings diluídos e desperdiçam "
            "contexto, não perdem vizinhos. C e D não afetam qual texto é recuperado.",
            _options(
                "Os chunks são grandes demais e diluem cada embedding; torná-los menores "
                "para ficarem mais focados.",
                "Os chunks são pequenos demais e separam informações relacionadas; usar "
                "chunks maiores ou mais sobreposição.",
                "Os vetores de embedding têm dimensões demais; reduzi-las para acelerar a "
                "busca.",
                "A temperatura de geração está baixa demais; aumentá-la para a resposta "
                "trazer mais detalhes.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q06",
        _RAG,
        MC,
        MEDIUM,
        ("a",),
        ("reranking", "cross-encoder"),
        _t(
            "Why is a cross-encoder reranker typically applied only to a shortlist of "
            "candidates instead of the whole corpus?",
            "A cross-encoder scores the query together with each candidate chunk, which is "
            "more precise but far too expensive to run over every chunk on every query, so a "
            "fast first stage retrieves a shortlist and the reranker reorders it. B is false: "
            "joint scoring is usually more accurate than comparing precomputed vectors. C and "
            "D invent restrictions.",
            _options(
                "Scoring each chunk jointly with the query is too costly per request, so it "
                "runs on a shortlist.",
                "Cross-encoders are less accurate than comparing precomputed vectors, which "
                "is why they are used last.",
                "Cross-encoders only work on keyword indexes, so they cannot rerank vector "
                "search results.",
                "Vector databases forbid reranking, so it has to happen outside the index.",
            ),
        ),
        _t(
            "Por que um reranker do tipo cross-encoder costuma ser aplicado apenas a uma lista "
            "curta de candidatos, e não ao corpus inteiro?",
            "Um cross-encoder avalia a consulta junto com cada chunk candidato, o que é mais "
            "preciso, porém caro demais para rodar em todos os chunks a cada consulta; então "
            "uma primeira etapa rápida recupera uma lista curta e o reranker a reordena. B é "
            "falsa: a avaliação conjunta costuma ser mais precisa do que comparar vetores "
            "pré-calculados. C e D inventam restrições.",
            _options(
                "Avaliar cada chunk em conjunto com a consulta é caro demais por requisição, "
                "então ele roda só em uma lista curta.",
                "Cross-encoders são menos precisos do que comparar vetores pré-calculados, e "
                "por isso são usados por último.",
                "Cross-encoders só funcionam em índices de palavras-chave, então não "
                "reordenam resultados de busca vetorial.",
                "Bancos de dados vetoriais proíbem reranking, então ele precisa ocorrer fora "
                "do índice.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q07",
        _RAG,
        MS,
        MEDIUM,
        ("a", "b", "c"),
        ("metadata-filtering", "retrieval"),
        _t(
            "Which are legitimate benefits of **metadata filtering** in retrieval? Select all "
            "that apply.",
            "Filtering can restrict results to what a tenant or user may see (enforced in the "
            "retrieval query, not left to the model), restrict to the right version, date or "
            "product, and shrink the candidate set so fewer irrelevant hits compete. D is "
            "false: filters do not replace chunking. E is false: nothing about filtering "
            "guarantees the generated answer is grounded.",
            _options(
                "Restricting results to documents the current user or tenant is allowed to see.",
                "Restricting results to the right product, version or date range.",
                "Reducing the number of irrelevant candidates, which improves precision.",
                "Removing the need to chunk documents.",
                "Guaranteeing that the generated answer is grounded in the context.",
            ),
        ),
        _t(
            "Quais são benefícios legítimos da **filtragem por metadados** na recuperação? "
            "Selecione todos que se aplicam.",
            "A filtragem pode restringir os resultados ao que um tenant ou usuário pode ver "
            "(aplicada na própria consulta de recuperação, e não deixada a cargo do modelo), "
            "restringir à versão, data ou produto corretos e reduzir o conjunto de candidatos, "
            "de modo que menos resultados irrelevantes concorram. D é falsa: filtros não "
            "substituem o chunking. E é falsa: nada na filtragem garante que a resposta "
            "gerada esteja ancorada.",
            _options(
                "Restringir os resultados aos documentos que o usuário ou tenant atual pode ver.",
                "Restringir os resultados ao produto, versão ou intervalo de datas corretos.",
                "Reduzir o número de candidatos irrelevantes, o que melhora a precisão.",
                "Eliminar a necessidade de dividir os documentos em chunks.",
                "Garantir que a resposta gerada esteja ancorada no contexto.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q08",
        _RAG,
        MC,
        MEDIUM,
        ("c",),
        ("embeddings", "migration"),
        _t(
            "A team wants to switch to a different embedding model for their RAG index. What "
            "must they do?",
            "Vectors from different embedding models live in different, incompatible spaces, "
            "so the whole corpus must be re-embedded with the new model and queries must use "
            "the same model. A is wrong: old and new vectors cannot be compared. B is wrong: "
            "there is no shared space across models. D fails because stored vectors would "
            "still be in the old space.",
            _options(
                "Embed only new documents; old vectors stay comparable with the new ones.",
                "Nothing, because all embedding models share the same vector space.",
                "Re-embed the entire corpus with the new model and embed queries with it too.",
                "Re-embed only the queries; stored vectors can stay as they are.",
            ),
        ),
        _t(
            "Uma equipe quer trocar o modelo de embedding do índice do seu RAG. O que ela "
            "precisa fazer?",
            "Vetores de modelos de embedding diferentes vivem em espaços distintos e "
            "incompatíveis, então todo o corpus precisa ser reindexado com o novo modelo, e as "
            "consultas devem usar o mesmo modelo. A está errada: vetores antigos e novos não "
            "podem ser comparados. B está errada: não existe um espaço compartilhado entre "
            "modelos. D falha porque os vetores armazenados continuariam no espaço antigo.",
            _options(
                "Gerar embeddings só dos documentos novos; os vetores antigos continuam "
                "comparáveis com os novos.",
                "Nada, pois todos os modelos de embedding compartilham o mesmo espaço vetorial.",
                "Refazer o embedding de todo o corpus com o novo modelo e usá-lo também nas "
                "consultas.",
                "Refazer só o embedding das consultas; os vetores armazenados podem ficar como "
                "estão.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q09",
        _RAG,
        MC,
        HARD,
        ("d",),
        ("failure-analysis", "retrieval-recall"),
        _t(
            "A RAG system gives a confidently wrong answer. The logs show that the passage "
            "with the correct answer exists in the index but was **not** among the chunks "
            "sent to the model. Which change addresses the root cause?",
            "The failure is in retrieval recall: the right passage never reached the model. "
            "Improving retrieval (hybrid search, better chunking, a wider candidate pool "
            "followed by a reranker) and then re-measuring recall fixes it. A and C change "
            "generation, and a larger model cannot use text it never received. B can make the "
            "system abstain more gracefully, but the question is still unanswerable because "
            "the evidence is missing.",
            _options(
                "Lower the generation temperature to 0 so the model sticks to the most "
                "likely answer.",
                "Add an instruction telling the model to say 'I don't know' whenever it is "
                "unsure about the evidence it was given.",
                "Switch to a larger generation model with a stronger grasp of the subject.",
                "Improve retrieval (hybrid search, better chunking, a reranker) and "
                "re-measure recall.",
            ),
        ),
        _t(
            "Um sistema RAG dá uma resposta errada com muita confiança. Os logs mostram que a "
            "passagem com a resposta correta existe no índice, mas **não** estava entre os "
            "chunks enviados ao modelo. Qual mudança ataca a causa raiz?",
            "A falha está no recall da recuperação: a passagem certa nunca chegou ao modelo. "
            "Melhorar a recuperação (busca híbrida, chunking melhor, um conjunto maior de "
            "candidatos seguido de um reranker) e medir o recall novamente resolve. A e C "
            "mudam a geração, e um modelo maior não consegue usar um texto que nunca recebeu. "
            "B pode fazer o sistema se abster com mais elegância, mas a pergunta continua sem "
            "resposta porque falta a evidência.",
            _options(
                "Reduzir a temperatura de geração para 0, para o modelo se ater à resposta "
                "mais provável.",
                "Adicionar uma instrução mandando o modelo dizer 'não sei' sempre que estiver "
                "em dúvida sobre a evidência recebida.",
                "Trocar por um modelo de geração maior, com domínio mais forte do assunto.",
                "Melhorar a recuperação (busca híbrida, chunking melhor, um reranker) e "
                "medir o recall novamente.",
            ),
        ),
    ),
    _q(
        "rag-architecture-q10",
        _RAG,
        SHORT,
        HARD,
        None,
        ("design", "groundedness"),
        _t(
            "Outline a RAG pipeline for a 10,000-page documentation set: chunking, metadata, "
            "retrieval, and how you would evaluate groundedness.",
            "Self-check: did you cover (1) structure-aware chunking with some overlap, (2) "
            "useful metadata, (3) hybrid retrieval plus reranking, and (4) evaluating both "
            "retrieval and whether answers are supported by the retrieved text?",
            model_answer="Parse the docs and chunk along their structure (headings, sections, "
            "code blocks) with moderate size and some overlap, keeping each chunk's title "
            "path, product, version and date as metadata. Embed the chunks and also keep a "
            "keyword index, then use hybrid retrieval with metadata filters, retrieve a wide "
            "candidate set and rerank it down to a few chunks for the prompt. Instruct the "
            "model to answer only from the context and cite the chunks it used. Evaluate on a "
            "golden set of real questions: retrieval recall (was the right passage "
            "retrieved?), and groundedness (is every claim in the answer supported by the "
            "cited chunks, checked by humans or a validated judge), plus whether it abstains "
            "when the docs do not cover the question.",
        ),
        _t(
            "Descreva um pipeline RAG para um conjunto de documentação de 10.000 páginas: "
            "chunking, metadados, recuperação e como avaliar o groundedness.",
            "Autoavaliação: você cobriu (1) chunking que respeita a estrutura, com alguma "
            "sobreposição, (2) metadados úteis, (3) recuperação híbrida com reranking e (4) "
            "avaliação tanto da recuperação quanto de a resposta ser sustentada pelo texto "
            "recuperado?",
            model_answer="Extrair o texto e dividir em chunks seguindo a estrutura "
            "(títulos, seções, blocos de código), com tamanho moderado e alguma sobreposição, "
            "guardando como metadados o caminho de títulos, o produto, a versão e a data de "
            "cada chunk. Gerar os embeddings e manter também um índice de palavras-chave; usar "
            "recuperação híbrida com filtros por metadados, buscar um conjunto amplo de "
            "candidatos e reranqueá-lo até poucos chunks para o prompt. Instruir o modelo a "
            "responder apenas com base no contexto e a citar os chunks usados. Avaliar com um "
            "conjunto golden de perguntas reais: recall da recuperação (a passagem certa foi "
            "recuperada?) e groundedness (cada afirmação da resposta é sustentada pelos chunks "
            "citados, verificada por humanos ou por um juiz validado), além de verificar se o "
            "sistema se abstém quando a documentação não cobre a pergunta.",
        ),
    ),
)

_AGENT_CODE = """```python
MAX_STEPS = 3

def run(llm, tools, task):
    messages = [{"role": "user", "content": task}]
    for _ in range(MAX_STEPS):
        reply = llm(messages)
        if reply["type"] == "final":
            return reply["text"]
        result = tools[reply["tool"]](**reply["args"])
        messages.append({"role": "tool", "content": result})
    return "stopped: step limit"

calls = []

def search(q):
    calls.append(q)
    return "no results"

def llm(messages):  # a stub model that never decides to finish
    return {"type": "tool", "tool": "search", "args": {"q": "weather"}}

print(run(llm, {"search": search}, "What is the weather?"), len(calls))
```"""

# ----------------------------------------------------------------------
# ai-agents-tool-use
# ----------------------------------------------------------------------
_AGENT = "ai-agents-tool-use"

AGENT_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "ai-agents-tool-use-q01",
        _AGENT,
        MC,
        EASY,
        ("c",),
        ("tool-calling", "mechanics"),
        _t(
            "Mechanically, how does tool calling work?",
            "The model only produces text: it emits a structured request naming a tool and "
            "its arguments. Your application executes the tool and sends the result back as "
            "new input for the model. A and B assume the model executes code or network calls "
            "itself, which it cannot. D is wrong: tools are defined at request time, not "
            "baked into the weights.",
            _options(
                "The model runs the function inside its own process and reports the return "
                "value.",
                "The model opens network connections to the tool's API directly, using "
                "credentials stored in its context window.",
                "The model emits a request (tool name and arguments); your application runs "
                "it and returns the result.",
                "Tools are compiled into the model's weights during training, so no "
                "definition is needed per request.",
            ),
        ),
        _t(
            "Do ponto de vista mecânico, como funciona o tool calling (chamada de ferramentas)?",
            "O modelo apenas produz texto: ele emite uma requisição estruturada com o nome da "
            "ferramenta e seus argumentos. Sua aplicação executa a ferramenta e devolve o "
            "resultado como nova entrada para o modelo. A e B supõem que o modelo executa "
            "código ou chamadas de rede por conta própria, o que ele não faz. D está errada: "
            "as ferramentas são definidas na requisição, não embutidas nos pesos.",
            _options(
                "O modelo executa a função dentro do próprio processo e informa o valor de "
                "retorno.",
                "O modelo abre conexões de rede diretamente com a API da ferramenta, usando "
                "credenciais guardadas em sua janela de contexto.",
                "O modelo emite uma requisição (nome da ferramenta e argumentos); sua "
                "aplicação a executa e devolve o resultado.",
                "As ferramentas são compiladas nos pesos do modelo durante o treinamento, sem "
                "precisar de definição a cada requisição.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q02",
        _AGENT,
        MC,
        EASY,
        ("b",),
        ("agent-loop", "definition"),
        _t(
            "What best distinguishes an **agent** from a single LLM call?",
            "An agent runs a loop in which the model chooses its next action (often a tool "
            "call) based on the results of earlier ones, until it decides it is done or a "
            "limit is reached. A confuses agents with prompt length, C with model size, and D "
            "describes a fixed workflow, where code rather than the model decides the steps.",
            _options(
                "It is any LLM call with a long prompt that packs in many instructions and "
                "examples.",
                "It loops: the model picks each next action from earlier results until it "
                "is done or hits a limit.",
                "It is a model with more parameters and a larger context window.",
                "It is a fixed pipeline where code decides every step in advance and calls "
                "the model only to fill in text.",
            ),
        ),
        _t(
            "O que melhor distingue um **agente** de uma única chamada a um LLM?",
            "Um agente executa um laço em que o modelo escolhe a próxima ação (geralmente uma "
            "chamada de ferramenta) com base nos resultados das anteriores, até decidir que "
            "terminou ou atingir um limite. A confunde agente com tamanho do prompt, C com "
            "tamanho do modelo, e D descreve um workflow fixo, em que o código, e não o "
            "modelo, decide as etapas.",
            _options(
                "É qualquer chamada a um LLM com um prompt longo, cheio de instruções e "
                "exemplos.",
                "Roda em laço: o modelo escolhe cada próxima ação pelos resultados "
                "anteriores até terminar ou bater num limite.",
                "É um modelo com mais parâmetros e uma janela de contexto maior.",
                "É um pipeline fixo em que o código decide cada etapa de antemão e só chama "
                "o modelo para preencher trechos de texto.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q03",
        _AGENT,
        MC,
        EASY,
        ("d",),
        ("tool-design", "descriptions"),
        _t(
            "Why do the name, description and parameter schema of a tool matter so much?",
            "The model chooses which tool to call, and with which arguments, mostly from those "
            "descriptions. Vague or overlapping ones lead to wrong or missed calls. A and B "
            "are wrong because the model is not given the tool's source code, and C is wrong "
            "because descriptions do not change the context window size.",
            _options(
                "The model reads the tool's source code to understand what it does before "
                "deciding to call it.",
                "They are only for human documentation and are ignored by the model.",
                "They enlarge the context window available to the model.",
                "The model decides which tool to call and how to fill the arguments from "
                "them.",
            ),
        ),
        _t(
            "Por que o nome, a descrição e o schema de parâmetros de uma ferramenta importam "
            "tanto?",
            "O modelo escolhe qual ferramenta chamar, e com quais argumentos, principalmente a "
            "partir dessas descrições. Descrições vagas ou sobrepostas levam a chamadas "
            "erradas ou omitidas. A e B estão erradas porque o modelo não recebe o código-fonte "
            "da ferramenta, e C está errada porque descrições não alteram o tamanho da janela "
            "de contexto.",
            _options(
                "O modelo lê o código-fonte da ferramenta para entender o que ela faz antes "
                "de decidir se a chama.",
                "Servem só como documentação para humanos e são ignorados pelo modelo.",
                "Ampliam a janela de contexto disponível para o modelo.",
                "O modelo decide qual ferramenta chamar e como preencher os argumentos "
                "sobretudo a partir delas.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q04",
        _AGENT,
        CODE,
        MEDIUM,
        ("b",),
        ("agent-loop", "stop-conditions"),
        _t(
            "What does this code print?\n\n" + _AGENT_CODE,
            "The stub model never returns a `final` reply, so each iteration calls the tool "
            "and the loop runs until `MAX_STEPS` (3) is exhausted. The function then returns "
            "the step-limit message and `calls` holds three entries. A and C assume the model "
            "stops early; D is wrong because the bounded `for` loop guarantees termination, "
            "which is exactly why agent loops need a step limit.",
            _options(
                "`What is the weather? 1`",
                "`stopped: step limit 3`",
                "`stopped: step limit 1`",
                "It never terminates.",
            ),
        ),
        _t(
            "O que este código imprime?\n\n" + _AGENT_CODE,
            "O modelo simulado nunca devolve uma resposta `final`, então cada iteração chama a "
            "ferramenta e o laço roda até esgotar `MAX_STEPS` (3). A função então retorna a "
            "mensagem de limite de passos e `calls` contém três entradas. A e C supõem que o "
            "modelo para antes; D está errada porque o laço `for` limitado garante a "
            "terminação, e é exatamente por isso que loops de agentes precisam de um limite "
            "de passos.",
            _options(
                "`What is the weather? 1`",
                "`stopped: step limit 3`",
                "`stopped: step limit 1`",
                "Nunca termina.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q05",
        _AGENT,
        MC,
        MEDIUM,
        ("c",),
        ("idempotency", "side-effects"),
        _t(
            "An agent calls a `create_invoice` tool; the call times out, the loop retries, and "
            "the customer ends up with two invoices. What is the most robust fix?",
            "Make the side-effecting tool idempotent, for example with an idempotency key so "
            "repeating the same request does not create a second invoice. Retries are normal "
            "in agent loops, so safety should not depend on the model's behavior. A hides the "
            "symptom, B relies on the model's judgment, and D is a prompt instruction, none of "
            "which gives a guarantee.",
            _options(
                "Increase the timeout so the call never fails.",
                "Rely on the model to check whether an invoice exists before each call.",
                "Make the tool idempotent, for example with an idempotency key, so repeated "
                "calls do not create duplicates.",
                "Tell the model in the prompt never to retry.",
            ),
        ),
        _t(
            "Um agente chama uma ferramenta `create_invoice`; a chamada expira por timeout, o "
            "laço tenta de novo e o cliente acaba com duas faturas. Qual é a correção mais "
            "robusta?",
            "Tornar a ferramenta com efeito colateral idempotente, por exemplo com uma "
            "idempotency key, de modo que repetir a mesma requisição não crie uma segunda "
            "fatura. Novas tentativas são normais em loops de agentes, então a segurança não "
            "deve depender do comportamento do modelo. A esconde o sintoma, B depende do "
            "julgamento do modelo e D é uma instrução no prompt; nenhuma dá garantia.",
            _options(
                "Aumentar o timeout para que a chamada nunca falhe.",
                "Confiar que o modelo verifique se a fatura existe antes de cada chamada.",
                "Tornar a ferramenta idempotente, por exemplo com uma idempotency key, para "
                "que chamadas repetidas não criem duplicatas.",
                "Dizer no prompt para o modelo nunca tentar de novo.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q06",
        _AGENT,
        MS,
        MEDIUM,
        ("a", "b", "c"),
        ("safety", "guardrails"),
        _t(
            "Which safeguards are appropriate for an agent that can call tools with side "
            "effects? Select all that apply.",
            "A step/time/cost limit prevents runaway loops, B (human confirmation for "
            "irreversible actions) keeps a person in control of risky steps, and C (least "
            "privilege) limits the damage a wrong call can do. D is unsafe: model-generated "
            "arguments must be validated like any untrusted input. E violates least "
            "privilege and widens the blast radius.",
            _options(
                "Limits on steps, time and cost for each run.",
                "Human confirmation before irreversible actions.",
                "Giving each agent only the tools and permissions its task needs.",
                "Trusting model-generated arguments without validation, since the model wrote "
                "them.",
                "Granting every tool to every agent in case it needs one.",
            ),
        ),
        _t(
            "Quais salvaguardas são apropriadas para um agente que pode chamar ferramentas com "
            "efeitos colaterais? Selecione todas que se aplicam.",
            "A (limites de passos, tempo e custo) evita loops descontrolados, B (confirmação "
            "humana para ações irreversíveis) mantém uma pessoa no controle dos passos "
            "arriscados, e C (menor privilégio) limita o dano de uma chamada errada. D é "
            "inseguro: argumentos gerados pelo modelo devem ser validados como qualquer "
            "entrada não confiável. E viola o menor privilégio e amplia o raio de dano.",
            _options(
                "Limites de passos, tempo e custo por execução.",
                "Confirmação humana antes de ações irreversíveis.",
                "Dar a cada agente apenas as ferramentas e permissões de que a tarefa precisa.",
                "Confiar nos argumentos gerados pelo modelo sem validação, já que foi o "
                "modelo que os escreveu.",
                "Conceder todas as ferramentas a todos os agentes, caso algum precise.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q07",
        _AGENT,
        MC,
        MEDIUM,
        ("a",),
        ("error-handling", "observations"),
        _t(
            "A tool call fails because the model passed an invalid argument. What is the best "
            "way to handle it in the loop?",
            "Return a clear error message as the tool result so the model can correct its "
            "arguments or choose another approach, and cap the number of retries. B gives "
            "the model no chance to recover. C leads it to assume success and build on a "
            "false premise. D invents data, which is worse than failing.",
            _options(
                "Return a clear error as the tool result so the model can adjust, with a "
                "retry cap.",
                "Abort the entire run on any tool error, even one the model could easily "
                "correct.",
                "Ignore the error silently and let the model assume the call worked as "
                "intended.",
                "Generate a plausible fake result in code so the loop can continue without "
                "interruption.",
            ),
        ),
        _t(
            "Uma chamada de ferramenta falha porque o modelo passou um argumento inválido. "
            "Qual é a melhor forma de tratar isso no laço?",
            "Devolver uma mensagem de erro clara como resultado da ferramenta, para que o "
            "modelo corrija os argumentos ou escolha outra abordagem, com um limite de "
            "tentativas. B não dá ao modelo chance de se recuperar. C o leva a assumir "
            "sucesso e construir sobre uma premissa falsa. D inventa dados, o que é pior do "
            "que falhar.",
            _options(
                "Devolver um erro claro como resultado da ferramenta para o modelo se "
                "ajustar, com limite de tentativas.",
                "Abortar a execução inteira a qualquer erro de ferramenta, mesmo um que o "
                "modelo corrigiria com facilidade.",
                "Ignorar o erro silenciosamente e deixar o modelo assumir que a chamada "
                "funcionou como esperado.",
                "Gerar em código um resultado falso, mas plausível, para o laço continuar "
                "sem nenhuma interrupção.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q08",
        _AGENT,
        MC,
        MEDIUM,
        ("d",),
        ("react", "planning"),
        _t(
            "What is the key idea of the ReAct pattern?",
            "ReAct interleaves reasoning with actions: the model reasons about what to do, "
            "calls a tool, observes the result, and uses that observation to decide the next "
            "step. A describes rigid up-front planning, which ReAct deliberately avoids. B "
            "describes voting among several agents, and C a single retrieval step followed "
            "by one answer.",
            _options(
                "Planning the full sequence of actions up front and never revising it, "
                "whatever the tool results show.",
                "Running several agents and taking a majority vote.",
                "Retrieving documents once and then producing a single answer.",
                "Interleaving reasoning with actions, feeding each observation back into "
                "the next step.",
            ),
        ),
        _t(
            "Qual é a ideia central do padrão ReAct?",
            "O ReAct intercala raciocínio e ação: o modelo raciocina sobre o que fazer, chama "
            "uma ferramenta, observa o resultado e usa essa observação para decidir o próximo "
            "passo. A descreve um planejamento rígido antecipado, que o ReAct evita "
            "deliberadamente. B descreve votação entre vários agentes, e C uma única etapa de "
            "recuperação seguida de uma resposta.",
            _options(
                "Planejar toda a sequência de ações de antemão e nunca revisá-la, não "
                "importa o que as ferramentas devolvam.",
                "Executar vários agentes e adotar o voto da maioria.",
                "Recuperar documentos uma vez e então produzir uma única resposta.",
                "Intercalar raciocínio e ação, realimentando cada observação para guiar o "
                "próximo passo.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q09",
        _AGENT,
        MC,
        HARD,
        ("a",),
        ("multi-agent", "tradeoffs"),
        _t(
            "A team proposes splitting a task into six specialized agents that pass work to "
            "one another. What is the most important reason to be cautious?",
            "Every handoff adds cost and latency, loses some context, and gives errors a "
            "chance to compound, so extra agents often make a system worse. Multiple agents "
            "pay off mainly when subtasks are truly independent or need separate contexts or "
            "tool sets. B is false: more agents do not improve accuracy by themselves. C "
            "and D are not real limits.",
            _options(
                "Each handoff adds cost and latency, loses context and lets errors compound, "
                "so extra agents often make things worse.",
                "Adding agents always improves accuracy, so six is too few.",
                "Models cannot read messages written by another agent.",
                "Agents cannot use more than one tool each.",
            ),
        ),
        _t(
            "Uma equipe propõe dividir uma tarefa em seis agentes especializados que passam o "
            "trabalho entre si. Qual é a razão mais importante para ter cautela?",
            "Cada transferência adiciona custo e latência, perde parte do contexto e dá aos "
            "erros chance de se acumular, então agentes extras muitas vezes pioram o sistema. "
            "Vários agentes compensam principalmente quando as subtarefas são realmente "
            "independentes ou exigem contextos ou conjuntos de ferramentas separados. B é "
            "falsa: mais agentes não melhoram a precisão por si só. C e D não são limites "
            "reais.",
            _options(
                "Cada transferência adiciona custo e latência, perde contexto e permite que "
                "erros se acumulem, então agentes extras muitas vezes pioram o sistema.",
                "Adicionar agentes sempre melhora a precisão, então seis é pouco.",
                "Modelos não conseguem ler mensagens escritas por outro agente.",
                "Agentes não podem usar mais de uma ferramenta cada.",
            ),
        ),
    ),
    _q(
        "ai-agents-tool-use-q10",
        _AGENT,
        SHORT,
        HARD,
        None,
        ("workflow", "architecture"),
        _t(
            "When would you choose a fixed workflow, a single agent, or a multi-agent system? "
            "Give the deciding criteria.",
            "Self-check: did you mention (1) fixed workflows for known, repeatable steps, "
            "(2) a single agent when the path is open-ended, (3) multi-agent only when "
            "subtasks are independent or need separate contexts, and (4) the cost of added "
            "complexity?",
            model_answer="Choose a fixed workflow (code-defined steps, possibly with LLM calls "
            "inside) when the task and its steps are known and repeatable: it is cheaper, "
            "faster, more predictable and easier to test. Choose a single agent with tools when "
            "the path cannot be known in advance and the model must decide the next step from "
            "intermediate results, accepting more cost, variance and the need for limits and "
            "guardrails. Move to multiple agents only when subtasks are genuinely independent "
            "(parallelism), need separate contexts or tool sets, or a single context is "
            "overloaded, because handoffs add latency, cost, context loss and compounding "
            "errors. Start with the simplest option that meets the requirement and add "
            "complexity only when evaluations show a need.",
        ),
        _t(
            "Quando você escolheria um workflow fixo, um único agente ou um sistema "
            "multiagente? Dê os critérios de decisão.",
            "Autoavaliação: você mencionou (1) workflows fixos para etapas conhecidas e "
            "repetíveis, (2) um único agente quando o caminho é aberto, (3) multiagente só "
            "quando as subtarefas são independentes ou exigem contextos separados e (4) o "
            "custo da complexidade adicional?",
            model_answer="Escolher um workflow fixo (etapas definidas em código, possivelmente "
            "com chamadas a LLM dentro) quando a tarefa e suas etapas são conhecidas e "
            "repetíveis: é mais barato, mais rápido, mais previsível e mais fácil de testar. "
            "Escolher um único agente com ferramentas quando o caminho não pode ser conhecido "
            "de antemão e o modelo precisa decidir o próximo passo a partir de resultados "
            "intermediários, aceitando mais custo, variância e a necessidade de limites e "
            "guardrails. Passar para vários agentes só quando as subtarefas forem realmente "
            "independentes (paralelismo), exigirem contextos ou conjuntos de ferramentas "
            "separados, ou um único contexto estiver sobrecarregado, pois as transferências "
            "adicionam latência, custo, perda de contexto e acúmulo de erros. Começar pela "
            "opção mais simples que atenda ao requisito e adicionar complexidade apenas "
            "quando as avaliações mostrarem necessidade.",
        ),
    ),
)

_RECALL_CODE = """```python
retrieved = ["d3", "d7", "d1", "d9"]  # ranked results
relevant = {"d1", "d2"}               # ground-truth relevant documents
k = 3

hits = [d for d in retrieved[:k] if d in relevant]
print(len(hits) / len(relevant), len(hits) / k)
```"""

# ----------------------------------------------------------------------
# ai-evaluation
# ----------------------------------------------------------------------
_EVAL = "ai-evaluation"

EVAL_QUESTIONS: tuple[QuestionSeed, ...] = (
    _q(
        "ai-evaluation-q01",
        _EVAL,
        MC,
        EASY,
        ("d",),
        ("evaluation", "motivation"),
        _t(
            "Why is it not enough to check a handful of outputs by hand and conclude that an "
            "LLM feature 'looks good'?",
            "A few examples cannot reveal failure rates or regressions, and LLM outputs vary "
            "across inputs, so you need systematic measurement on a representative dataset "
            "that you can re-run after every change. A is wrong because quality drifts as "
            "prompts, models and data change. B is false: outputs are not guaranteed to be "
            "deterministic. C is wrong because evaluation and monitoring complement each "
            "other.",
            _options(
                "Evaluation is only needed once, right before launch, since quality stays "
                "fixed afterwards.",
                "LLM outputs are deterministic, so a handful of manual checks is enough and "
                "tests are unnecessary.",
                "Evaluation replaces the need for production monitoring, since the dataset "
                "already covers real traffic.",
                "A few examples cannot reveal failure rates or regressions; you need "
                "systematic measurement.",
            ),
        ),
        _t(
            "Por que não basta verificar algumas saídas manualmente e concluir que uma "
            "funcionalidade com LLM 'parece boa'?",
            "Poucos exemplos não revelam taxas de falha nem regressões, e as saídas variam "
            "conforme a entrada, então é preciso medir de forma sistemática em um dataset "
            "representativo que possa ser reexecutado a cada mudança. A está errada porque a "
            "qualidade muda conforme prompts, modelos e dados mudam. B é falsa: as saídas não "
            "têm garantia de serem determinísticas. C está errada porque avaliação e "
            "monitoramento se complementam.",
            _options(
                "A avaliação só é necessária uma vez, logo antes do lançamento, pois a "
                "qualidade não muda depois.",
                "As saídas de LLMs são determinísticas, então algumas checagens manuais "
                "bastam e testes são desnecessários.",
                "A avaliação substitui a necessidade de monitoramento em produção, pois o "
                "dataset já cobre o tráfego real.",
                "Poucos exemplos não revelam taxas de falha nem regressões; é preciso medir "
                "de forma sistemática.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q02",
        _EVAL,
        MC,
        EASY,
        ("b",),
        ("golden-dataset",),
        _t(
            "What is a **golden dataset** in LLM evaluation?",
            "A golden dataset is a curated set of representative inputs, each with an expected "
            "output or grading criteria, including edge cases, that you reuse to measure "
            "quality over time. A (raw, unreviewed logs) lacks expected answers, C confuses "
            "evaluation data with training data, and D is not a real concept.",
            _options(
                "All production logs from the last quarter, stored exactly as they arrived, "
                "with no review or filtering.",
                "A curated set of representative inputs with expected outputs or grading "
                "criteria, reused over time.",
                "The data the model was originally trained on, kept for later comparison.",
                "A set of prompts run only at the highest temperature, to stress-test the "
                "model's randomness.",
            ),
        ),
        _t(
            "O que é um **golden dataset** na avaliação de LLMs?",
            "Um golden dataset é um conjunto curado de entradas representativas, cada uma com "
            "uma saída esperada ou critérios de avaliação, incluindo casos extremos, "
            "reutilizado para medir a qualidade ao longo do tempo. A (logs brutos, sem "
            "revisão) não tem respostas esperadas, C confunde dados de avaliação com dados de "
            "treinamento, e D não é um conceito real.",
            _options(
                "Todos os logs de produção do último trimestre, armazenados exatamente como "
                "chegaram, sem revisão nem filtragem.",
                "Um conjunto curado de entradas representativas, com saídas esperadas ou "
                "critérios de avaliação, reutilizado ao longo do tempo.",
                "Os dados com os quais o modelo foi originalmente treinado, guardados para "
                "comparação posterior.",
                "Um conjunto de prompts executados apenas na temperatura mais alta, para "
                "testar a aleatoriedade do modelo.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q03",
        _EVAL,
        MC,
        EASY,
        ("c",),
        ("deterministic-checks",),
        _t(
            "Which property of an output is best verified with a **deterministic** check "
            "rather than an LLM judge?",
            "Whether the output is valid JSON with the required fields can be checked exactly "
            "by code, which is cheap and has no judge variance. Tone, summary quality and "
            "clarity for a beginner are subjective and need rubric-based human or LLM "
            "evaluation.",
            _options(
                "Whether the tone of the reply is empathetic and appropriate for an upset "
                "customer.",
                "Whether a summary captures the key ideas without leaving out important "
                "caveats.",
                "Whether the output is valid JSON containing all required fields.",
                "Whether an explanation of the concept is clear to a beginner with no "
                "background.",
            ),
        ),
        _t(
            "Qual propriedade de uma saída é mais bem verificada com uma checagem "
            "**determinística**, e não com um LLM juiz?",
            "Se a saída é um JSON válido com os campos obrigatórios pode ser verificado "
            "exatamente por código, de forma barata e sem variância de um juiz. Tom, "
            "qualidade de um resumo e clareza para um iniciante são subjetivos e exigem "
            "avaliação humana ou por LLM com base em uma rubrica.",
            _options(
                "Se o tom da resposta é empático e adequado para um cliente irritado.",
                "Se um resumo captura as ideias principais sem deixar de fora ressalvas "
                "importantes.",
                "Se a saída é um JSON válido contendo todos os campos obrigatórios.",
                "Se uma explicação do conceito é clara para um iniciante sem nenhuma bagagem "
                "prévia.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q04",
        _EVAL,
        CODE,
        MEDIUM,
        ("b",),
        ("retrieval-metrics", "recall", "precision"),
        _t(
            "What does this code print?\n\n" + _RECALL_CODE,
            "Only `d1` appears among the top 3 results and is relevant, so there is 1 hit. "
            "Recall@3 is hits divided by all relevant documents (1/2 = 0.5), while "
            "precision@3 is hits divided by k (1/3). A swaps the two metrics. C and D use the "
            "wrong denominators: `d9` is outside the top 3 and does not count.",
            _options(
                "`0.3333333333333333 0.5`",
                "`0.5 0.3333333333333333`",
                "`1.0 0.3333333333333333`",
                "`0.5 0.5`",
            ),
        ),
        _t(
            "O que este código imprime?\n\n" + _RECALL_CODE,
            "Apenas `d1` aparece entre os 3 primeiros resultados e é relevante, então há 1 "
            "acerto. O recall@3 é acertos dividido por todos os documentos relevantes "
            "(1/2 = 0,5), enquanto a precisão@3 é acertos dividido por k (1/3). A troca as "
            "duas métricas. C e D usam denominadores errados: `d9` está fora dos 3 primeiros e "
            "não conta.",
            _options(
                "`0.3333333333333333 0.5`",
                "`0.5 0.3333333333333333`",
                "`1.0 0.3333333333333333`",
                "`0.5 0.5`",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q05",
        _EVAL,
        MC,
        MEDIUM,
        ("c",),
        ("llm-as-judge", "position-bias"),
        _t(
            "In a pairwise comparison, an LLM judge picks whichever answer is shown first "
            "about 80% of the time, even after you swap the order of the two answers. What is "
            "happening and what is a sound mitigation?",
            "This is position bias: the verdict depends on where the answer appears rather "
            "than on its quality. Evaluate both orders and count only consistent verdicts "
            "(treating disagreements as ties). A and B name other real biases, but they do "
            "not match the symptom, since the preference follows position and not length or "
            "authorship. D is not a fix: raising the temperature adds noise instead of "
            "removing bias.",
            _options(
                "Verbosity bias; ask the candidate models for shorter answers so length "
                "stops mattering.",
                "Self-preference; replace the judge with a larger model from another vendor "
                "and keep one order.",
                "Position bias; run each comparison in both orders and keep only consistent "
                "verdicts.",
                "Calibration drift; raise the judge's temperature so verdicts vary more.",
            ),
        ),
        _t(
            "Em uma comparação par a par, um LLM juiz escolhe a resposta mostrada primeiro em "
            "cerca de 80% dos casos, mesmo depois de você trocar a ordem das duas respostas. "
            "O que está acontecendo e qual é uma mitigação adequada?",
            "Isto é viés de posição: o veredito depende de onde a resposta aparece, e não de "
            "sua qualidade. Avalie as duas ordens e conte apenas os vereditos consistentes "
            "(tratando divergências como empate). A e B citam outros vieses reais, mas não "
            "combinam com o sintoma, pois a preferência acompanha a posição e não o tamanho ou "
            "a autoria. D não é correção: aumentar a temperatura adiciona ruído em vez de "
            "remover o viés.",
            _options(
                "Viés de verbosidade; pedir respostas mais curtas aos modelos candidatos "
                "para o tamanho deixar de pesar.",
                "Autopreferência; trocar o juiz por um modelo maior, de outro fornecedor, e "
                "manter uma única ordem.",
                "Viés de posição; executar cada comparação nas duas ordens e contar só os "
                "vereditos consistentes.",
                "Deriva de calibração; aumentar a temperatura do juiz para os vereditos "
                "variarem mais.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q06",
        _EVAL,
        MS,
        MEDIUM,
        ("a", "b", "c"),
        ("llm-as-judge", "biases"),
        _t(
            "Which are known failure modes of LLM-as-judge evaluation? Select all that apply.",
            "Judges can favor the answer in a particular position (position bias), prefer "
            "longer answers regardless of quality (verbosity bias), and favor outputs "
            "resembling their own (self-preference). D is false: temperature 0 makes the "
            "judge repeatable, not unbiased. E is false: these biases affect LLM judges "
            "directly, which is why they must be measured.",
            _options(
                "Position bias: favoring an answer because of where it appears.",
                "Verbosity bias: favoring longer answers regardless of quality.",
                "Self-preference: favoring outputs that resemble the judge model's own style.",
                "Setting temperature to 0 removes all of the judge's biases.",
                "Length bias only affects human raters, never LLM judges.",
            ),
        ),
        _t(
            "Quais são modos de falha conhecidos da avaliação com LLM como juiz "
            "(LLM-as-judge)? Selecione todos que se aplicam.",
            "Juízes podem favorecer a resposta em uma posição específica (viés de posição), "
            "preferir respostas mais longas independentemente da qualidade (viés de "
            "verbosidade) e favorecer saídas parecidas com as suas (autopreferência). D é "
            "falsa: temperatura 0 torna o juiz repetível, não imparcial. E é falsa: esses "
            "vieses afetam diretamente juízes LLM, e por isso precisam ser medidos.",
            _options(
                "Viés de posição: favorecer uma resposta pelo lugar onde ela aparece.",
                "Viés de verbosidade: favorecer respostas mais longas independentemente da "
                "qualidade.",
                "Autopreferência: favorecer saídas parecidas com o estilo do próprio modelo juiz.",
                "Definir a temperatura como 0 remove todos os vieses do juiz.",
                "O viés de tamanho afeta apenas avaliadores humanos, nunca juízes LLM.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q07",
        _EVAL,
        MC,
        MEDIUM,
        ("d",),
        ("regression-suite", "slices"),
        _t(
            "After a prompt change, your eval's overall score rises by two points, but the "
            "score on one category (refund questions) falls from 90 to 60. What should you "
            "do?",
            "Aggregate scores can hide regressions in slices, so inspect the per-category "
            "results and investigate the drop before shipping; the fix may be to adjust the "
            "prompt or accept a conscious trade-off. A ignores a serious regression. B "
            "dismisses a clear signal as noise without evidence. C is unrelated, since a "
            "judge's temperature does not explain a category drop.",
            _options(
                "Ship it, because the overall score improved and the average is what users "
                "will feel.",
                "Discard the results, assuming the eval is too noisy to trust, and rely on "
                "manual spot checks.",
                "Raise the judge's temperature and re-run until the refund category "
                "recovers to its old level.",
                "Inspect the per-category results and investigate the refund drop before "
                "deciding to ship.",
            ),
        ),
        _t(
            "Depois de uma mudança no prompt, a nota geral da avaliação sobe dois pontos, mas "
            "a nota de uma categoria (perguntas sobre reembolso) cai de 90 para 60. O que "
            "fazer?",
            "Notas agregadas podem esconder regressões em fatias, então examine os resultados "
            "por categoria e investigue a queda antes de publicar; a solução pode ser ajustar "
            "o prompt ou aceitar conscientemente um trade-off. A ignora uma regressão séria. B "
            "descarta um sinal claro como ruído sem evidência. C não tem relação, pois a "
            "temperatura do juiz não explica a queda de uma categoria.",
            _options(
                "Publicar, porque a nota geral melhorou e é a média que os usuários vão "
                "sentir.",
                "Descartar os resultados, supondo que a avaliação é ruidosa demais para "
                "confiar, e usar só checagens manuais.",
                "Aumentar a temperatura do juiz e reexecutar até a categoria de reembolso "
                "voltar ao nível antigo.",
                "Examinar os resultados por categoria e investigar a queda de reembolso "
                "antes de decidir se publica.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q08",
        _EVAL,
        MC,
        MEDIUM,
        ("a",),
        ("online-evaluation", "offline-evaluation"),
        _t(
            "Which of these can you only learn through **online** evaluation (on live "
            "traffic) and not from an offline golden dataset?",
            "Real users phrase requests in ways you did not anticipate, and their behavior "
            "(retries, abandonment, ratings) reveals satisfaction and distribution drift "
            "that a fixed dataset cannot show. B, C and D can all be measured offline on "
            "fixed or labeled data.",
            _options(
                "How real users actually phrase requests and whether they are satisfied or retry.",
                "Whether outputs match the required JSON schema on the golden set.",
                "Whether a prompt change regressed the fixed regression suite.",
                "How closely the judge agrees with human labels on a labeled sample.",
            ),
        ),
        _t(
            "Qual destas coisas você só descobre por meio de avaliação **online** (em tráfego "
            "real) e não a partir de um golden dataset offline?",
            "Usuários reais formulam pedidos de formas que você não previu, e o comportamento "
            "deles (novas tentativas, abandono, avaliações) revela satisfação e deriva da "
            "distribuição que um dataset fixo não mostra. B, C e D podem ser medidas offline "
            "em dados fixos ou rotulados.",
            _options(
                "Como usuários reais realmente formulam os pedidos e se ficam satisfeitos ou "
                "tentam de novo.",
                "Se as saídas seguem o schema JSON exigido no conjunto golden.",
                "Se uma mudança de prompt causou regressão na suíte de regressão fixa.",
                "O quanto o juiz concorda com rótulos humanos em uma amostra rotulada.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q09",
        _EVAL,
        MC,
        HARD,
        ("c",),
        ("overfitting", "held-out-set"),
        _t(
            "A team iterates on its prompt until the score on its golden dataset reaches 98%. "
            "What is the main risk, and what protects against it?",
            "Repeatedly tuning against the same examples overfits the prompt to them, so the "
            "score overestimates real-world quality. Keep a held-out set that is not used "
            "during tuning, and keep refreshing the data with new production cases. A is "
            "exactly the mistake being warned about. B and D are not real consequences.",
            _options(
                "None: a higher golden-set score always means better production quality.",
                "The dataset becomes too large to run.",
                "Overfitting to the eval set; keep a held-out set and refresh data with new "
                "production cases.",
                "The judge refuses to score examples it has seen before.",
            ),
        ),
        _t(
            "Uma equipe itera no prompt até a nota no seu golden dataset chegar a 98%. Qual é "
            "o principal risco e o que protege contra ele?",
            "Ajustar repetidamente contra os mesmos exemplos faz o prompt sofrer overfitting "
            "neles, e a nota superestima a qualidade real. Mantenha um conjunto separado "
            "(held-out) que não seja usado no ajuste e continue renovando os dados com novos "
            "casos de produção. A é exatamente o erro de que se está alertando. B e D não são "
            "consequências reais.",
            _options(
                "Nenhum: uma nota maior no conjunto golden sempre significa melhor qualidade "
                "em produção.",
                "O dataset fica grande demais para executar.",
                "Overfitting ao conjunto de avaliação; manter um conjunto held-out e renovar "
                "os dados com novos casos de produção.",
                "O juiz se recusa a avaliar exemplos que já viu antes.",
            ),
        ),
    ),
    _q(
        "ai-evaluation-q10",
        _EVAL,
        SHORT,
        HARD,
        None,
        ("llm-as-judge", "validation"),
        _t(
            "How would you validate an LLM judge before using it to gate releases, and when "
            "would you prefer a deterministic check instead?",
            "Self-check: did you mention (1) comparing the judge with human labels on a "
            "sample, (2) a clear rubric and bias mitigations such as swapping order, and "
            "(3) preferring deterministic checks for objective, code-verifiable properties?",
            model_answer="Have humans label a representative sample, run the judge on the same "
            "items and measure agreement, inspecting disagreements and slices where it fails. "
            "Give the judge a specific rubric, mitigate known biases (swap answer order, watch "
            "for length and self-preference), and re-check agreement when the judge, rubric or "
            "task changes. Use deterministic checks whenever a property can be verified by "
            "code, such as schema validity, required fields, exact values or forbidden "
            "content, because they are cheaper, exact and free of judge variance. Reserve the "
            "judge for subjective qualities such as helpfulness or faithfulness.",
        ),
        _t(
            "Como você validaria um LLM juiz antes de usá-lo para liberar releases, e quando "
            "preferiria uma checagem determinística?",
            "Autoavaliação: você mencionou (1) comparar o juiz com rótulos humanos em uma "
            "amostra, (2) uma rubrica clara e mitigações de vieses, como trocar a ordem, e "
            "(3) preferir checagens determinísticas para propriedades objetivas verificáveis "
            "por código?",
            model_answer="Pedir a humanos que rotulem uma amostra representativa, executar o "
            "juiz nos mesmos itens e medir a concordância, examinando as divergências e as "
            "fatias em que ele falha. Dar ao juiz uma rubrica específica, mitigar vieses "
            "conhecidos (trocar a ordem das respostas, observar tamanho e autopreferência) e "
            "verificar a concordância de novo quando o juiz, a rubrica ou a tarefa mudarem. "
            "Usar checagens determinísticas sempre que uma propriedade puder ser verificada "
            "por código, como validade de schema, campos obrigatórios, valores exatos ou "
            "conteúdo proibido, pois são mais baratas, exatas e livres de variância do juiz. "
            "Reservar o juiz para qualidades subjetivas, como utilidade ou fidelidade.",
        ),
    ),
)

QUESTIONS: tuple[QuestionSeed, ...] = (
    *LLM_QUESTIONS,
    *CONTEXT_QUESTIONS,
    *RAG_QUESTIONS,
    *AGENT_QUESTIONS,
    *EVAL_QUESTIONS,
)

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
    AssessmentSeed(
        code="ai-engineering-context-engineering-quiz",
        title="Context Engineering Quiz",
        description="Context budgets, pollution, compression, summaries and ordering.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="context-engineering",
        translations={
            "pt-BR": {
                "title": "Quiz de Context Engineering",
                "description": "Orçamento de contexto, poluição, compressão, resumos e ordenação.",
            }
        },
    ),
    AssessmentSeed(
        code="ai-engineering-rag-architecture-quiz",
        title="RAG Architecture Quiz",
        description="Ingestion, chunking, hybrid retrieval, reranking and diagnosing failures.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="rag-architecture",
        translations={
            "pt-BR": {
                "title": "Quiz de Arquitetura RAG",
                "description": "Ingestão, chunking, recuperação híbrida, reranking e "
                "diagnóstico de falhas.",
            }
        },
    ),
    AssessmentSeed(
        code="ai-engineering-ai-agents-tool-use-quiz",
        title="AI Agents and Tool Use Quiz",
        description="Tool calling, the agent loop, safeguards and choosing an architecture.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="ai-agents-tool-use",
        translations={
            "pt-BR": {
                "title": "Quiz de Agentes de IA e Uso de Ferramentas",
                "description": "Tool calling, o laço do agente, salvaguardas e escolha de "
                "arquitetura.",
            }
        },
    ),
    AssessmentSeed(
        code="ai-engineering-ai-evaluation-quiz",
        title="AI Evaluation Quiz",
        description="Golden datasets, deterministic checks, LLM-as-judge biases and metrics.",
        kind=AssessmentKind.COMPETENCY,
        competency_slug="ai-evaluation",
        translations={
            "pt-BR": {
                "title": "Quiz de Avaliação de IA",
                "description": "Golden datasets, checagens determinísticas, vieses do LLM "
                "como juiz e métricas.",
            }
        },
    ),
    AssessmentSeed(
        code="ai-engineering-checkpoint",
        title="AI Engineering Checkpoint",
        description="A mixed check across LLM fundamentals, context, RAG, agents and evaluation.",
        kind=AssessmentKind.MIXED,
        question_codes=(
            "llm-fundamentals-q02",
            "llm-fundamentals-q04",
            "context-engineering-q02",
            "context-engineering-q07",
            "rag-architecture-q03",
            "rag-architecture-q06",
            "ai-agents-tool-use-q05",
            "ai-agents-tool-use-q08",
            "ai-evaluation-q03",
            "ai-evaluation-q05",
        ),
        translations={
            "pt-BR": {
                "title": "Checkpoint de Engenharia de IA",
                "description": "Uma verificação mista entre fundamentos de LLMs, contexto, "
                "RAG, agentes e avaliação.",
            }
        },
        pass_threshold=70,
        completion_bonus_xp=40,
    ),
)


QUESTION_SET = SubjectQuestionSet(
    subject_slug="ai-engineering",
    questions=QUESTIONS,
    assessments=ASSESSMENTS,
)
