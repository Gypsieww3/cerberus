# MOSS Lab — interface web local

Esta aplicação é um **serviço local para um único utilizador**. Utiliza Python 3.11+ (biblioteca padrão), SQLite e Ollama instalado no computador. Não executa comandos do sistema a pedido da IA e não é o MOSS/KYVRAEL original completo.

## Iniciar no Windows

No CMD, atualiza o GitHub e inicia o servidor:

    cd /d "%USERPROFILE%\Desktop\cerberus"
    git pull --ff-only
    cd 01_MOSS_KYVRAEL
    ABRIR_MOSS_WEB.bat

Abre no browser: http://127.0.0.1:8765/

O terminal mostra um token temporário. Copia-o para o campo de acesso do browser. **Não publiques nem partilhes o token**. Deixa o CMD aberto durante a utilização. Para parar, usa Ctrl+C.

## Funcionalidades

- Diário de missões persistente em SQLite, com consulta de estados e eventos.
- Planos de pré-visualização de ações só de leitura, sem execução automática.
- Notas pessoais indexadas localmente.
- Deteção de modelos Ollama e geração de texto em loopback.
- Endpoint de saúde, autenticação bearer, limites de tamanho, proteção contra pedidos com origem externa e validação de entradas.

Os dados ficam em %USERPROFILE%\.cerberus\moss_lab (fora do repositório).

## Limites

Não expor a API na Internet nem encaminhar portas. Não oferece TLS, contas de utilizadores, gestão empresarial de segredos, limite de pedidos, auditoria independente, ou recuperação de dados de nível empresarial. Os dados em SQLite não são automaticamente encriptados. Para produção pública é necessária uma plataforma própria e uma auditoria de segurança.

## Conversa MOSS contextualizada

O painel utiliza o endpoint autenticado `POST /api/v1/chat`, enviando contexto estático dos projetos C.E.R.B.E.R.U.S. ao Ollama local através de `/api/chat`. O servidor mantém as últimas mensagens dentro de um limite de contexto, regista conversas em `chat.sqlite3` e disponibiliza `GET /api/v1/chat` e `DELETE /api/v1/chat`.

O MOSS Lab não é um modelo treinado de raiz: continua a utilizar Qwen, Llama ou outro modelo Ollama selecionado. O contexto melhora a pertinência das respostas, mas não lhe confere capacidades reais de execução de ferramentas nem garante rigor. Seleciona os modos Engenharia, Investigação ou Geral. O botão 'Apagar conversa' elimina apenas mensagens do chat, não as missões nem notas. As mensagens são persistidas localmente e não são automaticamente sincronizadas.
