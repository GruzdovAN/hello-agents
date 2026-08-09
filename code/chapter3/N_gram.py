import collections

# Пример корпуса, соответствующего корпусу в приведенном выше объяснении случая
corpus = "datawhale agent learns datawhale agent works"
tokens = corpus.split()
total_tokens = len(tokens)

# --- Шаг 1. Вычислите P(datawhale) ---
count_datawhale = tokens.count('datawhale')
p_datawhale = count_datawhale / total_tokens
print(f"Шаг первый: P(datawhale) = {count_datawhale}/{total_tokens} = {p_datawhale:.3f}")

# --- Шаг 2. Вычислите P(agent|datawhale) ---
# Сначала вычислите биграммы для последующих шагов
bigrams = zip(tokens, tokens[1:])
bigram_counts = collections.Counter(bigrams)
count_datawhale_agent = bigram_counts[('datawhale', 'agent')]
# count_datawhale был рассчитан на первом этапе
p_agent_given_datawhale = count_datawhale_agent / count_datawhale
print(f"Шаг 2: P(agent|datawhale) = {count_datawhale_agent}/{count_datawhale} = {p_agent_given_datawhale:.3f}")

# --- Шаг 3: Вычислите P(обучается|агент) ---
count_agent_learns = bigram_counts[('agent', 'learns')]
count_agent = tokens.count('agent')
p_learns_given_agent = count_agent_learns / count_agent
print(f"Шаг 3: P(learns|agent) = {count_agent_learns}/{count_agent} = {p_learns_given_agent:.3f}")

# ---Наконец: умножьте вероятности ---
p_sentence = p_datawhale * p_agent_given_datawhale * p_learns_given_agent
print(f"Наконец: P('агент datawhale учится') ≈ {p_datawhale:.3f} * {p_agent_given_datawhale:.3f} * {p_learns_given_agent:.3f} = {p_sentence:.3f}")
