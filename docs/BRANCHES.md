# Spatial — Branch policy (`test` / `dev` / `main`)

**Decision owner:** Sugandha (2026-11-10)  
**Repo Lead (merge to `dev` / `main`):** @Tanmay-Godse  
**Wiki:** Mirror this page on the [spatial wiki](https://github.com/saayam-for-all/spatial/wiki) once AWS inventory (SP-W1-002) is further along.

---

## Roles of each branch

| Branch | Role | Who writes | Who merges |
| --- | --- | --- | --- |
| **`test`** | **Default branch.** Day-to-day integration line for the Spatial sprint and ongoing work. | Engineers (feature / fix / docs / ci branches) | Peer review + Lead for P0 |
| **`dev`** | Stabilized integration line. Lead promotes from `test` when a set of changes is ready. | Lead (merge from `test`) | Lead only |
| **`main`** | Release / protected line. Currently thin (README + LICENSE historically). Lead promotes when appropriate. | Lead (merge from `dev` or agreed cut) | Lead only |

---

## Engineer workflow

1. `git fetch origin && git switch test && git pull`
2. Branch: `fix/SP-…`, `feature/SP-…`, `docs/SP-…`, or `ci/SP-…`
3. Open PR **into `test`**
4. Do **not** open routine PRs into `dev` or `main` unless Lead asks

### After 2026-11-06 note (superseded)

Earlier sprint guidance said “branch only from `dev` after SP-W1-004.” **That is superseded.** Per admin: stay on **`test`** as the default integration branch; Lead owns promotion to `dev` / `main`.

---

## Lead promotion checklist

When promoting `test` → `dev` (or `dev` → `main`):

- [ ] P0 fixes included (secrets, data integrity, etc.)
- [ ] Tests green locally (and CI once SP-W1-012 lands)
- [ ] `docs/DEPLOYMENT_FACTS.md` still accurate for anything deploy-related
- [ ] Wiki updated if branch roles or deploy targets changed
- [ ] Announce to the team which SHAs landed on `dev` / `main`

---

## Alignment status (as of 2026-11-10)

| Branch | Notable content | Gap |
| --- | --- | --- |
| `test` | #43 secret-print removal, #44 test deps; this PR also syncs #45 (SP-W1-006) | Was missing SP-W1-006 until this PR |
| `dev` | #48 baseline from `test` + #45 write-failure fix | Ahead of `test` before this sync |
| `main` | README / LICENSE heavy historically | Needs deliberate Lead promotion later — do not dump sprint WIP |

---

## Related

- [`docs/DEPLOYMENT_FACTS.md`](./DEPLOYMENT_FACTS.md) — AWS / Lambda / Cognito / SSM facts  
- Sprint plan (local): `spatial-engineering-plan/SPATIAL_MASTER_EXECUTION_PLAN.md`
