# Rated Worktops — Product Requirements

## Original Problem
A customer is looking for a kitchen worktop and splashback. They upload a photo of their kitchen and select a stone from a list of available options. The selected stone texture and pattern is applied to the worktop and splashback areas in the image, allowing the customer to visualize how the chosen stone would look in their own kitchen before making a decision.

## Stack
- FastAPI + MongoDB (motor) + JWT/Bearer (bcrypt + PyJWT)
- React 19 + React Router + Tailwind + shadcn UI + framer-motion + sonner
- AI: Gemini Nano Banana (`gemini-3.1-flash-image-preview`) via `emergentintegrations` + Emergent LLM key
- Auth: Email/password JWT, **Emergent Google OAuth (real)**, Phone (placeholder)

## Implemented
### Iteration 3 — Object Storage + Per-Stone SEO (current)
- **Object storage migration**: Generated kitchen + result PNGs now upload to Emergent object storage via `/app/backend/storage.py` on every render. MongoDB stores only the path + the backend-served URL; doc size dropped from ~700KB to ~1KB per render. Legacy renders (pre-iter-3) keep their inline base64 and serve via the same endpoint via a backward-compat path.
- **Public image endpoint** `GET /api/public/renders/{viz_id}/image/{kind}` (kitchen|result) — no auth, anyone with the render id can fetch the bytes (same capability model as `/r/:id`).
- **Per-stone SEO showroom** `GET /api/public/stones/{id}` → public `/stones/:id` page with hero image, type/finish/origin, description, and a "{stone} in real kitchens" grid of the 8 most recent renders. Each card links to `/r/:id`. Landing-page stone cards now link into their per-stone page.
- Renders payload in showroom is URL-only (lightweight) — never inlines base64 even for legacy renders.

### Iteration 2 — Lead-gen + Featured + Google Auth
- Featured stone flag, public render permalink, public quote-request endpoint, admin quote inbox, real Emergent Google sign-in.

### Iteration 1.x
- MVP, Stripe→PayPal swap (still mocked), DB-backed admin catalog manager.

## Mocked / Deferred
- Payments — Stripe replaced by PayPal in UI; all methods still MOCKED (no real charge). User confirmed no live PayPal credentials yet.
- Phone OTP login — placeholder "coming soon".

## Backlog (P1)
- Real PayPal sandbox checkout (just needs credentials)
- Twilio phone OTP
- Image masking UI for true hybrid (still text-refinement only)
- Split server.py (now ~840 lines) into modules

## Backlog (P2)
- Email reset-password flow
- Per-render thumbnail field for SEO/share previews (lightweight image)
- Rate-limit / captcha on public `/api/quotes` to prevent spam
- `published` flag on visualizations to curate per-stone showroom rows
