# ClaimWise frontend

This is the frontend for `insurance_project/backend`. It reuses the ClaimWise design from the reference project.

From this directory:

```powershell
npm.cmd ci
npm.cmd run dev
```

Open http://localhost:5173 and choose Client or Employee. Run FastAPI on port 8000. Configure `VITE_API_BASE_URL` in `.env.local` when using a different API address.

The temporary local Client workspace uses customer `C1001`. Sessions are saved under `claimwise-insurance-project-session`, independently of the reference application's session. This is a local demo, not authentication or backend access control.

Claims, counts, and analyses come from the API. Lists use the backend's default limit of 50 records. Analysis runs only when the employee presses Run analysis or Refresh analysis. Status decision and history controls remain unavailable because those backend routes are placeholders.

Submission requires an existing customer/policy relationship. Enter a real policy ID, not its policy number. Optional incident fields can be left blank. The backend stores the claim; the UI then opens its details and shows success feedback.

```powershell
npm.cmd run build
```

This checks all TypeScript and generates `dist/`.
