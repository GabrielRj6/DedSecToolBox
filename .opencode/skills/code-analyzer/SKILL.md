---
name: code-analyzer
description: Analisa codigos Python em busca de erros, bugs, problemas de funcionalidade e integridade. Use esta skill quando o usuario quiser revisar codigo, encontrar problemas, verificar integridade, checar se algo esta desconexo ou poderia ser feito de forma melhor. Sempre que o usuario mencionar analise de codigo, revisao de codigo, encontrar bugs, verificar codigo, ou algo similar, use esta skill.
---

# Code Analyzer - Analise de Codigo Python

Esta skill analisa codigos Python para identificar erros, bugs, problemas de funcionalidade e oportunidades de melhoria.

## Processo de Analise

### 1. Leitura do Codigo
- Leia o arquivo ou arquivos fornecidos
- Identifique a estrutura geral do codigo
- Note as dependencias e imports

### 2. Analise de Erros Comuns
Procure especificamente por:
- **Erros de sintaxe** (que passariam despercebidos)
- **Erros de indentacao**
- **Imports faltantes ou incorretos**
- **Variaveis nao definidas**
- **Tipos de dados incorretos** (ex: somar string com numero)
- **Referencias circulares**
- **Encoding issues**

### 3. Analise de Bugs Potenciais
Busque por:
- **Logica condicional incorreta** (if/else wrong)
- **Loops infinitos** ou condicoes de saida incorretas
- **Off-by-one errors** em iteracoes
- **Race conditions** em codigo assincrono
- **Tratamento inadequado de excecoes** (bare except, except pass)
- **Vazamentos de recursos** (arquivos nao fechados, conexoes nao fechadas)
- **Logica de negocio incorreta**

### 4. Analise de Integridade e Coerencia
Verifique:
- **Consistencia de nomes** (variaveis com nomes semelhantes mas propositos diferentes, ou vice-versa)
- **Conexao entre modulos** (imports condizentes com uso)
- **Parametros de funcoes** (uso condizente com definicao)
- **Retorno de funcoes** (todos os caminhos retornam algo consistente)
- **Escopo de variaveis** (uso de variaveis antes de atribuicao)
- **Dead code** (codigo inacessivel ou nunca utilizado)

### 5. Analise de Funcionalidade
Avalie se:
- **O codigo faz o que deveria fazer** (comparando nome de funcao/variavel com comportamento)
- **Ha funcoes desconexas** ou logica que parece fora de lugar
- **Ha redundancias** (codigo duplicado que poderia ser refatorado)
- **Ha complexidade desnecessaria** que poderia ser simplificada

## Formato da Saida

Para cada problema encontrado, use este formato:

```
## [TIPO] Descricao Curta

**Arquivo:** `caminho/arquivo.py`
**Linha:** XX
**Problema:** Descricao clara do problema
**Sugestao:** Como corrigir ou melhorar
```

### Tipos de Problemas
- `[ERRO]` - Erro que causara falha na execucao
- `[BUG]` - Bug que pode causar comportamento inesperado
- `[WARNING]` - Codigo que funciona mas e problematico
- `[SUGESTAO]` - Melhoria opcional para qualidade

## Exemplo de Saida

```
# Analise de Codigo

## [ERRO] Variavel indefinida

**Arquivo:** `main.py`
**Linha:** 15
**Problema:** A variavel `user_input` e usada mas nunca foi definida antes deste ponto.
**Sugestao:** Defina `user_input = input("...")` antes da linha 15.

## [WARNING] Except generico

**Arquivo:** `utils.py`
**Linha:** 42
**Problema:** Uso de `except:` captura todas as excecoes, incluindo SystemExit e KeyboardInterrupt.
**Sugestao:** Use `except Exception:` se quiser capturar apenas erros de programa.
```

## Regras

- Seja especifico sobre a linha e o arquivo
- Explique POR QUE algo e um problema
- Forneca sugestoes concretas de correcao
- Priorize problemas que causam falhas sobre melhorias de estilo
- Se o codigo parecer correto, diga isso explicitamente
- Marque claramente quando nao encontrar problemas
