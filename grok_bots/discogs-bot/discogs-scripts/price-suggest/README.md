# price-suggest

Wave 1 — live 2026-09-05.

## Endpoints
1. Market summary: `GET https://www.discogs.com/api/shop-page-api/market/release/{id}` (session Cookie).
2. In-collection: GraphQL GET `/service/catalog/api/graphql?operationName=UserReleaseData&variables={"discogsId":N}&extensions=persistedQuery`  
   sha256: `a5c6a6cf7e06b6a9d43ab71e49f9e0e4ecb0f204d0db43a63d0f279075bd06e4`
3. Community stats: public `GET https://api.discogs.com/releases/{id}` with **User-Agent only** (documented public API) — `community.have`/`want`, `lowest_price`, `num_for_sale`.

## Auth
`/home/box/discogs-auth/auth.env` for (1)(2); (3) uses USER_AGENT from jar, no Cookie.

## CLI
```bash
cd /workspace/discogs-scripts
python3 price-suggest/scripts/suggest.py 7146198
```
