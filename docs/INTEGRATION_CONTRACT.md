# C.E.R.B.E.R.U.S. — Control Plane Alpha 0.2: contrato de integração

**Implementado:** centro local de observação + missões de engenharia de execução supervisionada.
**Não implementado:** autonomia livre, código gerado/executado por IA, operações financeiras reais, controlo de hardware, API multiutilizador ou servidor Internet.

## Iniciar

No Windows, com Python 3.11+:
- Fazer duplo clique no atalho **CERBERUS Control Plane** ou em `03_CERBERUS_CORE/ABRIR_CONTROL_PLANE.bat`.
- Abrir `http://127.0.0.1:8890/` **no mesmo computador**.
- Copiar o token de sessão que aparece no terminal; nunca o publicar.
- Selecionar uma missão, clicar **Preparar missão**, ler o resumo e depois **Aprovar e executar**. A preparação isoladamente não executa código.
- Clicar **Consultar resultado** para atualizar o estado. **Cancelar missão** pede a paragem do contentor.

Para consultar apenas serviços no terminal: `py -3 03_CERBERUS_CORE/control_plane.py --once`.

## Requisitos das missões

Docker Desktop em funcionamento, com a imagem `python:3.12-alpine` já presente localmente. O comando Docker usa `--pull=never`; nunca descarrega imagem em execução.

A execução local foi verificada em 9/11/2026 no Windows:
- Regressões Python: **85 testes aprovados em Docker**, para esta versão de desenvolvimento.
- Verificador de referência RISC-V: concluído (não é simulação RTL ou teste FPGA).
- Robótica: cálculo estático concluído (não é medição de hardware).

A aprovação de cada missão é limitada a 90 segundos e utilizável uma única vez. Só uma missão pode executar de cada vez.

## Contrato HTTP (versão 1)

Todos os endpoints `/api/v1/*` exigem `Authorization: Bearer <token>` e Host local. O servidor apenas escuta `127.0.0.1`; a presença do cabeçalho Origin é verificada em pedidos autenticados. Pedidos POST exigem `Content-Type: application/json`, objeto JSON com esquema exato e corpo até 2 KiB.

| Método | Endpoint | Efeito |
| --- | --- | --- |
| GET | `/healthz` | Saúde do processo local, sem autenticação (não prova que Docker está disponível) |
| GET | `/api/v1/services` | Estado de saúde HTTP dos serviços conhecidos |
| GET | `/api/v1/missions/catalog` | Lista fixa de tarefas aprovadas |
| POST | `/api/v1/missions/prepare` | Recebe `{"task_id": "robotics_static"}`; devolve ticket efémero sem executar |
| POST | `/api/v1/missions/start` | Recebe `{"ticket": "...", "approve": true}`; inicia a missão aprovada |
| GET | `/api/v1/missions` | Últimos 15 registos |
| GET | `/api/v1/missions/<uuid>` | Detalhes e saída limitada a 5000 caracteres |
| POST | `/api/v1/missions/cancel` | Recebe `{"id": "<uuid>"}`; solicita cancelamento |

Todos os outros POST/PUT/PATCH/DELETE são rejeitados. Os comandos Docker não são controlados pelo conteúdo dos pedidos. Não existe endpoint para executar shell, fornecer argumentos, imagens, mounts, URLs, comandos personalizados ou código livre.

## Catálogo imutável desta versão

1. `engineering_tests`: `python tools/test_engineering.py`, tempo máximo 60 s.
2. `riscv_reference`: `python 09_HARDWARE/RV32I_TRACE/tools/verify_reference.py`, 20 s.
3. `robotics_static`: cálculo Python com argumentos fixos e sintéticos, 20 s.

Todas as operações acontecem dentro de um contentor Docker: rede desativada, imagem previamente armazenada, 1 CPU, 384 MiB RAM, 64 PIDs, UID não-root, capacidades Linux removidas, no-new-privileges, sistema de ficheiros e montagem do repositório só para leitura, apenas `/tmp` temporário em memória. Não existe fallback de execução no host.

## Estados e auditoria

- `RUNNING` → `PASSED`, `FAILED` ou `TIMED_OUT`.
- Quando o utilizador cancela: `CANCELLING` → `CANCELLED`.
- Após reinício, missões que estavam em `RUNNING` ou `CANCELLING` ficam registadas como `INTERRUPTED`; isso não é prova de que um contentor órfão foi eliminado.

Histórico SQLite local: `~/.cerberus/control_plane/missions.sqlite3`. **Não existe encriptação em repouso**, nem limpeza automática dos registos nesta Alpha. A saída é truncada e algumas formas de token são ocultadas por heurística; isto **não substitui uma auditoria de segredos**.

## Segurança, limites e próximos marcos

Não abrir esta API ao público, não criar tunnels ou reverse proxies e não usá-la em repositórios de clientes com código não confiável. Docker restringe capacidades mas não é uma garantia absoluta contra vulnerabilidades do kernel/runtime. Inspeção de qualidade e de segurança externa ainda está pendente.

A versão Alpha 0.2 **não** integra ainda o motor MOSS nem o Core Commander/Code Guard como executores de missões. O próximo marco é estabelecer uma API de capacidades granular para que o MOSS possa propor tarefas, sujeitas a revisão humana, testes e rollback — sem autoperpetuação de permissões.
