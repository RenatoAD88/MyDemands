# MyDemands - Redigir com IA (Hugging Face / OpenAI)

## Configurando o provedor de IA
No app, abra **Configurações da IA** e selecione o provedor desejado (**Hugging Face** ou **OpenAI**).

### Hugging Face
1. Acesse https://huggingface.co/settings/tokens.
2. Crie um token com permissão de inferência.
3. Em **Configurações da IA**, selecione **Hugging Face** e preencha **Token Hugging Face**.

### OpenAI
1. Acesse https://platform.openai.com/api-keys.
2. Gere uma chave de API.
3. Em **Configurações da IA**, selecione **OpenAI** e preencha **Chave OpenAI**.

## Arquivos de persistência por provedor
O app cria automaticamente configurações e cache separados por IA:

- `C:\MyDemands\ai_writing\huggingface\configIA.txt`
- `C:\MyDemands\ai_writing\huggingface\cacheIA.json`
- `C:\MyDemands\ai_writing\openai\configOpenAI.txt`
- `C:\MyDemands\ai_writing\openai\cacheOpenAI.json`

Formato padrão de `configIA.txt` (Hugging Face):

```txt
HF_API_TOKEN=xxxx
HF_MODEL=google/flan-t5-base
temperature=0.5
max_new_tokens=150
top_p=0.9
IA_USAGE_COUNT=0
IA_USAGE_LIMIT=200
IA_LAST_RESET=2026-01-01
IA_CACHE_ENABLED=true
```

Formato padrão de `configOpenAI.txt` (OpenAI):

```txt
OPENAI_API_KEY=xxxx
OPENAI_MODEL=gpt-4o-mini
temperature=0.5
max_new_tokens=150
top_p=0.9
IA_USAGE_COUNT=0
IA_USAGE_LIMIT=200
IA_LAST_RESET=2026-01-01
IA_CACHE_ENABLED=true
```

## Contador mensal e cache
- Contador e cache funcionam de forma independente por provedor.
- `IA_USAGE_COUNT` incrementa somente após resposta bem-sucedida.
- `IA_USAGE_LIMIT` bloqueia novas gerações ao atingir o limite.
- `IA_LAST_RESET` é usado para reset automático a cada 30 dias.
- Hash SHA256 usa `prompt + modelo + temperatura` dentro do cache da IA selecionada.
