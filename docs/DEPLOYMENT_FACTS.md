# Spatial — Deployment Facts

**Task:** SP-W1-002 (P0)  
**Owner:** Team Lead (@Tanmay-Godse) — covering Engineer 4 until assigned  
**Last updated:** 2026-11-10  
**Tracking:** [#47](https://github.com/saayam-for-all/spatial/issues/47)

Status labels used below:

| Label | Meaning |
| --- | --- |
| **Verified** | Confirmed from repository source, Git history, or an admin decision recorded on #47 |
| **Unknown** | Needs AWS console / DevSecOps / frontend confirmation |
| **Decision** | Organization process rule recorded on #47 (2026-11-10) |

---

## 1. Branch and merge policy

| Fact | Status | Source |
| --- | --- | --- |
| Default working branch is **`test`** | **Decision** | [#47](https://github.com/saayam-for-all/spatial/issues/47) (2026-11-10) |
| Team Lead merges into **`dev`** and **`main`** | **Decision** | [#47](https://github.com/saayam-for-all/spatial/issues/47) (2026-11-10) |
| Engineers open pull requests against **`test`** | **Decision** | Follows default-branch rule |
| `main` currently contains primarily README and LICENSE | **Verified** | Git history on `main` |
| Sprint security and reliability fixes are on `dev` (#43–#45, #48); SP-W1-006 was also applied on `test` (#50) | **Verified** | GitHub pull requests |

See also: [`docs/BRANCHES.md`](./BRANCHES.md).

---

## 2. Lambda handlers in this repository

Inventory of every `lambda_handler` defined in the repository:

| # | File | Handler string (typical) | Purpose | Likely status |
| --- | --- | --- | --- | --- |
| A | [`lambda_function.py`](../lambda_function.py) | `lambda_function.lambda_handler` | Bridges API Gateway to Flask (`serverless_wsgi`). Strips `/v1/spatial` and `/dev/spatial/v0.0.1`, then routes to `app.py`. | Intended current entry for `v1/spatial` — **Unknown** whether AWS runs this handler today |
| B | [`find_nearest_volunteers.py`](../find_nearest_volunteers.py) | `find_nearest_volunteers.lambda_handler` | Standalone POST nearby-volunteer search using tile-based lookup and older `user_location` / `users` tables | Legacy — **Unknown** if still deployed |
| C | [`get_user_location.py`](../get_user_location.py) | `get_user_location.lambda_handler` | Standalone GET location by `user_id` path parameter; older schema | Legacy — **Unknown** if still deployed |
| D | [`put_user_location.py`](../put_user_location.py) | `put_user_location.lambda_handler` | Standalone POST location update (IP / address); older schema | Legacy — **Unknown** if still deployed |

Flask routes served when handler A is configured ([`app.py`](../app.py)):

| Method | Path (after prefix strip) | Purpose |
| --- | --- | --- |
| POST | `/updateVolunteerLocation` | Save volunteer location (GPS or address) |
| POST | `/findNearbyVolunteers` | Nearby search via PostGIS helper |
| GET | `/getVolunteerLocation` | Latest location for a `user_id` |

### Historical deployment clue (not live proof)

| Fact | Status | Source |
| --- | --- | --- |
| Branch `lambda-ci-test-sudarshan` referenced Lambda **`saayam-geo-spatial-lambda`** (`us-east-1`), Python 3.9, handler **`find_nearest_volunteers.lambda_handler`** | **Verified** (Git history only) | Branch audit / [#47](https://github.com/saayam-for-all/spatial/issues/47) |
| Whether that function still exists or still uses that handler | **Unknown** | Needs AWS |

### Follow-up once AWS is checked

Per admin guidance on [#47](https://github.com/saayam-for-all/spatial/issues/47):

1. If a function or handler is **not active**, remove it (AWS configuration, and eventually unused repository code).
2. If a function or handler **is active**, publish a wiki page describing it.
3. For standalone Lambdas (B–D): confirm whether each is **stale (delete)** or **still used by the frontend** (AWS inventory plus frontend confirmation).

---

## 3. API Gateway and Cognito

| Fact | Status | Source |
| --- | --- | --- |
| Clients call `v1/spatial/...` (webapp and mobileapp endpoint maps) | **Verified** | Client `endpoints.json` (see SP-W1-011) |
| Cognito authentication and authorization are owned by the **frontend** team | **Decision** | [#47](https://github.com/saayam-for-all/spatial/issues/47) (2026-11-10) |
| Whether the Spatial API Gateway stage still requires a Cognito authorizer on the Spatial side | **Unknown** | Confirm with frontend and API Gateway; feeds SP-W1-009 |
| Authorizer type / name on `v1/spatial` today | **Unknown** | Needs AWS |

---

## 4. Credentials, Parameter Store, and secrets

| Fact | Status | Source |
| --- | --- | --- |
| Database configuration print statements removed from `test` / `dev` | **Verified** | [PR #43](https://github.com/saayam-for-all/spatial/pull/43) |
| Rotate the database password because of those prints | **Not required** (database refreshed) | [#46](https://github.com/saayam-for-all/spatial/issues/46) (closed) |
| Branch `AWSintegration` includes an SSM helper; example parameter path `/dev/saayam/db/Virginia/Spatial/user` | **Verified** (code on branch) | [`AWSintegration`](https://github.com/saayam-for-all/spatial/tree/AWSintegration) |
| Whether SSM is live for the **currently deployed** Lambda | **Unknown** | Confirm after the live handler is identified (blocks SP-W1-013) |
| Lambda IAM permissions for `ssm:GetParameter` / `kms:Decrypt` | **Unknown** | Needs AWS once the function name is known |

---

## 5. CloudWatch

| Fact | Status | Source |
| --- | --- | --- |
| CloudWatch access can be granted once an active Lambda is identified | **Decision** | [#47](https://github.com/saayam-for-all/spatial/issues/47) (2026-11-10) |
| Team Lead will request access by naming specific function(s) after inventory | Pending | Blocked on AWS list |

---

## 6. Open checklist (Team Lead / DevSecOps)

Use during the AWS review; mark items **Verified** when complete.

- [ ] List all Lambdas whose name or tags suggest Spatial / geo / location
- [ ] For each: **function name**, **runtime**, **handler**, **last modified**, **last invoke** (if available)
- [ ] Match handler string to row A–D above (or “other”)
- [ ] Confirm API Gateway routes for `v1/spatial` → which Lambda
- [ ] Confirm whether B–D are invoked by the frontend or are orphaned
- [ ] For each **active** function: draft wiki page; request CloudWatch for the Team Lead
- [ ] For each **inactive** function: propose deletion (admin approval)
- [ ] Only then resume SP-W1-013 (SSM) against the live function

---

## 7. Related sprint work

| ID | Impact of this document |
| --- | --- |
| SP-W1-013 | Blocked until the live handler and SSM facts are known |
| SP-W1-009 | Prefer “frontend owns Cognito”; add Spatial-side checks only if API Gateway still requires them or product asks |
| SP-W1-011 | Client paths assume `v1/spatial` and a Cognito token attached by the frontend |
| SP-W2-007 | Wiki pages for active Lambdas and the three Git branches |

---

## 8. Change log

| Date | Change |
| --- | --- |
| 2026-11-10 | Initial document: repository handler inventory, admin decisions from [#47](https://github.com/saayam-for-all/spatial/issues/47), [#46](https://github.com/saayam-for-all/spatial/issues/46) closed; Team Lead owns E4 / SP-W1-002 |
| 2026-11-10 | Editorial pass: professional wording for repository documentation |
