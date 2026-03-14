import { memo } from "react";
import { useFormContext } from "react-hook-form";

const fieldValueAsNumber = (type) => type === "range" || type === "number";

export const SectionDivider = memo(function SectionDivider({ title, hint }) {
  return (
    <div className="config-section-divider">
      <div>
        <h3>{title}</h3>
        {hint ? <p>{hint}</p> : null}
      </div>
    </div>
  );
});

export const RangeField = memo(function RangeField({
  name,
  label,
  min,
  max,
  step,
  unit,
  hint,
  type = "range"
}) {
  const {
    register,
    watch,
    formState: { errors }
  } = useFormContext();
  const value = watch(name);
  const error = errors[name];

  return (
    <label className="config-field">
      <div className="config-field-head">
        <span>{label}</span>
        <strong>
          {value}
          {unit ? <small>{unit}</small> : null}
        </strong>
      </div>
      <input
        {...register(name, {
          valueAsNumber: fieldValueAsNumber(type),
          min: { value: min, message: `min ${min}` },
          max: { value: max, message: `max ${max}` }
        })}
        type={type}
        min={min}
        max={max}
        step={step}
      />
      {hint ? <small className="field-hint">{hint}</small> : null}
      {error ? <small className="field-error">{error.message}</small> : null}
    </label>
  );
});

export const SelectField = memo(function SelectField({ name, label, options, hint }) {
  const {
    register,
    formState: { errors }
  } = useFormContext();
  const error = errors[name];

  return (
    <label className="config-field">
      <div className="config-field-head">
        <span>{label}</span>
      </div>
      <select {...register(name)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      {hint ? <small className="field-hint">{hint}</small> : null}
      {error ? <small className="field-error">{error.message}</small> : null}
    </label>
  );
});

export const ToggleField = memo(function ToggleField({ name, label, hint }) {
  const { register, watch } = useFormContext();
  const value = watch(name);

  return (
    <label className="toggle-field">
      <span>
        <strong>{label}</strong>
        {hint ? <small>{hint}</small> : null}
      </span>
      <input {...register(name)} type="checkbox" checked={Boolean(value)} />
    </label>
  );
});
