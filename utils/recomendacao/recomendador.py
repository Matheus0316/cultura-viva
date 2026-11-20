from django.core.cache import cache
from django.db.models import Count
from .atividade1 import Atividade1
from .atividade2 import similaridade
from .atividade3 import recomendar_produto
from artistas.models import Artista, SeguidorArtista
from grupos.models import Grupo
from perfil.models import SeguidorGrupo, Perfil

class RecomendadorCultural:
    def __init__(self):
        self.at1 = Atividade1()

    def _get_dados_brutos(self):
        dados = []
        # Artistas: (perfil_id, item_id, item_nome)
        for s in SeguidorArtista.objects.filter(artista__status='APPROVED').select_related('perfil', 'artista'):
            dados.append((str(s.perfil.id), f"ART:{s.artista.id}", s.artista.name))
        
        # Grupos: (perfil_id, item_id, item_nome)
        for s in SeguidorGrupo.objects.filter(grupo__status='APPROVED').select_related('perfil', 'grupo'):
            dados.append((str(s.perfil.id), f"GRP:{s.grupo.id}", s.grupo.name))
            
        return dados

    def recomendar(self, perfil_id, quantidade=20):
        perfil_id_str = str(perfil_id)
        cache_key = f"recom_cultural_{perfil_id_str}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result

        # 1. Recomendação Algorítmica (Colaborativa)
        dados = self._get_dados_brutos()
        resultados = []
        
        if dados:
            self.at1.processar_queryset(dados)
            if perfil_id_str in self.at1.map_c:
                cliente_idx = self.at1.map_c[perfil_id_str]
                sim = similaridade(self.at1.produtos, self.at1.clientes, self.at1.compras)
                recoms_raw = recomendar_produto(self.at1.produtos, self.at1.clientes, self.at1.compras, sim, cliente_idx, quantidade=quantidade)
                
                for item_id_prefixado in recoms_raw:
                    prefix, obj_id = item_id_prefixado.split(':', 1)
                    obj = self._get_object(prefix, obj_id)
                    if obj:
                        resultados.append({'tipo': 'artista' if prefix == 'ART' else 'grupo', 'objeto': obj})

        # 2. Recomendação Demográfica (Cold Start / Backfill)
        # Se tivermos menos que 8 itens (4 de cada), tentamos preencher
        if len(resultados) < 8:
            try:
                perfil = Perfil.objects.get(id=perfil_id)
                backfill = self._get_recomendacoes_demograficas(perfil, resultados)
                for item in backfill:
                    if len(resultados) >= quantidade:
                        break
                    # Evitar duplicados
                    if not any(r['objeto'].id == item['objeto'].id and r['tipo'] == item['tipo'] for r in resultados):
                        resultados.append(item)
            except Perfil.DoesNotExist:
                pass

        # Salvar no cache por 12 horas (43200 segundos)
        cache.set(cache_key, resultados, 43200)
        return resultados

    def _get_object(self, prefix, obj_id):
        try:
            if prefix == 'ART':
                return Artista.objects.get(id=obj_id, status='APPROVED')
            elif prefix == 'GRP':
                return Grupo.objects.get(id=obj_id, status='APPROVED')
        except:
            return None
        return None

    def _get_recomendacoes_demograficas(self, perfil, ja_recomendados):
        ids_pulados_art = [str(r['objeto'].id) for r in ja_recomendados if r['tipo'] == 'artista']
        ids_pulados_grp = [str(r['objeto'].id) for r in ja_recomendados if r['tipo'] == 'grupo']
        
        # Artistas que o perfil já segue
        seguindo_ids = list(SeguidorArtista.objects.filter(perfil=perfil).values_list('artista_id', flat=True))
        
        # Perfis similares (mesmo sexo, idade aproximada)
        perfis_similares = Perfil.objects.filter(
            sex=perfil.sex,
            age__gte=(perfil.age or 0) - 5,
            age__lte=(perfil.age or 100) + 5
        ).exclude(id=perfil.id)

        backfill = []
        
        # Top Artistas entre perfis similares
        top_artistas = Artista.objects.filter(
            seguidores__perfil__in=perfis_similares,
            status='APPROVED'
        ).exclude(
            id__in=seguindo_ids + ids_pulados_art
        ).annotate(num_seguidores=Count('seguidores')).order_by('-num_seguidores')[:5]
        
        for a in top_artistas:
            backfill.append({'tipo': 'artista', 'objeto': a})

        # Top Grupos entre perfis similares
        seguindo_grupos_ids = list(SeguidorGrupo.objects.filter(perfil=perfil).values_list('grupo_id', flat=True))
        top_grupos = Grupo.objects.filter(
            seguidores__perfil__in=perfis_similares,
            status='APPROVED'
        ).exclude(
            id__in=seguindo_grupos_ids + ids_pulados_grp
        ).annotate(num_seguidores=Count('seguidores')).order_by('-num_seguidores')[:5]

        for g in top_grupos:
            backfill.append({'tipo': 'grupo', 'objeto': g})

        return backfill
