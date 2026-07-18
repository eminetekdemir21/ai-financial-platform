import { useEffect, useState, type ChangeEvent } from "react";
import { useAuth } from "../context/AuthContext";
import * as accountsApi from "../api/accounts";
import * as txApi from "../api/transactions";
import * as healthApi from "../api/healthApi";
import { CategoryPieChart, MonthlyBarChart } from "../components/Charts";
import type { Account } from "../api/accounts";
import type { Transaction } from "../api/transactions";
import type { HealthScore } from "../api/healthApi";
import Spinner from "../components/Spinner";
import Toast, { type ToastMessage } from "../components/Toast";
import AssistantChat from "../components/AssistantChat";
import GoalPlanner from "../components/GoalPlanner";
import SavingsCoach from "../components/SavingsCoach";
import WhatIfSimulator from "../components/WhatIfSimulator";
import "../dark-theme.css";

const DEMO_BANKS = ["Ziraat Bankasi", "Garanti BBVA", "Is Bankasi", "Yapi Kredi", "Akbank"];
const PAGE_SIZE = 20;

const dk = {
  bg: "var(--dk-bg)",
  card: "var(--dk-card)",
  card2: "var(--dk-card2)",
  border: "var(--dk-border)",
  border2: "var(--dk-border2)",
  text: "var(--dk-text)",
  muted: "var(--dk-muted)",
  hint: "var(--dk-hint)",
  green: "var(--dk-green)",
  greenBg: "var(--dk-green-bg)",
  blue: "var(--dk-blue)",
  blueBg: "var(--dk-blue-bg)",
  red: "var(--dk-red)",
  redBg: "var(--dk-red-bg)",
  amber: "var(--dk-amber)",
  amberBg: "var(--dk-amber-bg)",
  purple: "var(--dk-purple)",
  purpleBg: "var(--dk-purple-bg)",
};

function card(extra = "") {
  return {
    background: dk.card,
    border: `0.5px solid ${dk.border}`,
    borderRadius: "12px",
    padding: "16px",
  } as React.CSSProperties;
}

function formatAmount(amount: string) {
  const n = parseFloat(amount);
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺`;
}

function categoryBadge(category: string | null) {
  if (!category) {
    return (
      <span style={{ background: "rgba(255,255,255,0.06)", color: dk.muted, padding: "2px 8px", borderRadius: "20px", fontSize: "11px" }}>
        kategorisiz
      </span>
    );
  }
  return (
    <span style={{ background: dk.blueBg, color: dk.blue, padding: "2px 8px", borderRadius: "20px", fontSize: "11px", border: `0.5px solid rgba(91,141,238,0.2)` }}>
      {category}
    </span>
  );
}

function extractErrorMessage(err: any, fallback: string): string {
  return err?.response?.data?.detail ?? fallback;
}

function scoreBarColor(score: number) {
  if (score >= 80) return dk.green;
  if (score >= 65) return dk.blue;
  if (score >= 50) return dk.amber;
  return dk.red;
}

function gradeColor(grade: string) {
  if (grade === "A") return dk.green;
  if (grade === "B") return dk.blue;
  if (grade === "C") return dk.amber;
  return dk.red;
}

function HealthScoreCard({ accountId }: { accountId: string }) {
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    healthApi.getHealthScore(accountId)
      .then(setHealth)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [accountId]);

  if (loading) return (
    <div style={card()}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", color: dk.muted, fontSize: "13px" }}>
        <Spinner size={14} /> Skor hesaplaniyor...
      </div>
    </div>
  );
  if (!health) return null;

  return (
    <div style={card()}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div>
          <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>
            Finansal Saglik Skoru
          </div>
          <div style={{ fontSize: "12px", color: dk.hint }}>{health.summary}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "32px", fontWeight: 500, color: gradeColor(health.grade), lineHeight: 1 }}>{health.grade}</div>
          <div style={{ fontSize: "16px", fontWeight: 500, color: dk.text }}>{health.score}<span style={{ fontSize: "12px", color: dk.muted }}> / 100</span></div>
        </div>
      </div>

      <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: "4px", height: "6px", marginBottom: "16px" }}>
        <div style={{ height: "6px", borderRadius: "4px", background: scoreBarColor(health.score), width: `${health.score}%`, transition: "width 0.8s ease" }} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {Object.entries(health.breakdown).map(([key, factor]) => (
          <div key={key}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontSize: "12px", color: dk.muted }}>{factor.label}</span>
              <span style={{ fontSize: "12px", fontWeight: 500, color: scoreBarColor(factor.score) }}>{factor.score}</span>
            </div>
            <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: "4px", height: "4px" }}>
              <div style={{ height: "4px", borderRadius: "4px", background: scoreBarColor(factor.score), width: `${factor.score}%` }} />
            </div>
            <div style={{ fontSize: "11px", color: dk.hint, marginTop: "2px" }}>{factor.comment}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [page, setPage] = useState(0);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [isLoadingTx, setIsLoadingTx] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunningAI, setIsRunningAI] = useState(false);
  const [isCreatingAccount, setIsCreatingAccount] = useState(false);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);
  const [healthKey, setHealthKey] = useState(0);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [showNewAccountForm, setShowNewAccountForm] = useState(false);
  const [showDemoBanks, setShowDemoBanks] = useState(false);
  const [newBankName, setNewBankName] = useState("");
  const [newAccountNumber, setNewAccountNumber] = useState("");

  useEffect(() => { loadAccounts(); }, []);
  useEffect(() => {
    if (selectedAccountId) { loadTransactions(selectedAccountId); setPage(0); }
  }, [selectedAccountId]);

  async function loadAccounts() {
    setIsLoadingAccounts(true);
    try {
      const data = await accountsApi.listAccounts();
      setAccounts(data);
      if (data.length > 0) setSelectedAccountId((prev) => prev ?? data[0].id);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Hesaplar yuklenemedi.") });
    } finally {
      setIsLoadingAccounts(false);
    }
  }

  async function loadTransactions(accountId: string) {
    setIsLoadingTx(true);
    try {
      const data = await txApi.listTransactions(accountId);
      setTransactions(data);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Islemler yuklenemedi.") });
    } finally {
      setIsLoadingTx(false);
    }
  }

  async function handleDeleteAccount(account: Account) {
    if (!window.confirm(`"${account.bank_name} - ${account.account_number_masked}" hesabini silmek istiyor musunuz?`)) return;
    setDeletingAccountId(account.id);
    try {
      await accountsApi.deleteAccount(account.id);
      const remaining = accounts.filter((a) => a.id !== account.id);
      setAccounts(remaining);
      if (selectedAccountId === account.id) {
        setSelectedAccountId(remaining.length > 0 ? remaining[0].id : null);
        if (remaining.length === 0) setTransactions([]);
      }
      setToast({ type: "success", text: `${account.bank_name} hesabi silindi.` });
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Hesap silinemedi.") });
    } finally {
      setDeletingAccountId(null);
    }
  }

  async function handleCreateAccount(bankName: string, accountNumber: string) {
    if (!bankName.trim() || !accountNumber.trim()) {
      setToast({ type: "error", text: "Banka adi ve hesap no bos birakilamaz." });
      return;
    }
    setIsCreatingAccount(true);
    try {
      const account = await accountsApi.createAccount({ bank_name: bankName, account_number_masked: accountNumber });
      setAccounts((prev) => [...prev, account]);
      setSelectedAccountId(account.id);
      setShowNewAccountForm(false);
      setShowDemoBanks(false);
      setNewBankName(""); setNewAccountNumber("");
      setToast({ type: "success", text: `${account.bank_name} hesabi olusturuldu.` });
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Hesap olusturulamadi.") });
    } finally {
      setIsCreatingAccount(false);
    }
  }

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedAccountId) return;
    setIsUploading(true);
    try {
      const result = await txApi.uploadCsv(selectedAccountId, file);
      const dupText = result.skipped_duplicates && result.skipped_duplicates > 0 ? ` (${result.skipped_duplicates} mukerrer atildi)` : "";
      setToast({ type: "success", text: `${result.imported_count} islem yuklendi${dupText}.` });
      await loadTransactions(selectedAccountId);
      setHealthKey((k) => k + 1);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Dosya yuklenemedi.") });
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  }

  async function handleRunAI() {
    if (!selectedAccountId) return;
    setIsRunningAI(true);
    try {
      const catResult = await txApi.runCategorization(selectedAccountId);
      const fraudResult = await txApi.runFraudDetection(selectedAccountId);
      setToast({ type: "success", text: `${catResult.total_categorized} kategorilendirildi, ${fraudResult.flagged_count} supheli.` });
      await loadTransactions(selectedAccountId);
      setHealthKey((k) => k + 1);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "AI analizi calistirilamadi.") });
    } finally {
      setIsRunningAI(false);
    }
  }

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);
  const totalPages = Math.ceil(transactions.length / PAGE_SIZE);
  const pagedTx = transactions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const totalIncome = transactions.filter(tx => parseFloat(tx.amount) > 0).reduce((s, tx) => s + parseFloat(tx.amount), 0);
  const totalExpense = transactions.filter(tx => parseFloat(tx.amount) < 0).reduce((s, tx) => s + Math.abs(parseFloat(tx.amount)), 0);

  return (
    <div style={{ minHeight: "100vh", background: dk.bg, fontFamily: "var(--font-sans, system-ui)" }}>
      {/* Header */}
      <header style={{ background: dk.card, borderBottom: `0.5px solid ${dk.border}`, padding: "0 24px", height: "56px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ color: dk.blue, fontSize: "18px" }}>⬡</span>
          <span style={{ color: dk.text, fontWeight: 500, fontSize: "15px" }}>AI Financial Platform</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ color: dk.muted, fontSize: "13px" }}>{user?.full_name}</span>
          <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: dk.purpleBg, border: `1px solid ${dk.purple}`, display: "flex", alignItems: "center", justifyContent: "center", color: dk.purple, fontSize: "11px", fontWeight: 500 }}>
            {user?.full_name?.slice(0, 2).toUpperCase() ?? "U"}
          </div>
          <button onClick={logout} style={{ color: dk.muted, fontSize: "13px", background: "none", border: "none", cursor: "pointer" }}
            onMouseOver={(e) => (e.currentTarget.style.color = dk.red)}
            onMouseOut={(e) => (e.currentTarget.style.color = dk.muted)}>
            Cikis
          </button>
        </div>
      </header>

      <main style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "16px" }}>
        <Toast message={toast} onDismiss={() => setToast(null)} />

        {/* Hesap secici */}
        <div style={card()}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>Hesaplar</span>
            <div style={{ display: "flex", gap: "12px" }}>
              <button onClick={() => { setShowDemoBanks(v => !v); setShowNewAccountForm(false); }}
                style={{ fontSize: "12px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>
                Bankami Bagla
              </button>
              <button onClick={() => { setShowNewAccountForm(v => !v); setShowDemoBanks(false); }}
                style={{ fontSize: "12px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>
                + Yeni Hesap
              </button>
            </div>
          </div>

          {isLoadingAccounts ? (
            <div style={{ color: dk.muted, fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}><Spinner size={14} /> Yukleniyor...</div>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {accounts.map((acc) => (
                <div key={acc.id} style={{ display: "inline-flex", alignItems: "center", borderRadius: "8px", border: `1px solid ${selectedAccountId === acc.id ? dk.blue : dk.border}`, background: selectedAccountId === acc.id ? dk.blueBg : "transparent", overflow: "hidden" }}>
                  <button onClick={() => setSelectedAccountId(acc.id)}
                    style={{ padding: "6px 12px", fontSize: "13px", color: selectedAccountId === acc.id ? dk.blue : dk.muted, background: "none", border: "none", cursor: "pointer" }}>
                    {acc.bank_name} - {acc.account_number_masked}
                  </button>
                  <button onClick={() => handleDeleteAccount(acc)} disabled={deletingAccountId === acc.id}
                    style={{ padding: "6px 8px", fontSize: "12px", color: dk.hint, background: "none", border: "none", cursor: "pointer" }}>
                    {deletingAccountId === acc.id ? <Spinner size={12} /> : "×"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {showDemoBanks && (
            <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: `0.5px solid ${dk.border}` }}>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "8px" }}>Demo banka secin:</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {DEMO_BANKS.map((bank, i) => (
                  <button key={bank} onClick={() => handleCreateAccount(bank, `**** ${1000 + i * 1111}`)} disabled={isCreatingAccount}
                    style={{ fontSize: "12px", color: dk.text, background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "6px 12px", cursor: "pointer" }}>
                    {bank}
                  </button>
                ))}
              </div>
            </div>
          )}

          {showNewAccountForm && (
            <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: `0.5px solid ${dk.border}`, display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "flex-end" }}>
              <div>
                <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Banka Adi</div>
                <input value={newBankName} onChange={(e) => setNewBankName(e.target.value)} placeholder="orn. Ziraat Bankasi"
                  style={{ background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "6px 12px", fontSize: "13px", color: dk.text, outline: "none" }} />
              </div>
              <div>
                <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Hesap No</div>
                <input value={newAccountNumber} onChange={(e) => setNewAccountNumber(e.target.value)} placeholder="**** 1234"
                  style={{ background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "6px 12px", fontSize: "13px", color: dk.text, outline: "none" }} />
              </div>
              <button onClick={() => handleCreateAccount(newBankName, newAccountNumber)} disabled={isCreatingAccount}
                style={{ background: dk.blueBg, border: `1px solid ${dk.blue}`, color: dk.blue, borderRadius: "8px", padding: "6px 16px", fontSize: "13px", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}>
                {isCreatingAccount && <Spinner size={13} />}
                {isCreatingAccount ? "Olusturuluyor..." : "Olustur"}
              </button>
            </div>
          )}
        </div>

        {selectedAccount && (
          <>
            {/* Metrik kartlar */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
              {[
                { label: "Toplam Gelir", value: `+${totalIncome.toLocaleString("tr-TR", { maximumFractionDigits: 0 })} ₺`, color: dk.green },
                { label: "Toplam Gider", value: `-${totalExpense.toLocaleString("tr-TR", { maximumFractionDigits: 0 })} ₺`, color: dk.red },
                { label: "Islem Sayisi", value: `${transactions.length} islem`, color: dk.blue },
              ].map((item) => (
                <div key={item.label} style={{ ...card(), padding: "14px 16px" }}>
                  <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>{item.label}</div>
                  <div style={{ fontSize: "20px", fontWeight: 500, color: item.color }}>{item.value}</div>
                </div>
              ))}
            </div>

            {/* CSV + AI butonlar */}
            <div style={{ ...card(), padding: "12px 16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <label style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: dk.card2, border: `0.5px solid ${dk.border2}`, color: dk.text, fontSize: "13px", borderRadius: "8px", padding: "7px 16px", cursor: isUploading ? "not-allowed" : "pointer", opacity: isUploading ? 0.6 : 1 }}>
                {isUploading && <Spinner size={13} />}
                {isUploading ? "Yukleniyor..." : "CSV Yukle"}
                <input type="file" accept=".csv" onChange={handleFileUpload} disabled={isUploading} style={{ display: "none" }} />
              </label>
              <button onClick={handleRunAI} disabled={isRunningAI || transactions.length === 0}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: dk.blueBg, border: `1px solid ${dk.blue}`, color: dk.blue, fontSize: "13px", borderRadius: "8px", padding: "7px 16px", cursor: "pointer", opacity: (isRunningAI || transactions.length === 0) ? 0.4 : 1 }}>
                {isRunningAI && <Spinner size={13} />}
                {isRunningAI ? "Analiz ediliyor..." : "AI Analizi Calistir"}
              </button>
            </div>

            {/* Satır 1: Health Score + Savings Coach */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <HealthScoreCard key={`${selectedAccountId}-${healthKey}`} accountId={selectedAccount.id} />
              <SavingsCoach accountId={selectedAccount.id} />
            </div>

            {/* Satır 2: Grafikler */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={card()}>
                <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "12px" }}>Kategori Dagilimi</div>
                <CategoryPieChart transactions={transactions} />
              </div>
              <div style={card()}>
                <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "12px" }}>Aylik Gelir / Gider</div>
                <MonthlyBarChart transactions={transactions} />
              </div>
            </div>

            {/* Satır 3: Goal Planner + Simulation */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <GoalPlanner accountId={selectedAccount.id} />
              <WhatIfSimulator accountId={selectedAccount.id} />
            </div>

            {/* İşlemler tablosu */}
            <div style={{ ...card(), padding: 0, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: `0.5px solid ${dk.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  Islemler ({transactions.length}){totalPages > 1 && ` — Sayfa ${page + 1}/${totalPages}`}
                </span>
                {totalPages > 1 && (
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                      style={{ fontSize: "12px", color: page === 0 ? dk.hint : dk.blue, background: "none", border: "none", cursor: page === 0 ? "not-allowed" : "pointer" }}>
                      ← Onceki
                    </button>
                    <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1}
                      style={{ fontSize: "12px", color: page === totalPages - 1 ? dk.hint : dk.blue, background: "none", border: "none", cursor: page === totalPages - 1 ? "not-allowed" : "pointer" }}>
                      Sonraki →
                    </button>
                  </div>
                )}
              </div>

              {isLoadingTx ? (
                <div style={{ padding: "16px", color: dk.muted, fontSize: "13px", display: "flex", alignItems: "center", gap: "8px" }}><Spinner size={14} /> Yukleniyor...</div>
              ) : transactions.length === 0 ? (
                <div style={{ padding: "16px", color: dk.muted, fontSize: "13px" }}>Bu hesapta henuz islem yok.</div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      {["Tarih", "Aciklama", "Kategori", "Tutar", "Fraud"].map((h, i) => (
                        <th key={h} style={{ padding: "10px 16px", fontSize: "11px", color: dk.hint, fontWeight: 400, textAlign: i >= 3 ? "right" : "left", borderBottom: `0.5px solid ${dk.border}`, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pagedTx.map((tx) => (
                      <tr key={tx.id} style={{ borderBottom: `0.5px solid ${dk.border}`, background: tx.is_flagged ? "rgba(255,107,107,0.05)" : "transparent" }}
                        onMouseOver={(e) => { if (!tx.is_flagged) e.currentTarget.style.background = "rgba(255,255,255,0.02)"; }}
                        onMouseOut={(e) => { e.currentTarget.style.background = tx.is_flagged ? "rgba(255,107,107,0.05)" : "transparent"; }}>
                        <td style={{ padding: "10px 16px", fontSize: "13px", color: dk.hint }}>{new Date(tx.transaction_date).toLocaleDateString("tr-TR")}</td>
                        <td style={{ padding: "10px 16px", fontSize: "13px", color: dk.text }}>{tx.description}</td>
                        <td style={{ padding: "10px 16px" }}>{categoryBadge(tx.category)}</td>
                        <td style={{ padding: "10px 16px", fontSize: "13px", fontWeight: 500, textAlign: "right", color: parseFloat(tx.amount) >= 0 ? dk.green : dk.red }}>
                          {formatAmount(tx.amount)}
                        </td>
                        <td style={{ padding: "10px 16px", textAlign: "right" }}>
                          {tx.is_flagged
                            ? <span style={{ fontSize: "11px", color: dk.red }}>Supheli ({tx.fraud_score})</span>
                            : <span style={{ fontSize: "11px", color: dk.hint }}>—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* AI Asistan */}
            <AssistantChat accountId={selectedAccount.id} />
          </>
        )}
      </main>
    </div>
  );
}
