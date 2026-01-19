from pathlib import Path
from typing import List, Dict
import time

from docx import Document
import pandas as pd


def create_docx(chapter_filename: str, translated_text: str, output_dir: str) -> str:
    """Create a .docx file named 'Capítulo X - [Traduzido - Revisado].docx' in output_dir."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    name = Path(chapter_filename).stem
    out_name = f"{name} - [Traduzido - Revisado].docx"
    out_path = p / out_name

    doc = Document()
    # Simple split paragraphs
    for para in translated_text.split('\n\n'):
        doc.add_paragraph(para.strip())

    doc.save(str(out_path))
    print(f"Escrevendo DOCX: {out_path}")
    return str(out_path)


def write_stats_excel(rows: List[Dict], output_path: str) -> str:
    """
    Write execution stats to Excel with 'Fidelidade de Volume' and '% de Retenção' metrics.
    
    Fidelidade de Volume = (palavras_traduzidas / palavras_originais) * 100
    % de Retenção = (caracteres_traduzidos / caracteres_originais) * 100
    
    Threshold: 90% minimum (changed from 85% for senior localization standard)
    If Retenção < 90%, a warning is emitted indicating possible summarization.
    """
    df = pd.DataFrame(rows)
    
    # Calculate Fidelidade de Volume (%) using word counts
    if "Palavras Originais" in df.columns and "Palavras Traduzidas" in df.columns:
        def calc_fidelidade(row):
            orig = row.get("Palavras Originais", 0)
            trad = row.get("Palavras Traduzidas", 0)
            if orig > 0:
                fidelidade = round((trad / orig) * 100, 1)
                # Flag if summarization detected (85% threshold)
                if fidelidade < 85:
                    return f"{fidelidade}% ⚠️ POSSÍVEL RESUMO"
                return f"{fidelidade}%"
            return "0%"
        
        df["Fidelidade de Volume"] = df.apply(calc_fidelidade, axis=1)
    
    # Calculate % de Retenção (%) using character counts - NEW METRIC
    # New 90% threshold for senior localization standard
    if "Caracteres Originais" in df.columns and "Caracteres Traduzidos" in df.columns:
        def calc_retencao(row):
            orig = row.get("Caracteres Originais", 0)
            trad = row.get("Caracteres Traduzidos", 0)
            if orig > 0:
                retencao = round((trad / orig) * 100, 1)
                # Flag if below 90% retention threshold (senior standard)
                if retencao < 90:
                    return f"{retencao}% ❌ ERRO: ABAIXO DO PADRÃO"
                return f"{retencao}%"
            return "0%"
        
        df["% de Retenção"] = df.apply(calc_retencao, axis=1)
    
    # Ensure correct column order
    cols = [
        "Nome do Ficheiro",
        "Palavras Originais",
        "Palavras Traduzidas",
        "Fidelidade de Volume",
        "Caracteres Originais",
        "Caracteres Traduzidos",
        "% de Retenção",
        "Novos Termos no Glossário",
        "Tempo de Execução (s)",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(str(out), index=False)
    print(f"Escrevendo estatísticas: {out}")
    return str(out)
