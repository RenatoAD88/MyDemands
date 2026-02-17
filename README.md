# MyDemands - Configuração de IA (OpenAI / Hugging Face)

## Instalação recomendada (Windows, com `venv`)
Para evitar conflitos de dependências globais (especialmente entre `transformers` e `huggingface_hub`), instale sempre em ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

> O `requirements.txt` fixa versões compatíveis, incluindo `transformers==4.57.6` e `huggingface_hub==0.34.4`.

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
AI_PROVIDER=huggingface

# OpenAI
OPENAI_API_KEY=xxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.5
OPENAI_MAX_OUTPUT_TOKENS=300

# Hugging Face
HF_API_TOKEN=xxxx
HF_MODEL=stepfun-ai/Step-3.5-Flash
HF_TEMPERATURE=0.5
HF_MAX_NEW_TOKENS=200
HF_TOP_P=0.9
IA_CACHE_ENABLED=true
```

## Observações
- Tokens/chaves são exibidos como campo de senha na tela.
- O app não expõe tokens em logs da funcionalidade.
- **Testar conexão** usa os valores atuais da modal (mesmo sem salvar) e **não** persiste em arquivo.
- O fluxo **Redigir com IA** respeita `AI_ENABLED` e o `AI_PROVIDER` salvo.
- Para Hugging Face, a integração usa `huggingface_hub.InferenceClient` com Chat Completions.
