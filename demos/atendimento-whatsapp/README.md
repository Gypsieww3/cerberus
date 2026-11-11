# CERBERUS — Demonstração de atendimento por regras

**Estado:** demonstração de interface e regras publicada em 11/11/2026. Nenhum envio real de WhatsApp, nenhuma ligação à Meta, nenhuma conversa com cliente real. Não há IA generativa nem serviço 24/7 neste protótipo.

## O que já existe
- Formulário para simular mensagens e respostas em português.
- Motor determinístico com seis regras: humano/reclamação, horário, preço, entrega, estado de pedido e saudação.
- Normalização de acentos, espaços e maiúsculas.
- Encaminhamento para humano em casos críticos ou não reconhecidos.
- Contagem local de mensagens e encaminhamentos.
- Nenhuma chamada de rede ou armazenamento de dados de conversas.

## Verificações executadas no desenvolvimento
O motor foi exercitado com oito casos básicos: saudação, horário, preços, entrega, rastreio, atendimento humano, texto desconhecido e texto vazio. Oito resultados corresponderam ao esperado, no ambiente de execução utilizado para preparar o commit. **Estes testes não demonstram integração, segurança ou prontidão de produção.**

## Etapas para uma integração real, apenas após contratação e autorização
1. Confirmar escopo, mensagens, horários, canal, número e volume de atendimento.
2. Verificar conta empresarial e elegibilidade para WhatsApp Business Platform / Cloud API, preços e regras vigentes.
3. Construir backend com webhook verificado, autenticação, deduplicação de eventos, limitação de ritmo e regras aprovadas.
4. Tratar privacidade, retenção e política de encaminhamento humano.
5. Testes ponta a ponta em ambiente autorizado e plano de reversão.
6. Entrega documentada e validação do cliente.

A demonstração não deve ser apresentada como integração real com a marca WhatsApp, nem deve ser usada para enviar mensagens em massa.

**Comercial:** preparação de candidatura a um pedido público de Workana publicado em 10/11/2026. Nenhuma proposta foi enviada e nenhum contrato foi firmado.
