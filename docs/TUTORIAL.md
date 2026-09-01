# Tutorial — Fase 03, Passo 3.1 (Infra: SearXNG + cliente de busca)

Este tutorial cobre **apenas os arquivos entregues neste passo**. Não acumula
histórico de passos anteriores (isso fica no `README.md` e no `docs/STATUS.md`).

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `docker-compose.yml` | `IA-LOCAL/docker-compose.yml` (substitui o antigo — o serviço `qdrant` continua igual, só foi somado o `searxng`) |
| `src/search/__init__.py` | `IA-LOCAL/src/search/__init__.py` (pasta nova) |
| `src/search/searxng_client.py` | `IA-LOCAL/src/search/searxng_client.py` |
| `scripts/search_web.py` | `IA-LOCAL/scripts/search_web.py` |
| `tests/test_searxng_client.py` | `IA-LOCAL/tests/test_searxng_client.py` |

Se algum arquivo já existir com esse nome (caso do `docker-compose.yml`), apague o antigo antes de copiar o novo.

## O que cada coisa faz

- **SearXNG**: meta-buscador self-hosted (agrega Google/Bing/DuckDuckGo etc). Sobe via Docker igual ao Qdrant, expõe REST API na porta `8080`.
- **`searxng_client.py`**: função `search(query, max_results, categories)` — chama o SearXNG e devolve resultados normalizados (`title`, `url`, `snippet`, `engine`).
- **`search_web.py`**: CLI manual para testar o cliente isoladamente, sem precisar escrever código.
- **`test_searxng_client.py`**: teste de integração (precisa do SearXNG no ar), confirma que a busca retorna resultados válidos e que `max_results` é respeitado.

## Setup (só deste passo)

```bash
cd ~/IA-LOCAL

# 1. Sobe o SearXNG (gera settings.yml padrão na primeira vez)
docker compose up -d searxng
```

### Configuração manual obrigatória

O SearXNG **bloqueia JSON por padrão** — sem isso o cliente Python não funciona.

```bash
nano searxng/settings.yml
```

Garanta na seção `search:`:
```yaml
search:
  formats:
    - html
    - json
```

Gere e cole uma `secret_key` real (o padrão vem com valor de exemplo inseguro, não usar em produção):
```bash
openssl rand -hex 32
```
Cole o resultado em `server.secret_key`, no mesmo arquivo.

```bash
docker compose restart searxng
```

## Como testar

```bash
# 1. Teste bruto via curl — confirma que o JSON está habilitado
curl "http://localhost:8080/search?q=teste&format=json"

# 2. CLI manual
python scripts/search_web.py "arch linux"
python scripts/search_web.py "arch linux" --max-results 3

# 3. Teste automatizado
python tests/test_searxng_client.py
```

## Checklist de validação

- [ ] `docker compose ps` mostra `ia_local_searxng` rodando
- [ ] `curl ".../search?q=teste&format=json"` retorna JSON com `"results"` preenchido (não HTML, não erro 403)
- [ ] `scripts/search_web.py` imprime resultados legíveis com título, url e snippet
- [ ] `tests/test_searxng_client.py` termina com `Todos os testes do cliente SearXNG passaram.`

## Próximo passo (3.2)

Fetch + extração de conteúdo das URLs candidatas via **Crawl4AI** (decisão já confirmada — resolve fetch e extração de markdown limpo num passo só, evitando montar Playwright + lib de extração separada).
