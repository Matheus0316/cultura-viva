def recomendar_produto(produtos, clientes, compras, matriz_similaridade, cliente_id, quantidade=None):

    clientes_similares = []

    for i in range(len(clientes)):
        if i != cliente_id and matriz_similaridade[cliente_id][i] < 1:
            clientes_similares.append(i)
    
    ranking_produtos = [1.0 for _ in range(len(produtos))]

    comprados_c = set(compras[cliente_id])

    for i in clientes_similares:
        score_similaridade = matriz_similaridade[cliente_id][i]

        for j in compras[i]:
            if j not in comprados_c:
                ranking_produtos[j] *= score_similaridade
    
    produto_ranking = [(i, ranking_produtos[i]) for i in range(len(produtos))]

    produto_ranking.sort(key=lambda x: x[1])

    recomendacao = []

    for produto_id, _ in produto_ranking:
        if produto_id not in comprados_c:
            recomendacao.append(produtos[produto_id])
        
        if quantidade and len(recomendacao) == quantidade:
            break

    return recomendacao

