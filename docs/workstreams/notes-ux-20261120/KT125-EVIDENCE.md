# KT-125 saved smart collections

Status: IN_PROGRESS. Branch codex/kt-125-collections, base e703e40 / PR57.
No merge, deployment, production database, Drive or AI-provider access.

Implemented query-definition model, CRUD/preview/paged dynamic results API,
sidebar SavedCollectionsPanel and main SavedCollectionScreen, existing-field
PropertyChips. Query schema is strict/allowlisted, SQL values are parameters,
group predicates use EXISTS to avoid duplicate Item IDs. No membership writes.

Host integration required: import SavedCollection at bottom of catalog/models.py;
mount collection_api.router in config/api.py. Root owns these shared changes.
Migration0007 depends0004 on this isolated branch; root will reconcile it after
KT122/123 migrations0005/0006. UI: collectionIdFromHash(hash) returns UUID/new;
LibraryScreen main renders SavedCollectionScreen csrf/id when selected, sidebar
renders SavedCollectionsPanel. Folder navigation must not strip collection=.

Current checks: TypeScript/Vite build PASS (existing bundle warning). Backend
6 tests include 30 independently calculated combinations, permissions/CSRF,
dynamic membership, 10k Items/100 groups/5 queries and stable pagination; running.
Native browser and frontend DOM acceptance pending. Read-only metadata only;
author/typed custom fields are not invented from Markdown templates. Kanban,
calendar and workflow triggers remain explicitly optional/deferred phase2.
