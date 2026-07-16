import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { EngineeringPanel } from "./engineering-panel";

describe("EngineeringPanel", () => {
  it("renders confidence engineering details collapsed by default", () => {
    const markup = renderToStaticMarkup(
      createElement(
        EngineeringPanel,
        { title: "Confidence engineering details" },
        "Raw confidence metrics",
      ),
    );

    expect(markup).toContain('<details data-default-state="collapsed"');
    expect(markup).not.toContain("<details open");
  });
});
