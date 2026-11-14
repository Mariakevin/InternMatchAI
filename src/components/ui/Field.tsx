import type { ReactNode } from "react";

type FieldProps = {
  htmlFor: string;
  label: string;
  required?: boolean;
  action?: ReactNode;
  help?: string;
  error?: string;
  children: ReactNode;
  className?: string;
};

export function Field({
  htmlFor,
  label,
  required = false,
  action,
  help,
  error,
  children,
  className,
}: FieldProps) {
  return (
    <div className={["field", className ?? ""].filter(Boolean).join(" ")}>
      <div className="field__head">
        <label className="field__label" htmlFor={htmlFor}>
          {label}
          {required ? (
            <span className="field__required" aria-hidden="true">
              {" *"}
            </span>
          ) : null}
        </label>
        {action}
      </div>
      {children}
      {help ? (
        <p className="field__help" id={`${htmlFor}-help`}>
          {help}
        </p>
      ) : null}
      {error ? (
        <p className="field__error" id={`${htmlFor}-error`} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
