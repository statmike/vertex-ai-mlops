# Looker runbook — what Mike does, in order

Follow-along checklist for standing up Path 2 and `p4_looker_ca` on the shared
`marketing-analytics` instance. The *why* behind each step is in
[`looker_setup.md`](looker_setup.md); this file is just the doing.

> ✅ **All steps complete as of 2026-09-01.** Path 2 and `p4_looker_ca` are live and verified;
> `make verify-isolation` covers them. Kept as the rebuild procedure — step 3 is the only part that
> has to be redone by hand, since LookML file content has no write API.

> 🚧 **The instance is shared.** Everything below only ever *adds* objects named
> `data_mcp_sandbox*`. If any step asks you to edit something that already exists, stop — that is a
> bug, and I want to hear about it rather than have you work around it.

---

## Step 0 — already done, nothing for you

For context, so you can tell what's new if you look at the console:

- [x] Looker service agent (`service-1026793852137@gcp-sa-looker.iam.gserviceaccount.com`) granted
      `roles/iam.serviceAccountTokenCreator` on `mcp-sandbox-t0` and `mcp-sandbox-t1`
- [x] `serviceconsumermanagement.googleapis.com` enabled (it was missing; the impersonation chain
      needs it)
- [x] Tier isolation re-verified under impersonation — t0 reads t0 ✅ / t1 ❌, t1 reads t1 ✅ / t0 ❌
- [x] `looker/` regenerated with one connection constant per tier
- [x] `scripts/looker_provision.py` written; `make check` clean
- [x] **Looker API credentials sorted — no new key needed.** See step 1.

Nothing exists on the Looker instance yet.

---

## Step 1 — API credentials *(done, but confirm you're happy with it)*

**No new key. Nothing to generate.**

A working API3 key for this exact instance already existed in another project on this machine — the
SDK reads `looker.ini` from the working directory automatically, which is why setting it up was
forgettable. That key is now **copied into this project** as `looker.ini` (0600, gitignored), and the
cross-project path is gone: nothing here reaches into another repo for a credential.

`looker.ini.template` is the tracked, empty shape of that file, so a collaborator knows what to fill
in without a secret ever being committed.

Verified working:

```
Looker credentials: looker.ini
Acting as: Mike Henderson (id 1)
```

### Why a key is needed at all, when we're using ADC

Two different auth systems, and ADC only covers one of them:

| | Who → what | Auth | Keys? |
|---|---|---|---|
| **Data plane** | Looker → BigQuery | ADC + per-tier impersonation | none |
| **Control plane** | our scripts → Looker API | API3 `client_id`/`secret` | unavoidable |

Looker API 4.0 has no ADC or Google-OAuth equivalent — the "OAuth" in Looker's API docs is CORS for
browser apps, not a substitute credential type. Requests run *as* the Looker user the key belongs to,
which is exactly why the two sweep users created in step 2 are non-admin and model-set scoped.

The two sweep users created in step 2 get their own sections in the same file — `[t0]` and `[t1]` —
written directly by the provisioner rather than printed, so their secrets never reach a terminal,
scrollback, or session transcript.

---

## Step 2 — provisioning ✅ DONE

Applied. All 13 objects created, nothing pre-existing touched:

| Kind | Names |
|---|---|
| Connections | `data_mcp_sandbox_t0`, `data_mcp_sandbox_t1` (ADC + impersonation) |
| Project | `data_mcp_sandbox` (empty shell) |
| Permission set | `data_mcp_sandbox_sweep` |
| Model sets | `data_mcp_sandbox_t0_only`, `data_mcp_sandbox_t1_only` |
| Roles | `data_mcp_sandbox_t0_role`, `data_mcp_sandbox_t1_role` |
| Users | `data_mcp_sandbox t0`, `data_mcp_sandbox t1` (non-admin) |
| OAuth app | `data_mcp_sandbox_agent` |

Created by your own Looker user (Mike Henderson, id 1). The four pre-existing models
(`advanced_ecomm`, `basic_ecomm`, `intermediate_ecomm`, `martech`) were not touched.

**Verified after applying:**

Both connections pass Looker's own tests, which means the ADC → impersonation chain is live and
executing real BigQuery queries:

```
data_mcp_sandbox_t0   [success] connect / kill / query
data_mcp_sandbox_t1   [success] connect / kill / query
```

Containment holds — each sweep user sees exactly one model, its own:

```
tier 0: as 'data_mcp_sandbox t0' (id 2) sees ['data_mcp_sandbox_t0']
tier 1: as 'data_mcp_sandbox t1' (id 3) sees ['data_mcp_sandbox_t1']
```

Neither can see the other tier's model, which matters as much as not seeing the neighbours': that
would have collapsed the tier contrast quietly rather than loudly.

Credentials for both landed in `looker.ini` as `[t0]` and `[t1]`, written directly to the 0600 file
and never echoed.

---

## Step 3 — load the LookML files ✅ DONE

Deployed by Mike on 2026-09-01. All 9 files are in production with the right structure, verified via
`all_project_files`:

```
manifest.lkml
data_mcp_sandbox_t0.model.lkml   data_mcp_sandbox_t0/{transactions,users,events}.view.lkml
data_mcp_sandbox_t1.model.lkml   data_mcp_sandbox_t1/{transactions,users,events}.view.lkml
```

Kept below as the procedure, since it is the one step that has to be repeated by hand if the project
is ever rebuilt.

**Why you and not me:** Looker has no file-write API. `all_project_files` and `project_file` are
read-only (I re-enumerated the SDK to be sure), so LookML content is the one thing that has to arrive
through a browser or a Git remote.

**Where you work:** entirely in the browser, plus a file manager to drag from. No CLI, no gcloud, no
console. Everything below happens at one URL.

**Time:** ~10 minutes. **Nine files, no typing** — they get dragged in, not pasted.

---

### 3.1 — Open the project in Development Mode

At the **bottom of the left navigation panel**, flip **Development Mode** on. Do this first — without
it the project is not editable. Nothing you do is visible to anyone else on this instance until 3.6.

Then go straight to the project's file browser:

> **https://1abfa29a-853e-4cf7-9ad6-8d3c587c4c42.looker.app/projects/data_mcp_sandbox**

You should land in the IDE with an empty **File Browser**. Skip to 3.3.

> 🚫 **If you go via Develop → Manage LookML Projects instead, do not click "Add LookML."** It is
> offered next to the models and it looks like the obvious way in. It is not — it opens Looker's
> legacy *generate-a-model* flow, which writes its own LookML from database tables and would bury the
> hand-authored files this whole experiment depends on. **Configure** next to a model is also not it;
> that edits the model configuration I already created in step 2.

---

### 3.2 — Git repo ✅ DONE, nothing for you

A project created through the API is a shell: Looker lists it as **pending** and refuses to commit or
deploy. That is what you saw, and it was expected rather than a failed run.

It is now cleared. `update_project(git_service_name="bare")` turned out to be the supported way to do
this from the API, so the project has a Looker-hosted bare Git repository and I ran it for you:

```
uses_git      True
can.commit    True
can.deploy    True
branches      ['dev-mike-henderson-frbt', 'master']
```

Bare rather than a GitHub remote on purpose: this LookML is *generated* by
`scripts/generate_lookml.py`, so the repo of record is already this one — a remote would just be a
second copy to keep in sync. Now folded into `scripts/looker_provision.py`, so a fresh run of
`make looker-apply` never leaves a project in the pending state again.

> ⚠️ Bare repo names cannot be reused, so if this project is ever deleted the name
> `data_mcp_sandbox` is spent. Not a problem now — just don't delete and recreate casually.

Looker now hosts the Git history on the Looker server itself. That is the right choice here: this
LookML is *generated* by `scripts/generate_lookml.py`, so the repo of record is already this one — a
GitHub remote would just be a second copy to keep in sync.

> ⚠️ Bare repo names cannot be reused, so if you ever delete this project, the name
> `data_mcp_sandbox` is spent. Not a problem now — just don't delete and recreate casually.

---

### 3.3 — Create the two folders

In the **File Browser** panel, click the **+** icon (**Add file or folder**) → **Create Folder**.

Create these two, exactly (names are case-sensitive, and must match — each model file does
`include: "/data_mcp_sandbox_tN/*.view.lkml"`):

```
data_mcp_sandbox_t0
data_mcp_sandbox_t1
```

---

### 3.4 — Drag the files in, in three passes

The files are on disk at:

```
/home/user/git/vertex-ai-mlops/Applied ML/AI Agents/data-mcp-sandbox/looker/
```

Drag them from your file manager into the Looker IDE. **Dropped files always land at the project
root**, then get moved into place — which is why this is three passes and not one drag.

> 🛑 **Why passes matter.** The two tiers deliberately use *identical* view filenames
> (`transactions.view.lkml` exists in both folders). If you drop all six at once they collide at the
> root and you will silently lose three of them. Move each set into its folder before dropping the
> next.

**Pass 1 — tier 0 views**

Drag these three from `looker/data_mcp_sandbox_t0/`:

```
transactions.view.lkml
users.view.lkml
events.view.lkml
```

Then move all three into the `data_mcp_sandbox_t0` folder — drag each onto the folder, or use the
**Bulk Edit** icon → tick the three → **Move Items** → pick `data_mcp_sandbox_t0` → **Move**.

**Confirm the root is clear of view files before continuing.**

**Pass 2 — tier 1 views**

Same three filenames, but from `looker/data_mcp_sandbox_t1/`. Move them into `data_mcp_sandbox_t1`.

**Pass 3 — the three root files**

Drag these from `looker/` and **leave them at the root**:

```
manifest.lkml
data_mcp_sandbox_t0.model.lkml
data_mcp_sandbox_t1.model.lkml
```

> Do **not** drag `looker/README.md` — that one is our documentation. Looker would treat it as a
> LookML document file and add clutter to the project.

**If drag-and-drop doesn't work for you**, use **+** → the matching file type (or **Folder Options**
→ create-file, for files inside a folder), then paste the contents. To read a file in the terminal:
`cat "looker/data_mcp_sandbox_t1/transactions.view.lkml"`.

You should end up with exactly this:

```
manifest.lkml
data_mcp_sandbox_t0.model.lkml
data_mcp_sandbox_t1.model.lkml
data_mcp_sandbox_t0/
    transactions.view.lkml
    users.view.lkml
    events.view.lkml
data_mcp_sandbox_t1/
    transactions.view.lkml
    users.view.lkml
    events.view.lkml
```

---

### 3.5 — Validate

Click **Validate LookML** (top right of the IDE).

Expected: **clean**. Two things worth knowing so a passing run doesn't look suspicious and a failing
one isn't misdiagnosed:

- **The duplicate view names are correct, not a mistake.** LookML view names collide only when a
  *single model* includes both. Each model here includes only its own folder, which is exactly the
  layout Google's own project-consolidation guidance recommends. I checked this specifically because
  it would otherwise have wasted your ten minutes.
- **Model names are unique instance-wide**, as Looker requires — `data_mcp_sandbox_t0` / `_t1` don't
  collide with the four models already on this instance.

---

### 3.6 — Commit and deploy

1. **Commit Changes & Push** → any message (`Initial LookML for data-mcp-sandbox` is fine).
2. **Deploy to Production**.

Until you deploy, the models exist only in your dev workspace and my checks — which run as the two
non-admin sweep users — will still report them missing.

---

### 3.7 — Check these two things, then hand back

- **Open `data_mcp_sandbox_t0` → Explore → Transactions (tier 0). There must be NO measures.** If
  `total_revenue` shows up here, a tier-1 file landed in the tier-0 folder. That single misplacement
  would leak governance into the control arm and flatten the one contrast this whole experiment is
  built to measure — it is the most consequential thing that can go wrong in this step, and it fails
  silently.
- **`data_mcp_sandbox_t1` → Explore → Transactions (tier 1)** should show a `Total Revenue` measure
  and an `Active User Status` dimension.

✋ **Then tell me it's deployed.** Paste any validator errors rather than fixing them — an error here
almost certainly means `scripts/generate_lookml.py` is wrong, and I'd rather fix the generator than
patch its output and have the next regeneration undo it.

---

## Step 4 — verification ✅ DONE

Nothing for you. Run after your deploy, on 2026-09-01.

```
Looker OK: data_mcp_sandbox_t0, data_mcp_sandbox_t1
```

**Field inventory, read as each sweep user** — the tier contrast is intact:

| | measures | governed dimension |
|---|---|---|
| `data_mcp_sandbox_t0` | *(none)* | absent |
| `data_mcp_sandbox_t1` | `transactions.total_revenue` | `users.active_user_status` |

**The semantic layer returns the governed answers**, matched against BigQuery computed independently
under the tier-1 service account:

| | via Looker | direct BigQuery | trap value if the agent gets it wrong |
|---|---|---|---|
| Net revenue | 4,032,361 | 4,032,361 ✅ | 4,582,096 ignoring refunds (T2) · 31,700,036 from `revenue_amount` (T1) |
| Active users | 2,768 | 2,768 ✅ | 3,520 from `is_active` alone (T3) |

That is the check that mattered most: it proves the LookML encodes the *governed* definitions rather
than merely resolving, and that the traps stay separable through Looker.

**The Path 2 fence holds in both directions**, and it is a real IAM 403 propagated through Looker's
JDBC layer, not a Looker-level ACL:

```
conn t0 -> data t0: 49702 rows      conn t0 -> data t1: Access Denied
conn t1 -> data t1: 49702 rows      conn t1 -> data t0: Access Denied
```

> `Access Denied: Table ...data_mcp_sandbox_t1.transactions_v2_final:
>  User does not have permission to query table`

Path 2 is now behind the same fence as every other arm, which was the open question when this
started.

**Codified, not left as a one-off.** `examples/verify_isolation.py` gained `verify_looker()`, so
`make verify-isolation` now runs 12 Looker checks alongside the rest — all passing. It tests both
axes, because Path 2 is the only path where the agent's identity and the identity that reaches
BigQuery are different accounts:

- **visibility** — each sweep user sees exactly one model, its own (on a shared instance the agent
  picks its model from `get_models`, so visibility is capability);
- **data** — the cross-tier read is refused. Issued deliberately with *admin* credentials: the sweep
  users have no `use_sql_runner`, so testing as the weaker identity would prove the wrong thing. What
  must hold is that even an admin cannot cross tiers through a tier's connection.

---

## Open decisions I need from you eventually (not blocking)

1. **The tokenCreator grant** from step 0 lets *any* connection on this shared instance impersonate
   the tier SAs. I judged that acceptable — those identities are read-only and see only the sandbox's
   trap datasets — but it is a real widening on infrastructure you share. Say the word and I'll
   revoke it and fall back to a Looker-ACL-only fence for Path 2.
2. **A `DATA_QUALITY` scan on the trap tables** (parked in `ROADMAP.md`). It's what would make the
   widened Path 3 catalog surface actually measurable — 10 of the 11 read-only tools I wired return
   nothing against this corpus today. It changes the corpus, so it moves ground truth, which is why
   I haven't done it.

---

## If something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `looker-sdk could not authenticate` | `looker.ini` missing from the project root | Copy `looker.ini.template` and fill in `[Looker]` |
| A create fails with 403/404 | The key in `[Looker]` is not admin after all | Generate a dedicated admin key into that section |
| `Refusing to provision '<name>'` | A `LOOKER_*` name in `.env` drifted outside the sandbox namespace | Working as intended — fix `.env`, don't bypass it |
| Project listed as **pending** | No Git repo yet | `make looker-apply` — `ensure_git` clears it |
| Commit / Deploy buttons greyed out | Same cause: no Git repo | As above |
| Project not visible / not editable | Not in Development Mode | Toggle it at the bottom of the left nav |
| Project suddenly full of unfamiliar views | Someone clicked **Add LookML** | Revert uncommitted changes; see the warning in 3.1 |
| Only 6 of 9 files present after dragging | Both tiers use the same view filenames; a one-shot drop overwrote them | Redo step 3.4 in three passes |
| `Unknown view` / `does not exist in model` | A view file sits at the root instead of its tier folder | Drag it into the folder named after its model |
| Model config "still needs a human" | Files not deployed to production | Finish step 3, re-run |
| Explore resolves but returns no rows | Impersonation chain incomplete | Confirm step 0's grant; IAM takes a few minutes to propagate |
| `403` on your *own* tier | Dataset grant missing | `make setup` |
