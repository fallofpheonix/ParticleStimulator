import { memo } from "react";

const ThemeSelector = memo(function ThemeSelector({ theme, onChange }) {
  return (
    <section className="subpanel">
      <div className="chart-header">
        <h3>Theme</h3>
        <span>{theme}</span>
      </div>
      <div className="actions">
        {["dark", "light"].map((value) => (
          <button
            key={value}
            type="button"
            className={theme === value ? "config-tab config-tab--active" : "ghost"}
            onClick={() => onChange(value)}
          >
            {value}
          </button>
        ))}
      </div>
    </section>
  );
});

export default ThemeSelector;
