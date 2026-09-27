# Insurance Claim Analysis frontend

React/Vite interface for client claims and employee analysis/review. Follow the
[root setup guide](../README.md) for the database, backend, models, and Clerk.

From `frontend/`, copy `.env.example` to `.env.local` on a new checkout. Set
`VITE_CLERK_PUBLISHABLE_KEY` from the same Clerk instance as the backend and
`VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`. Never put backend secrets in Vite variables.

```sh
npm ci
npm run dev
# TypeScript check and production bundle:
npm run build
```

Use http://localhost:5173 consistently with backend `FRONTEND_ORIGIN`.
Client/Employee selection chooses the workspace, not an authorization role.
Clerk handles sign-in, client sign-up, verification, sessions, and sign-out.
Clients link an existing demo Customer ID once; employees require a locally
provisioned mapping via `backend/scripts/create_user.py`. The backend database
role remains authoritative; selecting another workspace cannot grant access.

The API client obtains a Clerk bearer token for each request. Clients can submit
and view their own claims. Employees can inspect claims, run/retrieve analyses,
view similarity/history, and perform review/status actions. Data comes from the
backend; no AI results are fabricated. Analysis runs on explicit employee action.
The default claim list limit is 50. Customer linking is a controlled-demo feature,
not verification of real-world customer ownership. See the root README limitations.
