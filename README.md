# quickshell-chatgpt

Experimental open-source integration for using an eligible ChatGPT plan in the [end-4 illogical-impulse](https://github.com/end-4/dots-hyprland) Quickshell AI sidebar.

> **Status: v0.0.1 scaffold only.** Authentication, inference, and the Quickshell adapter are **not yet connected**. Nothing here grants ChatGPT plan usage on its own.

## Goal

Offer **Continue with ChatGPT** using OpenAI's documented open-source Sign in with ChatGPT (SIWC) flow, then stream eligible Responses API output into the existing Quickshell chat UI. Preserve other providers and avoid modifying upstream dotfiles until an adapter is proven.

## Architecture

- `bridge/`: local Python components for request validation, eventual OAuth/PKCE, credential storage and streamed inference.
- `quickshell/`: adapter/integration notes and eventual QML implementation.
- `docs/`: architecture, official protocol requirements, roadmap, security decisions.
- `tests/`: offline, standard-library tests.

The bridge will run as the signed-in local user. The Quickshell frontend must **never** receive access or refresh tokens. The bridge will not reuse Codex credentials.

## Developer setup

Python 3.12+ is recommended; current scaffold uses only the standard library.

```sh
git clone https://github.com/tovakai/quickshell-chatgpt.git
cd quickshell-chatgpt
python -m unittest discover -s tests -v
python -m bridge --help
```

No login or network calls are performed by these commands.

## Milestones

1. **v0.0.1**: audited skeleton, request contract, unit tests.
2. **v0.1.0**: full SIWC browser OAuth flow (host ID, dynamic client registration, PKCE, state/nonce, ID token validation, encrypted/protected credentials and rotation).
3. **v0.2.0**: account-specific model discovery and stream-complete Responses API bridge.
4. **v0.3.0**: end-4 Quickshell adapter, UX, reconnect and errors.
5. Later: upstreamable plugin architecture and optional support for other Quickshell configurations.

## Official protocol references

- [SIWC open-source overview](https://developers.openai.com/siwc/token-sharing-open-source)
- [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
- [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)
- [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

Not affiliated with or endorsed by OpenAI or end-4. The project is not an OAuth proxy for sharing subscriptions with other people.
