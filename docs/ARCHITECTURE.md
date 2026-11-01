# Mabel sidebar architecture

## Required routing

Quickshell is a front end only:

    QML → Python stdio bridge → Odysseus chat/session HTTP API → selected backend model provider

The model is selected by Odysseus. The bridge MUST NOT contact Strata, OpenAI, model inference APIs, or a parallel LLM tool router.

Odysseus endpoints used:
- GET /api/companion/ping
- GET /api/companion/models
- GET /api/sessions
- GET /api/history/{id}?limit=80
- POST /api/session
- POST /api/chat_stream
- GET /api/chat/resume/{id}
- POST /api/chat/stop/{id}

## Authentication and authority

The bridge runs as the local user and reads an Odysseus API token from a chmod 600 local file. The token never enters QML, logs, or the model prompt. Without a token only localhost URLs are accepted, for explicit auth-disabled local deployments or SSH tunnels. Redirects are rejected to avoid forwarding Authorization to another origin.

Model/endpoint IDs are validated against the backend inventory before new sessions; session permissions and effective model endpoint routing remain backend-owned.

Odysseus specifically prohibits delegated bearer tokens from approving gated tools. This is a correct security distinction: user-facing approval requires the interactive Mabel app for now. A future inline approval feature needs purpose-built, human-confirmed client authentication from the Odysseus backend, not a loophole.

## Stream and cancellation

Mabel SSE events are decoded incrementally. Reasoning deltas are hidden from the main visible response; final_response replaces earlier draft content; coarse tool activity is shown without dumping tool payloads. The bridge treats stream EOF without the [DONE] event as incomplete. Detached runs are canceled using the exact X-Odysseus-Run-Id to protect later concurrent sends; Resume uses Mabel's existing attachment endpoint.

## Next steps

Improve Markdown/agent traces, attachments and generated-image display, explicit backend-supported approval UI, and optional integration with end-4 using the same backend. Validate against the user's active Mabel release test branch.
