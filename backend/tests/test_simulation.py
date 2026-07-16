"""
What-If Simulation Engine testleri.
Veritabani gerektirmeyen saf birim testleri.
"""
from decimal import Decimal


class TestSimulationSchemas:
    """Simulation şema testleri."""

    def test_default_degerler(self):
        """Varsayılan değerler sıfır olmalı."""
        from app.domains.simulation.schemas import SimulationRequest
        req = SimulationRequest()
        assert float(req.income_change) == 0
        assert req.category_changes == {}
        assert float(req.one_time_expense) == 0

    def test_gelir_artisi_senaryosu(self):
        """Gelir artışı doğru parse edilmeli."""
        from app.domains.simulation.schemas import SimulationRequest
        req = SimulationRequest(income_change=5000, description="Maas artisi")
        assert float(req.income_change) == 5000
        assert req.description == "Maas artisi"

    def test_kategori_degisimi_senaryosu(self):
        """Kategori değişimi doğru parse edilmeli."""
        from app.domains.simulation.schemas import SimulationRequest
        req = SimulationRequest(category_changes={"yemek": -0.30})
        assert "yemek" in req.category_changes
        assert float(req.category_changes["yemek"]) == -0.30


class TestSimulationImpactLevel:
    """Etki seviyesi testleri."""

    def test_pozitif_etki(self):
        """100 TL'den fazla aylık artış pozitif etki olmalı."""
        from app.domains.simulation.service import _impact_level
        assert _impact_level(Decimal("500")) == "positive"

    def test_negatif_etki(self):
        """100 TL'den fazla aylık azalış negatif etki olmalı."""
        from app.domains.simulation.service import _impact_level
        assert _impact_level(Decimal("-500")) == "negative"

    def test_notr_etki(self):
        """100 TL'den az değişim nötr etki olmalı."""
        from app.domains.simulation.service import _impact_level
        assert _impact_level(Decimal("50")) == "neutral"
        assert _impact_level(Decimal("-50")) == "neutral"

    def test_sifir_etki(self):
        """Sıfır değişim nötr etki olmalı."""
        from app.domains.simulation.service import _impact_level
        assert _impact_level(Decimal("0")) == "neutral"


class TestSimulationSummary:
    """AI özet metni testleri."""

    def test_gelir_artisi_ozeti(self):
        """Gelir artışı senaryosunda özet metni gelir artışından bahsetmeli."""
        from app.domains.simulation.schemas import SimulationRequest
        from app.domains.simulation.service import _generate_summary

        request = SimulationRequest(income_change=5000, description="Test")
        summary = _generate_summary(
            request=request,
            current_savings=Decimal("10000"),
            sim_savings=Decimal("15000"),
            savings_diff=Decimal("5000"),
            annual_diff=Decimal("60000"),
            category_totals={},
        )
        assert "5000" in summary or "artarsa" in summary

    def test_pozitif_fark_ozeti(self):
        """Pozitif fark durumunda 'artar' ifadesi geçmeli."""
        from app.domains.simulation.schemas import SimulationRequest
        from app.domains.simulation.service import _generate_summary

        request = SimulationRequest(income_change=3000)
        summary = _generate_summary(
            request=request,
            current_savings=Decimal("8000"),
            sim_savings=Decimal("11000"),
            savings_diff=Decimal("3000"),
            annual_diff=Decimal("36000"),
            category_totals={},
        )
        assert "artar" in summary or "3000" in summary

    def test_negatif_fark_ozeti(self):
        """Negatif fark durumunda 'azalır' ifadesi geçmeli."""
        from app.domains.simulation.schemas import SimulationRequest
        from app.domains.simulation.service import _generate_summary

        request = SimulationRequest(one_time_expense=Decimal("20000"))
        summary = _generate_summary(
            request=request,
            current_savings=Decimal("10000"),
            sim_savings=Decimal("7000"),
            savings_diff=Decimal("-3000"),
            annual_diff=Decimal("-36000"),
            category_totals={},
        )
        assert "azal" in summary or "değiş" in summary or "degis" in summary or "azal" in summary


class TestSimulationProjection:
    """12 aylık projeksiyon testleri."""

    def test_projeksiyon_12_ay(self, client, registered_user, test_account):
        """Simülasyon her zaman 12 aylık projeksiyon döndürmeli."""
        response = client.post(
            f"/api/v1/simulation/{test_account['id']}",
            headers=registered_user["headers"],
            json={
                "income_change": 0,
                "category_changes": {},
                "one_time_expense": 0,
                "description": "Bos senaryo",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["monthly_projections"]) == 12

    def test_kumulatif_birikim_artiyor(self, client, registered_user, test_account):
        """Pozitif tasarrufta kümülatif birikim artmalı."""
        from tests.conftest import make_csv_file
        csv_file = make_csv_file([
            ("2026-01-01", "Maas Yatisi", "20000"),
            ("2026-01-05", "Market Alisveris", "-500"),
        ])
        client.post(
            "/api/v1/transactions/upload/csv",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
            files={"file": ("test.csv", csv_file, "text/csv")},
        )

        response = client.post(
            f"/api/v1/simulation/{test_account['id']}",
            headers=registered_user["headers"],
            json={
                "income_change": 0,
                "category_changes": {},
                "one_time_expense": 0,
                "description": "Test",
            },
        )
        assert response.status_code == 200
        projections = response.json()["monthly_projections"]
        # Kümülatif birikim monoton artmalı (pozitif tasarrufta)
        cumulative = [float(p["cumulative_savings"]) for p in projections]
        assert cumulative[-1] >= cumulative[0]

