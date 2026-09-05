# Capture notes — wantlist-add-remove

- Date: 2026-09-05
- HAR: `wave4.har` (this directory)
- Redacted curls: `curls.txt`
- Ops (exact hashes from HAR):
  - `AddReleasesToWantlist` sha `d07fa55f88404b5d0e5253faf962ed104ad1efd3af871c9281b76e874d4a2bf4`
    vars `{"input":{"releaseDiscogsIds":[2825456]}}`
  - `RemoveReleasesFromWantlist` sha `ab4a277f4c5d9da56ba17d4b88643c51a1935f500813133c55fe5a340625d06f`
    vars `{"input":{"releaseDiscogsIds":[2825456]}}`
- Client: `apollographql-client-name: release-page-client`, POST JSON body with persistedQuery.
- Cookies/secrets redacted; never log Cookie.
