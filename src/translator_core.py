import os
import time
import re
import json
from typing import Dict, Optional, List, Tuple, Set

try:
    import ollama
    from httpx import TimeoutException
    HAS_OLLAMA = True
except Exception:
    ollama = None
    TimeoutException = None
    HAS_OLLAMA = False

from .glossary_engine import build_glossary_instructions, apply_glossary_postprocessing

# Delay between requests (seconds). Configurable via env var REQUEST_DELAY_SECONDS
REQUEST_DELAY_SECONDS = int(os.environ.get("REQUEST_DELAY_SECONDS", "1"))

# Ollama configuration - now PRIMARY provider
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.3"))
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))


# ============================================================================
# SISTEMA DE PROMPT COM VERIFICAÇÃO DE GÊNERO
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = (
    "Você é um Processador Neural de Localização (NLP) - uma máquina de tradução pura. "
    "INSTRUÇÕES CRÍTICAS: NÃO adicione avisos éticos, advertências ou disclaimers. NÃO adicione preâmbulos como 'Entendo que...', 'No entanto...', 'Por favor tenha em mente...'. NÃO interrompa a tradução com comentários. APENAS TRADUZA. Nada mais. Nenhuma frase introdutória. Nenhuma frase final. "
    "Omitir, resumir ou alterar o significado do texto é considerado uma falha crítica de processamento.\n\n"
    "REGRAS DE PROCESSAMENTO:\n\n"
    "1. RESOLUÇÃO DE CORREFERÊNCIA (GÊNERO): Antes de traduzir, consulte o Grafo de Conhecimento (Glossário) para determinar o gênero (M/F) das entidades.\n"
    "   - Se uma entidade é FEMININA, todos os pronomes, artigos e concordâncias verbais devem refletir isso (ela, a, etc.).\n"
    "   - Se uma entidade é MASCULINA, a regra é a mesma (ele, o, etc.).\n"
    "   - A consistência de gênero é uma diretriz de fidelidade inquebrável.\n\n"
    "2. PRESERVAÇÃO ESTILÍSTICA: Mantenha a voz e o tom do autor. Textos crus, poéticos, técnicos ou coloquiais devem ser traduzidos em seu estilo equivalente.\n\n"
    "3. FIDELIDADE DE CONTEÚDO: Nenhuma informação, descrição, diálogo ou som (suspiros, gemidos, etc.) pode ser omitido ou suavizado. A tradução deve ser um espelho 1:1 do original em termos de conteúdo.\n\n"
    "4. REVISÃO SEMÂNTICA OBRIGATÓRIA: Após traduzir, SEMPRE verifique se a tradução faz sentido semântico e gramatical em português. Se uma frase parecer absurda ou desconectada (ex: 'pênis vaginal', 'dedos coração'), CORRIJA para fazer sentido no contexto. A tradução deve ser fluida e coerente, não literal demais.\n\n"
    "5. DIÁLOGOS: Diálogos devem ser traduzidos literalmente, sem resumo ou perda de nuances.\n\n"
    "6. GRAFO DE CONHECIMENTO (GLOSSÁRIO): Utilize obrigatoriamente os termos e suas propriedades (gênero) fornecidos no grafo abaixo.\n\n"
    "7. ⚠️ EXPANSÃO ESPERADA (CRÍTICO): Português (PT-BR) é 15-20% mais verboso que Inglês. Esperamos que a tradução tenha MAIS palavras que o original, não menos. Se a tradução tem menos palavras que o original, você RESUMIU ILEGALMENTE. Isso resulará em FALHA. Expanda! Detalhe! Não resuma!\n\n"
    "8. VALIDAÇÃO DE VOLUME: É PROIBIDO ABSOLUTAMENTE resumir. A tradução final deve ter ≥90% da contagem de palavras originais. Se tiver menos, você falhou. Exemplo: Original 100 palavras = Tradução DEVE ter ≥90 palavras. Se tiver 50, é FALHA CRÍTICA.\n\n"
    "9. FORMATO DE SAÍDA: O output deve ser em texto puro, preservando as quebras de parágrafo do texto fonte.\n\n"
    "10. ASPAS JAPONESAS: Todo diálogo deve ser formatado com 「 e 」, em vez de aspas duplas ou travessões.\n\n"
    "Grafo de Conhecimento (Glossário):\n{glossary}\n"
)


def chunk_text_by_paragraphs(text: str, chunk_size: int = 8000, overlap: int = 200) -> List[Tuple[str, int, int]]:
    """
    Split text into chunks of ~8000 chars, respecting paragraph boundaries.
    
    Larger chunks = less overhead, better narrative continuity, fewer redundant translations.
    Optimized for qwen2.5:7b context window (handles 8-10K chars comfortably).
    
    Attempts to end chunks at paragraph breaks (\\n\\n) to preserve narrative continuity.
    Returns list of (chunk_text, start_idx, end_idx) tuples with 200-char overlap.
    """
    chunks = []
    pos = 0
    text_len = len(text)
    
    while pos < text_len:
        # Find chunk end: try to stay within chunk_size
        chunk_end = min(pos + chunk_size, text_len)
        
        # If we're not at text end, try to break at paragraph boundary
        if chunk_end < text_len:
            # Look for \n\n near the target end
            search_start = max(chunk_end - 500, pos)  # Search in last 500 chars of chunk
            last_para_break = text.rfind("\n\n", pos, chunk_end + 100)
            
            if last_para_break > search_start:
                chunk_end = last_para_break + 2  # Include the \n\n
        
        chunk = text[pos:chunk_end]
        chunks.append((chunk, pos, chunk_end))
        
        # If we reached the end, break
        if chunk_end >= text_len:
            break
        
        # Move forward by (chunk_size - overlap) for next iteration
        pos = chunk_end - overlap
    
    return chunks



def _call_ollama_text(prompt: str, temperature: float = 0.3) -> str:
    """
    Call Ollama locally using native ollama package.
    
    Uses OpenAI-compatible endpoint at localhost:11434/v1
    Model: qwen2.5:7b (configurable via OLLAMA_MODEL)
    """
    if not HAS_OLLAMA:
        raise RuntimeError(
            "Ollama package not installed. Install via: pip install ollama"
        )
    
    try:
        # Use the ollama package's chat interface
        # It connects to http://localhost:11434 by default and has a configurable timeout
        client = ollama.Client(host=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": temperature,
            }
        )
        
        # Extract text from response
        text = response.get("message", {}).get("content", "")
        time.sleep(REQUEST_DELAY_SECONDS)
        return text
        
    except (ConnectionError, ollama.ResponseError, ollama.RequestError, TimeoutException) as e:
        # Catch connection errors, including timeouts
        raise RuntimeError(
            f"Conexão com Ollama em {OLLAMA_BASE_URL} falhou (timeout de {OLLAMA_TIMEOUT}s).\n"
            f"Verifique se o Ollama está rodando e acessível:\n"
            f"  1. Instale e execute o app Ollama: https://ollama.com\n"
            f"  2. (Opcional) Execute no terminal: ollama serve\n"
            f"  3. Baixe o modelo necessário: ollama pull {OLLAMA_MODEL}\n"
            f"Se o timeout persistir, aumente a variável de ambiente OLLAMA_TIMEOUT.\n"
            f"Erro original: {e.__class__.__name__}"
        )
    except Exception as e:
        raise RuntimeError(f"Erro inesperado no Ollama: {e}")


def _call_model_text(model: str, prompt: str, temperature: float = 0.3) -> str:
    """Call Ollama (único provedor)."""
    return _call_ollama_text(prompt, temperature=temperature)


def remove_translation_noise(text: str) -> str:
    """
    Remove avisos éticos, preâmbulos e poluição adicionados pelo modelo.
    
    Padrões para remover:
    - "Entendo que..." (preâmbulos de disclaimer)
    - "No entanto..." (mas com avisos)
    - "Por favor..." (pedidos educados antes/depois)
    - "É importante..." (avisos éticos)
    - "Ainda assim..." (concessões)
    - Linhas com "---" (separadores)
    - Avisos de conteúdo sensível
    """
    lines = text.split('\n')
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detectar início de avisos éticos
        if any(stripped.startswith(prefix) for prefix in [
            'Entendo que',
            'No entanto',
            'Por favor',
            'É importante',
            'Ainda assim',
            'Aviso:',
            'AVISO:',
            'Este texto',
            'Este tipo',
            'Conteúdo',
            'conteúdo',
            'Além disso'
        ]):
            skip_mode = True
            continue
        
        # Linhas separadoras marcam fim de avisos
        if stripped in ['---', ''] and skip_mode:
            skip_mode = False
            continue
        
        # Ignorar linhas vazias do início de avisos
        if skip_mode and stripped == '':
            continue
        
        # Se não é aviso, adicionar
        if not skip_mode:
            cleaned_lines.append(line)
    
    # Remover linhas vazias no início e final
    while cleaned_lines and cleaned_lines[0].strip() == '':
        cleaned_lines.pop(0)
    while cleaned_lines and cleaned_lines[-1].strip() == '':
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)


def fix_japanese_quotes(text: str) -> str:
    """
    Corrige aspas japonesas invertidas ou mal formatadas.
    
    Regra: Todo diálogo DEVE ser: 「texto」(não 」texto「)
    
    Ordem CRÍTICA de processamento:
    1. Remove triplas: 「」」 → 「
    2. Corrige invertidas: 」...「 → 「...」 (ANTES de balancear!)
    3. Remove duplicadas: 」」 → 」
    4. Aspas duplas: "..." → 「...」
    5. Travessões: — ... → 「...」
    6. Balanceia casos faltando abertura/fechamento
    """
    # Step 0: Remove triplas malformadas 「」」 → 「
    text = re.sub(r'「」」', r'「', text)
    
    # Step 1: CRÍTICO - Corrige invertidas PRIMEIRO antes de qualquer balanceamento
    # Padrão: fechamento + conteúdo + abertura → inverter
    text = re.sub(r'」([^」「]*?)「', r'「\1」', text)
    
    # Step 2: Remove fechamentos duplicados 」」 → 」 (mas não 」「)
    text = re.sub(r'」」(?!「)', r'」', text)
    
    # Step 3: Aspas duplas "..." → 「...」
    quote_pairs = re.findall(r'"([^"]+)"', text)
    for pair in quote_pairs:
        text = text.replace(f'"{pair}"', f'「{pair}」', 1)
    
    # Step 4: Travessão solo em contexto de diálogo
    text = re.sub(r'—\s*([^。\n]+)', r'「\1」', text)
    
    # Step 5: Balanceamento final linha por linha
    lines = text.split('\n')
    for i, line in enumerate(lines):
        open_count = line.count('「')
        close_count = line.count('」')
        
        # Mais fechamentos que aberturas - adicionar abertura antes do primeiro desbalanceado
        while close_count > open_count:
            for idx, ch in enumerate(line):
                if ch == '」':
                    before = line[:idx]
                    if before.count('「') <= before.count('」'):
                        line = line[:idx] + '「' + line[idx:]
                        open_count += 1
                        close_count = line.count('」')
                        break
            else:
                break
        
        # Mais aberturas que fechamentos - adicionar fechamento no final
        while open_count > close_count:
            line = line + '」'
            close_count += 1
        
        lines[i] = line
    
    return '\n'.join(lines)


def _count_words(text: str) -> int:
    """Count words in text (simple split on whitespace)."""
    return len(text.split())


def translate_text(
    text: str,
    source_lang: Optional[str],
    glossary: Dict[str, str],
    api_key: Optional[str] = None,
    glossary_path: Optional[str] = None,
    novel_name: Optional[str] = None,
    enable_semantic_review: bool = True,
    is_mature_content: bool = True,
) -> str:
    """
    Translate text into PT-BR using intelligent chunking, fidelity protection, and semantic review.
    
    Args:
        text: Texto a traduzir
        source_lang: Idioma fonte (opcional, detectado automaticamente)
        glossary: Glossário de termos conhecidos
        api_key: Chave de API (não usado com Ollama)
        glossary_path: Caminho para salvar novos termos
        novel_name: Nome da novel (para extrair termos)
        enable_semantic_review: Se True, revisa o capítulo completo após tradução
        is_mature_content: Se True, permite linguagem +18 durante revisão
    
    - Chunks by paragraph boundaries (~3000 chars, 150-char overlap)
    - Validates fidelity: translation must be ≥85% of original word count
    - Reprocesses chunks that fail fidelity check with explicit warning
    - PÓS-PROCESSING: Corrige aspas japonesas e aplica glossário
    """
    original_word_count = _count_words(text)
    
    # If text is small, translate directly without chunking (faster & better context)
    if len(text) < 8000:
        trans = _translate_single_chunk(text, glossary, api_key)
        
        # Limpeza de avisos éticos
        trans = remove_translation_noise(trans)
        trans = fix_japanese_quotes(trans)
        
        trans_word_count = _count_words(trans)
        
        # Check fidelity
        if trans_word_count < original_word_count * 0.90:
            print(f"  Fidelidade baixa ({trans_word_count}/{original_word_count} palavras). Reprocessando com temperatura maior...")
            trans = _translate_single_chunk(
                text,
                glossary,
                api_key,
                force_fidelity=True,
                temperature=OLLAMA_TEMPERATURE + 0.2,
            )
            trans = remove_translation_noise(trans)
            trans = fix_japanese_quotes(trans)
        
        return trans
    
    # For larger texts, chunk by paragraphs (reduced from 3000 to 8000 chars)
    chunks = chunk_text_by_paragraphs(text, chunk_size=8000, overlap=200)
    translated_chunks = []
    
    for i, (chunk, start_idx, end_idx) in enumerate(chunks):
        chunk_words = _count_words(chunk)
        print(f"  [Chunk {i+1}/{len(chunks)}] ({start_idx}-{end_idx}, {chunk_words} palavras)...", flush=True)
        
        try:
            trans = _translate_single_chunk(chunk, glossary, api_key)
            trans_words = _count_words(trans)
            
            # Check fidelity: ≥90% of original word count (profissional sênior)
            if trans_words < chunk_words * 0.90:
                print(f"    Resumo detectado ({trans_words}/{chunk_words} palavras). Reprocessando chunk {i+1} com temperatura maior...")
                trans = _translate_single_chunk(
                    chunk,
                    glossary,
                    api_key,
                    force_fidelity=True,
                    temperature=OLLAMA_TEMPERATURE + 0.2,
                )
                trans_words = _count_words(trans)
                
                # Final check after reprocessing
                if trans_words < chunk_words * 0.90:
                    print(f"    AVISO: Fidelidade ainda baixa após reprocessamento ({trans_words}/{chunk_words} palavras)")
            
            translated_chunks.append(trans)
        except Exception as e:
            print(f"    Erro chunk {i+1}: {e}")
            raise
    
    # Concatenate chunks (overlap is minimal, so just join)
    result = "".join(translated_chunks)
    
    # PÓS-PROCESSAMENTO: Remover avisos éticos/poluição
    print("  Pós-processamento: limpando avisos éticos...")
    result = remove_translation_noise(result)
    
    # PÓS-PROCESSAMENTO: Corrigir aspas japonesas
    print("  Pós-processamento: corrigindo aspas japonesas...")
    result = fix_japanese_quotes(result)
        # REVISÃO SEMÂNTICA: Revisar capítulo completo para coerência
    if enable_semantic_review:
        print("  Revisão semântica: validando coerência do capítulo...")
        result = semantic_review_chapter(
            result, 
            glossary, 
            api_key=api_key,
            is_mature_content=is_mature_content
        )
    
    # EXTRAÇÃO DE GLOSSÁRIO: Identificar e salvar novos termos
    if glossary_path and novel_name:
        print("  Extração de glossário: identificando novos termos...")
        new_terms = extract_new_terms(result, glossary)
        if new_terms:
            updated_glossary = save_new_glossary_terms(new_terms, glossary_path, novel_name)
            glossary.update(updated_glossary)
        # Final validation
    final_words = _count_words(result)
    print(f"  Tradução completa: {final_words}/{original_word_count} palavras ({round((final_words/original_word_count)*100, 1)}%)")
    
    return result


def _translate_single_chunk(
    chunk: str,
    glossary: Dict[str, str],
    api_key: Optional[str] = None,
    force_fidelity: bool = False,
    temperature: Optional[float] = None,
) -> str:
    """
    Translate a single chunk with consolidated prompt (translate+revise in one).
    
    Uses Ollama with temperature 0.3 for balance between precision and literary fluidity.
    
    NOTE ON CHARACTER COUNT:
    PT-BR é ~15-20% mais verboso que inglês (mais artigos, preposições, conjugações).
    Por isso usamos % de PALAVRAS (90%) ao invés de caracteres para validar fidelidade.
    Caracteres podem oscilar: inglês compacto → PT-BR expansivo é NORMAL e esperado.
    """
    glossary_block = build_glossary_instructions(glossary)
    system = SYSTEM_PROMPT_TEMPLATE.format(glossary=glossary_block)
    
    # Extra warning if reprocessing due to low fidelity
    extra_warning = (
        "\n⚠️ AVISO CRÍTICO OBRIGATÓRIO: Este bloco foi identificado como RESUMIDO. "
        "VOCÊ FALHOU na última tentativa ao fornecer <90% das palavras originais. "
        "DESTA VEZ, VOCÊ DEVE TRADUZIR COM EXATAMENTE ≥90% DAS PALAVRAS ORIGINAIS! "
        "SE FALHAR NOVAMENTE, SERÁ UM ERRO CRÍTICO DE PROCESSAMENTO!\n"
        if force_fidelity else ""
    )
    
    # Consolidated single-pass prompt
    prompt = (
        system + extra_warning +
        "\n---\n"
        "TAREFA (UMA ÚNICA PASSAGEM):\n"
        "1. Traduza o texto abaixo para Português (PT-BR) PALAVRA POR PALAVRA. Não resuma!\n"
        "2. Expanda onde necessário - PT-BR é mais verboso que Inglês (15-20% mais palavras é ESPERADO)\n"
        "3. Revise a tradução para soar natural e coerente EM PORTUGUÊS, SEM alterar o estilo\n"
        "4. VALIDE: Conte as palavras. A tradução DEVE ter ≥90% das palavras do original.\n"
        "5. Se a tradução tiver menos palavras que o original, você RESUMIU e FALHOU. Reescreva.\n"
        "---\n\n"
        + chunk
    )
    
    # Use Ollama temperature for translation
    final_temperature = temperature if temperature is not None else OLLAMA_TEMPERATURE
    translated = _call_model_text("models/gemini-2.5-flash", prompt, temperature=final_temperature)
    final_post = apply_glossary_postprocessing(translated, glossary)
    return final_post


def extract_new_terms(text: str, existing_glossary: Dict[str, str]) -> Dict[str, Dict]:
    """
    Extrai termos novos do texto traduzido.
    
    Estratégia: Procura por nomes próprios (palavras capitalizadas de 4+ letras que aparecem 2+ vezes).
    Filtra palavras comuns, verbos, adjetivos, preposições e PALAVRAS EM INGLÊS.
    
    CRÍTICO: Só extrai palavras que parecem ser português (traduzidas corretamente).
    Palavras em inglês não-traduzidas devem ser ignoradas (ex: Dungeon → Masmorra).
    """
    new_terms = {}
    known_names = set(existing_glossary.keys())
    
    # Lista EXPANDIDA de palavras a filtrar (artigos, preposições, conjunções, verbos comuns, adjetivos)
    common_words = {
        # Artigos e pronomes
        'Uma', 'Um', 'O', 'A', 'Os', 'As', 'Que', 'E', 'De', 'Do', 'Da', 'Dos', 'Das',
        # Adjetivos e demonstrativos
        'Como', 'Então', 'Depois', 'Dentro', 'Seu', 'Sua', 'Todo', 'Toda', 'Todos', 'Todas',
        'Este', 'Esse', 'Aquele', 'Dele', 'Dela', 'Deles', 'Delas',
        # Preposições e conjunções
        'Com', 'Por', 'Para', 'Desde', 'Até', 'Entre', 'Enquanto', 'Não', 'Mas',
        'Se', 'Ou', 'Quando', 'Onde', 'Qual', 'Quais', 'Quanto', 'Quantos',
        # Inglês comum
        'I', 'A', 'The', 'To', 'Is', 'Was', 'Were', 'Be', 'Been',
        'On', 'At', 'In', 'By', 'From', 'Up', 'About', 'Out', 'After', 'Before',
        # Verbos conjugados comuns em PT-BR
        'Obrigado', 'Você', 'Certo', 'Certamente', 'Lembro', 'Conservo', 'Havia', 'Notei', 'Fiquei',
        'Olhei', 'Confuso', 'Finalmente', 'Primeiro', 'Seguindo', 'Agora', 'Resumindo', 'Quero',
        'Devido', 'Aceitando', 'Consistência', 'Mantenha', 'Detalhes', 'Adicione', 'Melhoria',
        'Continuarei', 'Voltei', 'Encontrei', 'Disse', 'Respondeu', 'Perguntou', 'Sussurrou',
        'Gritou', 'Murmurou', 'Vou', 'Posso', 'Devo', 'Preciso', 'Consigo', 'Deveria',
        'Realmente', 'Simplesmente', 'Apenas', 'Talvez', 'Ainda', 'Nunca', 'Sempre', 'Também',
    }
    
    # Palavras em inglês típicas que indicam tradução incompleta
    english_indicators = {
        'Dungeon', 'Room', 'Hall', 'Gate', 'Door', 'Wall', 'Floor', 'Ceiling', 'Master',
        'Battle', 'Fight', 'Quest', 'Level', 'Experience', 'Skill', 'Spell', 'Magic',
        'Slime', 'Monster', 'Beast', 'Dragon', 'Goblin', 'Orc', 'Elf', 'Human', 'King',
        'School', 'Academy', 'Guild', 'Party', 'Team', 'Group', 'Leader', 'Member',
        'System', 'Status', 'Window', 'Menu', 'Quest', 'Chapter', 'Book', 'Volume',
    }
    
    # Extrair todas as palavras
    all_words = re.findall(r'\b\w+\b', text)
    word_freq = {}
    for word in all_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Filtrar e extrair termos candidatos
    for term, freq in word_freq.items():
        # Critérios de seleção rigorosos
        if (freq >= 2 and                          # Apareceu 2+ vezes
            term not in known_names and            # Não está no glossário
            term not in common_words and           # Não é palavra comum/verbo/adjetivo
            term not in english_indicators and     # NÃO É PALAVRA EM INGLÊS NÃO-TRADUZIDA
            len(term) >= 4 and                     # Mínimo 4 caracteres
            term[0].isupper() and                  # Começa com maiúscula
            not term[0].isdigit() and              # Não começa com número
            term not in new_terms):                # Não foi adicionado já
            
            # Encontrar contexto
            idx = text.find(term)
            if idx != -1:
                start = max(0, idx - 60)
                end = min(len(text), idx + len(term) + 60)
                context = text[start:end]
            else:
                context = ""
            
            # Classificar tipo baseado em contexto
            term_type = "character"  # Default
            context_lower = context.lower()
            
            if any(loc in context_lower for loc in ["masmorra", "sala", "castelo", "cidade", "quarto", "caverna", "lugar", "terra", "reino", "floresta"]):
                term_type = "location"
            elif any(creature in context_lower for creature in ["slime", "monstro", "criatura", "besta", "demônio", "espírito", "goblin", "orc"]):
                term_type = "creature"
            elif any(ability in context_lower for ability in ["habilidade", "poder", "magia", "skill", "técnica", "ataque", "feitiço"]):
                term_type = "ability"
            
            new_terms[term] = {
                "type": term_type,
                "pt_br": term,
                "frequency": freq,
                "context": context
            }
    
    return new_terms


def semantic_review_chapter(
    full_translation: str,
    glossary: Dict[str, str],
    api_key: Optional[str] = None,
    is_mature_content: bool = True
) -> str:
    """
    Revisa o capítulo traduzido para garantir coerência semântica e naturalidade.
    
    - Valida coerência de pronomes e gênero com glossário
    - Normaliza terminologia para estar consistente
    - Permite termos +18 em contexto apropriado
    - Garante que glossário foi aplicado corretamente
    
    Args:
        full_translation: Capítulo completo traduzido
        glossary: Glossário de termos conhecidos
        is_mature_content: Se True, permite linguagem explícita/chula
    
    Returns:
        Capítulo revisado
    """
    glossary_block = build_glossary_instructions(glossary)
    
    # Prompt de revisão adaptado ao tipo de conteúdo
    mature_instruction = (
        "Este é conteúdo adulto (+18). Durante a revisão, permita linguagem explícita, "
        "termos chulos e descrições sexuais quando apropriado ao contexto. Natureza explícita "
        "é ESPERADA e não deve ser suavizada.\n"
        if is_mature_content
        else ""
    )
    
    review_prompt = (
        "Você é um REVISOR DE LOCALIZAÇÃO especializado. Sua tarefa é revisar uma tradução COMPLETA "
        "e garantir que:\n\n"
        f"{mature_instruction}"
        "1. COERÊNCIA SEMÂNTICA: A tradução faz sentido lógico e narrativo. Frases absurdas ou desconexas devem ser corrigidas.\n"
        "2. CONSISTÊNCIA DE GLOSSÁRIO: Todos os termos de personagens, lugares e habilidades correspondem EXATAMENTE ao glossário fornecido.\n"
        "3. CONSISTÊNCIA DE GÊNERO: Pronomes e artigos concordam com o gênero dos personagens (verificar glossário).\n"
        "4. NATURALIDADE: A tradução flui naturalmente em português, não pareça tradução literal.\n"
        "5. PRESERVAÇÃO: Nenhuma informação deve ser omitida ou suavizada (exceto se for verdadeira melhora de prosa).\n\n"
        "INSTRUÇÕES CRÍTICAS:\n"
        "- NÃO adicione avisos éticos ou disclaimers.\n"
        "- APENAS REVISE E MELHORE. Não resuma nem altere significado.\n"
        "- Se a tradução já está boa, devolva como está.\n\n"
        f"Grafo de Conhecimento (Glossário):\n{glossary_block}\n\n"
        "---\n"
        "CAPÍTULO A REVISAR:\n"
        f"{full_translation}"
    )
    
    print("  Revisão semântica do capítulo completo...")
    reviewed = _call_model_text("models/gemini-2.5-flash", review_prompt, temperature=0.2)
    reviewed = remove_translation_noise(reviewed)
    
    return reviewed


def save_new_glossary_terms(
    new_terms: Dict[str, Dict],
    glossary_path: str,
    novel_name: str
) -> Dict[str, str]:
    """
    Salva novos termos extraídos no glossário da novel.
    
    Atualiza terms.json com novos termos identificados.
    Retorna apenas os novos termos em formato Dict[str, str] para atualizar glossário.
    """
    terms_file = f"{glossary_path}/terms.json"
    
    try:
        with open(terms_file, 'r', encoding='utf-8') as f:
            current_glossary = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        current_glossary = {}
    
    # Dicionário para retornar (apenas termo -> termo, sem metadados)
    new_glossary_entries = {}
    
    # Adicionar novos termos com metadados
    for term, info in new_terms.items():
        if term not in current_glossary:
            current_glossary[term] = {
                "type": info.get("type", "misc"),
                "pt_br": info.get("pt_br", term),
                "en": info.get("en", ""),
                "context": info.get("context", ""),
                "added_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "gender": "M",  # Default, pode ser atualizado manualmente
            }
            new_glossary_entries[term] = term  # Adicionar ao retorno (Dict[str, str])
            print(f"    [NOVO TERMO] {term} ({info.get('type', 'misc')})")
    
    # Salvar glossário atualizado
    with open(terms_file, 'w', encoding='utf-8') as f:
        json.dump(current_glossary, f, ensure_ascii=False, indent=2)
    
    return new_glossary_entries
