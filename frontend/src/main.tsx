import { ClerkProvider } from "@clerk/react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { SessionProvider } from "./services/session";
import "./styles.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {publishableKey ? <ClerkProvider publishableKey={publishableKey} afterSignOutUrl="/login">
    <BrowserRouter>
      <SessionProvider>
        <App />
      </SessionProvider>
    </BrowserRouter>
    </ClerkProvider> : <p role="alert">Set VITE_CLERK_PUBLISHABLE_KEY in frontend/.env.local to enable sign-in.</p>}
  </StrictMode>,
);
