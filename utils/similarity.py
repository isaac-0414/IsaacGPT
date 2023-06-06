import numpy as np
from numpy.linalg import norm

# dot product of two vectors
def dot_product_similarity(v1, v2): 
    return np.dot(v1, v2)

# cosine similarity of two vectors
def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (norm(v1) * norm(v2))