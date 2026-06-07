# Rated Worktops — Product Requirements

## Original Problem
A customer is looking for a kitchen worktop and splashback. They can upload a photo of their kitchen and select a stone from a list of available options. The selected stone texture and pattern is applied to the worktop and splashback areas in the image, allowing the customer to visualize how the chosen stone would look in their own kitchen before making a decision.

## Stack
- FastAPI + MongoDB (motor) + JWT (bcrypt + PyJWT) — Bearer token auth
- React 19 + React Router + Tailwind + shadcn UI + framer-motion + sonner
- AI: Gemini Nano Banana (gemini-3.1-flash-image-preview) via emergentintegrations + Emergent LLM key

## Architecture
- Bearer-token auth (token in localStorage `rw_token`, sent as `Authorization: Bearer`)
- Stones catalog: 12 predefined items (granite/marble/quartz/quartzite/travertine) + per-user custom uploads
- Visualizer flow: client base64-encodes kitchen image → POST `/api/visualize` with stone_id, mode (auto|hybrid), instructions → server fetches stone reference, calls Nano Banana with both images + prompt → returns generated base64 PNG, deducts 1 credit, persists to `visualizations` collection
- Credit system: 3 free credits on signup, MOCKED purchase endpoint with 4 payment-method buttons (Stripe / PayPal / Apple Pay / Google Pay) — instant credit grant

## Implemented (Feb 2026)
- Auth: register / login / me / logout
- Stones: GET catalog + user customs, POST custom-stone (base64)
- Visualize: 1-credit AI render with auto + hybrid prompt refinement
- Visualizations: list + delete, before/after compare slider
- Credits: balance + 3 packs + mock purchase + transaction history
- Pages: Landing, Login, Register, Dashboard, Stone Catalog, Gallery, Credits
- Premium dark "luxury showroom" theme — Playfair Display + Manrope + JetBrains Mono, gold accent #CBA153
- All interactive elements have `data-testid`

## Mocked / Deferred
- Stripe / PayPal / Apple Pay / Google Pay — MOCKED, returns instant credits
- Google OAuth — placeholder button, "coming soon" toast
- Phone OTP — placeholder button, "coming soon" toast

## Backlog (P1)
- Real Stripe checkout for credit packs
- Emergent Google OAuth + Twilio phone OTP
- Image masking UI for true hybrid (user paints worktop region)
- Admin dashboard: manage house catalog stones
- Shareable visualization links (public render permalink)

## Backlog (P2)
- Email reset-password flow
- Per-stone showroom landing pages for SEO
- Quote request form ("get a price for this render")
