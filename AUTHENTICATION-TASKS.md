# Authentication Tasks Roadmap

This document defines the implementation plan to move from custom JWT auth to a migration-safe, enterprise-ready authentication architecture.

## 1) Target Architecture (Decision)

- Adopt an **OIDC-first** design so the app is provider-agnostic.
- Near-term provider: **Keycloak** (self-hosted on VPS) or managed OIDC provider.
- Long-term objective: switch providers (Okta/Auth0/Azure/Entra) via config, not code rewrite.

## 2) Scope and Success Criteria

### In Scope
- Web login/logout/session for frontend and backend APIs.
- User identity mapping to internal user profile.
- Role/permission claims mapping.
- Security hardening, observability, and migration playbook.

### Success Criteria
- Login works through OIDC Authorization Code + PKCE.
- Backend validates tokens from provider JWKS.
- Existing app features continue to work with mapped user identity.
- Provider switch requires only env/config + claim mapping adjustments.

---

## 3) Work Breakdown (Phased Tasks)

## Phase A — Foundation and Design

- [ ] Finalize auth provider strategy (Keycloak now, enterprise migration later).
- [ ] Define required claims contract:
  - [ ] `sub`
  - [ ] `email`
  - [ ] `name`
  - [ ] roles/groups claim path
- [ ] Define internal user mapping model:
  - [ ] `external_subject`
  - [ ] `email`
  - [ ] `display_name`
  - [ ] `roles`
  - [ ] `last_login`
- [ ] Decide session model:
  - [ ] Frontend session storage approach
  - [ ] Backend stateless bearer token validation

Deliverable: signed-off auth design notes + claim mapping contract.

## Phase B — Identity Provider Setup

- [ ] Create provider tenant/realm.
- [ ] Register application clients:
  - [ ] Frontend public client (PKCE)
  - [ ] Backend API audience/scope registration
- [ ] Configure redirect URIs for local/dev/prod.
- [ ] Configure logout redirect URIs.
- [ ] Add provider roles/groups.
- [ ] Add test users and role assignments.

Deliverable: provider metadata documented (issuer, client IDs, endpoints).

## Phase C — Backend Integration (FastAPI)

- [ ] Add OIDC settings to backend config:
  - [ ] issuer URL
  - [ ] audience
  - [ ] JWKS URL (or discover via issuer metadata)
- [ ] Implement JWT verification against provider keys (RS256/ES256 expected).
- [ ] Replace/augment current `get_current_user` dependency to validate provider token.
- [ ] Build user upsert flow:
  - [ ] create internal profile on first login
  - [ ] update profile fields on subsequent logins
- [ ] Implement role mapping middleware/helpers.
- [ ] Gate admin routes by mapped role claim.
- [ ] Keep legacy auth endpoints temporarily behind feature flag for rollback.

Deliverable: backend auth works with provider-issued access tokens.

## Phase D — Frontend Integration (React)

- [ ] Add OIDC client integration (provider-agnostic library pattern).
- [ ] Implement login/logout buttons through provider flow.
- [ ] Handle callback route and token/session state.
- [ ] Update API client to send bearer token to backend.
- [ ] Update auth guard logic for routes/components.
- [ ] Update profile/menu UI to use provider identity fields.
- [ ] Remove direct dependency on local JWT issuance assumptions.

Deliverable: end-to-end browser login and protected route access.

## Phase E — Security Hardening

- [ ] Disable default/placeholder secrets in production.
- [ ] Enforce secure cookie and HTTPS settings in production.
- [ ] Add token validation checks:
  - [ ] issuer
  - [ ] audience
  - [ ] expiry/not-before
  - [ ] algorithm allow-list
- [ ] Add key rotation support (provider-managed key rollover).
- [ ] Add brute-force/abuse protections where applicable.
- [ ] Add auth event audit logging (login success/failure, role-denied).

Deliverable: production-ready auth security baseline.

## Phase F — Testing Strategy

- [ ] Unit tests:
  - [ ] token verification helpers
  - [ ] claims-to-user mapping
  - [ ] role checks
- [ ] Integration tests:
  - [ ] protected endpoints with valid/invalid tokens
  - [ ] first-login user provisioning
- [ ] Smoke tests:
  - [ ] login
  - [ ] protected API call
  - [ ] logout
- [ ] Negative tests:
  - [ ] expired token
  - [ ] wrong audience
  - [ ] missing role for admin route

Deliverable: green auth test suite in CI.

## Phase G — Migration and Cutover

- [ ] Add `AUTH_PROVIDER_MODE` feature flag (`legacy`, `oidc`, `dual`).
- [ ] Run dual mode in staging.
- [ ] Verify analytics and admin behavior with OIDC identities.
- [ ] Run production cutover window.
- [ ] Decommission legacy JWT issuance endpoints after stabilization.

Deliverable: clean migration with rollback path.

---

## 4) Environment Variables Checklist

## Backend

- [ ] `AUTH_PROVIDER_MODE=oidc`
- [ ] `OIDC_ISSUER_URL=`
- [ ] `OIDC_AUDIENCE=`
- [ ] `OIDC_CLIENT_ID=` (if required by validation flow)
- [ ] `ENVIRONMENT=production` (for strict validation behavior)

## Frontend

- [ ] `VITE_OIDC_ISSUER_URL=`
- [ ] `VITE_OIDC_CLIENT_ID=`
- [ ] `VITE_OIDC_REDIRECT_URI=`
- [ ] `VITE_OIDC_POST_LOGOUT_REDIRECT_URI=`
- [ ] `VITE_API_BASE_URL=`

---

## 5) Operational Tasks

- [ ] Backup and disaster recovery plan for identity config.
- [ ] Document emergency admin access procedure.
- [ ] Setup auth dashboards and alerts:
  - [ ] failed logins
  - [ ] token validation errors
  - [ ] unauthorized access spikes
- [ ] Define quarterly key/credential rotation policy.

---

## 6) Team Execution Plan

- [ ] Sprint 1: Phase A + B
- [ ] Sprint 2: Phase C + D
- [ ] Sprint 3: Phase E + F
- [ ] Sprint 4: Phase G + production cutover

---

## 7) Definition of Done

- [ ] OIDC login/logout works in local, staging, production.
- [ ] Role-based authorization verified for all protected endpoints.
- [ ] CI includes auth unit/integration/smoke tests.
- [ ] Runbooks and env docs updated.
- [ ] Legacy JWT path removed or explicitly retained with owner approval.

---

## 8) Priority Order (What to do next)

### P0 — Immediate (this week)

- [ ] Set production-safe auth environment values on VPS:
  - `ENVIRONMENT=production`
  - `DEBUG=false`
  - strong `JWT_SECRET_KEY`
- [ ] Finish backend token validation hardening and regression tests.
- [ ] Lock deployment baseline on Contabo using `CONTABO-HOSTING.md`.

### P1 — Near-Term

- [ ] Implement provider-agnostic OIDC auth path in backend/frontend.
- [ ] Keep legacy JWT flow behind `AUTH_PROVIDER_MODE` for rollback.
- [ ] Add role/claim mapping and enforce admin authorization via claims.

### P2 — Pre-Enterprise

- [ ] Run dual-auth staging cutover (`legacy` + `oidc`) and validate metrics.
- [ ] Add migration runbook for enterprise IdP switch (Okta/Auth0/Azure/Entra).
- [ ] Decommission legacy JWT issuance once OIDC is stable in production.
