import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  CardBadge,
  CardHand,
  CommunityBoard,
  getSuitColorClass,
  PlayingCard,
  parseCard,
} from "@/components/table/PlayingCard";

describe("PlayingCard Component Suite", () => {
  describe("parseCard utility", () => {
    it("parses valid card strings properly", () => {
      expect(parseCard("Ah")).toEqual({ isFacedown: false, rank: "A", suit: "h" });
      expect(parseCard("kd")).toEqual({ isFacedown: false, rank: "K", suit: "d" });
      expect(parseCard("10s")).toEqual({ isFacedown: false, rank: "10", suit: "s" });
      expect(parseCard("Tc")).toEqual({ isFacedown: false, rank: "T", suit: "c" });
    });

    it("identifies facedown cards", () => {
      expect(parseCard("hidden").isFacedown).toBe(true);
      expect(parseCard("??").isFacedown).toBe(true);
      expect(parseCard("back").isFacedown).toBe(true);
      expect(parseCard("XX").isFacedown).toBe(true);
    });
  });

  describe("Color semantics", () => {
    it("applies 2-color casino deck rules", () => {
      expect(getSuitColorClass("h", false)).toBe("text-red-600");
      expect(getSuitColorClass("d", false)).toBe("text-red-600");
      expect(getSuitColorClass("s", false)).toBe("text-slate-900");
      expect(getSuitColorClass("c", false)).toBe("text-slate-900");
    });

    it("applies 4-color online poker deck rules", () => {
      expect(getSuitColorClass("h", true)).toBe("text-red-600");
      expect(getSuitColorClass("d", true)).toBe("text-blue-600");
      expect(getSuitColorClass("c", true)).toBe("text-emerald-600");
      expect(getSuitColorClass("s", true)).toBe("text-slate-900");
    });
  });

  describe("Card rendering and structure", () => {
    it("renders uniform card anatomy with centered top rank and middle symbol", () => {
      render(<PlayingCard card="Kh" size="lg" />);
      expect(screen.getByTestId("card-center-top-rank")).toHaveTextContent("K");
      expect(screen.getByRole("img", { name: "King of Hearts" })).toBeInTheDocument();
    });

    it("renders 10 cleanly with rank and suit", () => {
      render(<PlayingCard card="10s" size="md" tenFormat="10" />);
      expect(screen.getByTestId("card-center-top-rank")).toHaveTextContent("10");
      expect(screen.getByRole("img", { name: "Ten of Spades" })).toBeInTheDocument();
    });

    it("renders facedown card with solid luxury back and test id", () => {
      render(<PlayingCard card="hidden" size="md" />);
      expect(screen.getByRole("img", { name: "Face-down card" })).toBeInTheDocument();
      expect(screen.getByTestId("playing-card-facedown")).toBeInTheDocument();
    });

    it("renders small cards with centered top rank and big symbol in middle", () => {
      render(<PlayingCard card="Ah" size="sm" />);
      expect(screen.getByTestId("card-center-top-rank")).toHaveTextContent("A");
      expect(screen.getByRole("img", { name: "Ace of Hearts" })).toBeInTheDocument();
    });
  });

  describe("CardHand component", () => {
    it("renders hole cards together", () => {
      render(<CardHand cards={["As", "Ks"]} size="md" overlap={true} />);
      expect(screen.getByRole("img", { name: "Ace of Spades" })).toBeInTheDocument();
      expect(screen.getByRole("img", { name: "King of Spades" })).toBeInTheDocument();
    });
  });

  describe("CommunityBoard component", () => {
    it("renders board cards and empty slots for remaining streets", () => {
      render(<CommunityBoard cards={["Ah", "Kd", "Qc"]} size="md" showPlaceholders={true} />);
      expect(screen.getByRole("img", { name: "Ace of Hearts" })).toBeInTheDocument();
      expect(screen.getByRole("img", { name: "King of Diamonds" })).toBeInTheDocument();
      expect(screen.getByRole("img", { name: "Queen of Clubs" })).toBeInTheDocument();
      // Should show TURN and RIVER placeholder slots
      expect(screen.getByText("TURN")).toBeInTheDocument();
      expect(screen.getByText("RIVER")).toBeInTheDocument();
    });
  });

  describe("CardBadge component", () => {
    it("renders inline text card chip", () => {
      render(<CardBadge card="Qd" fourColor={true} />);
      expect(screen.getByText("Q")).toBeInTheDocument();
    });
  });
});
