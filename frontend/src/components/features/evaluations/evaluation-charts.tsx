"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ChartRecord = {
  name: string;
  passed: number;
  review: number;
  failed: number;
  total: number;
};

export function OutcomeDistributionChart({
  title,
  description,
  data,
}: {
  title: string;
  description: string;
  data: ChartRecord[];
}) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-5" aria-labelledby={`${title.replaceAll(" ", "-").toLowerCase()}-title`}>
      <h2 id={`${title.replaceAll(" ", "-").toLowerCase()}-title`} className="text-base font-semibold text-neutral-900">{title}</h2>
      <p className="mt-1 text-sm text-neutral-600">{description}</p>
      <div className="mt-5 h-80" role="img" aria-label={`${title}. Passed, provider-review, and failed quality-gate case counts.`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 12, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="var(--neutral-200)" horizontal={false} />
            <XAxis type="number" allowDecimals={false} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={170} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <Tooltip cursor={{ fill: "var(--neutral-50)" }} />
            <Legend />
            <Bar dataKey="passed" name="Passed" fill="var(--success-700)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
            <Bar dataKey="review" name="Review provider" fill="var(--warning-700)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
            <Bar dataKey="failed" name="Failed quality gate" fill="var(--error-700)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export function ScoreDistributionChart({
  title,
  description,
  data,
}: {
  title: string;
  description: string;
  data: Array<{ name: string; score: number }>;
}) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-5" aria-labelledby={`${title.replaceAll(" ", "-").toLowerCase()}-title`}>
      <h2 id={`${title.replaceAll(" ", "-").toLowerCase()}-title`} className="text-base font-semibold text-neutral-900">{title}</h2>
      <p className="mt-1 text-sm text-neutral-600">{description}</p>
      <div className="mt-5 h-[420px]" role="img" aria-label={`${title}. Raw decimal score values.`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 12, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="var(--neutral-200)" horizontal={false} />
            <XAxis type="number" domain={[0, 1]} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={170} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <Tooltip cursor={{ fill: "var(--neutral-50)" }} />
            <Bar dataKey="score" name="Raw score" fill="var(--teal-700)" radius={[0, 4, 4, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
