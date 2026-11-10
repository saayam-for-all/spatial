# Spatial — Branch policy (`test` / `dev` / `main`)

**Decision recorded:** [#47](https://github.com/saayam-for-all/spatial/issues/47) (2026-11-10)  
**Team Lead (merge to `dev` / `main`):** @Tanmay-Godse  
**Wiki:** Mirror this page on the [spatial wiki](https://github.com/saayam-for-all/spatial/wiki) after the AWS inventory (SP-W1-002) is further along.

---

## Roles of each branch

| Branch | Role | Who writes | Who merges |
| --- | --- | --- | --- |
| **`test`** | **Default branch.** Day-to-day integration line for ongoing Spatial work. | Engineers (feature / fix / docs / ci branches) | Peer review; Team Lead approval for P0 |
| **`dev`** | Stabilized integration line. Team Lead promotes from `test` when a set of changes is ready. | Team Lead (merge from `test`) | Team Lead only |
| **`main`** | Release / protected line. Historically thin (README and LICENSE). Team Lead promotes when appropriate. | Team Lead (merge from `dev` or an agreed cut) | Team Lead only |

---

## Engineer workflow

1. `git fetch origin && git switch test && git pull`
2. Create a branch: `fix/SP-…`, `feature/SP-…`, `docs/SP-…`, or `ci/SP-…`
3. Open a pull request **into `test`**
4. Do **not** open routine pull requests into `dev` or `main` unless the Team Lead asks

### Earlier sprint note (superseded)

Earlier guidance said “branch only from `dev` after SP-W1-004.” **That guidance is superseded.** Per organization decision on [#47](https://github.com/saayam-for-all/spatial/issues/47): use **`test`** as the default integration branch; the Team Lead owns promotion to `dev` and `main`.

---

## Team Lead promotion checklist

When promoting `test` → `dev` (or `dev` → `main`):

- [ ] P0 fixes included (secrets, data integrity, and related)
- [ ] Tests green locally (and CI once SP-W1-012 lands)
- [ ] [`docs/DEPLOYMENT_FACTS.md`](./DEPLOYMENT_FACTS.md) still accurate for deploy-related facts
- [ ] Wiki updated if branch roles or deploy targets changed
- [ ] Team notified which commits landed on `dev` / `main`

---

## Alignment status (as of 2026-11-10)

| Branch | Notable content | Notes |
| --- | --- | --- |
| `test` | #43 secret-print removal, #44 test dependencies, #49 baseline doc, #50 deployment docs; SP-W1-006 write-failure fix applied via #50 | Default working branch |
| `dev` | #48 baseline from `test`, plus #45 write-failure fix | Stabilized line; Lead-managed |
| `main` | Historically README / LICENSE focused | Needs deliberate Lead promotion later — do not merge unfinished sprint work |

---

## Related

- [`docs/DEPLOYMENT_FACTS.md`](./DEPLOYMENT_FACTS.md) — AWS / Lambda / Cognito / SSM facts  
- Tracking issue: [#47](https://github.com/saayam-for-all/spatial/issues/47)
