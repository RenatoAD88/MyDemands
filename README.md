# MyDemands - Redigir com IA (Hugging Face)

## Token Hugging Face
1. Acesse https://huggingface.co/settings/tokens.
2. Crie um token com permissão de inferência.
3. Abra **Configurações da IA** no app e preencha **Token Hugging Face**.

## Arquivos de persistência
O app cria automaticamente:

- `C:\MyDemands\ai_writing\configIA.txt`
- `C:\MyDemands\ai_writing\cacheIA.json`

Formato padrão de `configIA.txt`:

```txt
HF_API_TOKEN=xxxx
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.2
temperature=0.5
max_new_tokens=150
top_p=0.9
IA_USAGE_COUNT=0
IA_USAGE_LIMIT=200
IA_LAST_RESET=2026-01-01
IA_CACHE_ENABLED=true
```

## Contador mensal
- `IA_USAGE_COUNT` incrementa somente após resposta bem-sucedida da API.
- `IA_USAGE_LIMIT` bloqueia novas gerações ao atingir o limite.
- `IA_LAST_RESET` é usado para reset automático a cada 30 dias.

## Cache inteligente
- Hash SHA256 com `prompt + modelo + temperatura`.
- Se o hash já existir em `cacheIA.json`, a resposta é retornada sem nova chamada.
- Em hits de cache, o contador **não** incrementa.
- Limite de 1000 entradas: remove os registros mais antigos quando ultrapassa.

## Dashboard de consumo
No modal **Consumo de IA** você visualiza:
- Uso atual e percentual
- Último reset e próxima data de reset
- Modelo atual e status do cache
- Barra de progresso com alertas visuais (>80% amarelo; limite vermelho)

## Limitações do free tier (Hugging Face)
- Pode haver latência maior e filas em horários de pico.
- Alguns modelos podem retornar 429 por limite de taxa.
- Certos modelos podem não estar disponíveis sem plano pago.
