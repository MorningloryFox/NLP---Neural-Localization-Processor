# NLP - Neural Localization Processor

**High-Fidelity Document Localization and Translation Pipeline** — Ollama-Only (Local, Offline, 100% Private)

---

## 🚀 Quick Start

### 1. Install Ollama
- Download: https://ollama.ai
- Run: `ollama serve` (leave running)
- Pull model: `ollama pull qwen2.5:7b` (or another high-quality model)

### 2. Setup Python
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Configure `.env`
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TEMPERATURE=0.3
OUTPUT_DIR=./output
```

### 4. Add Documents & Translate
```bash
# Place .txt files in:
input/your_project_name/chapter_01.txt
input/your_project_name/chapter_02.txt

# Run:
python main.py

# Output:
output/your_project_name/chapter_01.docx
output/your_project_name/stats_execucao.xlsx
```

---

## ✨ Features

- **100% Local & Private**: Runs entirely offline using Ollama. No data ever leaves your machine.
- **Context-Aware Translation**: Utilizes a per-project Knowledge Graph (glossary) to ensure terminological and contextual consistency (e.g., character gender).
- **Stateful Processing**: Maintains a memory of previous sections to inform the translation of subsequent sections, preserving narrative flow.
- **Semantic Normalization**: A pre-processing pipeline cleans and normalizes source text, restoring stylistic abbreviations and standardizing chapter titles.
- **Fidelity Validation**: Automatically validates translation volume against the source, re-translating any chunk that appears to be a summary.
- **Advanced Formatting Engine**: Enforces custom formatting rules, such as Japanese-style quotes (`「...」`), via a regex-based post-processing engine.

---

## 📊 Technical Standards

| Metric | Standard | Purpose |
|--------|----------|---------|
| **Volume Fidelity** | ≥85% word count | Prevents summarization and ensures a 1:1 content ratio. |
| **Character Retention** | ≥90% character count | A professional standard for high-fidelity localization. |
| **Dialogue Formatting** | `「...」` enforced | Maintains specific stylistic requirements of the source text. |
| **Co-reference Resolution** | Pronoun/Gender agreement | Ensures character consistency via the Knowledge Graph. |
| **Linguistic Fidelity** | Unaltered translation | Preserves the original author's tone, style, and meaning. |

---

## 📁 Project Structure

```
├── main.py                          # Main orchestrator for the NLP pipeline
├── requirements.txt                 # Dependencies
├── .env                             # Configuration for Ollama and file paths
│
├── src/
│   ├── document_loader.py           # Handles file I/O and semantic normalization (pre-processing)
│   ├── glossary_engine.py           # Manages the Knowledge Graph and stateful context memory
│   ├── translator_core.py           # Core translation logic via Ollama API
│   ├── exporter.py                  # Handles final output generation (.docx, .xlsx)
│   └── formatter.py                 # (Legacy) Currently unused, formatting handled by translator_core
│
├── input/                           # Source documents (*.txt)
├── output/                          # Translated documents and session files
├── glossary/                        # Project-specific Knowledge Graphs
└── config/                          # (Legacy) Novel-specific configurations
```

---

## 🔧 Configuration

Edit `.env` to customize:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server location
OLLAMA_MODEL=qwen2.5:7b                 # Model name
OLLAMA_TEMPERATURE=0.3                  # 0.0=precise, 1.0=creative
OUTPUT_DIR=./output                     # Where to save all outputs
```

---

## 📖 Documentation

- **[TECHNICAL_SPEC.md](REFACTOR_SENIOR_LOCALIZATION.md)** — Detailed technical documentation of the system architecture and NLP pipeline, including:
  - Semantic Normalization pipeline
  - Knowledge Graph and Co-reference Resolution
  - Japanese Quotation Enforcement
  - Fidelity and Retention Metrics

---

## ⚙️ Troubleshooting

**"Ollama não está disponível"**
- Check: Is Ollama running? `ollama serve`
- Check: Correct URL in .env

**Low translation quality**
- Adjust: `OLLAMA_TEMPERATURE` (try 0.2 or 0.4)
- Verify: Model exists: `ollama list`

**Python errors**
- Run: `python verify_setup.py`
- Reinstall: `pip install -r requirements.txt`

---

**Version**: 2.0 NLP | **Status**: ✅ Ready