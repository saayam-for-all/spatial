# Spatial — Deployment Facts

**Task:** SP-W1-002 (P0)  
**Owner:** Lead (@Tanmay-Godse) — covering Engineer 4 until assigned  
**Last updated:** 2026-11-10  
**Tracking:** [#47](https://github.com/saayam-for-all/spatial/issues/47)

Status labels used below:

| Label | Meaning |
| --- | --- |
| **Verified** | Confirmed from code, Git history, or an admin answer |
| **Unknown** | Needs AWS console / DevSecOps / frontend confirmation |
| **Decision** | Org/process rule from admin (Sugandha, 2026-11-10) |

---

## 1. Branch & merge policy

| Fact | Status | Source |
| --- | --- | --- |
| Default working branch is **`test`** | **Decision** | Sugandha, 2026-11-10 |
| Lead merges into **`dev`** and **`main`** | **Decision** | Sugandha, 2026-11-10 |
| Engineers open PRs against **`test`** | **Decision** | Follows default-branch rule |
| `main` today is mostly README + LICENSE | **Verified** | Git history on `main` |
| Sprint security/reliability fixes landed on `dev` via #43–#45 / #48; this PR also brings SP-W1-006 onto `test` | **Verified** | GitHub PRs |

See also: [`docs/BRANCHES.md`](./BRANCHES.md).

---

## 2. Lambda handlers in this repository

Source inventory of every `lambda_handler` in the repo:

| # | File | Handler string (typical) | What it does | Likely status |
| --- | --- | --- | --- | --- |
| A | [`lambda_function.py`](../lambda_function.py) | `lambda_function.lambda_handler` | Bridges API Gateway → Flask (`serverless_wsgi`). Strips `/v1/spatial` and `/dev/spatial/v0.0.1` then routes to `app.py`. | **Intended current** entry for `v1/spatial` — **Unknown** if this is what AWS actually runs |
| B | [`find_nearest_volunteers.py`](../find_nearest_volunteers.py) | `find_nearest_volunteers.lambda_handler` | Standalone POST “nearby volunteers” using **tile** search and older `user_location` / `users` tables | **Legacy** — **Unknown** if still deployed |
| C | [`get_user_location.py`](../get_user_location.py) | `get_user_location.lambda_handler` | Standalone GET location by `user_id` path param; older schema | **Legacy** — **Unknown** if still deployed |
| D | [`put_user_location.py`](../put_user_location.py) | `put_user_location.lambda_handler` | Standalone POST update location (IP/address); older schema | **Legacy** — **Unknown** if still deployed |

Flask routes served when (A) is the handler ([`app.py`](../app.py)):

| Method | Path (after prefix strip) | Purpose |
| --- | --- | --- |
| POST | `/updateVolunteerLocation` | Save volunteer location (GPS or address) |
| POST | `/findNearbyVolunteers` | Nearby search via PostGIS helper |
| GET | `/getVolunteerLocation` | Latest location for a `user_id` |

### Historical deploy clue (not live proof)

| Fact | Status | Source |
| --- | --- | --- |
| Branch `lambda-ci-test-sudarshan` pointed at Lambda **`saayam-geo-spatial-lambda`** (`us-east-1`), Python 3.9, handler **`find_nearest_volunteers.lambda_handler`** | **Verified** (git history only) | Sprint branch audit / #47 |
| Whether that function still exists or still uses that handler | **Unknown** | Needs AWS |

### Admin actions required once AWS is checked

Per Sugandha:

1. If a handler / function is **not active** → remove it (AWS + eventually dead code in repo).
2. If a handler / function **is active** → create a **wiki page** describing it.
3. Standalone Lambdas (B–D): either **stale (delete)** or **still used by frontend** — confirm with AWS list + frontend team.

---

## 3. API Gateway / Cognito

| Fact | Status | Source |
| --- | --- | --- |
| Clients call `v1/spatial/...` (webapp / mobileapp endpoint maps) | **Verified** | Client `endpoints.json` (see SP-W1-011) |
| Cognito authentication / authorization is owned by the **frontend** team | **Decision** | Sugandha, 2026-11-10 |
| Whether Spatial Lambda / API Gateway stage still needs a Cognito authorizer configured on the Spatial side | **Unknown** | Worth checking with frontend + API Gateway; feeds SP-W1-009 |
| Authorizer type / name on `v1/spatial` today | **Unknown** | Needs AWS |

---

## 4. Credentials / Parameter Store / secrets

| Fact | Status | Source |
| --- | --- | --- |
| Password-print bug fixed on `test`/`dev` (#43) | **Verified** | PR #43 |
| Rotate DB password because of those prints | **Not needed** (DB refreshed) | Sugandha → closed #46 |
| Branch `AWSintegration` has SSM helper; example path `/dev/saayam/db/Virginia/Spatial/user` | **Verified** (code on branch) | `AWSintegration` |
| Whether SSM is live for the **currently deployed** Lambda | **Unknown** | Sugandha: figure out **after** live handler is identified (blocks SP-W1-013) |
| Lambda IAM: `ssm:GetParameter` / `kms:Decrypt` | **Unknown** | Needs AWS once function name is known |

---

## 5. CloudWatch

| Fact | Status | Source |
| --- | --- | --- |
| CloudWatch access can be granted **if** an active Lambda is identified | **Decision** | Sugandha, 2026-11-10 |
| Lead will request access naming specific function(s) after inventory | Pending | Blocked on AWS list |

---

## 6. Open checklist (Lead / DevSecOps)

Copy into AWS session notes; mark Verified when done.

- [ ] List all Lambdas whose name or tags suggest Spatial / geo / location
- [ ] For each: **Function name**, **Runtime**, **Handler**, **Last modified**, **Last invoke** (if available)
- [ ] Match handler string to row A–D above (or “other”)
- [ ] Confirm API Gateway routes for `v1/spatial` → which Lambda
- [ ] Confirm whether B–D are invoked by frontend or orphaned
- [ ] For each **active** function: draft wiki page; request CloudWatch for Lead
- [ ] For each **inactive** function: propose delete (admin approval)
- [ ] Only then resume SP-W1-013 (SSM) against the live function

---

## 7. Related sprint work

| ID | Impact of this doc |
| --- | --- |
| SP-W1-013 | Blocked until live handler + SSM facts are known |
| SP-W1-009 | Prefer “frontend owns Cognito”; only add Spatial-side checks if Gateway still requires / if product asks |
| SP-W1-011 | Client paths assume `v1/spatial` + Cognito token from frontend |
| SP-W2-007 | Wiki pages for active Lambdas + three branches |

---

## 8. Change log

| Date | Change |
| --- | --- |
| 2026-11-10 | Initial doc from CodeGraph handler inventory + Sugandha answers; #46 closed; Lead owns E4/SP-W1-002 |
