import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

export function Button({
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={`button ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Input({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`field ${className}`} {...props} />;
}

export function Select({
  className = "",
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`field ${className}`} {...props} />;
}

export function Textarea({
  className = "",
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea className={`field min-h-32 resize-y ${className}`} {...props} />
  );
}

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="space-y-2 text-sm font-medium text-ink">
      <span className="flex items-center justify-between gap-2">
        {label}
        {hint && <span className="font-normal text-muted">{hint}</span>}
      </span>
      {children}
      {error && (
        <span className="block text-xs font-normal text-coral">{error}</span>
      )}
    </label>
  );
}

export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <section className={`card ${className}`}>{children}</section>;
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`status status-${status}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink md:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-2xl border border-line bg-white/60 text-sm text-muted">
      <span className="pulse-dot mr-2" />
      {label}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center rounded-2xl border border-dashed border-line bg-white/50 px-6 text-center">
      <p className="font-display text-lg font-semibold text-ink">{title}</p>
      <p className="mt-2 max-w-sm text-sm leading-6 text-muted">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-coral/20 bg-coral/5 px-5 py-4 text-sm text-coral">
      <p className="font-semibold">Something needs attention</p>
      <p className="mt-1 text-coral/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 font-semibold underline underline-offset-4"
        >
          Try again
        </button>
      )}
    </div>
  );
}
