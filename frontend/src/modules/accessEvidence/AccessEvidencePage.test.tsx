import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import { AccessEvidencePage } from "./AccessEvidencePage";


describe("AccessEvidencePage", () => {
  it("renders the operator evidence intake workspace", () => {
    const { container } = render(<AccessEvidencePage onResult={vi.fn()} />);

    expect(container.textContent).toContain("Access evidence intake");
    expect(container.textContent).toContain("Analyze evidence");
    expect(container.textContent).toContain("Generic access log text");
  });
});
