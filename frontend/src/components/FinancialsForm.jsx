import { Field, Input } from "./ui";

export const BALANCE_SHEET_FIELDS = [
  ["cash_and_equivalents", "Cash & equivalents"],
  ["receivables", "Receivables"],
  ["inventory", "Inventory"],
  ["other_current_assets", "Other current assets"],
  ["fixed_assets", "Fixed assets"],
  ["current_liabilities", "Current liabilities"],
  ["payables", "Payables"],
  ["long_term_debt", "Long-term debt"],
  ["equity", "Equity"],
];

export const INCOME_STATEMENT_FIELDS = [
  ["revenue", "Revenue"],
  ["cogs", "Cost of goods sold"],
  ["operating_expenses", "Operating expenses"],
  ["depreciation", "Depreciation"],
  ["interest_expense", "Interest expense"],
  ["net_income", "Net income"],
];

export function emptyYear() {
  return {
    balance_sheet: Object.fromEntries(BALANCE_SHEET_FIELDS.map(([k]) => [k, ""])),
    income_statement: Object.fromEntries(INCOME_STATEMENT_FIELDS.map(([k]) => [k, ""])),
  };
}

function NumberGrid({ section, fields, values, onChange, labelMap }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {fields.map(([key, label]) => (
        <Field key={key} label={label}>
          <Input
            type="number"
            step="any"
            value={values?.[key] ?? ""}
            onChange={(e) => onChange(section, key, e.target.value)}
          />
          {labelMap?.[key] && (
            <span className="block text-xs text-inkmuted mt-1 italic">from: "{labelMap[key]}"</span>
          )}
        </Field>
      ))}
    </div>
  );
}

export default function FinancialsForm({
  financialYear,
  onFinancialYearChange,
  current,
  onChangeCurrent,
  priorYear,
  onChangePrior,
  includePriorYear,
  onToggleIncludePriorYear,
  fieldLabels,
}) {
  return (
    <div className="space-y-8">
      <Field label="Financial year">
        <Input
          placeholder="e.g. FY2024-25"
          value={financialYear}
          onChange={(e) => onFinancialYearChange(e.target.value)}
        />
      </Field>

      <div>
        <h3 className="font-medium text-ink mb-3">Balance sheet</h3>
        <NumberGrid
          section="balance_sheet"
          fields={BALANCE_SHEET_FIELDS}
          values={current.balance_sheet}
          onChange={onChangeCurrent}
          labelMap={fieldLabels}
        />
      </div>

      <div>
        <h3 className="font-medium text-ink mb-3">Income statement</h3>
        <NumberGrid
          section="income_statement"
          fields={INCOME_STATEMENT_FIELDS}
          values={current.income_statement}
          onChange={onChangeCurrent}
          labelMap={fieldLabels}
        />
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm font-medium text-ink mb-3">
          <input type="checkbox" checked={includePriorYear} onChange={(e) => onToggleIncludePriorYear(e.target.checked)} />
          Add prior year (needed for cash flow, DSCR, and growth ratios)
        </label>
        {includePriorYear && priorYear && (
          <div className="space-y-6 pl-6 border-l-2 border-border">
            <div>
              <h4 className="text-sm font-medium text-inkmuted mb-3">Prior year balance sheet</h4>
              <NumberGrid
                section="balance_sheet"
                fields={BALANCE_SHEET_FIELDS}
                values={priorYear.balance_sheet}
                onChange={onChangePrior}
              />
            </div>
            <div>
              <h4 className="text-sm font-medium text-inkmuted mb-3">Prior year income statement</h4>
              <NumberGrid
                section="income_statement"
                fields={INCOME_STATEMENT_FIELDS}
                values={priorYear.income_statement}
                onChange={onChangePrior}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
