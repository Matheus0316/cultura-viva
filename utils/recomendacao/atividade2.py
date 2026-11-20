from numba import njit
import numpy as np

def transposta(A):
    m = len(A)
    n = len(A[0])

    T = [[0]*m for _ in range(n)]

    for i in range(m):
        for j in range(n):
            T[j][i] = A[i][j]

    return T

@njit
def multiplica(A, B):
    m, n = A.shape
    _, p = B.shape

    C = np.zeros((m, p), dtype=np.uint16)

    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C

def similaridade(produtos, clientes, compras):
    import math
    matriz = [[0 for _ in range(len(produtos))] for _ in range(len(clientes))]
    for i in range(len(compras)):
        for j in range(len(compras[i])):
            matriz[i][compras[i][j]] = 1   
    matriz_t = transposta(matriz)

    matriz = np.array(matriz, dtype=np.uint8)
    matriz_t = np.array(matriz_t, dtype=np.uint8)

    intersecao = multiplica(matriz, matriz_t)
    intersecao = intersecao.tolist()
    
    compras_p_cliente = np.sum(matriz, axis=1)
    compras_p_cliente = compras_p_cliente.tolist()

    similar = [[0 for _ in range(len(clientes))] for _ in range(len(clientes))]

    for i in range(len(clientes)):
        for j in range(len(clientes)):
            if i == j:
                similar[i][j] = 0.0 # Ignorar auto-similaridade para recomendação
                continue
                
            norm_a = compras_p_cliente[i]
            norm_b = compras_p_cliente[j]
            
            if norm_a > 0 and norm_b > 0:
                # Similaridade de Cosseno: dot(A, B) / (sqrt(norm_a) * sqrt(norm_b))
                # Sendo dot(A, B) a interseção
                val = intersecao[i][j] / (math.sqrt(norm_a) * math.sqrt(norm_b))
                # Transformamos em "distância" para manter compatibilidade com atividade3 (menor é melhor)
                # O algoritmo original da atividade3.py usa `recomendar_produto` com `ranking_produtos[j] *= score_similaridade`
                # e ordena por `sort(key=lambda x: x[1])`. 
                # Se usarmos o valor bruto do cosseno (0 a 1), quanto MAIOR mais similar.
                # Mas atividade3 usa `score_similaridade` MULTIPLICANDO o ranking inicial (1.0).
                # Se score_similaridade for 0, o ranking vira 0 (melhor no sort ascendente).
                # Se score_similaridade for 1, o ranking continua 1 (pior no sort).
                # Portanto, para manter compatibilidade: 1 - Cosseno
                similar[i][j] = 1.0 - val
            else:
                similar[i][j] = 1.0 # Dissimilar absoluto
    return similar

def cliente_similar(matriz, cliente_id):
    sim = float('inf')
    sim_id = -1

    for i in range(len(matriz)):
        if i != cliente_id and matriz[cliente_id][i] < sim:
            sim = matriz[cliente_id][i]
            sim_id = i
    return sim_id
