# MOSS / KYVRAEL — atribuição da família do modelo

O MOSS Lab é uma aplicação C.E.R.B.E.R.U.S. que utiliza modelos de linguagem locais através do Ollama.

A família **Qwen2.5** e **Qwen2.5-Coder** foi desenvolvida pela **equipa Qwen da Alibaba Cloud**. A Anthropic desenvolve a família Claude, não Qwen. Referência oficial: https://qwenlm.github.io/blog/qwen2.5/

O modelo pode gerar informações incorretas sobre si próprio. Por isso:
- O campo «Família / Origem» vem de `model_identity.py`, e não da resposta produzida pelo modelo.
- `GET /api/v1/models` inclui `model_details`; `POST /api/v1/chat` inclui `model_identity`.
- A verificação é por **nome de família** (tag do Ollama). **Não verifica hashes ou autenticidade dos pesos locais**.
- Um modelo personalizado (por exemplo, `ghost-engine`) tem origem marcada «por verificar» até análise da sua proveniência.
- Os modelos não controlam automaticamente ferramentas, ações no PC ou arquivos. O texto produzido por uma IA não é evidência de execução.

O código mantém o histórico de conversação numa base SQLite privada do PC. Para aplicar a atualização, termina a instância do servidor com Ctrl+C, executa `git pull --ff-only` na raiz do repositório e reinicia `ABRIR_MOSS_WEB.bat`. Atualiza o browser com Ctrl+F5.
