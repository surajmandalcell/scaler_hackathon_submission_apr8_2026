import { useState } from "react";
import DataEntry from "./admin/DataEntry.jsx";
import Upload from "./admin/Upload.jsx";
import TestRun from "./admin/TestRun.jsx";
import AnswerKey from "./admin/AnswerKey.jsx";

const ADMIN_TABS = [
  { id: "data",   label: "Data Entry" },
  { id: "upload", label: "Upload" },
  { id: "test",   label: "Test Run" },
  { id: "answer", label: "Answer Key" },
];

export default function AdminView({ taskId, setTaskId, scenario, onStoreMutated }) {
  const [tab, setTab] = useState("data");

  return (
    <div className="md-stack-lg">
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Admin sub-tabs">
        {ADMIN_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`md-tab md-tab-sub ${tab === t.id ? "is-active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="md-axis-y" key={tab}>
        {tab === "data"   && <DataEntry onStoreMutated={onStoreMutated} scenario={scenario} />}
        {tab === "upload" && <Upload onStoreMutated={onStoreMutated} />}
        {tab === "test"   && <TestRun taskId={taskId} setTaskId={setTaskId} />}
        {tab === "answer" && <AnswerKey taskId={taskId} setTaskId={setTaskId} />}
      </div>
    </div>
  );
}
