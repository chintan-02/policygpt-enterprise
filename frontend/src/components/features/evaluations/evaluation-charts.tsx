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

type ChartRecord = { name: string; passed: number; review: number; total: number };

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
      <div className="mt-5 h-72" role="img" aria-label={`${title}. Passed and review-required case counts.`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 20 }}>
            <CartesianGrid stroke="var(--neutral-200)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "var(--neutral-600)", fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={52} />
            <YAxis allowDecimals={false} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <Tooltip cursor={{ fill: "var(--neutral-50)" }} />
            <Legend />
            <Bar dataKey="passed" name="Passed" fill="var(--success-700)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="review" name="Needs review" fill="var(--error-700)" radius={[4, 4, 0, 0]} />
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
      <div className="mt-5 h-72" role="img" aria-label={`${title}. Raw decimal score values.`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -8, bottom: 20 }}>
            <CartesianGrid stroke="var(--neutral-200)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "var(--neutral-600)", fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={52} />
            <YAxis domain={[0, 1]} tick={{ fill: "var(--neutral-600)", fontSize: 11 }} />
            <Tooltip cursor={{ fill: "var(--neutral-50)" }} />
            <Bar dataKey="score" name="Raw score" fill="var(--teal-700)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
