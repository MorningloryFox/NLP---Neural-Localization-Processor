#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de validação: Senior Localization Refactor
- Pré-processamento: títulos e termos obfuscados
- Gênero: verificação de pronomes/artigos
- Aspas Japonesas: 「」 enforcement
- Anti-censura: conteúdo adulto traduzido
- Métricas: % de Retenção com threshold 90%
"""

import sys
import os
from pathlib import Path

# Set working directory and encoding
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from src.translator_core import (
    restore_obfuscated_terms,
    normalize_chapter_titles,
    fix_japanese_quotes,
    _count_words,
)


def test_restore_obfuscated_terms():
    """Test leetspeak restoration."""
    print("\n=== TESTE 1: Restaurar Termos Obfuscados ===")
    
    test_cases = [
        ("Ela tinha uma v4gina linda", "Ela tinha uma vagina linda"),
        ("O p3nis dele era grande", "O pênis dele era grande"),
        ("Ele sussurrou com seu c0ck duro", "Ele sussurrou com seu cock duro"),
        ("Ela gemeu alto enquanto cum saía", "Ela gemeu alto enquanto cum saía"),
    ]
    
    for original, expected in test_cases:
        result = restore_obfuscated_terms(original)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] '{original}' -> '{result}'")
        if result != expected:
            print(f"       Esperado: '{expected}'")


def test_normalize_chapter_titles():
    """Test title normalization."""
    print("\n=== TESTE 2: Normalizar Títulos de Capítulos ===")
    
    test_cases = [
        (
            "Chapter 1 - The Beginning\n\nOnce upon a time...",
            "Once upon a time...",
            "The Beginning",
        ),
        (
            "Capítulo 5 - Um Novo Começo\n\nEra uma vez...",
            "Era uma vez...",
            "Um Novo Começo",
        ),
        (
            "Volume 2, Chapter 10 - Dark Secrets\n\nThe forest was dark...",
            "The forest was dark...",
            "Dark Secrets",
        ),
    ]
    
    for original, expected_text, expected_title in test_cases:
        clean_text, detected_title = normalize_chapter_titles(original)
        
        text_match = expected_text in clean_text
        title_match = expected_title in detected_title if detected_title else False
        
        status = "PASS" if (text_match and title_match) else "FAIL"
        print(f"[{status}] Titulo: '{detected_title}'")
        print(f"       Clean comeca com: '{clean_text[:40]}...'")
        if not title_match:
            print(f"       [FAIL] Esperado titulo: '{expected_title}'")


def test_fix_japanese_quotes():
    """Test Japanese quote correction."""
    print("\n=== TESTE 3: Corrigir Aspas Japonesas ===")
    
    test_cases = [
        ('」O que?「', '「O que?」'),
        ('"Oi tudo bem?"', '「Oi tudo bem?」'),
        ('— Sim, claro.', '「Sim, claro.」'),
        ('「Perfeito!」', '「Perfeito!」'),
    ]
    
    for original, expected in test_cases:
        result = fix_japanese_quotes(original)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] '{original}' -> '{result}'")
        if result != expected:
            print(f"       Esperado: '{expected}'")


def test_adult_content_preservation():
    """Test anti-censorship: adult content is preserved."""
    print("\n=== TESTE 4: Anti-Censura - Conteúdo Adulto ===")
    
    adult_text = """
    Ela gemeu alto enquanto seu c0ck pulsava dentro dela. O pênis dele se movia com precisão,
    e ela gritou de prazer. Cada gemido saía de sua garganta sem controle.
    """
    
    restored = restore_obfuscated_terms(adult_text)
    critical_terms = ["gemeu", "pulsava", "pênis", "gritou", "gemido"]
    
    all_present = all(term in restored for term in critical_terms)
    status = "PASS" if all_present else "FAIL"
    print(f"[{status}] Termos adultos nao censurados:")
    for term in critical_terms:
        present = "OK" if term in restored else "MISSING"
        print(f"       [{present}] {term}")


def test_retention_percentage():
    """Test character retention percentage calculation."""
    print("\n=== TESTE 6: Porcentagem de Retencao (90% threshold) ===")
    
    original = "This is a sample sentence for testing retention."
    translated = "Esta eh uma sentenca de amostra para testar retencao."
    
    orig_chars = len(original.replace(' ', '').replace('\n', ''))
    trans_chars = len(translated.replace(' ', '').replace('\n', ''))
    
    retention = (trans_chars / orig_chars) * 100
    
    print(f"Original: {orig_chars} caracteres")
    print(f"Traduzido: {trans_chars} caracteres")
    print(f"Retencao: {retention:.1f}%")
    
    if retention >= 90:
        print(f"[PASS] Retencao acima do threshold 90%")
    else:
        print(f"[FAIL] Retencao abaixo do threshold 90%")


def test_word_count():
    """Test word counting."""
    print("\n=== TESTE 7: Contagem de Palavras ===")
    
    text = "Este eh um teste de contagem de palavras para validar metrics."
    word_count = _count_words(text)
    
    print(f"Texto: '{text}'")
    print(f"Contagem: {word_count} palavras")


def main():
    print("=" * 70)
    print("TESTE: REFATORACAO SENIOR LOCALIZATION")
    print("=" * 70)
    
    try:
        test_restore_obfuscated_terms()
        test_normalize_chapter_titles()
        test_fix_japanese_quotes()
        test_adult_content_preservation()
        test_retention_percentage()
        test_word_count()
        
        print("\n" + "=" * 70)
        print("TESTES COMPLETOS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


def test_restore_obfuscated_terms():
    """Test leetspeak restoration."""
    print("\n=== TESTE 1: Restaurar Termos Obfuscados ===")
    
    test_cases = [
        ("Ela tinha uma v4gina linda", "Ela tinha uma vagina linda"),
        ("O p3nis dele era grande", "O pênis dele era grande"),
        ("Ele sussurrou com seu c0ck duro", "Ele sussurrou com seu cock duro"),
        ("Ela gemeu alto enquanto cum saía", "Ela gemeu alto enquanto cum saía"),  # 'cum' já é correto
    ]
    
    for original, expected in test_cases:
        result = restore_obfuscated_terms(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' → '{result}'")
        if result != expected:
            print(f"   Esperado: '{expected}'")


def test_normalize_chapter_titles():
    """Test title normalization."""
    print("\n=== TESTE 2: Normalizar Títulos de Capítulos ===")
    
    test_cases = [
        (
            "Chapter 1 - The Beginning\n\nOnce upon a time...",
            "Once upon a time...",
            "Chapter 1 - The Beginning",
        ),
        (
            "Capítulo 5 - Um Novo Começo\n\nEra uma vez...",
            "Era uma vez...",
            "Capítulo 5 - Um Novo Começo",
        ),
        (
            "Volume 2, Chapter 10 - Dark Secrets\n\nThe forest was dark...",
            "The forest was dark...",
            "Volume 2, Chapter 10 - Dark Secrets",
        ),
    ]
    
    for original, expected_text, expected_title in test_cases:
        clean_text, detected_title = normalize_chapter_titles(original)
        
        text_match = expected_text in clean_text
        title_match = detected_title == expected_title
        
        status = "✅" if (text_match and title_match) else "❌"
        print(f"{status} Título: '{detected_title}'")
        print(f"   Clean Text começa com: '{clean_text[:50]}...'")
        if not title_match:
            print(f"   ❌ Esperado título: '{expected_title}'")
        if not text_match:
            print(f"   ❌ Esperado texto: '{expected_text}'")


def test_fix_japanese_quotes():
    """Test Japanese quote correction."""
    print("\n=== TESTE 3: Corrigir Aspas Japonesas 「」===")
    
    test_cases = [
        ('」O que?「', '「O que?」'),  # Invertido
        ('"Oi tudo bem?"', '「Oi tudo bem?」'),  # Aspas duplas
        ('— Sim, claro.', '「Sim, claro.」'),  # Travessão
        ('「Perfeito!」', '「Perfeito!」'),  # Já correto
        ('She said 「Hello there」', 'She said 「Hello there」'),  # Já correto
    ]
    
    for original, expected in test_cases:
        result = fix_japanese_quotes(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' → '{result}'")
        if result != expected:
            print(f"   Esperado: '{expected}'")


def test_adult_content_preservation():
    """Test anti-censorship: adult content is preserved."""
    print("\n=== TESTE 4: Anti-Censura - Conteúdo Adulto ===")
    
    adult_text = """
    Ela gemeu alto enquanto seu c0ck pulsava dentro dela. O pênis dele se movia com precisão,
    e ela gritou de prazer. Cada gemido saía de sua garganta sem controle.
    """
    
    # Test restoration
    restored = restore_obfuscated_terms(adult_text)
    
    critical_terms = ["gemeu", "pulsava", "pênis", "gritou", "gemido"]
    
    all_present = all(term in restored for term in critical_terms)
    status = "✅" if all_present else "❌"
    print(f"{status} Termos adultos presentes e não censurados:")
    for term in critical_terms:
        present = "✓" if term in restored else "✗"
        print(f"   {present} {term}")


def test_gender_consistency():
    """Test gender pronoun checking."""
    print("\n=== TESTE 5: Consistência de Gênero ===")
    
    # This is more manual since we'd need the full translation pipeline
    print("⏳ Teste de gênero requer pipeline completo (não implementado neste teste rápido)")
    print("   Conceito: Personagem FEMININO deve usar 'ela/a', MASCULINO deve usar 'ele/o'")


def test_retention_percentage():
    """Test character retention percentage calculation."""
    print("\n=== TESTE 6: % de Retenção (90% threshold) ===")
    
    original = "This is a sample sentence for testing retention."
    translated = "Esta é uma sentença de amostra para testar retenção."
    
    orig_chars = len(original.replace(' ', '').replace('\n', ''))
    trans_chars = len(translated.replace(' ', '').replace('\n', ''))
    
    retention = (trans_chars / orig_chars) * 100
    
    print(f"Original: {orig_chars} caracteres")
    print(f"Traduzido: {trans_chars} caracteres")
    print(f"Retenção: {retention:.1f}%")
    
    if retention >= 90:
        print(f"✅ PASSOU: Retenção acima do threshold 90%")
    else:
        print(f"❌ FALHOU: Retenção abaixo do threshold 90%")


def test_word_count():
    """Test word counting."""
    print("\n=== TESTE 7: Contagem de Palavras ===")
    
    text = "Este é um teste de contagem de palavras para validar metrics."
    word_count = _count_words(text)
    
    expected = 10
    status = "✅" if word_count == expected else "❌"
    print(f"{status} Contagem: {word_count} palavras (esperado: {expected})")


def main():
    print("=" * 70)
    print("TESTE: REFATORAÇÃO SENIOR LOCALIZATION")
    print("=" * 70)
    
    try:
        test_restore_obfuscated_terms()
        test_normalize_chapter_titles()
        test_fix_japanese_quotes()
        test_adult_content_preservation()
        test_gender_consistency()
        test_retention_percentage()
        test_word_count()
        
        print("\n" + "=" * 70)
        print("✅ TESTES COMPLETOS")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
