import { FileSearch, ListChecks, Lock } from "lucide-react";

const GUARANTEES = [
  { icon: ListChecks, label: "No black-box score" },
  { icon: FileSearch, label: "Evidence trails" },
  { icon: Lock, label: "Your data, in memory" },
];

export function Hero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="shell hero__grid">
        <div className="hero__copy">
          <p className="kicker">
            <span className="kicker__rule" aria-hidden="true" />
            01 / INTERNSHIP INSTRUMENT
          </p>
          <h1 id="hero-title">
            Know where you stand.
            <br />
            <span className="hero__underline">Before you apply.</span>
          </h1>
          <p className="hero__lede">
            Evaluate hard academic eligibility, verify skill evidence, align practical
            preferences, and inspect listing warnings — with visible rules and rationales,
            not an opaque score.
          </p>
          <ul className="guarantees" aria-label="Product guarantees">
            {GUARANTEES.map(({ icon: Icon, label }) => (
              <li key={label} className="guarantee">
                <Icon size={14} aria-hidden="true" />
                <span>{label}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="hero__art" aria-hidden="true">
          <div className="specimen-back" />
          <div className="specimen">
            <p className="specimen__eyebrow mono">ELIGIBILITY AUDIT</p>
            <div className="specimen__rows">
              <div className="specimen__row">
                <span className="mono">ELIGIBILITY</span>
                <strong className="mono">ELIGIBLE</strong>
              </div>
              <div className="specimen__row">
                <span className="mono">FIT</span>
                <strong className="mono">72 / 100</strong>
              </div>
              <div className="specimen__row">
                <span className="mono">EVIDENCE</span>
                <strong className="mono">4 OF 6</strong>
              </div>
            </div>
            <div className="specimen__stamp mono">SPECIMEN — NOT A PREDICTION</div>
          </div>
        </div>
      </div>
    </section>
  );
}
