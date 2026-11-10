"""Aísla las pruebas de la configuración de la máquina: ninguna lee el .env real ni usa una clave real."""
import pytest


@pytest.fixture(autouse=True)
def aislar_entorno(monkeypatch, tmp_path):
    for variable in ("GEMINI_API_KEY", "AIDA_PROVEEDOR", "AIDA_MODELO"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("AIDA_ENV", str(tmp_path / "no_existe.env"))
