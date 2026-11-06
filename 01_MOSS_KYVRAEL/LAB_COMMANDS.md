# MOSS Lab — Windows e Ollama local

O MOSS Lab é um protótipo independente do MOSS completo. Permite registar missões e conversar com um modelo **local** sem executar ferramentas, comandos do sistema ou tarefas com efeitos reais.

## Atualizar o código no CMD

```bat
cd /d "%USERPROFILE%\Desktop\cerberus"
git pull --ff-only
cd 01_MOSS_KYVRAEL
ABRIR_MOSS_LAB.bat status
```

## Verificar modelos Ollama disponíveis

Com o Ollama instalado e em execução no Windows:

```bat
ollama list
ABRIR_MOSS_LAB.bat ollama-check
```

Se não houver modelos, instalá-los exige descarregar dados da internet e espaço livre em disco. O MOSS Lab não faz downloads automáticos.

## Conversar com o modelo instalado

```bat
ABRIR_MOSS_LAB.bat ollama-ask "Explica o que e uma CPU RISC-V." --model qwen2.5:1.5b
```

Usa o nome exato devolvido por `ollama list`, se for diferente. Podes ajustar `--max-tokens 256` e `--timeout 60`.

- O servidor é fixo em `http://127.0.0.1:11434`, sem redirecionamentos.
- A ferramenta envia o texto apenas ao Ollama local e recebe uma resposta; não abre ficheiros, não executa scripts nem controla o PC.
- As respostas podem conter erros. Verifica qualquer código antes de o executar.
- Se o Ollama não estiver ligado, o comando apresenta uma mensagem de erro, sem danificar o diário de missões.
- Os diários e notas privadas ficam em `%USERPROFILE%\.cerberus\moss_lab`, fora do GitHub.
