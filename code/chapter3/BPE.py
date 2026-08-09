import re, collections

def get_stats(vocab):
    """Статистическая частота пар слов"""
    pairs = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols)-1):
            pairs[symbols[i],symbols[i+1]] += freq
    return pairs

def merge_vocab(pair, v_in):
    """Объединить пары токенов"""
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

# Подготовьте корпус, добавьте </w> в конце каждого слова, чтобы обозначить конец, и сегментируйте символы.
vocab = {'h u g </w>': 1, 'p u g </w>': 1, 'p u n </w>': 1, 'b u n </w>': 1}
num_merges = 4 # Установите количество слияний

for i in range(num_merges):
    pairs = get_stats(vocab)
    if not pairs:
        break
    best = max(pairs, key=pairs.get)
    vocab = merge_vocab(best, vocab)
    print(f"{i+1}-е слияние: {best} -> {''.join(best)}")
    print(f"Новый список словаря (часть): {list(vocab.keys())}")
    print("-" * 20)
