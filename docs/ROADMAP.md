# Roadmap

## v0.0.1 - skeleton
- [x] Repository scaffold, license and architecture
- [x] Offline Responses request contract
- [x] SSE parser and unit tests
- [ ] Live sign-in, network requests or Quickshell patch (intentionally deferred)

## v0.1.0 - auth proof
- [ ] Host ID persistence and per-account registrations
- [ ] PKCE, state, nonce and loopback callback
- [ ] Browser consent with approved SIWC UX
- [ ] Token exchange, JWKS verification and scope check
- [ ] Protected token storage, refresh rotation and sign-out
- [ ] Auth/error tests with mocks; no secrets in logs

## v0.2.0 - inference proof
- [ ] User-account model discovery
- [ ] Authenticated streaming Responses request
- [ ] Backpressure/cancellation, structured failures and rate limits
- [ ] Offline/integration tests, first live hello world

## v0.3.0 - Quickshell integration
- [ ] Locally authenticated bridge IPC protocol
- [ ] QML provider compatible with end-4 sidebar
- [ ] Account selector, model picker, status/errors
- [ ] Streaming display and persisted chat context
- [ ] Uninstall and upstream upgrade/patch instructions
