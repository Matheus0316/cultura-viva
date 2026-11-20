import csv
class Atividade1:
    def __init__(self):
        self.clientes = []
        self.produtos = []
        self.map_c = {}
        self.map_p = {}
        self.compras = []
        self.data = []
    def processar_dados(self, arquivos):
        for arquivo in arquivos:
            with open(arquivo, encoding="utf-8") as f:
                leitor = csv.reader(f)
                next(leitor)
                
                for linha in leitor:
                    self.data.append((linha[1], linha[2], linha[3]))

                    if linha[1] not in self.map_c:
                        indice = len(self.clientes)
                        self.map_c[linha[1]] = indice
                        self.clientes.append(linha[1])

                    if linha[2] not in self.map_p:
                        indice = len(self.produtos)
                        self.map_p[linha[2]] = indice
                        self.produtos.append(linha[3])

        self._finalizar_processamento()

    def processar_queryset(self, queryset):
        """
        Processa dados vindo do Django QuerySet.
        queryset deve retornar triplas/tuplas: (perfil_id, item_id, item_nome)
        """
        for perfil_id, item_id, item_nome in queryset:
            self.data.append((perfil_id, item_id, item_nome))

            if perfil_id not in self.map_c:
                indice = len(self.clientes)
                self.map_c[perfil_id] = indice
                self.clientes.append(perfil_id)

            if item_id not in self.map_p:
                indice = len(self.produtos)
                self.map_p[item_id] = indice
                self.produtos.append(item_id)

        self._finalizar_processamento()

    def _finalizar_processamento(self):
        self.compras = [[] for _ in range(len(self.clientes))]
        for cliente, produto, _ in self.data:
            cliente_id = self.map_c[cliente]
            produto_id = self.map_p[produto]
            self.compras[cliente_id].append(produto_id)