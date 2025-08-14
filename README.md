# Viewcraft
A modern, type-safe approach to composable Django class-based views.

> **Status:** Major rewrite in progress. API is still settling; code samples and docs will follow once stable.

## What it is

Viewcraft lets you assemble class-based views from small, reusable components with strict typing. Components attach to well-defined lifecycle hooks (e.g., before/after `dispatch`, `get_queryset`, `get_context_data`, or HTTP method handlers) and run in a predictable order.

## Why

* **Composable:** Add, remove, or reorder behavior without mixin soup.
* **Type-safe:** Designed for `mypy --strict`.
* **Pragmatic defaults:** Works out of the box; configurable when you need it.
* **Reusable configs:** Ship and share drop-in configurations for common behaviors.

## How it works (concept)

* You write component methods and mark when they should run using decorators that map to view lifecycle points (e.g., “before `get_queryset`”, “after `get_context_data`”, “after `post`”).
* Components can expose small, serializable “config” objects you reuse across views (e.g., `Ordering(fields=..., default=...)`), so teams share behavior without re-implementing it.
* Built-ins will cover common needs (ordering, search, pagination); writing your own follows the same pattern.

## Examples (conceptual)

* **Ordering:** Runs *after `get_queryset`* to apply `?order=` criteria with safe, declared fields.
* **Search:** Runs *after `get_queryset`* to filter by query terms without hand-rolling Q objects in each view.
* **Pagination:** Runs *after `get_context_data`* to attach a `page_obj` and page URLs using current filter/order state.
* **Permissions gate:** Runs *before `dispatch`* to enforce access rules early.
* **Audit log:** Runs *after `post`* to record who changed what, with the final object and response status in hand.
* **Query shaping:** Runs *before `get_queryset`* to add `select_related`/`prefetch_related` consistently.

## Philosophy

* Minimal surface area; predictable extension points.
* Config first: reusable, composable “configs” for team-wide consistency.
* Linted (Ruff) and typed end-to-end.

## Coming next

* Public API for lifecycle decorators and component registration
* Built-in components (ordering, search, pagination) with reusable configs
* Short, copy-pasteable examples once the API is locked
