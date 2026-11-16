"""Entrada: pergunta vazia e problemas com o arquivo."""
import pytest

from entrada import MAX_CARACTERES_PERGUNTA, MAX_CARACTERES_TRECHO, montar_entrada
from erros import ErroEntrada


@pytest.mark.parametrize("pergunta", ["", "   ", None])
def test_pergunta_vazia(trecho, pergunta):
    with pytest.raises(ErroEntrada, match="vazia"):
        montar_entrada(trecho, pergunta)


def test_pergunta_longa_demais(trecho):
    with pytest.raises(ErroEntrada, match="limite"):
        montar_entrada(trecho, "a" * (MAX_CARACTERES_PERGUNTA + 1))


def test_arquivo_inexistente():
    with pytest.raises(ErroEntrada, match="não encontrado"):
        montar_entrada("nao_existe.txt", "Pergunta?")


def test_arquivo_vazio(tmp_path):
    vazio = tmp_path / "vazio.txt"
    vazio.write_text("", encoding="utf-8")
    with pytest.raises(ErroEntrada, match="vazio"):
        montar_entrada(str(vazio), "Pergunta?")


def test_arquivo_fora_de_utf8(tmp_path):
    ruim = tmp_path / "ruim.txt"
    ruim.write_bytes("média".encode("latin-1"))
    with pytest.raises(ErroEntrada, match="UTF-8"):
        montar_entrada(str(ruim), "Pergunta?")


def test_trecho_longo_demais(tmp_path):
    longo = tmp_path / "longo.txt"
    longo.write_text("a" * (MAX_CARACTERES_TRECHO + 1), encoding="utf-8")
    with pytest.raises(ErroEntrada, match="limite"):
        montar_entrada(str(longo), "Pergunta?")


def test_entrada_valida_remove_espacos(trecho):
    entrada = montar_entrada(trecho, "  Qual a média?  ")
    assert entrada.pergunta == "Qual a média?" and "Art. 99" in entrada.trecho
