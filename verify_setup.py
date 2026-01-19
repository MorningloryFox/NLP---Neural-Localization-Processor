#!/usr/bin/env python
"""
Script de Verificação: Lume-Novel-Localizer com Ollama
Testa se a configuração está correta e pronta para tradução.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Teste 1: Verificar importações essenciais"""
    print("\n[1/5] Verificando importações...")
    try:
        import ollama
        print("  ✓ ollama importado")
        
        import pandas
        print("  ✓ pandas importado")
        
        from src.translator_core import (
            chunk_text_by_paragraphs,
            _count_words,
            _call_ollama_text,
            translate_text,
        )
        print("  ✓ Funções translator_core importadas")
        
        from src.exporter import write_stats_excel
        print("  ✓ Função exporter importada")
        
        return True
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def test_chunking():
    """Teste 2: Verificar algoritmo de chunking"""
    print("\n[2/5] Testando chunking com parágrafos...")
    try:
        from src.translator_core import chunk_text_by_paragraphs
        
        test_text = (
            "Primeiro parágrafo com conteúdo.\n\n"
            "Segundo parágrafo mais longo com várias palavras para teste.\n\n"
            "Terceiro parágrafo final."
        )
        
        chunks = chunk_text_by_paragraphs(test_text, chunk_size=50, overlap=10)
        
        if len(chunks) > 0:
            print(f"  ✓ Chunking funcionando: {len(chunks)} chunks")
            for i, (chunk, start, end) in enumerate(chunks[:2]):
                words = len(chunk.split())
                print(f"    Chunk {i+1}: {end-start} chars, {words} palavras")
            return True
        else:
            print("  ✗ Nenhum chunk gerado")
            return False
            
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def test_word_counting():
    """Teste 3: Verificar contagem de palavras"""
    print("\n[3/5] Testando contagem de palavras...")
    try:
        from src.translator_core import _count_words
        
        test_cases = {
            "hello world": 2,
            "one two three four five": 5,
            "": 0,
            "   ": 0,
        }
        
        all_ok = True
        for text, expected in test_cases.items():
            result = _count_words(text)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{text[:20]}...' -> {result} palavras")
            if result != expected:
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def test_configuration():
    """Teste 4: Verificar configuração .env"""
    print("\n[4/5] Verificando configuração .env...")
    try:
        ollama_base = os.environ.get("OLLAMA_BASE_URL", "não definido")
        ollama_model = os.environ.get("OLLAMA_MODEL", "não definido")
        ollama_temp = os.environ.get("OLLAMA_TEMPERATURE", "não definido")
        
        print(f"  OLLAMA_BASE_URL: {ollama_base}")
        print(f"  OLLAMA_MODEL: {ollama_model}")
        print(f"  OLLAMA_TEMPERATURE: {ollama_temp}")
        
        if all([ollama_base != "não definido", 
                ollama_model != "não definido",
                ollama_temp != "não definido"]):
            print("  ✓ Configuração Ollama está OK")
            return True
        else:
            print("  ✗ Faltam variáveis .env")
            return False
            
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def test_directory_structure():
    """Teste 5: Verificar estrutura de diretórios"""
    print("\n[5/5] Verificando estrutura de diretórios...")
    try:
        required_dirs = ["input", "output", "src"]
        required_files = [".env", "main.py", "requirements.txt"]
        
        project_root = Path.cwd()
        
        all_ok = True
        
        for d in required_dirs:
            path = project_root / d
            status = "✓" if path.is_dir() else "✗"
            print(f"  {status} {d}/")
            if not path.is_dir():
                all_ok = False
        
        for f in required_files:
            path = project_root / f
            status = "✓" if path.is_file() else "✗"
            print(f"  {status} {f}")
            if not path.is_file():
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return False


def main():
    """Executar todos os testes"""
    print("=" * 60)
    print("VERIFICAÇÃO: Lume-Novel-Localizer com Ollama")
    print("=" * 60)
    
    # Carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception as e:
        print(f"Aviso: .env não foi carregado: {e}")
    
    results = [
        ("Importações", test_imports()),
        ("Chunking", test_chunking()),
        ("Word Count", test_word_counting()),
        ("Configuração .env", test_configuration()),
        ("Estrutura", test_directory_structure()),
    ]
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES:")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status}: {name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n" + "=" * 60)
        print("✓ SISTEMA PRONTO PARA TRADUÇÃO!")
        print("=" * 60)
        print("\nPróximos passos:")
        print("1. Execute em outro terminal: ollama serve")
        print("2. Execute: python main.py")
        print("3. Coloque seus arquivos em: input/novel_name/*.txt")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ PROBLEMAS DETECTADOS")
        print("=" * 60)
        print("Veja os erros acima e corrija antes de prosseguir.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
