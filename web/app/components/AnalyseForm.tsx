"use client";

import { useState } from "react";
import styles from "./AnalyseForm.module.css";

type TaskResult = {
  status?: string;
  thread_id?: string;
  report?: unknown;
  error?: string;
};

async function parseJson(res: Response) {
  const text = await res.text();
  let data: Record<string, unknown> = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Invalid JSON (${res.status}): ${text.slice(0, 160)}`);
  }
  if (!res.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail ?? data) || `Request failed (${res.status})`,
    );
  }
  return data;
}

async function pollTask(taskId: string): Promise<TaskResult> {
  const started = Date.now();
  const timeoutMs = 15 * 60 * 1000;
  while (Date.now() - started < timeoutMs) {
    const data = await parseJson(
      await fetch(`/api/backend/tasks/${taskId}`, { credentials: "same-origin" }),
    );
    const status = String(data.status || "").toLowerCase();
    if (status === "success") return (data.result as TaskResult) || {};
    if (status === "failed") {
      throw new Error(String(data.error || "Background task failed"));
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("Timed out waiting for background task");
}

export function AnalyseForm() {
  const [cloneUrl, setCloneUrl] = useState("");
  const [filePath, setFilePath] = useState("");
  const [branch, setBranch] = useState("master");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);

  async function onAnalyse(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const queued = await parseJson(
        await fetch("/api/backend/analyse", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            clone_url: cloneUrl.trim(),
            file_path: filePath.trim(),
            branch: branch.trim() || "master",
          }),
        }),
      );
      if (!queued.task_id) throw new Error("Server did not return a task_id");
      const data = await pollTask(String(queued.task_id));
      setThreadId(data.thread_id ?? null);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDecide(decision: "approve" | "reject") {
    if (!threadId) {
      setError("Missing thread_id — run analyse again.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const queued = await parseJson(
        await fetch("/api/backend/approve", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ thread_id: threadId, decision }),
        }),
      );
      if (!queued.task_id) throw new Error("Server did not return a task_id");
      const data = await pollTask(String(queued.task_id));
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.wrap}>
      <form className={styles.form} onSubmit={onAnalyse}>
        <label>
          Repository URL
          <input
            value={cloneUrl}
            onChange={(e) => setCloneUrl(e.target.value)}
            placeholder="https://github.com/org/repo.git"
            required
          />
        </label>
        <label>
          File path
          <input
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder="app.py"
            required
          />
        </label>
        <label>
          Branch
          <input
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="master"
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Working…" : "Analyse"}
        </button>
      </form>

      {error ? <p className={styles.error}>{error}</p> : null}

      {result ? (
        <div className={styles.result}>
          <div className={styles.resultHead}>
            <strong>Status:</strong> {result.status || "unknown"}
            {threadId ? (
              <span className={styles.muted}> · thread {threadId.slice(0, 8)}…</span>
            ) : null}
          </div>
          {result.status === "awaiting_approval" ? (
            <div className={styles.actions}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onDecide("approve")}
              >
                Approve
              </button>
              <button
                type="button"
                className={styles.ghost}
                disabled={busy}
                onClick={() => onDecide("reject")}
              >
                Reject
              </button>
            </div>
          ) : null}
          <pre>{JSON.stringify(result.report ?? result, null, 2)}</pre>
        </div>
      ) : null}
    </div>
  );
}
