# Authorization Findings — Who can read or write a volunteer's location?

**Task:** SP-W1-009 (investigation). **Status:** DRAFT — code-side evidence gathered; gateway-side questions are open.
**Branch:** `docs/SP-W1-009-authorization-findings` (from `origin/dev` @ `714e4e3`).

Labels: **Verified** = read directly in code on the named ref, or in installed library source. **Inferred** = reasoned from Verified facts, not confirmed. **Unverified** = not confirmed; needs an owner. Nothing here was executed against AWS.

## 1. Question

Who is allowed to write or read a volunteer's location, and what enforces that today?

## 2. Short answer

- **Spatial code enforces nothing.** (Verified) Any request that reaches the Lambda can write any `user_id`'s location and read anyone's latest position.
- **Whether API Gateway enforces anything is Unverified.** The webapp does send a Cognito ID token, which suggests an authorizer may exist, but even a working authorizer only proves *a* valid user is calling, not that the body/query `user_id` belongs to them.
- So today the best case is "any logged-in user can act as any volunteer"; the worst case is "anyone on the internet can".

## 3. Evidence

### 3.1 Spatial (this repo, `dev` @ `714e4e3`)

| # | Finding | Label |
|---|---|---|
| 1 | `app.py` never reads `request.headers`, `request.environ`, or any identity data. `user_id` comes only from the JSON body (`POST /updateVolunteerLocation`) or the query string (`GET /getVolunteerLocation?user_id=`). | Verified |
| 2 | `POST /updateVolunteerLocation` only checks `user_id` is truthy. It does not check the user exists or is a volunteer. | Verified |
| 3 | `GET /getVolunteerLocation` returns lat/lon/`updated_at` for any `user_id` supplied. | Verified |
| 4 | `POST /findNearbyVolunteers` returns the `user_id`s of volunteers within a radius of any caller-supplied point (radius up to the unvalidated value sent; see SP-W2-002). This lets a caller enumerate volunteers in an area. The SQL also selects lat/lon but the response includes only `user_id`. | Verified |
| 5 | `lambda_function.py` hands the full API Gateway event to `serverless_wsgi.handle_request`. It rewrites `event["path"]` by stripping `/dev/spatial/v0.0.1` or `/v1/spatial`, so the event has a top-level `path` key. | Verified |
| 6 | No docs, config, or IaC in this repo describe the API Gateway authorizer. | Verified (absence in repo) |

### 3.2 How identity reaches Flask (`serverless-wsgi` 3.1.0, installed from unpinned `requirements.txt`)

| # | Finding | Label |
|---|---|---|
| 7 | For payload v1 events (`event["version"]` missing or `1.0`) the library sets WSGI environ `serverless.authorizer = event["requestContext"]["authorizer"]`, plus `serverless.event` (whole event) and `REMOTE_USER` (from the authorizer context). For v2.0 events the same keys are set. | Verified (library source, `handle_payload_v1` / `handle_payload_v2`) |
| 8 | In Flask these are readable as `request.environ["serverless.authorizer"]`. It is a gateway-populated value, not a client header, so it is safe to trust **if** an authorizer is configured. If none is, it is `None`. | Verified (7) + Inferred (trust) |
| 9 | `requirements.txt` has `serverless-wsgi` unpinned, so behaviour could change between builds. If SP-W2-003 relies on this, pin it (Engineer 3 owns `requirements.txt`). | Verified |
| 10 | The event has a top-level `path` and the Lambda strips a stage prefix, which is consistent with payload v1 (REST API, or HTTP API with format 1.0). | Inferred |

### 3.3 Webapp (`saayam-for-all/webapp`, `test` and `dev`)

| # | Finding | Label |
|---|---|---|
| 11 | `src/services/api.js` adds an axios request interceptor that sets `Authorization: <Cognito ID token>` — the **raw token, no `Bearer ` prefix**. | Verified (`test`) |
| 12 | A raw token in `Authorization` is the form a **REST API Cognito user-pool authorizer** accepts. An HTTP API JWT authorizer normally expects `Bearer <token>`. This leans toward REST + Cognito authorizer, but it is only a lean. | Inferred |
| 13 | `userDbId` (sent as `user_id`) is **not a token claim**. At login `authActions.js` calls `getUserId(email)` (`v1/volunteer/getUserIdByEmail`) and stores `result.data.user_id \|\| result.data.id` in Redux and `localStorage`. | Verified (`test`) |
| 14 | `volunteerLocationTracker.js` (exists on `test` and `dev`, not on `main`) reads `user_id` from `auth.user.userDbId` and POSTs `{user_id, latitude, longitude}` (or `{user_id, address}` on fallback) to `v1/spatial/updateVolunteerLocation`. | Verified |
| 15 | The client checks Cognito groups `Volunteers`/`Volunteer` before tracking. This is client-side only and not an enforcement point. | Verified |
| 16 | `endpoints.json` lists only `UPDATE_VOLUNTEER_LOCATION` for Spatial; no webapp caller of `getVolunteerLocation` or `findNearbyVolunteers` was seen in the three files read. | Verified for the 3 files; whole-repo search not done |
| 17 | Groups are read from the **access** token payload, but the Authorization header carries the **ID** token. | Verified |

### 3.4 Mapping Cognito identity to `user_id`

The token carries Cognito claims (`sub`, `email` if the pool exposes it, `cognito:groups`). The DB `user_id` is a different identifier, resolved from email by the Volunteer service. Therefore comparing "token identity" to "body `user_id`" in Spatial needs one of:

1. a **custom claim** carrying the DB id (Unverified whether one exists; none seen in the webapp),
2. a **DB lookup** in Spatial, `users` by email or Cognito `sub` to `user_id` (Unverified whether `users` has an email or `sub` column; `config.TABLE_USERS` is already joined by the nearby query, so Spatial has DB access to that schema),
3. a **call** to `v1/volunteer/getUserIdByEmail` (new cross-service dependency; adds latency and failure modes).

Caching is possible per Lambda container, but entries could go stale if a user's mapping changes.

## 4. Options

| | Description | Cross-team changes | Effort | Risk to webapp | Protects |
|---|---|---|---|---|---|
| **(a)** Derive user from claims; reject body `user_id` that doesn't match | Spatial reads `serverless.authorizer` claims, resolves to DB `user_id` (see 3.4), returns 403 on mismatch. Behind flag `ENFORCE_IDENTITY` (default off). | Gateway owner confirms authorizer and claims. Possibly Cognito/Lambda-trigger change for a custom claim. DB owner confirms `users` columns. | 1.5–2 d | Medium: the webapp already sends its own id, so mismatches should not occur, but a stale or missing `userDbId` (login lookup failure leaves it `null`) must be handled. Flag-off rollout mitigates. | Write path and per-user read |
| **(b)** Gateway-level checks only | Authorizer on all `v1/spatial` routes, optional group check (`Volunteers`). | Gateway owner only. | Small for us; outside this repo | Low | Anonymous access only. Does **not** stop one logged-in user from using another's `user_id`. |
| **(c)** Restrict `GET /getVolunteerLocation` to the volunteer themself or the assigned requester | Needs identity (as in a) plus a request-assignment lookup against the Request tables. | As (a), plus the Request team's schema/semantics. | 2+ d | Low (no known caller of GET) | Read privacy |
| **(d)** Defer and document | Record the gap and owners. | None | Small | None | Nothing |

Not covered by any option above: `findNearbyVolunteers` lets any authenticated caller list volunteers near any point. Suggest an extra decision on whether it should be limited to requester or admin roles (also an identity question).

## 5. Recommendation for D4 (to be confirmed by the Lead)

1. **Do (b) first**, owned by the gateway owner. It is cheap and needs no Spatial change. Confirm it before anything else.
2. **Implement (a) behind `ENFORCE_IDENTITY` (default off)** once questions Q1–Q4 are answered. This is the smallest change that stops one user writing as another, and the flag lets it be enabled only after the webapp is confirmed compatible.
3. **Treat (c) and the `findNearbyVolunteers` exposure as follow-ups**, dependent on product input.
4. If Q1–Q4 can't be answered by Day 5, choose **escalate** for SP-W2-003 (file a GitHub issue with this document) rather than guess at claim structures.

## 6. Open questions

| # | Question | Owner | Why it matters |
|---|---|---|---|
| Q1 | Is there an authorizer on `v1/spatial` routes? Is it a REST Cognito user-pool authorizer or an HTTP API JWT authorizer? Are all three routes covered? | Gateway / AWS owner | Decides whether anonymous access is possible today and where claims appear (`requestContext.authorizer.claims` for REST, `...authorizer.jwt.claims` for HTTP). |
| Q2 | Which claims reach the Lambda: `sub`, `email`, `cognito:groups`, any custom DB-id claim? Is the authorizer set up to validate the **ID** token (the one the webapp sends)? | Gateway owner / Cognito owner | Needed to map identity to `user_id`. |
| Q3 | Does `users` have a column holding email or Cognito `sub`? Which one does `getUserIdByEmail` use? | Volunteer-service / DB owner | Decides option 3.4 route 2 vs 3. |
| Q4 | Is the event payload format 1.0 or 2.0 for this Lambda integration? | Gateway owner | `serverless.authorizer` is populated either way, but the claim path differs. |
| Q5 | Is `serverless-wsgi` pinned anywhere in the deployment package? | Engineer 3 / deployment owner | Behaviour stability. |
| Q6 | Who is allowed to read a volunteer's location (self, assigned requester, admins)? Who may call `findNearbyVolunteers`? | Product / Lead | Needed for option (c). |
| Q7 | Does anything other than the webapp call these endpoints (mobile app, other services)? | Lead | Compatibility when enforcing. |
| Q8 | Does the Request service need Spatial's `user_id` semantics to stay unchanged? (It reads the table directly.) | Request-service owner | Avoids breaking readers when enforcing. |

## 7. Limits of this investigation

- No AWS console or IaC access; nothing about the live gateway, Cognito pool, or Lambda configuration was observed.
- Webapp files were read via raw GitHub for three paths plus `authActions.js`/`authSlice.js`; a full repo search for other callers was not done (the GitHub search API required authentication).
- The `serverless-wsgi` behaviour is from the installed 3.1.0 source in a local virtualenv. The deployed version is Unverified (Q5).
- The `docs/` directory did not exist on this branch (`dev`); this file creates `docs/security/`. Engineer 4 should confirm placement.
