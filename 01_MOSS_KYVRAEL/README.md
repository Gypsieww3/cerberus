# MOSS/KYVRAEL — Laboratório de engenharia local

Este repositório contém um **MOSS Lab operacional**, independente do arquivo histórico do motor MOSS/KYVRAEL. O sistema implementa API HTTP apenas em `127.0.0.1`, painel web local, Ollama, modelos, memória lexical e diário de missões com SQLite.

## Funcionalidades verificáveis

- Missões persistentes, eventos e transições controladas.
- Planeamento e pré-visualizações sem execução automática.
- Conversas com modelos Ollama locais, história privada e identificação da família do modelo.
- Inspeção do repositório: número de ficheiros de código por projeto, sem alegações de conclusão.
- Auditoria estática (AST) de Python com erros de sintaxe e sinais de execução dinâmica, chamadas de shell ou exceções demasiado genéricas; análise heurística, não certificação de segurança.
- **Motor de engenharia supervisionado:** quatro tarefas estáticas (testes de regressão, referência RV32I, referência ALU, sintaxe do MOSS), execução Python com `shell=False` e tempo máximo de 120 s.
- Histórico auditável de testes em SQLite; resultados interrompidos são identificados como `INTERRUPTED` após reinício.
- Autorização explícita do utilizador para cada teste. O modelo de IA **não** pode convocar ferramentas ou executar comandos.

## Windows

No CMD, com Python e Git instalados:

```bat
cd /d "%USERPROFILE%\Desktop\cerberus"
git pull --ff-only
py -3 tools\test_engineering.py
cd 01_MOSS_KYVRAEL
ABRIR_MOSS_WEB.bat
```

Abre http://127.0.0.1:8765/ e introduz o token gerado no CMD. Não partilhes o token. O painel inclui a secção **Motor de engenharia MOSS**.

## Dados privados

Bases SQLite locais: `%USERPROFILE%\.cerberus\moss_lab`. A informação não é carregada automaticamente para o GitHub. Faz cópias de segurança antes de importar dados de versões históricas.

## Estado real

O **MOSS Lab** permite executar verificações locais sob aprovação, mas ainda **não é a integração integral do motor histórico v5.25.4**. Faltam agentes capazes de agir em projetos por meio de autorização granular, reparação de código com testes e reversão, isolamento/sandbox de ferramentas e comparação aprofundada com o arquivo canónico. Os testes verificam comportamento exercitado, não garantem ausência de erros ou qualidade de produção para acesso público.

Não exponhas este servidor na Internet. Não existe encriptação transparente das bases SQLite nem revisão de segurança independente para implantação multiutilizador.
