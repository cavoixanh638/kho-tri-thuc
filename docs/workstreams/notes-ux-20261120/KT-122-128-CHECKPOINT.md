# KT-122–128 delivery checkpoint

Status: IN_PROGRESS. User explicitly assigned KT-122–128.
Base PR57: e00b3cacd02decdb852dc6e17e7b297d83acaccf, OPEN/unmerged.
Branch codex/knowledge-journeys; new PR must target codex/notes-ux-integration.
No PR57/main writes, no merge, no deployment, no production data or provider.

Entry: INDEX.md + G00-FEATURE-TRACEABILITY.md and the seven task specifications.
Current main docs1f64f50 were carried into this branch without changing code.
Historical CURRENT_STATE additions are reconciled only by root at integration.

Owners/dependencies:
- explorer: KT122+123 placement/hierarchy models/services/API/explorer UI and
  their migrations, owner/cycle/concurrency/capture/lazy-scale tests.
- navigation: KT124 wiki-link authoring/UUID links/TOC/palette/context panels,
  components and independent tests; root mounts App/ItemScreen common glue.
- collections: KT125 saved filter model/API/UI/properties and query validation,
  dynamic membership, owner/30-combination/10k tests; root mounts common glue.
- root: KT126 clipper/annotations; KT127 portable vault after placement/hierarchy
  contract; KT128 actual browser journeys, integration, docs and final CI.

Independent workers start from the same baseline; unique branch/worktree and
checkpoint each. Models/import/router/UI conflicts resolved by root, not force
push. Worker PRs target PR57 branch; final combined candidate also targets PR57.

Completion: visible usable journeys for every required KT122–127 behavior,
PostgreSQL safety/scale/portable roundtrip, real Chromium1920/1440/768/390,
raw note/UUID/Event/Asset preservation, final-head CI, pushed evidence and PRs.
External Android/native IME/production Drive/PDF/100GB remain NOT_RUN without
evidence. No unit-only UX_COMPLETE claim. Optional phase2/KT129/130 stays deferred.

Tests: NOT_RUN on new work. Next: implement isolated scopes, pin contracts for
vault/host glue, run and fix joint journeys, update traceability/checkpoints.
