import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AccessEvidencePage } from "./AccessEvidencePage";


describe("AccessEvidencePage", () => {
  it("renders the operator evidence intake form", () => {
    render(<AccessEvidencePage onResult={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Access evidence intake" })).toBeTruthy();
    expect(screen.getByLabelText("Source type")).toBeTruthy();
    expect(screen.getByLabelText("Affected user")).toBeTruthy();
    expect(screen.getByLabelText("Affected service/resource")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Analyze evidence" })).toBeTruthy();
  });
});
