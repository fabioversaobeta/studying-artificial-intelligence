"""Question bank for the Interview Preparation subject (coding patterns,
system design interviews, behavioral interviews, technical communication; ten
questions each, English + Brazilian Portuguese).

Written by Claude (``source=ai_generated``) and awaiting the owner's review,
as decided in docs/PROPOSAL_TRACK_I.md (D6). Rules: ``validate.py``. Every
Python snippet in a ``code_reading`` question was executed to confirm the
stated output.
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


def _options(*pairs: str) -> tuple[OptionSeed, ...]:
    """_options("text a", "text b", ...) -> options with ids a, b, c..."""
    return tuple(OptionSeed(id=chr(ord("a") + i), text=text) for i, text in enumerate(pairs))


_WINDOW_CODE = """```python
def best(nums, k):
    window = sum(nums[:k])
    best = window
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best

print(best([2, 1, 5, 1, 3, 2], 3))
```"""

_BFS_CODE = """```python
from collections import deque

graph = {"A": ["B", "C"], "B": ["D"], "C": ["D", "E"], "D": ["F"], "E": ["F"], "F": []}

def bfs(start, goal):
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        node, dist = queue.popleft()
        if node == goal:
            return dist
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return -1

print(bfs("A", "F"), bfs("F", "A"))
```"""

_STACK_CODE = """```python
def next_greater(nums):
    result = [-1] * len(nums)
    stack = []
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            result[stack.pop()] = x
        stack.append(i)
    return result

print(next_greater([2, 1, 2, 4, 3]))
```"""


_CODING: tuple[QuestionSeed, ...] = (
    # ------------------------------------------------------------------
    # coding-interview-patterns
    # ------------------------------------------------------------------
    QuestionSeed(
        code="coding-interview-patterns-q01",
        competency_slug="coding-interview-patterns",
        type=MC,
        difficulty=EASY,
        correct=("c",),
        tags=("two-pointers", "pattern-recognition"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You get a **sorted** array and must decide whether any two elements add "
                "up to a target, in a single pass with O(1) extra space. Which approach fits?",
                options=_options(
                    "Check every pair with two nested loops.",
                    "Walk the array once while storing the values seen so far in a hash set.",
                    "Keep one pointer at each end and move the left or right one inward "
                    "depending on whether the current sum is too small or too big.",
                    "Slide a fixed window of width 2 across the array.",
                ),
                explanation="Sortedness is the cue for opposite-end two pointers: if the sum is "
                "too small only moving the left pointer can raise it, and if it is too big only "
                "moving the right one can lower it. That is O(n) time and O(1) space. Nested "
                "loops are O(n²), the hash set needs O(n) extra space, and a width-2 window only "
                "sees adjacent elements, not arbitrary pairs.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você recebe um array **ordenado** e precisa decidir se dois elementos "
                "quaisquer somam um valor-alvo, em uma única passada e com O(1) de espaço extra. "
                "Qual abordagem se encaixa?",
                options=_options(
                    "Verificar todos os pares com dois loops aninhados.",
                    "Percorrer o array uma vez guardando os valores já vistos em um hash set.",
                    "Manter um ponteiro em cada extremidade e mover o da esquerda ou o da "
                    "direita para dentro, conforme a soma atual seja pequena ou grande demais.",
                    "Deslizar uma janela fixa de largura 2 pelo array.",
                ),
                explanation="Estar ordenado é a pista para two pointers nas extremidades: se a "
                "soma é pequena demais, só mover o ponteiro da esquerda pode aumentá-la; se é "
                "grande demais, só mover o da direita pode diminuí-la. Isso dá O(n) de tempo e "
                "O(1) de espaço. Loops aninhados são O(n²), o hash set usa O(n) de espaço extra "
                "e uma janela de largura 2 só enxerga elementos adjacentes, não pares quaisquer.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q02",
        competency_slug="coding-interview-patterns",
        type=MC,
        difficulty=EASY,
        correct=("b",),
        tags=("sliding-window", "pattern-recognition"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Given an array of **positive** integers and a limit S, you must find the "
                "length of the longest contiguous subarray whose sum is at most S. Which "
                "pattern should you reach for first?",
                options=_options(
                    "Binary search on the array, since the answer is a position.",
                    "A variable-size sliding window: grow it on the right, shrink it from the "
                    "left while the sum exceeds S.",
                    "Breadth-first search over the array indices.",
                    "A hash map from each value to its complement, as in two-sum.",
                ),
                explanation="The words 'contiguous subarray' plus a property that changes "
                "predictably when one element enters or leaves (all values are positive, so the "
                "sum only grows or shrinks monotonically) point to a sliding window with O(n) "
                "time. The array is not sorted, so binary search has nothing to split on; there "
                "is no graph for BFS; and a complement map finds an exact pair, not the longest "
                "range under a limit.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Dado um array de inteiros **positivos** e um limite S, você deve achar o "
                "tamanho do maior subarray contíguo cuja soma seja no máximo S. Qual padrão "
                "usar primeiro?",
                options=_options(
                    "Busca binária no array, já que a resposta é uma posição.",
                    "Uma sliding window de tamanho variável: crescer pela direita e encolher "
                    "pela esquerda enquanto a soma passar de S.",
                    "Busca em largura (BFS) sobre os índices do array.",
                    "Um hash map de cada valor para seu complemento, como no two-sum.",
                ),
                explanation="As palavras 'subarray contíguo' mais uma propriedade que muda de "
                "forma previsível quando um elemento entra ou sai (todos os valores são "
                "positivos, então a soma só cresce ou encolhe monotonicamente) apontam para uma "
                "sliding window com O(n) de tempo. O array não está ordenado, então a busca "
                "binária não tem o que dividir; não há grafo para BFS; e um mapa de complementos "
                "acha um par exato, não o maior intervalo sob um limite.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q03",
        competency_slug="coding-interview-patterns",
        type=MC,
        difficulty=EASY,
        correct=("d",),
        tags=("bfs", "graphs", "pattern-recognition"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You are asked for the **fewest moves** needed to get from the start cell "
                "to the exit of a grid maze, where each move to an adjacent open cell costs the "
                "same. What is the simplest approach that is both correct and optimal?",
                options=_options(
                    "Depth-first search with a visited set; return the first path found.",
                    "Dijkstra's algorithm with a heap, because it is the only way to find "
                    "shortest paths.",
                    "Sort the open cells by Manhattan distance to the exit and walk them in "
                    "that order.",
                    "Breadth-first search with a queue, stopping when the exit is dequeued.",
                ),
                explanation="With equal edge costs, BFS visits cells in non-decreasing distance "
                "order, so the first time it reaches the exit is the shortest path, in O(V + E). "
                "DFS returns some path, not necessarily the shortest. Dijkstra also works but "
                "adds a log factor for no benefit when all weights are equal, and it is not the "
                "only option. Manhattan ordering ignores walls.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Pedem o **menor número de movimentos** para ir da célula inicial até a "
                "saída de um labirinto em grade, em que cada movimento para uma célula vizinha "
                "livre custa o mesmo. Qual é a abordagem mais simples que é correta e ótima?",
                options=_options(
                    "Busca em profundidade (DFS) com um conjunto de visitados; retornar o "
                    "primeiro caminho encontrado.",
                    "O algoritmo de Dijkstra com heap, porque é a única forma de achar "
                    "caminhos mínimos.",
                    "Ordenar as células livres pela distância de Manhattan até a saída e "
                    "percorrê-las nessa ordem.",
                    "Busca em largura (BFS) com uma fila, parando quando a saída sair da fila.",
                ),
                explanation="Com custos iguais nas arestas, a BFS visita as células em ordem "
                "não decrescente de distância, então a primeira vez que chega à saída é o "
                "caminho mínimo, em O(V + E). A DFS devolve algum caminho, não necessariamente o "
                "menor. Dijkstra também funciona, mas acrescenta um fator logarítmico sem "
                "benefício quando todos os pesos são iguais, e não é a única opção. Ordenar por "
                "Manhattan ignora as paredes.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q04",
        competency_slug="coding-interview-patterns",
        type=CODE,
        difficulty=MEDIUM,
        correct=("a",),
        tags=("sliding-window", "complexity", "code-reading"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What does this code print, and what is its time complexity for an input "
                "of length n?\n\n" + _WINDOW_CODE,
                options=_options(
                    "It prints `9`, in O(n) time: each step updates the window sum in O(1).",
                    "It prints `8`, because only the first window is evaluated.",
                    "It prints `9`, but in O(n·k) time, because every window is summed again.",
                    "It prints `6`, because the loop ends on the last window.",
                ),
                explanation="The windows of size 3 sum to 8, 7, 9 and 6, so `best` ends at 9 "
                "(the window `[5, 1, 3]`). The code adds the element entering the window and "
                "subtracts the one leaving it, so each step is O(1) and the total is O(n). "
                "Re-summing every window would be O(n·k), which is exactly what this technique "
                "avoids.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O que este código imprime, e qual é sua complexidade de tempo para uma "
                "entrada de tamanho n?\n\n" + _WINDOW_CODE,
                options=_options(
                    "Imprime `9`, em O(n): cada passo atualiza a soma da janela em O(1).",
                    "Imprime `8`, porque só a primeira janela é avaliada.",
                    "Imprime `9`, mas em O(n·k), porque cada janela é somada de novo.",
                    "Imprime `6`, porque o loop termina na última janela.",
                ),
                explanation="As janelas de tamanho 3 somam 8, 7, 9 e 6, então `best` termina em "
                "9 (a janela `[5, 1, 3]`). O código soma o elemento que entra na janela e "
                "subtrai o que sai, então cada passo é O(1) e o total é O(n). Somar cada janela "
                "de novo seria O(n·k), exatamente o que essa técnica evita.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q05",
        competency_slug="coding-interview-patterns",
        type=MC,
        difficulty=MEDIUM,
        correct=("c",),
        tags=("two-pointers", "complexity"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="A sliding-window solution has a `while` loop (moving the left pointer) "
                "nested inside a `for` loop (moving the right pointer). Both pointers only ever "
                "move forward. Why is the total time O(n) and not O(n²)?",
                options=_options(
                    "Because the inner `while` loop runs only O(log n) times per iteration.",
                    "Because hash-map operations are O(1), so the rest of the code does not "
                    "matter.",
                    "Because each pointer advances at most n times in total, so the combined "
                    "work across the whole run is at most about 2n steps.",
                    "Because the alphabet is bounded, so the window can never be longer than "
                    "the alphabet.",
                ),
                explanation="The argument is amortized: the inner loop does not restart for each "
                "outer iteration, because the left pointer never moves back. Total movement of "
                "both pointers is bounded by 2n. O(1) map operations are needed for the "
                "constant work per step but do not explain the nested loop, and the bound on "
                "window length by the alphabet is specific to some problems, not the general "
                "reason.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Uma solução de sliding window tem um loop `while` (que move o ponteiro "
                "esquerdo) aninhado em um loop `for` (que move o ponteiro direito). Os dois "
                "ponteiros só andam para frente. Por que o tempo total é O(n) e não O(n²)?",
                options=_options(
                    "Porque o `while` interno roda apenas O(log n) vezes por iteração.",
                    "Porque operações em hash map são O(1), então o resto do código não "
                    "importa.",
                    "Porque cada ponteiro avança no máximo n vezes no total, então o trabalho "
                    "combinado de toda a execução é de cerca de 2n passos.",
                    "Porque o alfabeto é limitado, então a janela nunca pode ser maior que o "
                    "alfabeto.",
                ),
                explanation="O argumento é amortizado: o loop interno não recomeça a cada "
                "iteração externa, pois o ponteiro esquerdo nunca volta. O movimento total dos "
                "dois ponteiros é limitado por 2n. Operações O(1) no mapa são necessárias para "
                "o trabalho constante por passo, mas não explicam o loop aninhado, e limitar a "
                "janela pelo alfabeto vale só para alguns problemas, não é a razão geral.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q06",
        competency_slug="coding-interview-patterns",
        type=MS,
        difficulty=MEDIUM,
        correct=("a", "c", "e"),
        tags=("heap", "pattern-recognition"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which problem statements are strong signals that a **heap** "
                "(priority queue) is the right tool? Select all that apply.",
                options=_options(
                    "Keep track of the k largest values in a stream of numbers.",
                    "Check whether a string reads the same backwards.",
                    "Merge k sorted lists into one sorted list.",
                    "Find a target value in a sorted array.",
                    "Repeatedly process the task with the earliest deadline while new tasks "
                    "keep arriving.",
                ),
                explanation="A heap shines when you repeatedly need the smallest or largest "
                "element of a collection that keeps changing: a size-k min-heap for the top k "
                "of a stream, a heap holding the head of each list for a k-way merge, and a "
                "priority queue for deadlines. A palindrome check is a two-pointer scan, and "
                "searching a sorted array is binary search; neither needs a changing "
                "extreme.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Quais enunciados são fortes sinais de que um **heap** (fila de "
                "prioridade) é a ferramenta certa? Selecione todos que se aplicam.",
                options=_options(
                    "Manter os k maiores valores de um fluxo de números.",
                    "Verificar se uma string é igual lida de trás para frente.",
                    "Mesclar k listas ordenadas em uma única lista ordenada.",
                    "Encontrar um valor-alvo em um array ordenado.",
                    "Processar repetidamente a tarefa com o prazo mais próximo enquanto novas "
                    "tarefas continuam chegando.",
                ),
                explanation="O heap brilha quando você precisa repetidamente do menor ou do "
                "maior elemento de uma coleção que muda: um min-heap de tamanho k para os top k "
                "de um fluxo, um heap com a cabeça de cada lista no merge de k listas e uma "
                "fila de prioridade para prazos. Checar palíndromo é uma varredura com two "
                "pointers, e buscar em array ordenado é busca binária; nenhum precisa de um "
                "extremo mutável.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q07",
        competency_slug="coding-interview-patterns",
        type=MC,
        difficulty=MEDIUM,
        correct=("b",),
        tags=("binary-search", "pattern-recognition"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Packages with known weights must be shipped **in the given order** "
                "within D days, and each day's load cannot exceed the ship's capacity. You "
                "must find the minimum capacity that works. Which approach is best?",
                options=_options(
                    "A fixed-size sliding window of D packages.",
                    "Binary search over the capacity, using a greedy O(n) check of whether a "
                    "given capacity finishes within D days.",
                    "Breadth-first search over every way to split the packages into days.",
                    "A hash map of prefix sums keyed by day.",
                ),
                explanation="Feasibility is monotonic: if capacity C works, any larger capacity "
                "works too. That lets you binary search the answer itself (between the heaviest "
                "package and the total weight) and test each candidate greedily in O(n), for "
                "O(n log W) overall. Enumerating all splits is exponential, and a fixed window "
                "or prefix-sum map has no way to express the capacity condition.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Pacotes com pesos conhecidos devem ser enviados **na ordem dada** em "
                "até D dias, e a carga de cada dia não pode passar da capacidade do navio. "
                "Você precisa achar a menor capacidade que funciona. Qual abordagem é a "
                "melhor?",
                options=_options(
                    "Uma sliding window de tamanho fixo com D pacotes.",
                    "Busca binária sobre a capacidade, usando uma checagem gulosa em O(n) de "
                    "se uma dada capacidade termina em D dias.",
                    "Busca em largura (BFS) sobre todas as formas de dividir os pacotes em "
                    "dias.",
                    "Um hash map de somas de prefixo indexado por dia.",
                ),
                explanation="A viabilidade é monotônica: se a capacidade C funciona, qualquer "
                "capacidade maior também funciona. Isso permite fazer busca binária na própria "
                "resposta (entre o pacote mais pesado e o peso total) e testar cada candidata "
                "de forma gulosa em O(n), para O(n log W) no total. Enumerar todas as divisões "
                "é exponencial, e uma janela fixa ou um mapa de somas de prefixo não expressa "
                "a condição de capacidade.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q08",
        competency_slug="coding-interview-patterns",
        type=CODE,
        difficulty=MEDIUM,
        correct=("c",),
        tags=("bfs", "graphs", "code-reading"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What does this code print?\n\n" + _BFS_CODE,
                options=_options(
                    "`4 -1`",
                    "`3 0`",
                    "`3 -1`",
                    "It raises a `KeyError`.",
                ),
                explanation="The shortest route A → B → D → F has 3 edges, and BFS returns "
                "the distance in edges (`4` would count nodes). The graph is directed and `F` "
                "has no outgoing edges, so from `F` the goal `A` is never reached: the queue "
                "empties and the function returns -1. Every node appears as a key, so there is "
                "no `KeyError`.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O que este código imprime?\n\n" + _BFS_CODE,
                options=_options(
                    "`4 -1`",
                    "`3 0`",
                    "`3 -1`",
                    "Lança um `KeyError`.",
                ),
                explanation="O caminho mais curto A → B → D → F tem 3 arestas, e a BFS retorna "
                "a distância em arestas (`4` contaria nós). O grafo é direcionado e `F` não "
                "tem arestas de saída, então, partindo de `F`, o destino `A` nunca é "
                "alcançado: a fila esvazia e a função retorna -1. Todo nó aparece como chave, "
                "então não há `KeyError`.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q09",
        competency_slug="coding-interview-patterns",
        type=CODE,
        difficulty=HARD,
        correct=("d",),
        tags=("monotonic-stack", "complexity", "code-reading"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which statement about this code is correct?\n\n" + _STACK_CODE,
                options=_options(
                    "It prints `[4, 2, 4, -1, -1]` and runs in O(n²) in the worst case, "
                    "because a `while` loop is nested in a `for` loop.",
                    "It prints `[2, 2, 4, -1, -1]` and runs in O(n).",
                    "It prints `[4, 2, 4, -1, -1]` and runs in O(n log n), because of the "
                    "stack operations.",
                    "It prints `[4, 2, 4, -1, -1]` and runs in O(n) amortized, because each "
                    "index is pushed once and popped at most once.",
                ),
                explanation="Each element gets the next strictly greater value to its right "
                "(the `<` comparison means the equal `2` at index 2 does not resolve index 0, "
                "so it ends up with 4, not 2). Counting work per element instead of per loop: "
                "every index is pushed exactly once and popped at most once, so the total "
                "number of inner-loop iterations over the entire run is at most n. Stack push "
                "and pop are O(1), so there is no log factor.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual afirmação sobre este código está correta?\n\n" + _STACK_CODE,
                options=_options(
                    "Imprime `[4, 2, 4, -1, -1]` e roda em O(n²) no pior caso, porque há um "
                    "`while` aninhado em um `for`.",
                    "Imprime `[2, 2, 4, -1, -1]` e roda em O(n).",
                    "Imprime `[4, 2, 4, -1, -1]` e roda em O(n log n), por causa das "
                    "operações na pilha.",
                    "Imprime `[4, 2, 4, -1, -1]` e roda em O(n) amortizado, porque cada "
                    "índice entra na pilha uma vez e sai no máximo uma vez.",
                ),
                explanation="Cada elemento recebe o próximo valor estritamente maior à sua "
                "direita (o `<` faz com que o `2` igual no índice 2 não resolva o índice 0, "
                "que fica com 4, não 2). Contando o trabalho por elemento e não por loop: cada "
                "índice entra na pilha exatamente uma vez e sai no máximo uma, então o número "
                "total de iterações do loop interno em toda a execução é no máximo n. Push e "
                "pop na pilha são O(1), então não há fator logarítmico.",
            ),
        },
    ),
    QuestionSeed(
        code="coding-interview-patterns-q10",
        competency_slug="coding-interview-patterns",
        type=SHORT,
        difficulty=HARD,
        correct=None,
        tags=("dynamic-programming", "communication"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="In an interview you are asked for the minimum number of coins needed to "
                "make a given amount from a set of denominations, and your first recursive "
                "solution is exponential. How do you recognize that dynamic programming applies, "
                "and how do you walk from that brute force to an efficient solution? State the "
                "final complexity.",
                model_answer="Recognition: the problem asks for an optimum, and the best answer "
                "for amount a is built from best answers for smaller amounts (optimal "
                "substructure), while the plain recursion recomputes the same amounts again and "
                "again (overlapping subproblems). Walk-through: say the brute force first, "
                "define the state (fewest coins for amount a), write the recurrence "
                "f(a) = 1 + min(f(a - c)) over coins c, with f(0) = 0 and unreachable amounts "
                "as infinity, then add memoization or fill a bottom-up table from 0 to the "
                "target. Complexity: O(amount × number of coins) time and O(amount) space, "
                "versus exponential for the brute force.",
                explanation="Self-check: did you mention (1) optimal substructure and "
                "overlapping subproblems as the recognition signal, (2) starting from brute "
                "force and defining state plus recurrence and base case, (3) memoization or a "
                "bottom-up table, and (4) O(amount × coins) time with O(amount) space?",
            ),
            Language.PT_BR: QuestionText(
                prompt="Em uma entrevista pedem o menor número de moedas necessárias para formar "
                "um valor a partir de um conjunto de denominações, e sua primeira solução "
                "recursiva é exponencial. Como você reconhece que programação dinâmica se "
                "aplica, e como vai da força bruta até uma solução eficiente? Informe a "
                "complexidade final.",
                model_answer="Reconhecimento: o problema pede um ótimo, e a melhor resposta para "
                "o valor a é construída a partir das melhores respostas para valores menores "
                "(subestrutura ótima), enquanto a recursão simples recalcula os mesmos valores "
                "várias vezes (subproblemas sobrepostos). Passo a passo: apresentar primeiro a "
                "força bruta, definir o estado (menor número de moedas para o valor a), "
                "escrever a recorrência f(a) = 1 + min(f(a - c)) sobre as moedas c, com f(0) = 0 "
                "e valores inalcançáveis como infinito, e então adicionar memoização ou "
                "preencher uma tabela bottom-up de 0 até o alvo. Complexidade: O(valor × "
                "número de moedas) de tempo e O(valor) de espaço, contra exponencial na força "
                "bruta.",
                explanation="Autoavaliação: você mencionou (1) subestrutura ótima e subproblemas "
                "sobrepostos como sinal de reconhecimento, (2) partir da força bruta e definir "
                "estado, recorrência e caso base, (3) memoização ou tabela bottom-up e "
                "(4) O(valor × moedas) de tempo com O(valor) de espaço?",
            ),
        },
    ),
)

_SYSTEM_DESIGN: tuple[QuestionSeed, ...] = (
    # ------------------------------------------------------------------
    # system-design-interviews
    # ------------------------------------------------------------------
    QuestionSeed(
        code="system-design-interviews-q01",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=EASY,
        correct=("b",),
        tags=("requirements", "process"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="The interviewer says: \"Design a ride-sharing service.\" What is the best "
                "first move?",
                options=_options(
                    "Start drawing the database, cache and message queue you plan to use.",
                    "Ask clarifying questions about what the system must do and at what "
                    "scale, and agree on the scope.",
                    "Announce the technology stack you would pick and why.",
                    "Begin estimating how many petabytes of storage you will need.",
                ),
                explanation="System design prompts are deliberately vague, and interviewers "
                "grade whether you pin down functional and non-functional requirements before "
                "designing. Drawing components, choosing a stack or running numbers without "
                "agreed requirements means you are designing for an unknown problem.",
            ),
            Language.PT_BR: QuestionText(
                prompt="O entrevistador diz: \"Projete um serviço de caronas (ride-sharing).\" "
                "Qual é o melhor primeiro passo?",
                options=_options(
                    "Começar a desenhar o banco de dados, o cache e a fila de mensagens que "
                    "pretende usar.",
                    "Fazer perguntas de esclarecimento sobre o que o sistema deve fazer e em "
                    "que escala, e combinar o escopo.",
                    "Anunciar a stack de tecnologia que escolheria e por quê.",
                    "Começar a estimar quantos petabytes de armazenamento serão necessários.",
                ),
                explanation="Os enunciados de system design são vagos de propósito, e os "
                "entrevistadores avaliam se você define os requisitos funcionais e não "
                "funcionais antes de projetar. Desenhar componentes, escolher uma stack ou "
                "fazer contas sem requisitos combinados é projetar para um problema "
                "desconhecido.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q02",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=EASY,
        correct=("d",),
        tags=("estimation",),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="What is the main purpose of back-of-envelope estimation in a system "
                "design interview?",
                options=_options(
                    "To produce exact numbers that the interviewer will verify.",
                    "To show off your arithmetic speed.",
                    "To fill time while you think about the architecture.",
                    "To get order-of-magnitude figures (requests per second, storage, "
                    "bandwidth) that justify design choices such as caching or sharding.",
                ),
                explanation="Estimates matter because they drive decisions: a few hundred "
                "requests per second may fit on one database, while hundreds of thousands "
                "probably need caching and partitioning. Round numbers and clearly stated "
                "assumptions are fine; exactness is not the goal.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual é o principal objetivo da estimativa de \"guardanapo\" "
                "(back-of-envelope) em uma entrevista de system design?",
                options=_options(
                    "Produzir números exatos que o entrevistador vai conferir.",
                    "Mostrar sua rapidez de cálculo.",
                    "Preencher o tempo enquanto você pensa na arquitetura.",
                    "Obter ordens de grandeza (requisições por segundo, armazenamento, "
                    "banda) que justifiquem escolhas como cache ou sharding.",
                ),
                explanation="As estimativas importam porque guiam decisões: algumas centenas "
                "de requisições por segundo podem caber em um único banco, enquanto centenas de "
                "milhares provavelmente exigem cache e particionamento. Números redondos e "
                "premissas declaradas com clareza bastam; exatidão não é o objetivo.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q03",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=EASY,
        correct=("a",),
        tags=("requirements", "non-functional"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which of these is a **non-functional** requirement for a social feed?",
                options=_options(
                    "The feed loads within 300 ms for 99% of requests.",
                    "Users can follow and unfollow other users.",
                    "Users can attach a photo to a post.",
                    "Moderators can remove a post.",
                ),
                explanation="Non-functional requirements describe qualities such as latency, "
                "availability, consistency and scale. The other three describe things a user "
                "or moderator can do, which are functional requirements.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Qual destes é um requisito **não funcional** de um feed social?",
                options=_options(
                    "O feed carrega em até 300 ms em 99% das requisições.",
                    "Usuários podem seguir e deixar de seguir outros usuários.",
                    "Usuários podem anexar uma foto a uma publicação.",
                    "Moderadores podem remover uma publicação.",
                ),
                explanation="Requisitos não funcionais descrevem qualidades como latência, "
                "disponibilidade, consistência e escala. Os outros três descrevem coisas que "
                "um usuário ou moderador pode fazer, ou seja, requisitos funcionais.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q04",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("c",),
        tags=("trade-offs", "communication"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You proposed PostgreSQL for the main data store and the interviewer asks "
                "\"Why not a NoSQL database?\" Which answer is strongest?",
                options=_options(
                    "\"PostgreSQL is the industry standard, so it is the safe choice.\"",
                    "\"NoSQL does not scale, so I avoid it.\"",
                    "\"Our data is relational and we need transactions across entities. At "
                    "the estimated load a single primary with read replicas is enough, and "
                    "if writes grew far beyond that I would revisit partitioning or a "
                    "different store.\"",
                    "\"I have used PostgreSQL for years and know it best.\"",
                ),
                explanation="A strong answer ties the choice to the stated requirements "
                "(data shape, consistency, estimated load), acknowledges the cost, and says "
                "what would change the decision. 'Industry standard' and 'I know it best' are "
                "not requirements-based, and 'NoSQL does not scale' is both false and "
                "dismissive.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você propôs PostgreSQL como armazenamento principal e o entrevistador "
                "pergunta \"Por que não um banco NoSQL?\". Qual resposta é a mais forte?",
                options=_options(
                    "\"PostgreSQL é o padrão da indústria, então é a escolha segura.\"",
                    "\"NoSQL não escala, então eu evito.\"",
                    "\"Nossos dados são relacionais e precisamos de transações entre "
                    "entidades. Na carga estimada, um primário com réplicas de leitura é "
                    "suficiente, e se as escritas crescessem muito além disso eu revisitaria o "
                    "particionamento ou outro tipo de armazenamento.\"",
                    "\"Uso PostgreSQL há anos e é o que melhor conheço.\"",
                ),
                explanation="Uma resposta forte liga a escolha aos requisitos declarados "
                "(formato dos dados, consistência, carga estimada), reconhece o custo e diz o "
                "que mudaria a decisão. 'Padrão da indústria' e 'é o que melhor conheço' não "
                "se baseiam em requisitos, e 'NoSQL não escala' é falso e desdenhoso.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q05",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("a",),
        tags=("estimation", "qps"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="A service has 10 million daily active users, and each user performs "
                "about 5 writes per day. Which estimate of write load is most reasonable?",
                options=_options(
                    "Roughly 580 writes per second on average; plan for peaks a few times "
                    "higher.",
                    "Roughly 58 writes per second on average.",
                    "Roughly 5,800 writes per second on average.",
                    "Roughly 50 million writes per second.",
                ),
                explanation="10M × 5 = 50M writes per day. A day has about 86,400 seconds "
                "(close to 100,000 for quick math), so the average is about 580 writes per "
                "second. Real traffic is not flat, so mention a peak factor of two to three "
                "times. The other values are off by a factor of ten or by the whole day.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Um serviço tem 10 milhões de usuários ativos por dia, e cada usuário "
                "faz cerca de 5 escritas por dia. Qual estimativa de carga de escrita é a mais "
                "razoável?",
                options=_options(
                    "Cerca de 580 escritas por segundo em média; planejar picos algumas "
                    "vezes maiores.",
                    "Cerca de 58 escritas por segundo em média.",
                    "Cerca de 5.800 escritas por segundo em média.",
                    "Cerca de 50 milhões de escritas por segundo.",
                ),
                explanation="10M × 5 = 50M de escritas por dia. Um dia tem cerca de 86.400 "
                "segundos (perto de 100.000 para a conta rápida), então a média é de cerca de "
                "580 escritas por segundo. O tráfego real não é constante, então mencione um "
                "fator de pico de duas a três vezes. Os outros valores erram por um fator de "
                "dez ou pelo dia inteiro.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q06",
        competency_slug="system-design-interviews",
        type=MS,
        difficulty=MEDIUM,
        correct=("a", "b", "d"),
        tags=("process", "communication"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which behaviors help in a system design interview? Select all that "
                "apply.",
                options=_options(
                    "Stating your assumptions out loud and confirming them.",
                    "Asking the interviewer which component they would like to explore in "
                    "more depth.",
                    "Working through the estimates silently so you do not make mistakes in "
                    "front of the interviewer.",
                    "Naming at least one alternative for key decisions and why you did not "
                    "pick it.",
                    "Presenting the architecture of a famous system from memory, even when "
                    "the requirements differ.",
                ),
                explanation="Interviewers evaluate your reasoning, so make it visible: stated "
                "assumptions can be corrected early, checking in steers the conversation "
                "toward what matters to them, and alternatives show you understand trade-offs. "
                "Silent arithmetic hides your process, and a memorized architecture ignores "
                "the requirements actually agreed in this conversation.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Quais comportamentos ajudam em uma entrevista de system design? "
                "Selecione todos que se aplicam.",
                options=_options(
                    "Declarar suas premissas em voz alta e confirmá-las.",
                    "Perguntar ao entrevistador qual componente ele gostaria de explorar com "
                    "mais profundidade.",
                    "Fazer as estimativas em silêncio para não errar na frente do "
                    "entrevistador.",
                    "Citar pelo menos uma alternativa nas decisões-chave e por que não foi "
                    "escolhida.",
                    "Apresentar de memória a arquitetura de um sistema famoso, mesmo quando "
                    "os requisitos são diferentes.",
                ),
                explanation="Os entrevistadores avaliam seu raciocínio, então torne-o visível: "
                "premissas declaradas podem ser corrigidas cedo, perguntar direciona a conversa "
                "para o que importa a eles, e alternativas mostram que você entende os "
                "trade-offs. Contas em silêncio escondem seu processo, e uma arquitetura "
                "decorada ignora os requisitos combinados nesta conversa.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q07",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("d",),
        tags=("scaling", "trade-offs"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Midway through, the interviewer asks: \"What if traffic grows 10x?\" "
                "What is the best way to respond?",
                options=_options(
                    "Add sharding, a cache and a message queue everywhere, to be safe.",
                    "Say the design already scales and move on.",
                    "Start over with a distributed architecture from scratch.",
                    "Re-run the estimates, identify which component becomes the bottleneck "
                    "first, scale that one and say what stays unchanged.",
                ),
                explanation="Scaling questions test whether you can find the actual "
                "bottleneck (database writes, a hot key, network bandwidth) from your numbers "
                "and apply a targeted fix with its trade-offs. Adding everything is "
                "over-engineering, a bare assertion offers no reasoning, and a restart throws "
                "away a design that mostly holds.",
            ),
            Language.PT_BR: QuestionText(
                prompt="No meio da entrevista, o entrevistador pergunta: \"E se o tráfego "
                "crescer 10 vezes?\" Qual é a melhor forma de responder?",
                options=_options(
                    "Adicionar sharding, cache e fila de mensagens em todo lugar, por "
                    "segurança.",
                    "Dizer que o design já escala e seguir em frente.",
                    "Recomeçar com uma arquitetura distribuída do zero.",
                    "Refazer as estimativas, identificar qual componente vira o gargalo "
                    "primeiro, escalar esse e dizer o que permanece igual.",
                ),
                explanation="Perguntas de escala testam se você consegue achar o gargalo real "
                "(escritas no banco, uma hot key, banda de rede) a partir dos seus números e "
                "aplicar uma correção direcionada com seus trade-offs. Adicionar tudo é "
                "over-engineering, uma afirmação seca não mostra raciocínio, e recomeçar "
                "descarta um design que em grande parte se mantém.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q08",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("b",),
        tags=("process", "ambiguity"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Twenty minutes in, you realize you misunderstood a requirement and part "
                "of your design contradicts it. What should you do?",
                options=_options(
                    "Keep going and hope the interviewer does not notice.",
                    "Say so, confirm the correct requirement, and adjust only the affected "
                    "parts while explaining the impact.",
                    "Discard the whole design and restart from the requirements.",
                    "Argue that your interpretation was also reasonable.",
                ),
                explanation="Interviewers expect requirements to be revised during a real "
                "design discussion; what they evaluate is how you react. Naming the issue and "
                "repairing the affected components shows honesty and adaptability. Hiding it "
                "is worse, restarting wastes the time left, and defending a wrong reading "
                "turns a small slip into a communication problem.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Vinte minutos depois, você percebe que entendeu errado um requisito e "
                "parte do seu design o contradiz. O que fazer?",
                options=_options(
                    "Continuar e torcer para o entrevistador não perceber.",
                    "Dizer isso, confirmar o requisito correto e ajustar só as partes "
                    "afetadas, explicando o impacto.",
                    "Descartar o design inteiro e recomeçar pelos requisitos.",
                    "Argumentar que sua interpretação também era razoável.",
                ),
                explanation="Os entrevistadores esperam que os requisitos sejam revistos "
                "durante uma discussão de design real; o que avaliam é como você reage. Nomear "
                "o problema e corrigir os componentes afetados mostra honestidade e "
                "adaptabilidade. Esconder é pior, recomeçar desperdiça o tempo restante, e "
                "defender uma leitura errada transforma um deslize pequeno em um problema de "
                "comunicação.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q09",
        competency_slug="system-design-interviews",
        type=MC,
        difficulty=HARD,
        correct=("c",),
        tags=("deep-dive", "prioritization"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You have finished the high-level design of a chat application and have "
                "about 15 minutes left for deep dives. Which choice is strongest?",
                options=_options(
                    "Go deep on the component you know best, so you can answer follow-ups "
                    "confidently.",
                    "Spend one minute on each component so that everything is covered.",
                    "Propose one or two components where the hardest requirement-driven "
                    "trade-offs live (for example message delivery and ordering, or group "
                    "fan-out), and confirm the choice with the interviewer.",
                    "Detail the database schema, including every column and type.",
                ),
                explanation="Deep dives are chosen where the interesting trade-offs are, "
                "which come from the requirements, and the interviewer gets a say in what "
                "they want to see. Picking only what you know best may dodge the hard part, "
                "touching everything stays shallow, and exhaustive schema detail rarely "
                "reveals design judgment.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você terminou o design de alto nível de um aplicativo de chat e tem "
                "cerca de 15 minutos para os deep dives. Qual escolha é a mais forte?",
                options=_options(
                    "Aprofundar o componente que você conhece melhor, para responder com "
                    "segurança às perguntas seguintes.",
                    "Gastar um minuto em cada componente para cobrir tudo.",
                    "Propor um ou dois componentes onde estão os trade-offs mais difíceis "
                    "ditados pelos requisitos (por exemplo, entrega e ordenação de mensagens, "
                    "ou fan-out de grupos) e confirmar a escolha com o entrevistador.",
                    "Detalhar o schema do banco, com todas as colunas e tipos.",
                ),
                explanation="Os deep dives são escolhidos onde estão os trade-offs "
                "interessantes, que vêm dos requisitos, e o entrevistador opina sobre o que "
                "quer ver. Escolher só o que você domina pode desviar da parte difícil, tocar "
                "em tudo fica superficial, e detalhar todo o schema raramente revela "
                "julgamento de design.",
            ),
        },
    ),
    QuestionSeed(
        code="system-design-interviews-q10",
        competency_slug="system-design-interviews",
        type=SHORT,
        difficulty=HARD,
        correct=None,
        tags=("time-management", "process"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You have 45 minutes for the prompt \"design a rate limiter\". Outline "
                "how you would split your time, what you would produce in each phase, and how "
                "you would decide what to cut if time runs short.",
                model_answer="Roughly: 5-10 minutes on requirements (who is limited, per user "
                "or per IP, limits and window, hard or soft rejection, latency budget, "
                "single region or distributed) and a quick estimate of request volume; "
                "about 15 minutes on a high-level design (where the limiter sits, the "
                "algorithm choice such as token bucket or sliding window, where counters "
                "live, how rules are configured); 15 minutes on one or two deep dives chosen "
                "with the interviewer (for example consistency of counters across nodes, race "
                "conditions, failure behavior when the counter store is down); the last few "
                "minutes to summarize trade-offs and next steps. If time runs short, cut "
                "polish and secondary features first, keep the requirements and the core "
                "design, and say explicitly what you would add with more time.",
                explanation="Self-check: did you mention (1) requirements and estimation "
                "first, (2) a high-level design before deep dives, (3) deep dives chosen "
                "with the interviewer, and (4) a rule for what to cut that protects the core "
                "design and says out loud what is left out?",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você tem 45 minutos para o enunciado \"projete um rate limiter\". "
                "Descreva como dividiria o tempo, o que produziria em cada fase e como "
                "decidiria o que cortar se o tempo apertar.",
                model_answer="Aproximadamente: 5 a 10 minutos em requisitos (quem é limitado, "
                "por usuário ou por IP, limites e janela, rejeição rígida ou branda, "
                "orçamento de latência, região única ou distribuído) e uma estimativa rápida "
                "do volume de requisições; cerca de 15 minutos no design de alto nível (onde "
                "o limiter fica, a escolha do algoritmo, como token bucket ou sliding window, "
                "onde ficam os contadores, como as regras são configuradas); 15 minutos em um "
                "ou dois deep dives escolhidos com o entrevistador (por exemplo, consistência "
                "dos contadores entre nós, condições de corrida, comportamento quando o "
                "armazenamento dos contadores cai); os últimos minutos para resumir "
                "trade-offs e próximos passos. Se o tempo apertar, cortar primeiro o polimento "
                "e as funcionalidades secundárias, manter os requisitos e o design central e "
                "dizer explicitamente o que acrescentaria com mais tempo.",
                explanation="Autoavaliação: você mencionou (1) requisitos e estimativa "
                "primeiro, (2) design de alto nível antes dos deep dives, (3) deep dives "
                "escolhidos com o entrevistador e (4) uma regra de corte que protege o design "
                "central e diz em voz alta o que ficou de fora?",
            ),
        },
    ),
)

_BEHAVIORAL: tuple[QuestionSeed, ...] = (
    # ------------------------------------------------------------------
    # behavioral-interviews
    # ------------------------------------------------------------------
    QuestionSeed(
        code="behavioral-interviews-q01",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=EASY,
        correct=("c",),
        tags=("star", "structure"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="In a STAR answer (Situation, Task, Action, Result), which part should "
                "usually get the most of your time?",
                options=_options(
                    "Situation, so the interviewer understands the company's background.",
                    "Task, so the goal is stated in detail.",
                    "Action: what you personally did and why you chose it.",
                    "Result, repeated several times for emphasis.",
                ),
                explanation="Interviewers use behavioral questions to learn how you act, so "
                "the Action (your own decisions, trade-offs and reasoning) carries the most "
                "signal. Situation and Task should be brief, just enough context, and the "
                "Result should be concrete but concise.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Em uma resposta no método STAR (Situation, Task, Action, Result), qual "
                "parte normalmente deve ocupar a maior parte do seu tempo?",
                options=_options(
                    "Situation, para o entrevistador entender o contexto da empresa.",
                    "Task, para declarar o objetivo em detalhes.",
                    "Action: o que você mesmo fez e por que escolheu fazer assim.",
                    "Result, repetido várias vezes para dar ênfase.",
                ),
                explanation="Os entrevistadores usam perguntas comportamentais para entender "
                "como você age, então a Action (suas decisões, trade-offs e raciocínio) é a "
                "que mais informa. Situation e Task devem ser breves, só o contexto "
                "necessário, e o Result deve ser concreto, porém conciso.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q02",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=EASY,
        correct=("a",),
        tags=("failure", "self-awareness"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="An interviewer asks: \"Tell me about a time you failed.\" Which approach "
                "is best?",
                options=_options(
                    "Describe a real failure with genuine consequences, own your part in it, "
                    "and explain what you changed afterwards.",
                    "Describe a disguised strength, such as \"I care too much about quality.\"",
                    "Explain how outside circumstances made the failure unavoidable.",
                    "Say you cannot think of one, because you prepare carefully.",
                ),
                explanation="This question probes self-awareness and growth. A real failure, "
                "honest ownership and a concrete change in behavior show all of that. "
                "Disguised strengths and blame-shifting are easy to spot and read as a lack of "
                "reflection, and having no example suggests you have not taken risks or have "
                "not looked back at your work.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Um entrevistador pergunta: \"Conte sobre uma vez em que você "
                "falhou.\" Qual abordagem é a melhor?",
                options=_options(
                    "Descrever uma falha real, com consequências genuínas, assumir sua parte "
                    "nela e explicar o que você mudou depois.",
                    "Descrever uma qualidade disfarçada, como \"eu me importo demais com "
                    "qualidade\".",
                    "Explicar como circunstâncias externas tornaram a falha inevitável.",
                    "Dizer que não lembra de nenhuma, porque você se prepara com cuidado.",
                ),
                explanation="Essa pergunta avalia autoconsciência e crescimento. Uma falha "
                "real, a responsabilidade assumida com honestidade e uma mudança concreta de "
                "comportamento mostram tudo isso. Qualidades disfarçadas e transferência de "
                "culpa são fáceis de notar e passam falta de reflexão, e não ter exemplo "
                "sugere que você não assumiu riscos ou não revisitou seu trabalho.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q03",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=EASY,
        correct=("d",),
        tags=("star", "ownership"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You are describing a project a team of six delivered together. "
                "Interviewers keep asking \"but what did *you* do?\" What is the best way to "
                "tell the story?",
                options=_options(
                    "Use \"we\" throughout to show you are a team player.",
                    "Claim the whole result as your own so your impact is clear.",
                    "Skip the team context entirely and talk only about code.",
                    "Give the team context briefly, then say \"I\" for your own decisions "
                    "and actions, crediting teammates for theirs.",
                ),
                explanation="The interviewer is hiring you, not the team, so they need to "
                "see your specific contribution. Using only 'we' hides it, while taking credit "
                "for everything hurts credibility and signals poor collaboration. A short "
                "team context plus precise 'I' statements, with credit given where due, "
                "satisfies both needs.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você está descrevendo um projeto entregue por uma equipe de seis "
                "pessoas. Os entrevistadores insistem em perguntar \"mas o que *você* fez?\". "
                "Qual é a melhor forma de contar a história?",
                options=_options(
                    "Usar \"nós\" o tempo todo para mostrar que você trabalha bem em equipe.",
                    "Atribuir todo o resultado a si mesmo para deixar seu impacto claro.",
                    "Pular o contexto da equipe e falar apenas de código.",
                    "Dar o contexto da equipe rapidamente e então dizer \"eu\" para as suas "
                    "decisões e ações, dando crédito aos colegas pelas deles.",
                ),
                explanation="O entrevistador está contratando você, não a equipe, então "
                "precisa ver sua contribuição específica. Usar só 'nós' a esconde, enquanto "
                "levar crédito por tudo prejudica a credibilidade e sugere pouca "
                "colaboração. Um contexto curto da equipe com afirmações precisas em primeira "
                "pessoa, creditando os colegas quando cabe, atende as duas necessidades.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q04",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("b",),
        tags=("conflict", "collaboration"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="\"Tell me about a time you disagreed with a teammate.\" Interviewers "
                "look for a specific example, ownership of your own part, collaboration and a "
                "clear outcome. Which answer summary meets those criteria best?",
                options=_options(
                    "\"A colleague kept writing sloppy code. I told the team how careless "
                    "they were and eventually they changed.\"",
                    "\"We disagreed on whether to build a queue or call the service "
                    "directly. I asked about their constraints, realized I had underweighted "
                    "operational cost, and we agreed to prototype both and compare latency. "
                    "We shipped the simpler option, and we still pair on design reviews.\"",
                    "\"I have never had a real conflict; I get along with everyone.\"",
                    "\"I escalated to my manager right away and they decided for us.\"",
                ),
                explanation="The strongest answer is one concrete event, shows curiosity about "
                "the other view, admits where the narrator was wrong, uses evidence to resolve "
                "the disagreement and ends with a result and a healthy relationship. Venting "
                "about a colleague, claiming no conflicts, or immediate escalation each avoid "
                "showing how you handle disagreement yourself.",
            ),
            Language.PT_BR: QuestionText(
                prompt="\"Conte sobre uma vez em que você discordou de um colega.\" Os "
                "entrevistadores procuram um exemplo específico, responsabilidade pela sua "
                "parte, colaboração e um resultado claro. Qual resumo de resposta atende "
                "melhor a esses critérios?",
                options=_options(
                    "\"Um colega escrevia código descuidado. Eu disse ao time como ele era "
                    "relaxado e, com o tempo, ele mudou.\"",
                    "\"Discordamos sobre criar uma fila ou chamar o serviço diretamente. "
                    "Perguntei sobre as restrições dele, percebi que eu tinha subestimado o "
                    "custo operacional e combinamos prototipar as duas opções e comparar a "
                    "latência. Entregamos a opção mais simples e ainda fazemos design reviews "
                    "juntos.\"",
                    "\"Nunca tive um conflito de verdade; eu me dou bem com todo mundo.\"",
                    "\"Escalei para o meu gestor imediatamente e ele decidiu por nós.\"",
                ),
                explanation="A resposta mais forte é um evento concreto, mostra curiosidade "
                "pelo outro ponto de vista, admite onde o narrador errou, usa evidências para "
                "resolver a discordância e termina com um resultado e uma relação saudável. "
                "Desabafar sobre um colega, dizer que nunca houve conflito ou escalar de "
                "imediato evitam mostrar como você mesmo lida com discordâncias.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q05",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("d",),
        tags=("story-bank", "preparation"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You have a week to prepare for behavioral rounds that will cover "
                "conflict, failure, leadership, ambiguity and incidents. What is the most "
                "effective preparation?",
                options=_options(
                    "Write and memorize a word-for-word script for every question you can "
                    "think of.",
                    "Prepare one excellent story and reuse it for every question.",
                    "Prepare a different story for each possible question and never repeat "
                    "any.",
                    "Pick a handful of real, substantial experiences, map each to several "
                    "themes, and rehearse short versions you can emphasize differently.",
                ),
                explanation="A small story bank that covers multiple themes is flexible: the "
                "same project can illustrate ambiguity in one answer and leadership in "
                "another. Memorized scripts sound robotic and break when the question is "
                "phrased differently, a single story is repetitive, and trying to prepare a "
                "unique story per question is unrealistic.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você tem uma semana para se preparar para rodadas comportamentais que "
                "vão cobrir conflito, falha, liderança, ambiguidade e incidentes. Qual é a "
                "preparação mais eficaz?",
                options=_options(
                    "Escrever e decorar um roteiro palavra por palavra para cada pergunta "
                    "imaginável.",
                    "Preparar uma única história excelente e reutilizá-la em todas as "
                    "perguntas.",
                    "Preparar uma história diferente para cada pergunta possível e nunca "
                    "repetir nenhuma.",
                    "Escolher algumas experiências reais e substanciais, associar cada uma a "
                    "vários temas e ensaiar versões curtas que você possa enfatizar de formas "
                    "diferentes.",
                ),
                explanation="Um pequeno banco de histórias que cobre vários temas é flexível: "
                "o mesmo projeto pode ilustrar ambiguidade em uma resposta e liderança em "
                "outra. Roteiros decorados soam robóticos e falham quando a pergunta vem com "
                "outra formulação, uma única história é repetitiva, e preparar uma história "
                "única por pergunta é irrealista.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q06",
        competency_slug="behavioral-interviews",
        type=MS,
        difficulty=MEDIUM,
        correct=("a", "c", "e"),
        tags=("star", "answer-quality"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Which elements make a behavioral answer strong? Select all that apply.",
                options=_options(
                    "One specific, real situation with enough context to see what was at "
                    "stake.",
                    "A description of how you generally behave (\"I usually...\") instead of "
                    "a single event.",
                    "Your own decisions and the trade-offs you weighed.",
                    "Several minutes of background about the company and its products.",
                    "A concrete result, plus what you would do differently now.",
                ),
                explanation="Strong answers are anchored in one real event, show your "
                "reasoning and decisions, and close with a measurable result and a reflection. "
                "General statements about habits are unverifiable, and long background eats "
                "the time you need for the Action, which carries the most signal.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Quais elementos tornam forte uma resposta comportamental? Selecione "
                "todos que se aplicam.",
                options=_options(
                    "Uma situação real e específica, com contexto suficiente para ver o que "
                    "estava em jogo.",
                    "Uma descrição de como você costuma agir (\"eu normalmente...\") em vez "
                    "de um único evento.",
                    "Suas próprias decisões e os trade-offs que você ponderou.",
                    "Vários minutos de contexto sobre a empresa e seus produtos.",
                    "Um resultado concreto, mais o que você faria diferente hoje.",
                ),
                explanation="Respostas fortes se ancoram em um evento real, mostram seu "
                "raciocínio e suas decisões e terminam com um resultado mensurável e uma "
                "reflexão. Afirmações genéricas sobre hábitos não são verificáveis, e muito "
                "contexto consome o tempo da Action, que é a parte que mais informa.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q07",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("a",),
        tags=("honesty", "preparation"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You are asked to describe a time you led a project without formal "
                "authority, and no experience fits exactly. What should you do?",
                options=_options(
                    "Take a moment, pick the closest real experience, and say how it relates "
                    "to the question, noting any difference in context.",
                    "Invent a convincing story, since nobody can verify it.",
                    "Answer hypothetically with \"I would...\" and describe an ideal approach.",
                    "Say you have not had that experience and wait for the next question.",
                ),
                explanation="Pausing to choose a relevant real example is normal, and "
                "being open about the context gap is honest and still gives evidence. "
                "Invented stories collapse under follow-up questions and damage trust. "
                "Hypotheticals do not show past behavior, which is what the question tests, "
                "and giving up wastes the chance to show related strengths.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Pedem que você descreva uma vez em que liderou um projeto sem "
                "autoridade formal, e nenhuma experiência sua se encaixa exatamente. O que "
                "fazer?",
                options=_options(
                    "Pedir um momento, escolher a experiência real mais próxima e explicar "
                    "como ela se relaciona com a pergunta, apontando a diferença de contexto.",
                    "Inventar uma história convincente, já que ninguém pode verificar.",
                    "Responder de forma hipotética, com \"eu faria...\", descrevendo uma "
                    "abordagem ideal.",
                    "Dizer que não teve essa experiência e esperar a próxima pergunta.",
                ),
                explanation="Fazer uma pausa para escolher um exemplo real relevante é "
                "normal, e ser claro sobre a diferença de contexto é honesto e ainda traz "
                "evidência. Histórias inventadas desmoronam diante de perguntas de "
                "aprofundamento e minam a confiança. Hipóteses não mostram comportamento "
                "passado, que é o que a pergunta testa, e desistir desperdiça a chance de "
                "mostrar pontos fortes relacionados.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q08",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=MEDIUM,
        correct=("c",),
        tags=("result", "learning"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="You worked hard on a project that was cancelled before launch, and you "
                "want to use it for \"tell me about a challenging project.\" How should you "
                "handle the Result?",
                options=_options(
                    "Skip the Result and end the story at the last thing you built.",
                    "Say the project was a success because the team learned a lot, without "
                    "mentioning the cancellation.",
                    "State plainly that it was cancelled, say why you understand that "
                    "happened, and describe what you took from it and applied later.",
                    "Blame the leadership's decision and explain why they were wrong.",
                ),
                explanation="A mixed or negative outcome is acceptable if you are honest and "
                "reflective. Omitting the Result looks evasive, reframing a cancellation as a "
                "success is not credible, and blaming others shows poor judgment. Stating the "
                "outcome plainly and showing a concrete lesson you later applied turns it "
                "into evidence of growth.",
            ),
            Language.PT_BR: QuestionText(
                prompt="Você trabalhou duro em um projeto que foi cancelado antes do "
                "lançamento e quer usá-lo para \"conte sobre um projeto desafiador\". Como "
                "tratar o Result?",
                options=_options(
                    "Pular o Result e encerrar a história na última coisa que você "
                    "construiu.",
                    "Dizer que o projeto foi um sucesso porque a equipe aprendeu muito, sem "
                    "mencionar o cancelamento.",
                    "Dizer com clareza que foi cancelado, explicar por que entende que isso "
                    "aconteceu e descrever o que tirou dessa experiência e aplicou depois.",
                    "Culpar a decisão da liderança e explicar por que ela estava errada.",
                ),
                explanation="Um resultado misto ou negativo é aceitável se você for honesto "
                "e reflexivo. Omitir o Result parece evasivo, reapresentar um cancelamento "
                "como sucesso não é crível, e culpar outros mostra mau julgamento. Dizer o "
                "resultado com clareza e mostrar uma lição concreta que você aplicou depois "
                "o transforma em evidência de crescimento.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q09",
        competency_slug="behavioral-interviews",
        type=MC,
        difficulty=HARD,
        correct=("b",),
        tags=("judgment", "decision-making"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="\"Tell me about a decision you made with incomplete information.\" "
                "Which answer summary best shows sound judgment?",
                options=_options(
                    "\"I kept collecting data for three weeks until I was certain, then "
                    "decided.\"",
                    "\"I listed what I knew and did not know, chose the option that was "
                    "easiest to reverse, told stakeholders my confidence level and what would "
                    "make me change course, and reviewed the outcome at a set checkpoint.\"",
                    "\"I trusted my gut because of my experience, and it worked out.\"",
                    "\"I escalated so my manager would own the decision.\"",
                ),
                explanation="Incomplete information is the normal case, so good judgment is "
                "about bounding the risk: separating known from unknown, preferring "
                "reversible choices, communicating uncertainty and setting a checkpoint. "
                "Waiting for certainty has its own cost, a gut call that happened to work does "
                "not show a repeatable method, and escalating by default avoids ownership.",
            ),
            Language.PT_BR: QuestionText(
                prompt="\"Conte sobre uma decisão que você tomou com informação "
                "incompleta.\" Qual resumo de resposta melhor demonstra bom julgamento?",
                options=_options(
                    "\"Continuei coletando dados por três semanas até ter certeza e só "
                    "então decidi.\"",
                    "\"Listei o que eu sabia e o que não sabia, escolhi a opção mais fácil "
                    "de reverter, contei aos stakeholders meu nível de confiança e o que me "
                    "faria mudar de rumo, e revisei o resultado em um checkpoint "
                    "combinado.\"",
                    "\"Confiei na minha intuição por causa da minha experiência, e deu "
                    "certo.\"",
                    "\"Escalei para que meu gestor fosse o dono da decisão.\"",
                ),
                explanation="Informação incompleta é o caso normal, então bom julgamento é "
                "limitar o risco: separar o conhecido do desconhecido, preferir escolhas "
                "reversíveis, comunicar a incerteza e definir um checkpoint. Esperar certeza "
                "tem seu próprio custo, uma intuição que por acaso funcionou não mostra um "
                "método repetível, e escalar por padrão evita a responsabilidade.",
            ),
        },
    ),
    QuestionSeed(
        code="behavioral-interviews-q10",
        competency_slug="behavioral-interviews",
        type=SHORT,
        difficulty=HARD,
        correct=None,
        tags=("star", "communication", "stakeholders"),
        source=AI,
        text={
            Language.EN: QuestionText(
                prompt="Describe how you would structure a two-to-three-minute answer to "
                "\"Tell me about a time you had to deliver bad news to a stakeholder.\" What "
                "goes into each STAR part, and what would make the answer credible?",
                model_answer="Situation (a sentence or two): a real project with a date and "
                "stakes, and what went wrong, for example a delivery slipping because of an "
                "underestimated dependency. Task: you owned the communication and the "
                "recovery plan. Action (the longest part): you gathered the facts first, "
                "told the stakeholder early and directly instead of waiting, explained cause "
                "and impact without blaming individuals, and arrived with options and a "
                "recommendation; also mention one thing you would do better, such as raising "
                "the risk a week sooner. Result: the concrete outcome (the decision made, the "
                "new date and whether it held, what the stakeholder said or did afterward), "
                "plus what you changed in your process. Credibility comes from specific "
                "details, honest imperfection and an outcome that is not too tidy.",
                explanation="Self-check: did you include (1) a brief, specific situation, "
                "(2) your own actions: early, factual communication with options, (3) a "
                "concrete result and a lesson, and (4) honesty about what did not go "
                "perfectly?",
            ),
            Language.PT_BR: QuestionText(
                prompt="Descreva como você estruturaria uma resposta de dois a três minutos "
                "para \"Conte sobre uma vez em que você precisou dar uma má notícia a um "
                "stakeholder.\" O que entra em cada parte do STAR e o que tornaria a resposta "
                "crível?",
                model_answer="Situation (uma ou duas frases): um projeto real, com data e o "
                "que estava em jogo, e o que deu errado, por exemplo uma entrega atrasando "
                "por causa de uma dependência subestimada. Task: você era responsável pela "
                "comunicação e pelo plano de recuperação. Action (a parte mais longa): você "
                "levantou os fatos primeiro, avisou o stakeholder cedo e de forma direta em "
                "vez de esperar, explicou causa e impacto sem culpar pessoas e chegou com "
                "opções e uma recomendação; mencione também algo que faria melhor, como "
                "levantar o risco uma semana antes. Result: o desfecho concreto (a decisão "
                "tomada, a nova data e se foi cumprida, o que o stakeholder disse ou fez "
                "depois), mais o que você mudou no seu processo. A credibilidade vem de "
                "detalhes específicos, de imperfeição honesta e de um desfecho que não seja "
                "arrumado demais.",
                explanation="Autoavaliação: você incluiu (1) uma situação breve e específica, "
                "(2) suas próprias ações: comunicação cedo e baseada em fatos, com opções, "
                "(3) um resultado concreto e uma lição e (4) honestidade sobre o que não deu "
                "totalmente certo?",
            ),
        },
    ),
)

# @@COMMUNICATION@@

QUESTION_SET = SubjectQuestionSet(
    subject_slug="interview-preparation",
    questions=_CODING + _SYSTEM_DESIGN + _BEHAVIORAL,
)
