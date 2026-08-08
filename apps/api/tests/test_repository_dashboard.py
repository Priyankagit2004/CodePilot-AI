from app.services.repository_dashboard import RepositoryDashboardService


def test_dashboard_insights_flag_high_symbol_density() -> None:
    insights = RepositoryDashboardService._insights(total_files=4, average_symbols=10, endpoints=2, frameworks=["FastAPI"], debt=50)

    titles = {item.title for item in insights}
    assert "High symbol density" in titles
    assert "API surface detected" in titles
    assert "Technical debt attention" in titles
