"use client";

import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { OutcomeCards } from "@/components/features/evaluations/evaluation-shared";
import { Button } from "@/components/ui/button";
import {
  adaptEvaluationArtifact,
  type EvaluationViewModel,
} from "@/lib/domain/evaluation";
import {
  type OverviewEvaluationState,
  prepareOverviewEvaluationCards,
  prepareOverviewEvaluationPlaceholders,
} from "@/lib/domain/overview";
import { formatEvaluationDate } from "@/lib/formatters/evaluation";

type EvaluationPanelState =
  | { state: "ready"; data: EvaluationViewModel }
  | { state: OverviewEvaluationState };

function errorStateForStatus(status: number): OverviewEvaluationState {
  if (status === 404) return "not_found";
  if (status === 422) return "invalid";
  return "unavailable";
}

async function fetchLatestEvaluation(
  signal?: AbortSignal,
): Promise<EvaluationPanelState> {
  try {
    const response = await fetch("/api/evaluations/latest", {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal,
    });
    if (!response.ok) {
      return { state: errorStateForStatus(response.status) };
    }
    const payload: unknown = await response.json().catch(() => null);
    return { state: "ready", data: adaptEvaluationArtifact(payload) };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    return { state: "unavailable" };
  }
}

export function OverviewEvaluationPanel() {
  const [panel, setPanel] = useState<EvaluationPanelState>({ state: "loading" });
  const [refreshing, setRefreshing] = useState(false);

  const refreshLatest = useCallback(async () => {
    setRefreshing(true);
    setPanel(await fetchLatestEvaluation());
    setRefreshing(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void fetchLatestEvaluation(controller.signal)
      .then(setPanel)
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  const cards =
    panel.state === "ready"
      ? prepareOverviewEvaluationCards(panel.data)
      : prepareOverviewEvaluationPlaceholders(panel.state);
  const updatedAt =
    panel.state === "ready"
      ? formatEvaluationDate(panel.data.artifact.updated_at)
      : null;

  return (
    <section aria-labelledby="latest-evaluation-heading">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="latest-evaluation-heading" className="text-lg font-semibold text-neutral-900">
            Latest evaluation
          </h2>
          {updatedAt && updatedAt !== "N/A" ? (
            <p className="font-metric mt-1 text-xs text-neutral-500">
              Updated {updatedAt} UTC
            </p>
          ) : null}
          <p className="mt-1 text-sm text-neutral-600">
            Read-only metrics from the latest validated benchmark artifact.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => void refreshLatest()}
          disabled={refreshing}
        >
          <RefreshCw aria-hidden="true" className={refreshing ? "animate-spin" : ""} />
          Refresh evaluation
        </Button>
      </div>
      <OutcomeCards cards={cards} />
    </section>
  );
}
