# repositories/auditoria_repository.py
from sqlalchemy import text
from config.database import SessionLocal

class AuditoriaRepository:
    def obter_dados_peps(self, referencia_inventario: str = None):
        query = text("""
        WITH dados_inventario AS (
            SELECT 
                id,
                data_fim_contagem 
            FROM inventario_estoque
            WHERE referencia = COALESCE(:referencia_inventario, 
                  (SELECT referencia 
                   FROM inventario_estoque 
                   ORDER BY data_fim_contagem DESC 
                   LIMIT 1))
        ),

        entradas_ordenadas AS (
            SELECT
                pfa.produto_id,
                ne.data_emissao,
                (ine.quantidade * pfa.quantidade_por_grade) AS quantidade_unidades,
                ine.valor AS valor_unitario,
                (ine.quantidade * pfa.quantidade_por_grade) * ine.valor AS valor_total_lote
            FROM
                itens_nota_entrada ine
            JOIN notas_entrada ne ON
                ine.nota_entrada_id = ne.id
            JOIN produto_fornecedor_associacao pfa ON
                ine.codigo_produto_fornecedor = pfa.codigo_produto_fornecedor
                AND ne.fornecedor_id = pfa.fornecedor_id,
                dados_inventario di
            WHERE
                ne.data_emissao <= di.data_fim_contagem
            ORDER BY
                ne.data_emissao ASC
        ),

        camadas_peps AS (
            SELECT
                produto_id,
                data_emissao,
                quantidade_unidades,
                valor_unitario,
                valor_total_lote,
                SUM(quantidade_unidades) OVER (
                    PARTITION BY produto_id
                    ORDER BY data_emissao ASC
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS quantidade_acumulada
            FROM
                entradas_ordenadas
        ),

        ultimo_inventario AS (
            SELECT
                ii.produto_id,
                SUM(ii.quantidade_contada) AS quantidade_inventario
            FROM
                itens_inventario ii,
                dados_inventario di
            WHERE
                ii.inventario_id = di.id
            GROUP BY
                ii.produto_id
        ),

        total_entradas_saidas AS (
            SELECT
                c.produto_id,
                SUM(c.quantidade_unidades) AS total_entradas,
                ui.quantidade_inventario,
                SUM(c.quantidade_unidades) - COALESCE(ui.quantidade_inventario, 0) AS quantidade_saida
            FROM
                camadas_peps c
            LEFT JOIN ultimo_inventario ui ON
                c.produto_id = ui.produto_id
            GROUP BY
                c.produto_id,
                ui.quantidade_inventario
        ),

        consumo_por_camada AS (
            SELECT
                c.produto_id,
                c.data_emissao,
                c.quantidade_unidades,
                c.valor_unitario,
                c.valor_total_lote,
                c.quantidade_acumulada,
                ts.quantidade_saida,
                CASE
                    WHEN ts.quantidade_saida >= c.quantidade_acumulada THEN c.quantidade_unidades
                    WHEN ts.quantidade_saida > COALESCE(LAG(c.quantidade_acumulada, 1) OVER (
                        PARTITION BY c.produto_id 
                        ORDER BY c.data_emissao
                    ), 0) 
                    THEN ts.quantidade_saida - COALESCE(LAG(c.quantidade_acumulada, 1) OVER (
                        PARTITION BY c.produto_id 
                        ORDER BY c.data_emissao
                    ), 0)
                    ELSE 0
                END AS quantidade_consumida
            FROM
                camadas_peps c
            LEFT JOIN total_entradas_saidas ts ON
                c.produto_id = ts.produto_id
        )

        SELECT
            cc.produto_id,
            p.nome,
            cc.data_emissao,
            cc.quantidade_unidades,
            cc.valor_unitario,
            cc.valor_total_lote,
            cc.quantidade_acumulada,
            ts.quantidade_saida,
            cc.quantidade_consumida,
            (cc.quantidade_unidades - cc.quantidade_consumida) AS saldo_remanescente,
            (cc.quantidade_consumida * cc.valor_unitario) AS valor_consumido,
            ((cc.quantidade_unidades - cc.quantidade_consumida) * cc.valor_unitario) AS valor_saldo_remanescente,
            di.data_fim_contagem AS data_corte_inventario
        FROM
            consumo_por_camada cc
        INNER JOIN produtos p ON
            p.id = cc.produto_id
        LEFT JOIN total_entradas_saidas ts ON
            ts.produto_id = cc.produto_id,
            dados_inventario di
        ORDER BY
            cc.produto_id,
            cc.data_emissao ASC;
        """)

        with SessionLocal() as session:
            result = session.execute(
                query, 
                {"referencia_inventario": referencia_inventario}
            )
            return [dict(row) for row in result.mappings()]