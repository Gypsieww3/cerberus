# C.E.R.B.E.R.U.S. — Telemetry Studio 1.0

**Programa local para análise de telemetria CSV — protótipo funcional, não certificado.**

Importa dados em CSV com `timestamp,sensor,value,unit`, valida os registos, guarda histórico em SQLite, mostra gráficos e alarmes por limite e exporta os dados. O servidor liga apenas a `127.0.0.1`; não lê sensores industriais automaticamente e não controla motores.

**Evidência:** 11 testes locais Windows concluídos em 9/11/2026, incluindo rotas HTTP, validação e persistência; regressões automáticas em Windows e Linux também aprovadas no repositório privado. Compatibilidade com equipamentos e máquinas de clientes ainda não foi validada.

**Distribuição:** o código-fonte e o pacote ZIP estão num repositório privado do titular. Não é uma oferta de download público ou uma autorização de utilização comercial. Demonstração supervisionada e eventual licença exigem acordo escrito.

[Solicitar avaliação piloto não confidencial](https://github.com/Gypsieww3/cerberus/issues/new?template=telemetry-pilot.md).

© 2026 C.E.R.B.E.R.U.S. — direitos sobre trabalho original reservados aos titulares legítimos, com respeito pelas licenças de terceiros.
