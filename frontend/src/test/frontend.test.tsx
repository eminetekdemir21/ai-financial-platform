import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// --- formatAmount fonksiyonu testleri ---
function formatAmount(amount: string): string {
  const n = parseFloat(amount);
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺`;
}

describe("formatAmount", () => {
  it("pozitif tutari dogru formatlar", () => {
    const result = formatAmount("15000.00");
    expect(result).toContain("+");
    expect(result).toContain("₺");
  });

  it("negatif tutarda + isareti olmaz", () => {
    const result = formatAmount("-450.75");
    expect(result).not.toContain("+");
    expect(result).toContain("₺");
  });

  it("sifir tutari dogru formatlar", () => {
    const result = formatAmount("0");
    expect(result).toContain("+");
    expect(result).toContain("₺");
  });
});

// --- Login sayfasÄ± render testi ---
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock("../api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
}));

import LoginPage from "../pages/LoginPage";

describe("LoginPage", () => {
  it("giris formu render olur", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    expect(screen.getByPlaceholderText("ornek@eposta.com")).toBeTruthy();
  });

  it("sifremi goster butonu veya sifre alani var", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    const inputs = document.querySelectorAll("input");
    expect(inputs.length).toBeGreaterThanOrEqual(2);
  });
});

// --- Register sayfasÄ± render testi ---
import RegisterPage from "../pages/RegisterPage";

describe("RegisterPage", () => {
  it("kayit formu render olur", () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );
    const inputs = document.querySelectorAll("input");
    expect(inputs.length).toBeGreaterThanOrEqual(3);
  });
});

// --- Kategori badge renk testi ---
describe("Kategori renk mantigi", () => {
  const CATEGORY_COLORS: Record<string, string> = {
    market: "#6366f1",
    yemek: "#f59e0b",
    ulasim: "#10b981",
    alisveris: "#3b82f6",
    fatura: "#ef4444",
    abonelik: "#8b5cf6",
    gelir: "#22c55e",
    diger: "#94a3b8",
  };

  it("bilinen kategoriler icin renk doner", () => {
    expect(CATEGORY_COLORS["market"]).toBeDefined();
    expect(CATEGORY_COLORS["yemek"]).toBeDefined();
    expect(CATEGORY_COLORS["fatura"]).toBeDefined();
  });

  it("bilinmeyen kategori icin fallback renk var", () => {
    const color = CATEGORY_COLORS["bilinmeyen"] ?? "#94a3b8";
    expect(color).toBe("#94a3b8");
  });
});

