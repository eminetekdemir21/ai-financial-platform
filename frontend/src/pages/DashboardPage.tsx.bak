import { useEffect, useState, type ChangeEvent } from "react";
import { useAuth } from "../context/AuthContext";
import * as accountsApi from "../api/accounts";
import * as txApi from "../api/transactions";
import * as healthApi from "../api/healthApi";
import { CategoryPieChart, MonthlyBarChart, HealthScoreGauge } from "../components/Charts";
import type { Account } from "../api/accounts";
import type { Transaction } from "../api/transactions";
import type { HealthScore } from "../api/healthApi";
import Spinner from "../components/Spinner";
import Toast, { type ToastMessage } from "../components/Toast";
import AssistantChat from "../components/AssistantChat";
import GoalPlanner from "../components/GoalPlanner";

const DEMO_BANKS = ["Ziraat Bankasi", "Garanti BBVA", "Is Bankasi", "Yapi Kredi", "Akbank"];

function formatAmount(amount: string) {
  const n = parseFloat(amount);
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺`;
}

function categoryBadge(category: string | null) {
  if (!category) {
    return (
      <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-500">
        kategorisiz
      </span>
    );
  }
  return (
    <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-700 border border-indigo-200">
      {category}
    </span>
  );
}

function extractErrorMessage(err: any, fallback: string): string {
  return err?.response?.data?.detail ?? fallback;
}

function gradeColor(grade: string) {
  switch (grade) {
    case "A": return "text-emerald-600";
    case "B": return "text-blue-600";
    case "C": return "text-yellow-600";
    case "D": return "text-orange-600";
    case "F": return "text-red-600";
    default: return "text-slate-600";
  }
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 65) return "bg-blue-500";
  if (score >= 50) return "bg-yellow-500";
  if (score >= 35) return "bg-orange-500";
  return "bg-red-500";
}

function HealthScoreCard({ accountId }: { accountId: string }) {
  const [health, setHealth] = useState<HealthScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    healthApi
      .getHealthScore(accountId)
      .then(setHealth)
      .catch((err) => setError(extractErrorMessage(err, "Skor yuklenemedi.")))
      .finally(() => setLoading(false));
  }, [accountId]);

  if (loading) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} /> Finansal saglik skoru hesaplaniyor...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <p className="text-sm text-slate-400">{error}</p>
      </section>
    );
  }

  if (!health) return null;

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-sm font-medium text-slate-700 mb-1">
            Finansal Saglik Skoru
          </h2>
          <p className="text-xs text-slate-400">{health.summary}</p>
        </div>
        <div className="text-right ml-4 shrink-0">
          <div className={`text-4xl font-bold ${gradeColor(health.grade)}`}>
            {health.grade}
          </div>
          <div className="text-lg font-semibold text-slate-700">
            {health.score}
            <span className="text-sm font-normal text-slate-400"> / 100</span>
          </div>
        </div>
      </div>

      <div className="w-full bg-slate-100 rounded-full h-2 mb-5">
        <div
          className={`h-2 rounded-full transition-all ${scoreBarColor(health.score)}`}
          style={{ width: `${health.score}%` }}
        />
      </div>

      <div className="space-y-3">
        {Object.entries(health.breakdown).map(([key, factor]) => (
          <div key={key}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-700">
                  {factor.label}
                </span>
                <span className="text-xs text-slate-400">
                  (%{Math.round(factor.weight * 100)} agirlik)
                </span>
              </div>
              <span
                className={`text-xs font-semibold ${
                  factor.score >= 75
                    ? "text-emerald-600"
                    : factor.score >= 50
                    ? "text-yellow-600"
                    : "text-red-500"
                }`}
              >
                {factor.score}
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mb-1">
              <div
                className={`h-1.5 rounded-full ${scoreBarColor(factor.score)}`}
                style={{ width: `${factor.score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400">{factor.comment}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const { user, logout } = useAuth();

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [isLoadingTx, setIsLoadingTx] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunningAI, setIsRunningAI] = useState(false);
  const [isCreatingAccount, setIsCreatingAccount] = useState(false);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);
  const [healthKey, setHealthKey] = useState(0);

  const [toast, setToast] = useState<ToastMessage | null>(null);

  const [showNewAccountForm, setShowNewAccountForm] = useState(false);
  const [newBankName, setNewBankName] = useState("");
  const [newAccountNumber, setNewAccountNumber] = useState("");

  const [showBankPicker, setShowBankPicker] = useState(false);
  const [connectingBank, setConnectingBank] = useState<string | null>(null);

  useEffect(() => { loadAccounts(); }, []);
  useEffect(() => {
    if (selectedAccountId) loadTransactions(selectedAccountId);
  }, [selectedAccountId]);

  async function loadAccounts() {
    setIsLoadingAccounts(true);
    try {
      const data = await accountsApi.listAccounts();
      setAccounts(data);
      if (data.length > 0) setSelectedAccountId((prev) => prev ?? data[0].id);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Hesaplar yuklenirken bir sorun olustu.") });
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
      setToast({ type: "error", text: extractErrorMessage(err, "Islemler yuklenirken bir sorun olustu.") });
    } finally {
      setIsLoadingTx(false);
    }
  }

  async function handleDeleteAccount(account: Account) {
    const confirmed = window.confirm(
      `"${account.bank_name} - ${account.account_number_masked}" hesabini silmek istediginize emin misiniz?`
    );
    if (!confirmed) return;
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

  async function handleCreateAccount() {
    if (!newBankName.trim() || !newAccountNumber.trim()) {
      setToast({ type: "error", text: "Banka adi ve hesap no bos birakilamaz." });
      return;
    }
    setIsCreatingAccount(true);
    try {
      const account = await accountsApi.createAccount({
        bank_name: newBankName.trim(),
        account_number_masked: newAccountNumber.trim(),
      });
      setAccounts((prev) => [...prev, account]);
      setSelectedAccountId(account.id);
      setShowNewAccountForm(false);
      setNewBankName("");
      setNewAccountNumber("");
      setToast({ type: "success", text: `${account.bank_name} hesabi olusturuldu.` });
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Hesap olusturulamadi.") });
    } finally {
      setIsCreatingAccount(false);
    }
  }

  async function handleConnectBank(bankName: string) {
    setConnectingBank(bankName);
    try {
      const result = await accountsApi.connectBank(bankName);
      setAccounts((prev) => [...prev, result.account]);
      setSelectedAccountId(result.account.id);
      setShowBankPicker(false);
      setHealthKey((k) => k + 1);
      setToast({
        type: "success",
        text: `${bankName} baglandi. ${result.imported_count} islem cekildi, ${result.categorized_count} tanesi kategorilendirildi.`,
      });
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "Bankaya baglanilamadi.") });
    } finally {
      setConnectingBank(null);
    }
  }

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !selectedAccountId) return;
    setIsUploading(true);
    try {
      const result = await txApi.uploadCsv(selectedAccountId, file);
      const dupText = result.skipped_duplicates && result.skipped_duplicates > 0
        ? ` (${result.skipped_duplicates} mukerrer atildi)` : "";
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
      setToast({
        type: "success",
        text: `${catResult.total_categorized} kategorilendirildi, ${fraudResult.flagged_count} supheli.`,
      });
      await loadTransactions(selectedAccountId);
      setHealthKey((k) => k + 1);
    } catch (err) {
      setToast({ type: "error", text: extractErrorMessage(err, "AI analizi calistirilamadi.") });
    } finally {
      setIsRunningAI(false);
    }
  }

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">AI Financial Platform</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">{user?.full_name}</span>
          <button onClick={logout} className="text-sm text-slate-500 hover:text-red-600 transition">
            Cikis Yap
          </button>
        </div>
      </header>

      <main className="p-6 max-w-5xl mx-auto space-y-4">
        <Toast message={toast} onDismiss={() => setToast(null)} />

        {/* Hesap secici */}
        <section className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-slate-700">Hesaplar</h2>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowBankPicker((v) => !v)}
                className="text-sm text-emerald-600 hover:underline"
              >
                Bankami Bagla
              </button>
              <button onClick={() => setShowNewAccountForm((v) => !v)} className="text-sm text-indigo-600 hover:underline">
                + Yeni Hesap
              </button>
            </div>
          </div>

          {isLoadingAccounts ? (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Spinner size={14} /> Hesaplar yukleniyor...
            </div>
          ) : accounts.length === 0 ? (
            <p className="text-sm text-slate-400">Henuz hesap yok. "Bankami Bagla" ya da "+ Yeni Hesap" ile baslayin.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className={`inline-flex items-center rounded-lg border overflow-hidden transition ${
                    selectedAccountId === acc.id
                      ? "bg-indigo-600 border-indigo-600"
                      : "bg-white border-slate-200 hover:border-indigo-300"
                  }`}
                >
                  <button
                    onClick={() => setSelectedAccountId(acc.id)}
                    className={`px-3 py-2 text-sm ${selectedAccountId === acc.id ? "text-white" : "text-slate-700"}`}
                  >
                    {acc.bank_name} - {acc.account_number_masked}
                  </button>
                  <button
                    onClick={() => handleDeleteAccount(acc)}
                    disabled={deletingAccountId === acc.id}
                    className={`px-2 py-2 text-xs transition disabled:opacity-50 ${
                      selectedAccountId === acc.id
                        ? "text-indigo-100 hover:text-white hover:bg-indigo-700"
                        : "text-slate-400 hover:text-red-600 hover:bg-red-50"
                    }`}
                  >
                    {deletingAccountId === acc.id ? <Spinner size={12} /> : "x"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {showBankPicker && (
            <div className="mt-4 border-t border-slate-100 pt-4">
              <p className="text-xs text-slate-500 mb-2">
                Bir banka secin, islem gecmisiniz otomatik cekilsin (demo):
              </p>
              <div className="flex flex-wrap gap-2">
                {DEMO_BANKS.map((bank) => (
                  <button
                    key={bank}
                    onClick={() => handleConnectBank(bank)}
                    disabled={connectingBank !== null}
                    className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 border border-emerald-200 text-sm rounded-lg px-3 py-2 hover:bg-emerald-100 transition disabled:opacity-50"
                  >
                    {connectingBank === bank && <Spinner size={14} />}
                    {connectingBank === bank ? "Baglaniyor..." : bank}
                  </button>
                ))}
              </div>
            </div>
          )}

          {showNewAccountForm && (
            <div className="mt-4 flex flex-wrap gap-2 items-end border-t border-slate-100 pt-4">
              <div>
                <label className="block text-xs text-slate-500 mb-1">Banka Adi</label>
                <input
                  value={newBankName}
                  onChange={(e) => setNewBankName(e.target.value)}
                  disabled={isCreatingAccount}
                  className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm disabled:opacity-50"
                  placeholder="orn. Ziraat Bankasi"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Hesap No</label>
                <input
                  value={newAccountNumber}
                  onChange={(e) => setNewAccountNumber(e.target.value)}
                  disabled={isCreatingAccount}
                  className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm disabled:opacity-50"
                  placeholder="**** 1234"
                />
              </div>
              <button
                onClick={handleCreateAccount}
                disabled={isCreatingAccount}
                className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm rounded-lg px-4 py-1.5 hover:bg-indigo-700 transition disabled:opacity-50"
              >
                {isCreatingAccount && <Spinner size={14} />}
                {isCreatingAccount ? "Olusturuluyor..." : "Olustur"}
              </button>
            </div>
          )}
        </section>

        {selectedAccount && (
          <>
            {/* Health Score */}
            <HealthScoreCard
              key={`${selectedAccountId}-${healthKey}`}
              accountId={selectedAccount.id}
            />

            {/* Yukleme + AI */}
            <section className="bg-white rounded-xl border border-slate-200 p-4 flex flex-wrap items-center gap-3">
              <label className={`inline-flex items-center gap-2 bg-slate-900 text-white text-sm rounded-lg px-4 py-2 transition ${isUploading ? "opacity-60 cursor-not-allowed" : "cursor-pointer hover:bg-slate-800"}`}>
                {isUploading && <Spinner size={14} />}
                {isUploading ? "Yukleniyor..." : "CSV Yukle"}
                <input type="file" accept=".csv" onChange={handleFileUpload} disabled={isUploading} className="hidden" />
              </label>

              <button
                onClick={handleRunAI}
                disabled={isRunningAI || transactions.length === 0}
                className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 border border-indigo-200 text-sm rounded-lg px-4 py-2 hover:bg-indigo-100 transition disabled:opacity-40"
              >
                {isRunningAI && <Spinner size={14} />}
                {isRunningAI ? "Analiz ediliyor..." : "AI Analizi Calistir"}
              </button>
            </section>


            {/* Grafikler */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <section className="bg-white rounded-xl border border-slate-200 p-4">
                <h2 className="text-sm font-medium text-slate-700 mb-3">Kategori Dagilimi</h2>
                <CategoryPieChart transactions={transactions} />
              </section>
              <section className="bg-white rounded-xl border border-slate-200 p-4">
                <h2 className="text-sm font-medium text-slate-700 mb-3">Aylik Gelir / Gider</h2>
                <MonthlyBarChart transactions={transactions} />
              </section>
            </div>

            {/* Islem tablosu */}
            <section className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <h2 className="text-sm font-medium text-slate-700">
                  Islemler ({transactions.length})
                </h2>
              </div>

              {isLoadingTx ? (
                <div className="flex items-center gap-2 text-sm text-slate-400 p-4">
                  <Spinner size={14} /> Islemler yukleniyor...
                </div>
              ) : transactions.length === 0 ? (
                <p className="text-sm text-slate-400 p-4">
                  Bu hesapta henuz islem yok. CSV yukleyin ya da bir banka baglayin.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-100">
                      <th className="px-4 py-2 font-normal">Tarih</th>
                      <th className="px-4 py-2 font-normal">Aciklama</th>
                      <th className="px-4 py-2 font-normal">Kategori</th>
                      <th className="px-4 py-2 font-normal text-right">Tutar</th>
                      <th className="px-4 py-2 font-normal text-right">Fraud</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr
                        key={tx.id}
                        className={`border-b border-slate-50 transition-colors ${tx.is_flagged ? "bg-red-50" : "hover:bg-slate-50"}`}
                      >
                        <td className="px-4 py-2 text-slate-500">
                          {new Date(tx.transaction_date).toLocaleDateString("tr-TR")}
                        </td>
                        <td className="px-4 py-2 text-slate-900">{tx.description}</td>
                        <td className="px-4 py-2">{categoryBadge(tx.category)}</td>
                        <td className={`px-4 py-2 text-right font-medium ${parseFloat(tx.amount) >= 0 ? "text-emerald-600" : "text-slate-900"}`}>
                          {formatAmount(tx.amount)}
                        </td>
                        <td className="px-4 py-2 text-right">
                          {tx.is_flagged ? (
                            <span className="text-xs text-red-600 font-medium">
                              Supheli ({tx.fraud_score})
                            </span>
                          ) : (
                            <span className="text-xs text-slate-300">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            {/* Finansal Hedefler (AI Goal Planner) */}
            <GoalPlanner accountId={selectedAccount.id} />

            {/* AI Finansal Asistan */}
            <AssistantChat accountId={selectedAccount.id} />
          </>
        )}
      </main>
    </div>
  );
}
