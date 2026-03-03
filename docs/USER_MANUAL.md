# CompoundMeds - Manual do Utilizador

**Plataforma de Gestão de Medicamentos Manipulados**
Versão 1.0 | Fevereiro 2026

---

## Indice

1. [Introducao](#1-introducao)
2. [Acesso ao Sistema](#2-acesso-ao-sistema)
3. [Painel de Controlo (Dashboard)](#3-painel-de-controlo-dashboard)
4. [Gestao de Encomendas](#4-gestao-de-encomendas)
5. [Gestao de Clientes](#5-gestao-de-clientes)
6. [Producao](#6-producao)
7. [Formulacoes](#7-formulacoes)
8. [Controlo de Qualidade](#8-controlo-de-qualidade)
9. [Rotulo e Ficha de Preparacao](#9-rotulo-e-ficha-de-preparacao)
10. [Calculo de Custos](#10-calculo-de-custos)
11. [Inventario de Materias-Primas](#11-inventario-de-materias-primas)
12. [Gestao de Lotes](#12-gestao-de-lotes)
13. [Fornecedores](#13-fornecedores)
14. [Alertas de Inventario](#14-alertas-de-inventario)
15. [Substancias Proibidas](#15-substancias-proibidas)
16. [Orcamentos](#16-orcamentos)
17. [Faturacao](#17-faturacao)
18. [Administracao do Sistema](#18-administracao-do-sistema)
19. [Perfis e Permissoes](#19-perfis-e-permissoes)
20. [Conformidade Regulatoria](#20-conformidade-regulatoria)

---

## 1. Introducao

O CompoundMeds e uma plataforma de gestao integrada para farmacias de manipulacao, desenvolvida em conformidade com a legislacao portuguesa:

- **Portaria 594/2004** - Boas Praticas de Preparacao (Ficha de Preparacao, CQ, rotulagem, rastreabilidade)
- **Decreto-Lei 95/2004** - Requisitos de prescricao e responsabilidades do farmaceutico
- **Portaria 769/2004** - Formula de calculo de preco (honorarios + materias-primas + embalagem)
- **Deliberacao 1985/2015** - Lista de substancias proibidas
- **RGPD** - Protecao de dados pessoais

### Funcionalidades Principais

| Modulo | Descricao |
|--------|-----------|
| Encomendas | Gestao completa do ciclo de encomendas |
| Producao | Controlo de lotes de producao com fluxo de estados |
| Formulacoes | Receitas com ingredientes e procedimentos passo a passo |
| Controlo de Qualidade | Verificacoes organolepticas, pH e peso/volume |
| Inventario | Gestao de materias-primas, lotes e movimentos de stock |
| Faturacao | Orcamentos e faturas integrados com encomendas |
| Administracao | Gestao de utilizadores, registo de auditoria, conformidade RGPD |

---

## 2. Acesso ao Sistema

### 2.1 Iniciar Sessao

1. Aceda ao endereco da aplicacao no navegador
2. Introduza o seu **e-mail** e **palavra-passe**
3. Clique em **Iniciar sessao**

> Se nao possui credenciais, contacte o administrador do sistema.

### 2.2 Terminar Sessao

1. Clique no seu nome no canto superior direito
2. Selecione **Terminar sessao**

### 2.3 Alterar Palavra-passe

1. Clique no seu nome no canto superior direito
2. Selecione **Perfil**
3. Clique em **Alterar Palavra-passe**
4. Preencha a palavra-passe atual e a nova palavra-passe
5. Clique em **Guardar**

### 2.4 Editar Perfil

1. Aceda a **Perfil** pelo menu do utilizador
2. Atualize os campos desejados (nome, telefone, idioma)
3. Clique em **Guardar**

---

## 3. Painel de Controlo (Dashboard)

O painel principal apresenta uma visao geral do estado da farmacia com cartoes de resumo:

| Cartao | Descricao | Visivel para |
|--------|-----------|--------------|
| Encomendas Pendentes | Numero de encomendas a aguardar acao | Admin, Farmaceutico, Rececao |
| Em Producao | Lotes atualmente em producao | Admin, Farmaceutico, Rececao |
| Alertas de Stock Baixo | Materiais abaixo do minimo | Admin, Farmaceutico |
| Faturas por Pagar | Faturas em estado "Enviada" ou "Vencida" | Admin, Farmaceutico |

Cada cartao inclui um link **Ver todos** para aceder ao modulo respetivo.

---

## 4. Gestao de Encomendas

### 4.1 Fluxo de Estados

Uma encomenda segue o seguinte ciclo de vida:

```
Novo Pedido → A Aguardar Orcamento → A Aguardar Receita → Pronto para Producao → Em Producao → Pronto → Concluido
```

Em qualquer estado (ate "Em Producao") e possivel **Cancelar** ou marcar como **Erro**.

### 4.2 Listar Encomendas

1. No menu lateral, clique em **Encomendas** > **Todas as Encomendas**
2. Utilize os filtros disponíveis:
   - **Estado** - Filtrar por estado da encomenda
   - **Cliente** - Filtrar por cliente
   - **Prioridade** - Baixa, Normal, Alta, Urgente
   - **Origem** - E-mail, Telefone, WhatsApp, Presencial
   - **Data** - Intervalo de datas

### 4.3 Criar Nova Encomenda

1. Na lista de encomendas, clique em **Nova Encomenda**
2. Preencha os campos:
   - **Cliente** (obrigatorio) - Selecione o cliente
   - **Origem** - Canal de entrada (e-mail, telefone, etc.)
   - **Prioridade** - Nivel de urgencia
   - **Atribuido a** - Responsavel pela encomenda
   - **Ficheiro de receita** - Upload da prescricao (opcional)
   - **Notas** - Observacoes adicionais
3. Clique em **Guardar**

### 4.4 Ver Detalhes da Encomenda

A pagina de detalhes mostra:

- **Cabecalho**: Numero, cliente, origem, estado e prioridade
- **Itens**: Lista de produtos/manipulados encomendados
- **Acoes de Estado**: Botoes para avancar no fluxo (ex: "→ A Aguardar Orcamento")
- **Cronologia**: Historico de alteracoes de estado com data e utilizador
- **Detalhes**: Atribuido a, data de criacao

### 4.5 Adicionar Itens a uma Encomenda

1. Na pagina de detalhes da encomenda, clique em **+ Adicionar Item**
2. Preencha: Descricao, Quantidade, Unidade, Preco Unitario
3. Clique em **Adicionar**

### 4.6 Atualizar Estado

1. Na pagina de detalhes, localize a secao **Acoes de Estado** na barra lateral
2. Clique no botao correspondente a transicao desejada
3. O sistema atualiza o estado e regista a alteracao na cronologia

### 4.7 Exportar Encomendas

1. Na lista de encomendas, clique em **Exportar CSV** (disponivel para Admin e Farmaceutico)

---

## 5. Gestao de Clientes

### 5.1 Listar Clientes

1. Menu lateral: **Encomendas** > **Clientes**
2. Utilize a barra de pesquisa para procurar por nome

### 5.2 Criar Cliente

1. Clique em **Novo Cliente**
2. Preencha: Nome, Tipo (Farmacia/Instituicao/Particular), NIF, E-mail, Telefone, Codigo Infarmed
3. Clique em **Guardar**

### 5.3 Detalhes do Cliente

A pagina mostra:
- Informacao de contacto (e-mail, telefone, codigo Infarmed)
- Encomendas recentes associadas ao cliente

---

## 6. Producao

### 6.1 Fluxo de Producao

Um lote de producao segue o seguinte ciclo:

```
Planeado → Em Curso → Controlo de Qualidade → Aprovado → Concluido
                                             ↘ Rejeitado
```

**Regras importantes:**
- Apenas um **Farmaceutico** ou **Administrador** pode aprovar um lote
- A aprovacao requer um **Controlo de Qualidade aprovado**
- Tecnicos de laboratorio **nao** podem aprovar lotes

### 6.2 Listar Lotes de Producao

1. Menu lateral: **Producao** > **Lotes**
2. Filtre por estado utilizando as abas no topo da pagina

### 6.3 Criar Novo Lote

1. Clique em **Novo Lote**
2. Preencha:
   - **Encomenda** - Selecione a encomenda associada
   - **Formulacao** - Selecione a formulacao/receita
   - **Quantidade Produzida** e **Unidade**
   - **Data de Validade**
   - **Produzido por** - Tecnico responsavel
   - **Condicoes de Armazenamento** (opcional - sobrepoe a formulacao)
   - **Precaucoes Especiais** (opcional)
3. Clique em **Guardar**

O sistema gera automaticamente um numero de lote no formato `BAT-AAAAMM-0001`.

### 6.4 Detalhes do Lote

A pagina de detalhes apresenta:

**Area Principal:**
- **Passos de Producao** - Lista numerada com estado de conclusao (checkmark verde = concluido)
- **Utilizacao de Material** - Tabela com materias-primas utilizadas, lote de origem e quantidade
- **Avisos de Substancias Proibidas** - Alerta vermelho se a formulacao contem substancias da lista da Deliberacao 1985/2015
- **Controlo de Qualidade** - Resumo do CQ ou botao para registar
- **Discriminacao de Custos** - Materias-primas, embalagem, honorarios e total

**Barra Lateral:**
- **Acoes de Estado** - Botoes para transicoes de estado
- **Detalhes** - Produzido por, verificado por, validade, quantidade

**Botoes de Acao (cabecalho):**
- **Relatorio PDF** - Gera a Ficha de Preparacao completa
- **Rotulo** - Gera rotulo de 100x70mm
- **Custo** - Calcula o custo do lote

### 6.5 Concluir Passos de Producao

1. Na pagina de detalhes do lote, localize o passo a concluir
2. Clique no botao **Concluir** ao lado do passo
3. Preencha as **observacoes** e eventuais **parametros**
4. Clique em **Marcar como Concluido**

O sistema regista automaticamente quem executou o passo e a data/hora.

### 6.6 Avancar Estado do Lote

1. Na secao **Acoes de Estado**, clique na transicao desejada:
   - **Planeado** → Clique "→ In_Progress" para iniciar
   - **Em Curso** → Clique "→ Quality_Check" para enviar para CQ
   - **Controlo de Qualidade** → Clique "→ Approved" (requer farmaceutico + CQ aprovado) ou "→ Rejected"
   - **Aprovado** → Clique "→ Complete" para concluir

---

## 7. Formulacoes

### 7.1 Listar Formulacoes

1. Menu lateral: **Producao** > **Formulacoes**
2. Visualize a lista com codigo, nome, forma farmaceutica e prazo de validade

### 7.2 Criar Formulacao

1. Clique em **Nova Formulacao** (apenas Farmaceutico/Admin)
2. Preencha:
   - **Codigo** - Codigo unico (ex: F-001)
   - **Nome** - Nome da formulacao
   - **Forma Farmaceutica** - Creme, capsula, solucao, etc.
   - **Via de Administracao** - Oral, topica, nasal, etc.
   - **Posologia** - Instrucoes de dosagem
   - **Multi-fase** - Se a preparacao envolve multiplas etapas
   - **Prazo de Validade** - Em dias
   - **Condicoes de Armazenamento** - Ex: "Conservar entre 15-25C"
3. Clique em **Guardar**

### 7.3 Adicionar Ingredientes

1. Na pagina de detalhes da formulacao, clique em **+ Adicionar**
2. Preencha:
   - **Materia-prima** - Selecione do inventario
   - **Quantidade** e **Unidade**
   - **Substancia ativa** - Marque se e o principio ativo
   - **Ordem de adicao** - Sequencia de incorporacao
3. Clique em **Guardar**

### 7.4 Passos do Procedimento

Os passos de producao sao definidos na formulacao e replicados para cada lote. Cada passo inclui:
- Numero do passo
- Titulo
- Descricao detalhada
- Duracao estimada

---

## 8. Controlo de Qualidade

### 8.1 Registar Controlo de Qualidade

1. Na pagina de detalhes do lote, clique em **Registar CQ** (ou aceda por **Lotes** > selecione lote > **CQ**)
2. Preencha os campos:

**Verificacoes Organolepticas:**
- **Aspeto** (obrigatorio) - Descricao visual (ex: "Creme branco, homogeneo")
- **Odor** - Descricao olfativa
- **Textura** - Descricao tactil

**Medicoes:**
- **Valor de pH** - Medicao do pH
- **Peso Esperado** - Peso/volume teorico
- **Peso Real** - Peso/volume medido

**Resultado:**
- **Aprovado** - Marque se o CQ passou
- **Observacoes** - Notas adicionais

3. Clique em **Guardar Registo de CQ**

> O sistema calcula automaticamente o **desvio percentual de peso** com base nos valores esperado e real.

### 8.2 Consultar Resultados do CQ

1. Na pagina de detalhes do lote, clique em **Ver relatorio de CQ completo**
2. A pagina mostra todos os dados registados, o resultado (Aprovado/Reprovado), quem realizou e quando

---

## 9. Rotulo e Ficha de Preparacao

### 9.1 Gerar Rotulo do Medicamento Manipulado

1. Na pagina de detalhes do lote, clique em **Rotulo**
2. O sistema gera um PDF com formato 100x70mm contendo:
   - Cabecalho **"Medicamento Manipulado"**
   - Nome da farmacia e numero ANF
   - Nome do utente
   - Nome da formulacao e forma farmaceutica
   - Via de administracao e posologia
   - Numero de lote e data de validade
   - Condicoes de conservacao
   - Aviso **"Manter fora do alcance das criancas"**

> A data de geracao do rotulo e registada automaticamente no lote.

### 9.2 Gerar Ficha de Preparacao (PDF)

1. Na pagina de detalhes do lote, clique em **Relatorio PDF**
2. O sistema gera a Ficha de Preparacao conforme a Portaria 594/2004, incluindo:
   - **Cabecalho da Farmacia** - Nome, numero ANF, morada, NIF, diretor tecnico
   - **Designacao**: "Medicamento Manipulado"
   - **Dados da Preparacao** - Numero de lote, formulacao, forma farmaceutica, via de administracao, quantidade, validade, condicoes de armazenamento
   - **Dados da Prescricao** - Nome do utente, NIF, morada, medico prescritor e cedula
   - **Materias-Primas Utilizadas** - Rastreabilidade completa (nome, lote, fornecedor, quantidade)
   - **Procedimento de Preparacao** - Passos executados com responsavel e data/hora
   - **Controlo de Qualidade** - Resultado, verificacoes organolepticas, pH, peso, desvio
   - **Calculo de Preco** - Discriminacao segundo Portaria 769/2004
   - **Areas de Assinatura** - Preparado por / Verificado por

---

## 10. Calculo de Custos

### 10.1 Calcular Custo do Lote

O calculo segue a formula da **Portaria 769/2004**:

```
Preco = Materias-Primas + Embalagem + Honorarios de Preparacao
```

1. Na pagina de detalhes do lote, clique em **Custo**
2. O sistema calcula automaticamente o **custo de materias-primas** com base em:
   - Quantidade utilizada de cada materia-prima
   - Custo por unidade registado no lote de origem
3. Preencha os campos adicionais:
   - **Custo de Embalagem** - Material de embalagem
   - **Honorarios de Preparacao** - Honorarios do farmaceutico
4. Clique em **Calcular Total**

O resultado e guardado e apresentado na secao **Discriminacao de Custos** da pagina de detalhes do lote e na Ficha de Preparacao.

---

## 11. Inventario de Materias-Primas

### 11.1 Listar Materiais

1. Menu lateral: **Inventario** > **Materiais**
2. Pesquise por codigo ou nome na barra de pesquisa
3. A tabela mostra:
   - Codigo e Nome
   - Indicador de **Substancia Controlada** (se aplicavel)
   - Unidade base
   - **Stock atual** (a vermelho se abaixo do minimo)
   - Fornecedor preferencial

### 11.2 Criar Material

1. Clique em **Novo Material** (apenas Farmaceutico/Admin)
2. Preencha:
   - **Codigo** - Codigo unico (ex: RM-001)
   - **Nome** - Nome do material
   - **Numero CAS** - Identificacao quimica (Chemical Abstracts Service)
   - **Unidade predefinida** - g, mL, un, etc.
   - **Substancia controlada** - Marque se aplicavel
   - **Stock minimo** - Quantidade minima antes de alerta
   - **Ponto de reposicao** - Quantidade para reposicao
   - **Fornecedor preferencial** - Selecione da lista
   - **Referencia Farmacopeia** - Ex: "FP X", "Ph.Eur.", "USP"
3. Clique em **Guardar**

### 11.3 Detalhes do Material

A pagina mostra:
- **Informacao de Stock**: Stock atual, minimo, ponto de reposicao, fornecedor
- **Lotes Ativos**: Todos os lotes disponiveis com quantidades e validades
- **Movimentos Recentes**: Ultimos 20 movimentos de stock

### 11.4 Exportar Inventario

1. Na lista de materiais, clique em **Exportar CSV**
2. O ficheiro CSV inclui: Codigo, Nome, Unidade, Stock Atual, Stock Minimo, Ponto de Reposicao, Fornecedor, Controlada, Stock Baixo

---

## 12. Gestao de Lotes

### 12.1 Politica FEFO

O sistema utiliza a politica **FEFO** (First Expiry, First Out) - os lotes com validade mais proxima sao consumidos primeiro na producao.

### 12.2 Listar Lotes

1. Menu lateral: **Inventario** > **Lotes**
2. Filtre por estado: Todos, Ativos, Em Quarentena, Esgotados
3. Os lotes sao apresentados por ordem de validade (mais proximos primeiro)

### 12.3 Rececionar Lote

1. Clique em **Rececionar Lote** (Lab Technician/Farmaceutico/Admin)
2. Preencha:
   - **Materia-prima** - Selecione o material
   - **Numero do Lote** - Identificacao do fornecedor
   - **Fornecedor** - Selecione da lista
   - **Quantidade Inicial** e **Quantidade Atual**
   - **Data de Rececao** e **Data de Validade**
   - **Certificado de Analise** - Upload do documento (opcional)
   - **Custo por Unidade** - Custo unitario (para calculo de custos da producao)
   - **Em Quarentena** - Marque se o lote necessita de aprovacao antes de uso
3. Clique em **Guardar**

O sistema cria automaticamente um **movimento de stock** de tipo "Rececao".

### 12.4 Detalhes do Lote

A pagina mostra:
- Informacoes do lote (material, fornecedor, quantidades, datas)
- Estado atual (Ativo / Em Quarentena / Esgotado)
- **Historico de Movimentos** - Tabela com todos os movimentos:
  - Data, Tipo, Quantidade (verde = entrada, vermelho = saida), Saldo, Utilizador

### 12.5 Ajustar Stock

1. Na pagina de detalhes do lote, clique em **Ajustar**
2. Introduza:
   - **Quantidade** - Positivo para adicionar, negativo para subtrair
   - **Notas** - Justificacao do ajuste
3. Clique em **Ajustar**

> Se a quantidade resultante chegar a zero, o lote e marcado automaticamente como **esgotado**.

### 12.6 Libertar Lote da Quarentena

1. Na pagina de detalhes de um lote em quarentena, clique em **Libertar**
2. Confirme a acao

> Apenas **Farmaceuticos** e **Administradores** podem libertar lotes da quarentena.

---

## 13. Fornecedores

### 13.1 Listar Fornecedores

1. Menu lateral: **Inventario** > **Fornecedores**
2. Pesquise por nome na barra de pesquisa

### 13.2 Criar Fornecedor

1. Clique em **Novo Fornecedor** (apenas Farmaceutico/Admin)
2. Preencha: Nome, NIF, E-mail, Telefone, Morada, Ativo
3. Clique em **Guardar**

### 13.3 Detalhes do Fornecedor

A pagina mostra:
- Informacao de contacto
- Lotes recentes fornecidos

---

## 14. Alertas de Inventario

1. Menu lateral: **Inventario** > **Alertas**
2. A pagina apresenta tres secoes:

| Secao | Cor | Descricao |
|-------|-----|-----------|
| Materiais com Stock Baixo | Vermelho | Materiais com stock atual abaixo do minimo configurado |
| A Expirar em Breve (30 dias) | Amarelo | Lotes com validade nos proximos 30 dias |
| Lotes Expirados | Vermelho | Lotes com validade ultrapassada |

Cada item inclui link direto para o material ou lote respetivo.

---

## 15. Substancias Proibidas

### 15.1 Consultar Lista

1. Menu lateral: **Inventario** > **Substancias Proibidas**
2. A lista mostra: Nome, Numero CAS, Regulamentacao

### 15.2 Adicionar Substancia

1. Clique em **Adicionar Substancia** (apenas Farmaceutico/Admin)
2. Preencha:
   - **Nome** - Nome da substancia
   - **Numero CAS** - Identificacao CAS
   - **Regulamentacao** - Ex: "Deliberacao 1985/2015"
3. Clique em **Guardar**

### 15.3 Verificacao Automatica

O sistema verifica automaticamente cada formulacao contra a lista de substancias proibidas. A verificacao e feita por:
- **Numero CAS** - Correspondencia exata
- **Nome** - Correspondencia por nome (insensivel a maiusculas/minusculas)

Se uma formulacao contem substancias proibidas, um **alerta vermelho** e apresentado na pagina de detalhes do lote de producao.

---

## 16. Orcamentos

### 16.1 Listar Orcamentos

1. Menu lateral: **Faturacao** > **Orcamentos**

### 16.2 Criar Orcamento

1. Clique em **Novo Orcamento** (apenas Farmaceutico/Admin)
2. Preencha: Encomenda, Cliente, Valido ate, Notas
3. Clique em **Guardar**

### 16.3 Adicionar Linhas

1. Na pagina de detalhes do orcamento, clique em **+ Adicionar Linha**
2. Preencha: Descricao, Quantidade, Unidade, Preco Unitario, Taxa IVA
3. Clique em **Adicionar**

### 16.4 Converter em Fatura

1. Na pagina de detalhes do orcamento, clique em **Converter em Fatura**
2. O sistema cria automaticamente uma fatura com todas as linhas do orcamento

---

## 17. Faturacao

### 17.1 Fluxo de Faturacao

```
Rascunho → Enviada → Paga
                   ↘ Vencida → Paga
Qualquer estado → Cancelada
```

### 17.2 Listar Faturas

1. Menu lateral: **Faturacao** > **Faturas**
2. Filtre por estado: Todas, Rascunho, Enviada, Paga, Vencida, Cancelada

### 17.3 Criar Fatura

1. Clique em **Nova Fatura** (apenas Farmaceutico/Admin)
2. Preencha: Encomenda, Cliente, Data de Vencimento, Notas
3. Clique em **Guardar**

### 17.4 Gerir Estado da Fatura

Na pagina de detalhes, utilize os botoes de acao:

| Estado Atual | Acoes Disponiveis |
|--------------|-------------------|
| Rascunho | Enviar, Cancelar |
| Enviada | Marcar Paga, Marcar Vencida, Cancelar |
| Vencida | Marcar Paga |

### 17.5 Adicionar Linhas

1. Clique em **+ Adicionar Linha**
2. Preencha: Descricao, Quantidade, Unidade, Preco, IVA
3. O total e calculado automaticamente (com IVA)

---

## 18. Administracao do Sistema

> Apenas utilizadores com perfil **Administrador** tem acesso a estas funcionalidades.

### 18.1 Gestao de Utilizadores

1. Menu lateral: **Administracao** > **Utilizadores**
2. A lista mostra: E-mail, Nome, Funcao, Estado (Ativo/Inativo)

**Criar Utilizador:**
1. Clique em **Adicionar Utilizador**
2. Preencha: E-mail, Primeiro Nome, Apelido, Funcao, Palavra-passe
3. Clique em **Guardar**

**Editar Utilizador:**
1. Clique em **Editar** ao lado do utilizador
2. Atualize os campos desejados
3. Clique em **Guardar**

### 18.2 Registo de Auditoria

1. Menu lateral: **Administracao** > **Registo de Auditoria**
2. O registo mostra as ultimas 200 acoes do sistema:
   - Data e hora
   - Utilizador
   - Acao (Criar, Atualizar, Eliminar, Ver, Exportar, Anonimizar)
   - Modelo afetado
   - ID do objeto
   - Endereco IP

> O registo de auditoria e **imutavel** - nao pode ser editado ou eliminado. Os registos sao mantidos durante **10 anos** conforme a legislacao.

---

## 19. Perfis e Permissoes

O sistema suporta cinco perfis de utilizador com permissoes diferenciadas:

### 19.1 Administrador

- Acesso total a todas as funcionalidades
- Gestao de utilizadores e registo de auditoria
- Aprovacao de lotes de producao
- Gestao de formulacoes e inventario
- Gestao de faturacao

### 19.2 Farmaceutico

- Criacao e gestao de formulacoes
- **Aprovacao de lotes de producao** (exclusivo com Admin)
- Libertacao de lotes de quarentena
- Gestao de materias-primas e substancias proibidas
- Criacao de orcamentos e faturas
- Exportacao de dados
- Nao pode gerir utilizadores

### 19.3 Tecnico de Laboratorio

- Criacao e gestao de lotes de producao
- Conclusao de passos de producao
- Registo de controlos de qualidade
- Rececao e ajuste de lotes de inventario
- **Nao pode** aprovar lotes de producao
- **Nao pode** criar formulacoes
- **Nao pode** gerir faturacao

### 19.4 Rececao (Front Desk)

- Gestao de encomendas e clientes
- Visualizacao de producao e inventario (apenas leitura)
- Nao pode gerir producao, inventario ou faturacao

### 19.5 Visualizador

- Acesso apenas de leitura a todas as secoes
- Nao pode criar, editar ou eliminar qualquer registo

### Tabela Resumo de Permissoes

| Funcionalidade | Admin | Farmaceutico | Tec. Lab. | Rececao | Visualizador |
|----------------|:-----:|:------------:|:---------:|:-------:|:------------:|
| Gerir encomendas | Sim | Sim | - | Sim | - |
| Gerir clientes | Sim | Sim | - | Sim | - |
| Criar formulacoes | Sim | Sim | - | - | - |
| Criar lotes producao | Sim | Sim | Sim | - | - |
| Aprovar lotes | Sim | Sim | **Nao** | - | - |
| Registar CQ | Sim | Sim | Sim | - | - |
| Gerir materiais | Sim | Sim | - | - | - |
| Rececionar lotes | Sim | Sim | Sim | - | - |
| Ajustar stock | Sim | Sim | Sim | - | - |
| Libertar quarentena | Sim | Sim | **Nao** | - | - |
| Gerir substancias proibidas | Sim | Sim | - | - | - |
| Gerir faturacao | Sim | Sim | - | - | - |
| Gerir utilizadores | Sim | - | - | - | - |
| Ver registo auditoria | Sim | - | - | - | - |
| Exportar dados | Sim | Sim | - | - | - |

---

## 20. Conformidade Regulatoria

### 20.1 Portaria 594/2004 - Boas Praticas de Preparacao

O CompoundMeds assegura conformidade atraves de:

- **Ficha de Preparacao** completa com todos os campos obrigatorios
- **Rastreabilidade** total de materias-primas (lote de origem → lote de producao)
- **Controlo de Qualidade** com verificacoes organolepticas, pH e peso/volume
- **Rotulagem** conforme os requisitos legais
- **Registo de responsaveis** em cada passo de producao

### 20.2 Decreto-Lei 95/2004 - Responsabilidades

- Apenas **farmaceuticos** podem aprovar lotes de producao
- Prescricoes registadas com dados do medico e cedula profissional
- Cedulas profissionais verificaveis no perfil de utilizador

### 20.3 Portaria 769/2004 - Calculo de Precos

- Discriminacao de custos: Materias-primas + Embalagem + Honorarios
- Custo de materias-primas calculado automaticamente a partir dos lotes utilizados
- Informacao incluida na Ficha de Preparacao

### 20.4 Deliberacao 1985/2015 - Substancias Proibidas

- Base de dados de substancias proibidas mantida no sistema
- Verificacao automatica por CAS e nome em cada formulacao
- Alerta visual na pagina de producao

### 20.5 RGPD - Protecao de Dados

- Registo de auditoria imutavel de todas as acoes
- Gestao de consentimentos
- Campos anonimizaveis (nome e NIF do paciente)
- Retencao de dados configuravel (7 anos predefinido, 10 anos para auditoria)
- Eliminacao suave (soft delete) - dados marcados como eliminados mas preservados

---

## Anexo A - Atalhos e Dicas

| Acao | Dica |
|------|------|
| Pesquisa rapida | A pesquisa em listas e atualizada em tempo real (HTMX) |
| Navegacao | Utilize o menu lateral colapsavel para aceder a qualquer modulo |
| Estados | Os badges coloridos indicam o estado atual (verde=ok, amarelo=atencao, vermelho=problema) |
| Stock baixo | Materiais com stock abaixo do minimo aparecem a vermelho na lista |
| PDF | Se o WeasyPrint nao estiver instalado, os relatorios sao apresentados em HTML |

## Anexo B - Glossario

| Termo | Descricao |
|-------|-----------|
| ANF | Associacao Nacional das Farmacias |
| CAS | Chemical Abstracts Service (identificacao quimica) |
| CQ | Controlo de Qualidade |
| FEFO | First Expiry, First Out (politica de consumo de stock) |
| FSM | Finite State Machine (maquina de estados para gerir fluxos) |
| Infarmed | Autoridade Nacional do Medicamento e Produtos de Saude |
| NIF | Numero de Identificacao Fiscal |
| Ph.Eur. | Farmacopeia Europeia |
| RGPD | Regulamento Geral de Protecao de Dados |
| USP | United States Pharmacopeia |

---

*Manual gerado para CompoundMeds v1.0 - Fevereiro 2026*
