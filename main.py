"""Orquestra a leitura, tradução e escrita de arquivos de novel por sessões com configuração automática."""
from dotenv import load_dotenv
load_dotenv()

import os
import json
import time
from pathlib import Path
from src.document_loader import (
    read_text_file,
    normalize_stylistic_abbreviations,
    normalize_chapter_titles,
)
from src.glossary_engine import (
    load_terms_for_novel,
    ensure_novel_session,
    append_context_memory,
    read_context_memory,
    append_suggestion,
)
from src.translator_core import translate_text
from src.exporter import create_docx, write_stats_excel


def count_new_terms_in_source(source_text: str, glossary_keys) -> int:
    # Very simple heuristic: count unique words (non-ascii sequences) not in glossary
    import re

    tokens = set(re.findall(r"[\w\u4e00-\u9fff\uac00-\ud7af]+", source_text))
    new = 0
    for t in tokens:
        if t not in glossary_keys:
            # Heuristic: consider non-ASCII tokens/words as potential new terms
            if any(ord(c) > 127 for c in t):
                new += 1
    return new


def count_words(text: str) -> int:
    """Count words in text (simple split on whitespace)."""
    return len(text.split())


def count_chars(text: str) -> int:
    """Count characters in text (excluding whitespace)."""
    return len(text.replace('\n', '').replace(' ', '').replace('\t', ''))


def process_novel_session(novel_name: str, input_dir: Path, output_dir: Path, project_root: Path):
    # Diretório de saída para a novel específica.
    out_novel_dir = output_dir / novel_name
    out_novel_dir.mkdir(parents=True, exist_ok=True)
    
    # Crie um subdiretório 'session' para arquivos de estado (glossário, memória).
    session_dir = out_novel_dir / "session"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Garanta os diretórios da sessão e carregue o glossário + contexto a partir do diretório de sessão.
    ensure_novel_session(novel_name, str(session_dir))
    glossary = load_terms_for_novel(novel_name, str(session_dir))
    context = read_context_memory(novel_name, str(session_dir))

    files = sorted(list(input_dir.glob("*.txt")))
    stats = []
    api_key = os.environ.get("GOOGLE_API_KEY")

    for f in files:
        start = time.time()
        print(f"\n[{novel_name}] Processando: {f.name}")
        
        # Etapa de Carregamento e Normalização Semântica
        raw_text = read_text_file(str(f))
        
        print("  Aplicando normalização semântica...")
        normalized_text = normalize_stylistic_abbreviations(raw_text)
        clean_text, detected_title = normalize_chapter_titles(normalized_text)
        if detected_title:
            print(f"     → Título detectado e normalizado: '{detected_title}'")

        # Guarde o texto original limpo para contagem de palavras
        original_text_for_stats = clean_text

        # Forneça a memória de contexto no topo para o modelo (se presente)
        if context:
            text_to_translate = f"Contexto anterior:\n{context}\n---\n{clean_text}"
        else:
            text_to_translate = clean_text

        # Traduza usando o Core. Erros são capturados por arquivo para que o processamento continue.
        try:
            translated = translate_text(
                text_to_translate, 
                source_lang=None, 
                glossary=glossary, 
                api_key=api_key,
                glossary_path=str(session_dir),
                novel_name=novel_name,
                enable_semantic_review=True,
                is_mature_content=True,
            )
        except Exception as e:
            print(f"[{novel_name}] Erro ao traduzir {f.name}: {e}")
            # Grave a estatística de falha e continue para o próximo arquivo
            stats.append(
                {
                    "Nome do Ficheiro": f.name,
                    "Palavras Originais": count_words(original_text_for_stats),
                    "Palavras Traduzidas": 0,
                    "Caracteres Originais": count_chars(original_text_for_stats),
                    "Caracteres Traduzidos": 0,
                    "Novos Termos no Glossário": 0,
                    "Tempo de Execução (s)": 0,
                }
            )
            continue

        # Exporte para docx: salve na estrutura da pasta output/
        docx_path = create_docx(f.name, translated, str(out_novel_dir))

        elapsed = time.time() - start
        stats.append(
            {
                "Nome do Ficheiro": f.name,
                "Palavras Originais": count_words(original_text_for_stats),
                "Palavras Traduzidas": count_words(translated),
                "Caracteres Originais": count_chars(original_text_for_stats),
                "Caracteres Traduzidos": count_chars(translated),
                "Novos Termos no Glossário": count_new_terms_in_source(original_text_for_stats, glossary.keys()),
                "Tempo de Execução (s)": round(elapsed, 2),
            }
        )
        print(f"[{novel_name}] Escrito: {docx_path} (tempo {elapsed:.2f}s)")

        # CRÍTICO: Anexe o resultado à memória de contexto para o próximo arquivo.
        append_context_memory(novel_name, translated, base_dir=str(session_dir))
        context = f"{context}\n\n{translated}".strip()

    # Escreva as estatísticas do Excel por novel na pasta output/
    stats_path = out_novel_dir / "stats_execucao.xlsx"
    write_stats_excel(stats, str(stats_path))
    print(f"[{novel_name}] Estatísticas: {stats_path}")
    
    # Mostre a localização do arquivo de sugestões
    suggestions_path = session_dir / "glossary" / novel_name / "suggestions.json"
    print(f"[{novel_name}] Sugestões de termos: {suggestions_path}")


def main():
    project_root = Path.cwd()
    input_root = project_root / "input"
    
    # Use OUTPUT_DIR from .env, or default to ./output
    output_dir_env = os.environ.get("OUTPUT_DIR", "./output")
    output_root = Path(output_dir_env)
    output_root.mkdir(parents=True, exist_ok=True)

    # Batch processing: look for subdirectories per novel; if none, treat root files as a single session named 'default'
    novel_dirs = [p for p in input_root.iterdir() if p.is_dir()] if input_root.exists() else []
    if not novel_dirs:
        # process files in input/ as default novel
        default_dir = input_root
        if not input_root.exists() or not any(default_dir.glob("*.txt")):
            print("Nenhum arquivo .txt encontrado em input/ — coloque arquivos e execute novamente.")
            return
        process_novel_session("default", default_dir, output_root, project_root)
    else:
        for nd in sorted(novel_dirs):
            if not any(nd.glob("*.txt")):
                print(f"\nNenhum arquivo .txt em input/{nd.name} — pulando...")
                continue
            process_novel_session(nd.name, nd, output_root, project_root)


if __name__ == "__main__":
    main()