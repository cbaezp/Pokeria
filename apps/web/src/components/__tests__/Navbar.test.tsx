import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Navbar } from "@/components/Navbar";
import { GameConfigurationProvider } from "@/lib/game-configuration-context";
import { ProfileProvider } from "@/lib/profile-context";
import { ThemeProvider } from "@/lib/theme";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("Navbar", () => {
  it("renders brand title and all primary navigation links", () => {
    render(
      <ThemeProvider>
        <ProfileProvider>
          <GameConfigurationProvider>
            <Navbar />
          </GameConfigurationProvider>
        </ProfileProvider>
      </ThemeProvider>,
    );

    expect(screen.getByText("POKERIA")).toBeInTheDocument();
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Practice")).toBeInTheDocument();
    expect(screen.getByText("Strategy Library")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("Simulate")).toBeInTheDocument();
  });

  it("renders theme toggle button with accessible label", () => {
    render(
      <ThemeProvider>
        <ProfileProvider>
          <GameConfigurationProvider>
            <Navbar />
          </GameConfigurationProvider>
        </ProfileProvider>
      </ThemeProvider>,
    );

    const toggleBtn = screen.getByRole("button", { name: /switch to/i });
    expect(toggleBtn).toBeInTheDocument();
  });
});
