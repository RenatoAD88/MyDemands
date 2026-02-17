# MyDemands - Configuração de IA (OpenAI / Hugging Face)

## Onde fica o arquivo de configuração
As preferências de IA são persistidas em:

- `C:\MyDemands\ai_writing\configIA.txt`

O app cria automaticamente a pasta/arquivo com valores padrão seguros caso não existam.

## Como habilitar e trocar provedor
1. Abra **Configuração de IA** no app.
2. Marque **Habilitar IA**.
3. Em **Provedor de IA**, escolha **OpenAI** ou **Hugging Face**.
4. Preencha os campos do provedor selecionado.
5. Clique em **Testar conexão** e depois em **Salvar**.

> Ao trocar o provedor, os dados do outro provedor não são apagados.

## Chaves/variáveis salvas em `configIA.txt`
```txt
AI_ENABLED=true
AI_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=xxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.5
OPENAI_MAX_OUTPUT_TOKENS=300

# Hugging Face
HF_API_TOKEN=xxxx
HF_MODEL=HuggingFaceH4/zephyr-7b-beta
HF_TEMPERATURE=0.5
HF_MAX_NEW_TOKENS=150
HF_TOP_P=0.9
IA_CACHE_ENABLED=true
```

## Observações
- Tokens/chaves são exibidos como campo de senha na tela.
- O app não expõe tokens em logs da funcionalidade.
- O fluxo **Redigir com IA** respeita `AI_ENABLED` e o `AI_PROVIDER` salvo.
- Para Hugging Face, o app prioriza `router.huggingface.co/hf-inference` quando `api-inference.huggingface.co` estiver descontinuado (HTTP 410).
