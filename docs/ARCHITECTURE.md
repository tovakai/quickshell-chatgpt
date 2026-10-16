# Architecture and security boundaries

## Intended data flow

```text
end-4 AI sidebar (QML)
    | stdin/stdout or private local IPC (design TBD)
    v
unprivileged bridge process
    | OAuth PKCE login, protected token storage, refresh
    | HTTPS: model list and streamed Responses inference
    v
OpenAI public endpoints (never ChatGPT backend-api)
```

The end-4 sidebar currently uses a `Process` + `SplitParser` and separate Gemini/OpenAI/Mistral strategies. We should add a separate provider/bridge adapter instead of patching its existing OpenAI API-key strategy or copying API tokens into QML.

## Authentication contract (not implemented)

Follow the [official OSS SIWC flow](https://developers.openai.com/siwc/token-sharing-open-source/sign-in):

- Stable `ext_agent_host_id` per installation.
- Dynamic first-time registration; save issued client ID **per verified ChatGPT account/workspace**.
- New state, nonce and PKCE verifier for each attempt; local loopback callback.
- Verify ID token signature with JWKS, issuer, audience, expiry and nonce before accepting identity.
- Require `chatgpt.tokens.use.direct` before attempting plan-backed inference.
- Protect credentials; refresh tokens rotate and must be serialized. No credentials in logs, QML or repository.
- Never reuse ~/.codex authentication files or scrape browser cookies.
- Handle sign-out/revocation, multiple accounts and explicit consent.

## Responses contract

Discover permitted model IDs from the authorized account, do not hardcode consumer model names. For direct HTTP inference use public `/v1/responses`, `store: false`, `stream: true`; pass context in `input`. See [preview restrictions](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations). Do not send forbidden convenience parameters such as `temperature`, `previous_response_id`, `conversation`, or `max_output_tokens`.

Process SSE text deltas, but regard output as **successful only on `response.completed`**. Handle explicit failure, incompletion, timeout, cancellation and subscription usage errors separately. Keep account credentials inside a single local user process.

## Current status

Only offline request-validation and SSE transport parsing are implemented. No OAuth login, secret storage, IPC endpoint, HTTP transport or UI patch has been implemented or tested against an actual account.
