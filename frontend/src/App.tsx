import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  applyBulkMap,
  applyEdit,
  createJob,
  deleteJob,
  exportJob,
  getIssues,
  getJob,
  getRows,
} from "./api";
import type { Issue, JobState, RowsResponse } from "./types";

type View = "upload" | "overview" | "issues" | "rows";

const DEFAULT_PAGE_SIZE = 10;

export default function App() {
  const [view, setView] = useState<View>("upload");
  const [job, setJob] = useState<JobState | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [rows, setRows] = useState<RowsResponse | null>(null);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(DEFAULT_PAGE_SIZE);
  const [filters, setFilters] = useState<
    { column: string; op: "eq" | "neq" | "contains" | "is_null"; value?: string }[]
  >([]);
  const [error, setError] = useState<{ status?: number; message: string } | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const canonicalColumns = useMemo(
    () => job?.dataset?.canonical_columns ?? [],
    [job]
  );

  useEffect(() => {
    if (view === "issues" && job) {
      setLoading(true);
      setError(null);
      getIssues(job.job_id)
        .then((data) => setIssues(data))
        .catch((err) => handleError(err, setError, () => resetJob(setJob, setView)))
        .finally(() => setLoading(false));
    }
  }, [view, job]);

  useEffect(() => {
    if (view === "rows" && job) {
      setLoading(true);
      setError(null);
      getRows(job.job_id, offset, limit, filters)
        .then((data) => setRows(data))
        .catch((err) => handleError(err, setError, () => resetJob(setJob, setView)))
        .finally(() => setLoading(false));
    }
  }, [view, job, offset, limit]);

  useEffect(() => {
    if (view === "rows" && job) {
      getIssues(job.job_id)
        .then((data) => setIssues(data))
        .catch((err) => handleError(err, setError, () => resetJob(setJob, setView)));
    }
  }, [view, job]);

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const created = await createJob(file);
      setJob(created);
      setView("rows");
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setLoading(false);
    }
  };

  const refreshJob = async () => {
    if (!job) return;
    setLoading(true);
    setError(null);
    try {
      const latest = await getJob(job.job_id);
      setJob(latest);
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!job) return;
    const confirmed = window.confirm("Delete this job and all stored files?");
    if (!confirmed) return;
    setLoading(true);
    setError(null);
    try {
      await deleteJob(job.job_id);
      setJob(null);
      setIssues([]);
      setRows(null);
      setView("upload");
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setLoading(false);
    }
  };

  const handleSingleEdit = async (
    rowId: string,
    column: string,
    value: string
  ) => {
    if (!job) return;
    setLoading(true);
    setError(null);
    try {
      const result = await applyEdit(job.job_id, rowId, column, value);
      setJob((current) =>
        current
          ? { ...current, validation: result.validation ?? null, issues: result.issues }
          : current
      );
      if (view === "issues") {
        setIssues(result.issues);
      }
      if (view === "rows") {
        const updated = await getRows(job.job_id, offset, limit, filters);
        setRows(updated);
      }
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setLoading(false);
    }
  };

  const handleBulkMap = async (payload: {
    column: string;
    apply_to?: "all" | "missing" | "errors";
    mapping?: Record<string, string | null>;
    defaultValue?: string;
    replaceFrom?: string;
    replaceTo?: string;
  }) => {
    if (!job) return;
    setLoading(true);
    setError(null);
    try {
      const result = await applyBulkMap(job.job_id, payload);
      setJob((current) =>
        current
          ? { ...current, validation: result.validation ?? null, issues: result.issues }
          : current
      );
      if (view === "issues") {
        setIssues(result.issues);
      }
      if (view === "rows") {
        const updated = await getRows(job.job_id, offset, limit, filters);
        setRows(updated);
      }
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!job) return;
    setExporting(true);
    setError(null);
    try {
      const blob = await exportJob(job.job_id);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "databuddy_export.csv";
      anchor.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      handleError(err, setError, () => resetJob(setJob, setView));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <img src="/logo.svg" alt="Databuddy HR logo" />
          <div>
            <h1>Databuddy HR</h1>
            <p>Upload, validate, and export HR census files.</p>
          </div>
        </div>
        <div className="header-meta">
          <div className="status-pill">
            {job ? `Job status: ${job.status}` : "No active job"}
          </div>
          {job && (
            <nav>
              <button onClick={() => setView("overview")}>Overview</button>
              <button onClick={() => setView("issues")}>Issues</button>
              <button onClick={() => setView("rows")}>Rows</button>
            </nav>
          )}
        </div>
      </header>

      {error && (
        <div className="alert">
          <strong>{error.status ?? "Error"}:</strong> {error.message}
        </div>
      )}
      {loading && <div className="status">Loading…</div>}
      {exporting && <div className="status">Exporting…</div>}

      {view === "upload" && (
        <UploadView onUpload={handleUpload} disabled={loading} />
      )}

      {view === "overview" && job && (
        <OverviewView
          job={job}
          onRefresh={refreshJob}
          onDelete={handleDelete}
          onExport={handleExport}
          disabled={loading || exporting}
        />
      )}

      {view === "issues" && job && (
        <IssuesView issues={issues} />
      )}

      {view === "rows" && job && (
        <RowsView
          rows={rows}
          columns={canonicalColumns}
          issues={issues}
          offset={offset}
          limit={limit}
          total={rows?.total_filtered ?? rows?.total_rows ?? 0}
          filters={filters}
          onFilterChange={(next) => {
            setFilters(next);
            setOffset(0);
          }}
          onCellEdit={handleSingleEdit}
          onBulkMap={handleBulkMap}
          disabled={loading}
          onPrev={() => setOffset(Math.max(0, offset - limit))}
          onNext={() => setOffset(offset + limit)}
          onLimitChange={(value) => {
            setLimit(value);
            setOffset(0);
          }}
        />
      )}
    </div>
  );
}

function UploadView({
  onUpload,
  disabled,
}: {
  onUpload: (file: File) => void;
  disabled: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);

  return (
    <section className="card">
      <h2>Upload</h2>
      <p>Select a CSV or XLSX file to start a new job.</p>
      <input
        type="file"
        accept=".csv,.xlsx"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        disabled={disabled}
      />
      <button
        className="primary"
        onClick={() => file && onUpload(file)}
        disabled={!file || disabled}
      >
        Upload file
      </button>
    </section>
  );
}

function OverviewView({
  job,
  onRefresh,
  onDelete,
  onExport,
  disabled,
}: {
  job: JobState;
  onRefresh: () => void;
  onDelete: () => void;
  onExport: () => void;
  disabled: boolean;
}) {
  const dataset = job.dataset;
  const validation = job.validation;

  return (
    <section className="stack">
      <div className="card">
        <h2>Job Overview</h2>
        <div className="grid">
          <div>
            <h3>Dataset</h3>
            {dataset ? (
              <ul>
                <li>Total rows: {dataset.total_rows}</li>
                <li>Total columns: {dataset.total_columns}</li>
                <li>
                  Canonical columns: {dataset.canonical_columns.join(", ")}
                </li>
                <li>
                  Unknown columns: {dataset.unknown_columns.join(", ") || "None"}
                </li>
              </ul>
            ) : (
              <p>No dataset metadata yet.</p>
            )}
          </div>
          <div>
            <h3>Validation</h3>
            {validation ? (
              <ul>
                <li>Errors: {validation.error_count}</li>
                <li>Warnings: {validation.warning_count}</li>
                <li>Last validated: {validation.last_validated_at}</li>
              </ul>
            ) : (
              <p>No validation summary yet.</p>
            )}
          </div>
        </div>
        <div className="actions">
          <button onClick={onRefresh} disabled={disabled}>
            Refresh
          </button>
          <button onClick={onExport} disabled={disabled}>
            Export CSV
          </button>
          <button className="danger" onClick={onDelete} disabled={disabled}>
            Delete Job
          </button>
        </div>
      </div>
    </section>
  );
}

function IssuesView({ issues }: { issues: Issue[] }) {
  return (
    <section className="card">
      <h2>Issues</h2>
      {issues.length === 0 ? (
        <p>No issues found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Severity</th>
              <th>Type</th>
              <th>Row</th>
              <th>Column</th>
              <th>Message</th>
              <th>Suggestion</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <tr key={`${issue.type}-${issue.row_id}-${index}`}>
                <td>{issue.severity}</td>
                <td>{issue.type}</td>
                <td>{issue.row_id ?? "-"}</td>
                <td>{issue.column ?? "-"}</td>
                <td>{issue.message}</td>
                <td>{issue.suggestion ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function RowsView({
  rows,
  columns,
  issues,
  offset,
  limit,
  total,
  filters,
  onFilterChange,
  onCellEdit,
  onBulkMap,
  disabled,
  onPrev,
  onNext,
  onLimitChange,
}: {
  rows: RowsResponse | null;
  columns: string[];
  issues: Issue[];
  offset: number;
  limit: number;
  total: number;
  filters: { column: string; op: "eq" | "neq" | "contains" | "is_null"; value?: string }[];
  onFilterChange: (
    next: { column: string; op: "eq" | "neq" | "contains" | "is_null"; value?: string }[]
  ) => void;
  onCellEdit: (rowId: string, column: string, value: string) => void;
  onBulkMap: (payload: {
    column: string;
    apply_to?: "all" | "missing" | "errors";
    mapping?: Record<string, string | null>;
    defaultValue?: string;
    replaceFrom?: string;
    replaceTo?: string;
  }) => void;
  disabled: boolean;
  onPrev: () => void;
  onNext: () => void;
  onLimitChange: (value: number) => void;
}) {
  const [column, setColumn] = useState(columns[0] ?? "");
  const [defaultValue, setDefaultValue] = useState("");
  const [localEdits, setLocalEdits] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<{ value: string; label: string } | null>(
    null
  );
  const [filterColumn, setFilterColumn] = useState(columns[0] ?? "");
  const [filterOp, setFilterOp] = useState<"eq" | "neq" | "contains" | "is_null">(
    "eq"
  );
  const [filterValue, setFilterValue] = useState("");
  const [bulkScope, setBulkScope] = useState<"all" | "missing" | "errors">("all");
  const [replaceFrom, setReplaceFrom] = useState("");
  const [replaceTo, setReplaceTo] = useState("");

  useEffect(() => {
    if (columns.length && !columns.includes(column)) {
      setColumn(columns[0]);
    }
  }, [columns, column]);

  useEffect(() => {
    if (columns.length && !columns.includes(filterColumn)) {
      setFilterColumn(columns[0]);
    }
  }, [columns, filterColumn]);

  useEffect(() => {
    setLocalEdits({});
  }, [rows]);

  const issueMap = useMemo(() => {
    const map = new Map<string, Issue>();
    for (const issue of issues) {
      if (!issue.row_id || !issue.column) continue;
      map.set(`${issue.row_id}:${issue.column}`, issue);
    }
    return map;
  }, [issues]);

  const visibleRows = rows?.rows ?? [];

  const handleChange = (rowId: string, col: string, value: string) => {
    setLocalEdits((prev) => ({ ...prev, [`${rowId}:${col}`]: value }));
  };

  const handleBlur = (rowId: string, col: string, original: string | null) => {
    const key = `${rowId}:${col}`;
    const next = localEdits[key];
    if (next === undefined) return;
    const originalValue = original ?? "";
    if (next === originalValue) return;
    onCellEdit(rowId, col, next);
    setLocalEdits((prev) => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });
  };

  return (
    <section className="card">
      <h2>Rows</h2>
      <div className="card inset">
        <h3>Bulk map (set all values)</h3>
        <form
          className="form"
          onSubmit={(event) => {
            event.preventDefault();
            if (column) {
              onBulkMap({
                column,
                apply_to: bulkScope,
                mapping: replaceFrom ? { [replaceFrom]: replaceTo } : {},
                defaultValue: defaultValue || undefined,
                replaceFrom: replaceFrom || undefined,
                replaceTo: replaceTo || undefined,
              });
            }
          }}
        >
          <label>
            Column
            <select
              value={column}
              onChange={(e) => setColumn(e.target.value)}
              disabled={disabled}
            >
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </label>
          <label>
            Scope
            <select
              value={bulkScope}
              onChange={(event) =>
                setBulkScope(event.target.value as typeof bulkScope)
              }
              disabled={disabled}
            >
              <option value="all">All rows</option>
              <option value="missing">Missing only</option>
              <option value="errors">Errors only</option>
            </select>
          </label>
          <label>
            Replace from
            <input
              value={replaceFrom}
              onChange={(e) => setReplaceFrom(e.target.value)}
              disabled={disabled}
            />
          </label>
          <label>
            Replace to
            <input
              value={replaceTo}
              onChange={(e) => setReplaceTo(e.target.value)}
              disabled={disabled}
            />
          </label>
          <label>
            Default value
            <input
              value={defaultValue}
              onChange={(e) => setDefaultValue(e.target.value)}
              disabled={disabled}
            />
          </label>
          <button className="primary" type="submit" disabled={disabled}>
            Apply bulk map
          </button>
        </form>
      </div>
      <div className="actions">
        <button onClick={onPrev} disabled={disabled || offset === 0}>
          Previous
        </button>
        <button onClick={onNext} disabled={disabled || offset + limit >= total}>
          Next
        </button>
        <label>
          Page size
          <select
            value={limit}
            onChange={(event) => onLimitChange(Number(event.target.value))}
            disabled={disabled}
          >
            {[5, 10, 20, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <div className="filter-bar">
          <label>
            Filter column
            <select
              value={filterColumn}
              onChange={(event) => setFilterColumn(event.target.value)}
              disabled={disabled}
            >
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </label>
          <label>
            Op
            <select
              value={filterOp}
              onChange={(event) =>
                setFilterOp(event.target.value as typeof filterOp)
              }
              disabled={disabled}
            >
              <option value="eq">equals</option>
              <option value="neq">not equal</option>
              <option value="contains">contains</option>
              <option value="is_null">is empty</option>
            </select>
          </label>
          {filterOp !== "is_null" && (
            <label>
              Value
              <input
                value={filterValue}
                onChange={(event) => setFilterValue(event.target.value)}
                disabled={disabled}
              />
            </label>
          )}
          <button
            type="button"
            onClick={() => {
              if (!filterColumn) return;
              const next = [
                {
                  column: filterColumn,
                  op: filterOp,
                  value: filterOp === "is_null" ? undefined : filterValue,
                },
              ];
              onFilterChange(next);
            }}
            disabled={disabled}
          >
            Apply filter
          </button>
          <button
            type="button"
            onClick={() => {
              onFilterChange([]);
            }}
            disabled={disabled || filters.length === 0}
          >
            Clear
          </button>
        </div>
      </div>
      {rows ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row) => (
                <tr key={row.row_id as string}>
                  {columns.map((col) => {
                    const key = `${row.row_id as string}:${col}`;
                    const value =
                      localEdits[key] ?? ((row[col] as string | null) ?? "");
                    const issue = issueMap.get(key);
                    const tooltip = issue
                      ? `${issue.severity.toUpperCase()}: ${issue.message}${
                          issue.suggestion ? ` (${issue.suggestion})` : ""
                        }`
                      : "";
                    const showExpand = value.length > 24;
                    return (
                      <td key={col}>
                        <div className="cell">
                          <input
                            value={value}
                            onChange={(event) =>
                              handleChange(
                                row.row_id as string,
                                col,
                                event.target.value
                              )
                            }
                            onBlur={() =>
                              handleBlur(
                                row.row_id as string,
                                col,
                                row[col] as string | null
                              )
                            }
                            disabled={disabled}
                            className={
                              issue
                                ? issue.severity === "warning"
                                  ? "cell-input warning"
                                  : "cell-input error"
                                : "cell-input"
                            }
                          />
                          {issue && (
                            <span className="cell-flag" data-tooltip={tooltip}>
                              !
                            </span>
                          )}
                          {showExpand && (
                            <button
                              className="cell-expand"
                              type="button"
                              onClick={() =>
                                setExpanded({ value, label: `${col}` })
                              }
                            >
                              View
                            </button>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>Loading rows…</p>
      )}
      {expanded && (
        <div className="modal-backdrop" onClick={() => setExpanded(null)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <h4>{expanded.label}</h4>
            <pre>{expanded.value}</pre>
            <button onClick={() => setExpanded(null)}>Close</button>
          </div>
        </div>
      )}
    </section>
  );
}

function handleError(
  err: unknown,
  setError: (value: { status?: number; message: string } | null) => void,
  onNotFound: () => void
) {
  if (err instanceof ApiError) {
    if (err.status === 404) {
      onNotFound();
    }
    setError({ status: err.status, message: err.message });
    return;
  }
  setError({
    message: err instanceof Error ? err.message : "Something went wrong",
  });
}

function resetJob(
  setJob: (value: JobState | null) => void,
  setView: (value: View) => void
) {
  setJob(null);
  setView("upload");
}
