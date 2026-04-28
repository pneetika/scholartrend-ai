import { describe, expect, it } from "vitest";

import { durationLabel, formatScore } from "./format";

describe("format helpers", () => {
  it("formats scores as percentages", () => {
    expect(formatScore(0.84)).toBe("84%");
  });

  it("formats durations with seconds for longer spans", () => {
    expect(
      durationLabel("2026-01-01T00:00:00.000Z", "2026-01-01T00:00:01.250Z"),
    ).toBe("1.3 s");
  });
});

