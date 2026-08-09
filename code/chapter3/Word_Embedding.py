import numpy as np

# Предположим, мы выучили упрощенный двумерный вектор слов.
embeddings = {
    "king": np.array([0.9, 0.8]),
    "queen": np.array([0.9, 0.2]),
    "man": np.array([0.7, 0.9]),
    "woman": np.array([0.7, 0.3])
}

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    return dot_product / norm_product

# king - man + woman
result_vec = embeddings["king"] - embeddings["man"] + embeddings["woman"]

# Вычислить сходство полученного вектора и «ферзя»
sim = cosine_similarity(result_vec, embeddings["queen"])

print(f"король — вектор результата мужчина + женщина: {result_vec}")
print(f"Результат аналогичен «королеве»: {sim:.4f}")