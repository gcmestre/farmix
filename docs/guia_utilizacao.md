# Guia de Utilização — CompoundMeds

Manual de operação do sistema CompoundMeds para gestão de medicamentos manipulados em farmácia comunitária.

---

## Índice

1. [Matérias-Primas](#1-matérias-primas)
2. [Fornecedores](#2-fornecedores)
3. [Lotes e Stock](#3-lotes-e-stock)
4. [Formulações](#4-formulações)
5. [Calculadora de Batch](#5-calculadora-de-batch)
6. [Encomendas](#6-encomendas)
7. [Produção (Batches)](#7-produção-batches)
8. [Controlo de Qualidade](#8-controlo-de-qualidade)
9. [Custos e Faturação](#9-custos-e-faturação)
10. [Formulações FGP Pré-carregadas](#10-formulações-fgp-pré-carregadas)

---

## 1. Matérias-Primas

As matérias-primas são os ingredientes base utilizados na preparação dos medicamentos manipulados.

### Criar uma matéria-prima

1. Aceder a **Inventário > Matérias-Primas**
2. Clicar em **"+ Nova Matéria-Prima"**
3. Preencher os campos:
   - **Código** — Código interno (ex: `MP-001`)
   - **Nome** — Designação da matéria-prima (ex: "Ácido Salicílico")
   - **Número CAS** — Identificador Chemical Abstracts Service (ex: `69-72-7`)
   - **Unidade por defeito** — `g` (gramas), `mL` (mililitros), `un` (unidades)
   - **Stock mínimo** — Quantidade abaixo da qual o sistema gera alerta
   - **Ponto de reabastecimento** — Quantidade que dispara aviso de reposição
   - **Fornecedor preferencial** — Fornecedor habitual
   - **Substância controlada** — Assinalar se aplicável (Deliberação 1985/2015)
   - **Referência farmacopeica** — Ex: `FP X`, `Ph.Eur.`, `USP`

### Alertas automáticos

O sistema monitoriza continuamente:
- **Stock baixo** — Quando a quantidade em stock desce abaixo do mínimo definido
- **Lotes a expirar** — Lotes com validade próxima (30 dias)
- **Lotes expirados** — Lotes cuja validade já passou

---

## 2. Fornecedores

### Registar um fornecedor

1. Aceder a **Inventário > Fornecedores**
2. Clicar em **"+ Novo Fornecedor"**
3. Preencher: Nome, NIF, Email, Telefone, Morada
4. O fornecedor fica disponível para associar a lotes e matérias-primas

Cada fornecedor deve cumprir os requisitos da **Deliberação n.º 1497/2004** (condições exigidas aos fornecedores de matérias-primas).

---

## 3. Lotes e Stock

### Receção de um lote

Cada entrega de matéria-prima é registada como um **lote**:

1. Aceder a **Inventário > Matérias-Primas > [matéria-prima] > Lotes**
2. Clicar em **"+ Novo Lote"**
3. Preencher:
   - **Número de lote** — Número do lote do fornecedor
   - **Fornecedor** — Fornecedor de origem
   - **Quantidade inicial** — Quantidade recebida
   - **Data de receção** — Data em que foi recebido
   - **Data de validade** — Prazo de utilização
   - **Certificado de análise** — Carregar o certificado (PDF)
   - **Custo por unidade** — Preço por grama/mL (para cálculo de custos)
   - **Quarentena** — Assinalar se o lote necessita de libertação

### Gestão FEFO

O sistema utiliza automaticamente o método **FEFO** (First Expiry, First Out): ao consumir stock para produção, utiliza primeiro os lotes com validade mais próxima.

### Movimentos de stock

Todos os movimentos são registados automaticamente no livro de movimentos:
- **Receção** — Entrada de novo lote
- **Uso em produção** — Consumo durante fabrico de um batch
- **Ajuste** — Correções de inventário
- **Eliminação** — Descarte de material expirado ou contaminado
- **Devolução** — Material devolvido ao fornecedor

---

## 4. Formulações

Uma formulação é a "receita" de um medicamento manipulado. Define os ingredientes, quantidades e passos de preparação.

### Criar uma formulação

1. Aceder a **Produção > Formulações**
2. Clicar em **"+ Nova Formulação"**
3. Preencher:
   - **Código** — Código único (ex: `FGP-001`)
   - **Nome** — Nome da preparação (ex: "Pomada de Vaselina Salicilada 5%")
   - **Forma farmacêutica** — Pomada, Creme, Solução, Suspensão, Pasta, Cápsula, etc.
   - **Via de administração** — Cutânea, Oral, Auricular, Nasal, etc.
   - **Instruções de dosagem** — Posologia e modo de utilização
   - **Prazo de utilização (dias)** — Conforme FGP:
     - Preparações não aquosas: máximo **180 dias**
     - Preparações aquosas: máximo **14 dias** (conservar no frigorífico)
     - Outras: duração do tratamento, máximo **30 dias**
   - **Condições de conservação** — Ex: "Conservar a T < 25°C, ao abrigo da luz"
   - **Quantidade base** — Quantidade de referência da formulação (ex: `100`)
   - **Unidade base** — Unidade da quantidade base (ex: `g` ou `mL`)
   - **Multi-etapa** — Assinalar se a preparação tem fases distintas (ex: cremes O/A)

### Adicionar ingredientes

Após criar a formulação:

1. Na página de detalhe da formulação, clicar em **"+ Adicionar"** na secção de Ingredientes
2. Preencher:
   - **Matéria-prima** — Selecionar do inventário
   - **Quantidade** — Quantidade para a base definida (ex: 5g para base de 100g)
   - **Unidade** — `g`, `mL`, etc.
   - **Ingrediente ativo** — Assinalar se é o princípio ativo
   - **Ordem de adição** — Sequência de incorporação

### Adicionar passos de preparação

Cada formulação deve ter passos de preparação documentados conforme a **Portaria 594/2004**:

1. Na página de detalhe, secção "Passos"
2. Definir para cada passo:
   - **Número do passo** — Sequência (1, 2, 3...)
   - **Título** — Descrição curta (ex: "Fundir a vaselina")
   - **Descrição** — Procedimento detalhado
   - **Duração estimada** — Tempo previsto (ex: 10 minutos)

### Verificação de substâncias proibidas

O sistema verifica automaticamente se algum ingrediente da formulação está na lista de **substâncias proibidas** (Deliberação 1985/2015). Em caso de violação, é exibido um aviso.

---

## 5. Calculadora de Batch

A calculadora permite escalar automaticamente as quantidades de uma formulação para qualquer tamanho de batch.

### Como utilizar

1. Aceder a **Produção > Formulações > [formulação]**
2. Clicar no botão **"Calculadora de Batch"**
3. Introduzir a **quantidade desejada** (ex: `1000` para 1 kg)
4. Clicar em **"Calcular"**

### Resultado

O sistema apresenta:
- **Fator de escala** — Ex: 10x (de 100g para 1000g)
- **Tabela de ingredientes** com:
  - Quantidade original (para a base)
  - Quantidade calculada (para o batch pretendido)
  - Unidade
  - Indicação de ingrediente ativo
- **Peso total** do batch

### Exemplo prático

**Pomada de Vaselina Salicilada 5%** — Base: 100g

| Material | Base (100g) | Batch (1kg) |
|----------|------------|-------------|
| Ácido Salicílico | 5 g | 50 g |
| Vaselina Branca | 95 g | 950 g |
| **Total** | **100 g** | **1000 g** |

Fator de escala: **10x**

---

## 6. Encomendas

### Registar uma encomenda

1. Aceder a **Encomendas > Lista de Encomendas**
2. Clicar em **"+ Nova Encomenda"**
3. Preencher:
   - **Cliente** — Farmácia, instituição ou particular
   - **Origem** — WhatsApp, email, presencial, telefone
   - **Prioridade** — Baixa, normal, alta, urgente
   - **Itens** — Descrição do(s) manipulado(s), formulação associada, quantidade
   - **Receita médica** — Carregar ficheiro da prescrição

### Fluxo de estados

Uma encomenda passa pelos seguintes estados:

```
Novo Pedido → Aguarda Orçamento → Aguarda Receita → Pronto para Produção
→ Em Produção → Pronto → Concluído
```

Em qualquer momento pode ser **Cancelada** (exceto após conclusão).

### Prescrição (dados RGPD)

A prescrição contém dados sensíveis (nome e NIF do utente) protegidos pelo RGPD:
- Os dados são anonimizáveis após o período de retenção legal
- O sistema cumpre os requisitos da legislação portuguesa de proteção de dados

---

## 7. Produção (Batches)

Um batch é a produção efetiva de um medicamento manipulado.

### Criar um batch

1. Aceder a **Produção > Batches**
2. Clicar em **"+ Novo Batch"**
3. Preencher:
   - **Encomenda** — Encomenda associada
   - **Formulação** — Receita a seguir
   - **Quantidade produzida** — Quantidade total
   - **Unidade** — Unidade do produto final
   - **Data de validade** — Calculada com base no prazo da formulação
   - **Condições de conservação** — Pode sobrepor as da formulação
   - **Precauções especiais** — Se aplicável

O sistema gera automaticamente um **número de batch** no formato `BAT-AAAAMM-NNNN`.

### Fluxo de produção

```
Planeado → Em Produção → Controlo de Qualidade → Aprovado → Concluído
                                                → Rejeitado
```

- **Iniciar** — O técnico de laboratório inicia a produção
- **Registar passos** — Cada passo é registado com observações e hora
- **Enviar para CQ** — Após conclusão dos passos
- **Aprovar/Rejeitar** — Apenas o farmacêutico pode aprovar (Portaria 594/2004)
- **Concluir** — Batch aprovado pronto para dispensa

### Registo de materiais utilizados

Durante a produção, o sistema regista:
- Que **lotes** de matérias-primas foram utilizados
- Que **quantidade** de cada lote foi consumida
- Rastreabilidade completa do lote ao batch final

### Documentação do batch

Para cada batch é possível gerar:
- **Ficha de produção** (PDF) — Relatório completo com todos os dados
- **Rótulo** (PDF) — Para colar na embalagem do manipulado

---

## 8. Controlo de Qualidade

Conforme a **Portaria 594/2004**, cada batch deve ter um registo de controlo de qualidade.

### Realizar o CQ

1. Na página do batch, clicar em **"Controlo de Qualidade"**
2. Preencher:
   - **Aspeto** — Descrição visual (ex: "Pomada branca, homogénea")
   - **Odor** — Inodoro, característico, etc.
   - **Textura** — Lisa, granulosa, etc.
   - **pH** — Valor medido (se aplicável)
   - **Peso esperado** — Peso teórico do batch
   - **Peso real** — Peso medido
   - **Desvio** — Calculado automaticamente (tolerância: ±5%)
   - **Aprovado** — Sim/Não
   - **Observações** — Notas adicionais

O desvio de peso é calculado automaticamente: `|peso_real - peso_esperado| / peso_esperado × 100`

---

## 9. Custos e Faturação

### Cálculo de custos (Portaria 769/2004)

O preço de venda ao público dos manipulados é composto por:

1. **Custo das matérias-primas** — Calculado automaticamente a partir dos lotes consumidos
2. **Custo da embalagem** — Introduzido manualmente
3. **Honorários de preparação** — Introduzido manualmente
4. **Total** = Matérias-primas + Embalagem + Honorários

### Orçamentos e faturas

O sistema suporta:
- **Orçamentos** — Com linhas detalhadas e IVA
- **Faturas** — Com integração possível com Sipharma
- **Estados da fatura**: Rascunho → Enviada → Paga / Em atraso → Cancelada

---

## 10. Formulações FGP Pré-carregadas

O sistema inclui 10 formulações do **Formulário Galénico Português** pré-carregadas, prontas a utilizar:

| Código | Nome | Forma | Base | Prazo |
|--------|------|-------|------|-------|
| FGP-001 | Pomada de Vaselina Salicilada 5% | Pomada | 100 g | 180 dias |
| FGP-002 | Solução Alcoólica de Ácido Bórico à Saturação | Solução cutânea | 100 mL | 180 dias |
| FGP-003 | Creme de Permetrina 5% | Creme | 100 g | 90 dias |
| FGP-004 | Suspensão Oral de Trimetoprim 1% | Suspensão oral | 100 mL | 14 dias |
| FGP-005 | Solução de Minoxidil 5% | Solução cutânea | 100 mL | 180 dias |
| FGP-006 | Solução Oral de Propranolol 0.1% | Solução oral | 100 mL | 14 dias |
| FGP-007 | Pasta de Lassar (Pasta de Zinco) | Pasta | 100 g | 180 dias |
| FGP-008 | Creme Hidratante (Base de Beeler) | Creme | 100 g | 90 dias |
| FGP-009 | Solução de Ácido Salicílico 2% | Solução cutânea | 100 mL | 180 dias |
| FGP-010 | Suspensão Oral de Hidrocortisona 0.1% | Suspensão oral | 100 mL | 14 dias |

Cada formulação inclui ingredientes com quantidades e passos de preparação completos.

### Carregar as formulações FGP

Para carregar os dados de exemplo na base de dados:

```bash
python manage.py loaddata raw_materials_fgp
python manage.py loaddata formulations_fgp
```

Isto cria 24 matérias-primas e 10 formulações completas com ingredientes e passos.

### Prazos de utilização (FGP)

Regras gerais conforme o Formulário Galénico Português:

| Tipo de preparação | Prazo máximo |
|-------------------|-------------|
| Preparações não aquosas (líquidas e sólidas) | 6 meses |
| Preparações aquosas (a partir de substância ativa sólida) | 14 dias (conservar no frigorífico) |
| Outras preparações | Duração do tratamento, máximo 30 dias |

---

## Referências Legais

- **Decreto-Lei n.º 95/2004** — Prescrição e preparação de medicamentos manipulados
- **Portaria n.º 594/2004** — Boas Práticas na preparação de medicamentos manipulados
- **Portaria n.º 769/2004** — Cálculo do preço de venda ao público dos manipulados
- **Deliberação n.º 1985/2015** — Substâncias proibidas em manipulados
- **Deliberação n.º 1497/2004** — Condições exigidas aos fornecedores de matérias-primas
- **Formulário Galénico Português** (ANF, 2001/2005/2009) — Formulações oficinais
- **Farmacopeia Portuguesa X** — Monografias de matérias-primas
- **Regulamento Geral de Proteção de Dados (RGPD)** — Proteção de dados pessoais
