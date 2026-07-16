import { CasesWorkspace } from "@/components/features/evaluations/cases-workspace";
import { DiagnosticRunNotice, EvaluationErrorState } from "@/components/features/evaluations/evaluation-shared";
import { PageHeader } from "@/components/system/page-header";
import { loadEvaluationPageState } from "@/lib/api/evaluations";

export default async function EvaluationCasesPage() {
  const state = await loadEvaluationPageState();
  return (
    <>
      <PageHeader title="Evaluation cases" description="Filter benchmark cases, inspect structured diagnostics, and trace evidence, completeness, confidence, and provider outcomes." />
      {state.state === "error" ? <EvaluationErrorState state={state} /> : <><DiagnosticRunNotice data={state.data} /><CasesWorkspace data={state.data} /></>}
    </>
  );
}
