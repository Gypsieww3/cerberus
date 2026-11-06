# Importar o motor MOSS original v5.25.4 sem perder dados

O MOSS Lab atual (interface web, Ollama, diário SQLite e testes) é **independente** do motor completo v5.25.4. O arquivo original tem mais módulos e precisa de integração e validação, não de substituir automaticamente o sistema que funciona.

## Arquivo preparado

Usa `CERBERUS_MOSS_5254_SOURCE_SAFE.zip`, fornecido nesta conversa. Inclui 147 fontes Python do núcleo e ferramentas de validação, com SHA-256 por ficheiro. Exclui bases SQLite, pastas `data`, `workspace`, configurações privadas e ficheiros binários.

## No CMD do Windows

Descarrega o ZIP para a pasta Downloads, sem o renomear. Com o repositório atualizado:

```bat
cd /d "%USERPROFILE%\Desktop\cerberus"
git pull --ff-only
py -3 tools\import_legacy_moss.py "%USERPROFILE%\Downloads\CERBERUS_MOSS_5254_SOURCE_SAFE.zip"
```

O primeiro comando apenas **verifica** o conteúdo, lista o destino e não extrai ficheiros. Para importar:

```bat
py -3 tools\import_legacy_moss.py "%USERPROFILE%\Downloads\CERBERUS_MOSS_5254_SOURCE_SAFE.zip" --apply
```

O importador valida nomes, tamanho, versão, hashes e bloqueia percursos que saiam do destino. Os ficheiros ficam em `01_MOSS_KYVRAEL\legacy_v5_25_4`, **ignorado pelo Git**, para impedir exposição acidental. A importação não executa o código antigo. Se a pasta existir, o importador recusa sobrescrevê-la.

## Validação

Os testes do MOSS Lab atual permanecem independentes. Uma amostra de 34 testes antigos passou em revisão isolada; a suite antiga completa não terminou dentro do limite desta análise e não deve ser tratada como aprovada. Os fontes de legado importados não passam a integrar automaticamente o servidor web. A integração exigirá adaptadores de permissões, migração de dados com backups, execução isolada e correção de eventuais falhas do Windows.

**Nunca partilhes bases de dados, logs com dados pessoais, tokens, chaves ou a pasta `data` no GitHub público.**
