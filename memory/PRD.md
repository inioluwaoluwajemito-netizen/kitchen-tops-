# Rated Worktops — Product Requirements

## Original Problem
A customer is looking for a kitchen worktop and splashback. They upload a photo of their kitchen and select a stone from a list of available options. The selected stone texture and pattern is applied to the worktop and splashback areas in the image, allowing the customer to visualize how the chosen stone would look in their own kitchen before making a decision.

## Stack
- FastAPI + MongoDB (motor) + JWT/Bearer (bcrypt + PyJWT)
- React 19 + React Router + Tailwind + shadcn UI + framer-motion + sonner
- AI: Gemini Nano Banana (`gemini-3.1-flash-image-preview`) via `emergentintegrations` + Emergent LLM key
- Auth: Email/password JWT, **Emergent Google OAuth (real)**, Phone (placeholder)

## Implemented
### Iteration 1 — MVP (Feb 2026)
- Auth: register / login / me / logout (Bearer in `localStorage.rw_token`)
- Stones catalog (12 curated) + per-user custom uploads
- Visualize endpoint: real Gemini Nano Banana, auto + hybrid modes, credit deduction
- My Renders gallery with before/after compare slider, download
- Credits: 3 free on signup, 3 packs (Starter/Pro/Studio), MOCKED purchase
- Pages: Landing, Login, Register, Dashboard, Catalog, Gallery, Credits

### Iteration 1.1 — Stripe swapped for PayPal (still mocked)
- `/api/credits/purchase` accepts only `paypal`, `apple_pay`, `google_pay`
- Credits page UI: PayPal replaces Stripe button

### Iteration 1.2 — DB-backed admin catalog manager
- `house_stones` collection seeded from `stones_data.py` on first boot
- Admin-only CRUD: `/api/admin/stones` GET/POST · `/api/admin/stones/{id}` PATCH/DELETE
- `/admin/catalog` UI: grid + add/edit modal (image URL preview, swatch color picker, show/hide toggle, delete)

### Iteration 2 — Lead-gen + Featured + Google Auth (current)
- **Featured stones**: `featured` boolean on house stones; admin toggle in form. Featured stones float to the top of `/api/stones` and `/api/public/stones`, surfaced on the landing page hero cards.
- **Public render permalink**: `GET /api/public/renders/{id}` (no auth) → `/r/:id` page with compare slider + "Request a quote" CTA + share button.
- **Quote-request lead-gen**:
  - Public `POST /api/quotes` (no auth) — captures name, email, phone, notes, optional visualization_id/stone_id
  - Admin `GET /api/admin/quotes` (+ status filter) · `PATCH` (status: new|contacted|closed) · `DELETE`
  - `/admin/quotes` inbox UI with status filter tabs, counts, mark-contacted/close/reopen/delete
  - Visualizations page now exposes share + "Get a quote" buttons per render
- **Emergent Google Auth (real)**: `POST /api/auth/google` exchanges Emergent session_id for our JWT bearer token. Frontend `/auth/callback`-style handler detects `#session_id=…` synchronously in `AppRouter` and processes before any protected route check.
- **Test coverage**: 19/19 new tests + 16/16 regression all green.

## Mocked / Deferred
- Stripe / PayPal / Apple Pay / Google Pay — payment **MOCKED** (instant credits)
- Phone OTP login — placeholder button, "coming soon"
- Image masking UI for true hybrid (still text-refinement only)

## Backlog (P1)
- Real Stripe / PayPal sandbox checkout (just needs credentials)
- Twilio phone OTP
- Object storage migration for generated images (off Mongo)
- Per-render lightweight thumbnail for SEO/share previews

## Backlog (P2)
- Email reset-password flow
- Image masking UI for hybrid
- Per-stone showroom landing pages (SEO)
- Rate-limit / captcha on public `/api/quotes` to prevent spam
