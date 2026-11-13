# NIRF Insight

**Interactive Higher Education Analytics & Visualization Platform**

A production-grade Streamlit analytics platform for exploring, analyzing, and visualizing NIRF (National Institutional Ranking Framework) data spanning 2017 to 2025 across all institutional categories in India.

---

## 🌟 Application Architecture & Pages

| Page | Description | Status |
|------|-------------|--------|
| **Overview** | KPI cards, longitudinal score trends, discipline distributions, top institutions | ✅ Complete (Phase 1) |
| **Dataset Explorer** | Filterable records browser, column audit, and interactive Data Quality Audit Report | ✅ Complete (Phase 1/2) |
| **Dynamic Graph Builder** | Fully interactive chart generator with 18 chart types, statistical aggregations & presets | ✅ Complete (Phase 4) |
| **Question Explorer** | All 40 official analytical questions across 8 core domains with live execution & CSV download | ✅ Complete (Phase 3) |
| **Geospatial Analysis** | State/City representation hubs, regional discipline dominance, interstate comparisons | ✅ Complete (Phase 1/2) |
| **Correlation & Analytics**| Bivariate scatter regressions, Pearson/Spearman matrix heatmaps, IQR/Z-score outlier detection | ✅ Complete (Phase 2) |
| **AI Chatbot** | **Dataset-grounded natural-language conversational assistant powered by OpenAI API & Pandas** | ✅ Complete (Phase 5) |

---

## 🤖 AI Chatbot Engine (Phase 5)

The NIRF Insight AI Assistant features an architecture that prevents LLM hallucinations by coupling OpenAI's natural language understanding with verified Python/Pandas mathematical execution:

```
User Query (e.g., "Top 10 Engineering colleges in 2024")
          │
          ▼
┌───────────────────────────────────────────────┐
│       OpenAI Natural Language Parser          │  (Extracts intent, filters & parameters)
│      (or Intelligent Heuristic Fallback)       │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│         Controlled Tool Registry              │  (15 Whitelisted analytics tools)
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│     Pandas / NumPy Dataset Calculation        │  (100% Mathematically accurate results)
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│         Automatic Plotly Visualizer           │  (Bar, Line, Scatter, Radar, etc.)
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│          Grounded Answer Synthesis            │  (Facts + Data Tables + Plotly Figure)
└──────────────────────┬────────────────────────┘
                       │
                       ▼
            Streamlit Chat Interface
```

### Whitelisted Analytics Tools
1. `get_dataset_summary` — High-level dataset metrics, records, categories, states
2. `get_available_years` — Ranking editions present (2017–2025)
3. `get_available_columns` — Dataset schema and descriptions
4. `get_top_institutions` — Top N rankings filtered by discipline, year, and state
5. `get_institution_details` — Historical trajectory & parameter profiles for specific institutions
6. `compare_institutions` — Head-to-head comparison across pillars
7. `get_yearly_trends` — National or institutional score/rank trends over time
8. `get_state_analysis` — State density, counts, and top regional performers
9. `get_category_analysis` — Inter-discipline comparisons and benchmarks
10. `get_parameter_analysis` — 5-pillar evaluations (TLR, RPC, GO, OI, Perception)
11. `get_score_statistics` — Five-number summary, mean, std dev, and IQR
12. `get_correlation_analysis` — Pearson $r$ and Spearman $\rho$ with scatter trendlines
13. `get_rank_changes` — Biggest climbers and decliners between editions
14. `get_distribution_analysis` — Histograms, boxplots, and quartile spreads
15. `get_filtered_dataset_summary` — Multi-parameter cohort queries

---

## 🔑 OpenAI API Configuration

The chatbot is designed to read credentials strictly from environment variables or a local `.env` file. Keys are **never hardcoded or exposed**.

### Setup Instructions
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your OpenAI API key and chosen model in `.env`:
   ```env
   OPENAI_API_KEY=sk-proj-your-actual-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Restart the Streamlit application:
   ```bash
   python -m streamlit run app.py
   ```

*Note:* If `OPENAI_API_KEY` is not provided, the chatbot automatically operates in **Grounded Heuristic Analytics Mode**, ensuring full conversational analytics, real data calculation, tables, and charts even without an active OpenAI subscription.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard
```bash
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 3. Run Automated Tests
```bash
python -m pytest tests/ -q
```
All **123/123 automated tests** pass, validating preprocessing, all 40 questions, the 18 dynamic chart types, and the complete chatbot pipeline.

---

## 📁 Repository Structure

```
MainProject/
├── app.py                          # Streamlit multi-page setup & navigation
├── assets/styles.css               # Nature-inspired palette (#3D6247, #5D7A60, #F7F8F4)
├── requirements.txt                # Python dependencies
├── .env.example                    # Template for OpenAI credentials
├── .gitignore                      # Protects .env and caches
│
├── core/
│   ├── data_loader.py              # Cached dataset loading & validation
│   ├── preprocessing.py            # Cleaning, string normalization & filtering
│   ├── analytics.py                # Descriptive statistics, correlations & outliers
│   ├── data_validation.py          # Quality audit & schema verification
│   ├── query_engine.py             # Multi-parameter cohort filtering
│   └── dynamic_chart_engine.py     # 18-chart generation engine (Phase 4)
│
├── questions/                      # Phase 3 Question Explorer Engine
│   ├── question_config.py          # Catalog of 40 questions in 8 domains
│   ├── question_functions.py       # Pure statistical algorithms for Q1-Q40
│   ├── chart_mapping.py            # Specialized Plotly chart renderers
│   └── question_engine.py          # Master question coordinator
│
├── chatbot/                        # Phase 5 AI Chatbot Engine
│   ├── __init__.py
│   ├── llm_service.py              # OpenAI SDK client & environment configuration
│   ├── tool_registry.py            # 15 Whitelisted function calling schemas
│   ├── intent_parser.py            # OpenAI tool calling + Heuristic fallback
│   ├── analytics_executor.py       # Deterministic Python/Pandas calculations & charts
│   ├── response_generator.py       # Grounded answer synthesis
│   ├── conversation_manager.py     # Multi-turn context memory & follow-ups
│   └── chatbot_service.py          # End-to-end pipeline orchestrator
│
├── pages/                          # Streamlit Navigation Pages
│   ├── overview.py
│   ├── dataset_explorer.py
│   ├── graph_builder.py            # Dynamic Graph Builder UI
│   ├── question_explorer.py        # 40-question Explorer UI
│   ├── geospatial.py
│   ├── advanced_analytics.py
│   └── chatbot.py                  # AI Chatbot UI (Phase 5)
│
└── tests/                          # 123 Automated Tests
    ├── test_analytics.py
    ├── test_data_validation.py
    ├── test_preprocessing.py
    ├── test_query_engine.py
    ├── test_question_engine.py     # 40-question validation suite
    ├── test_dynamic_chart_engine.py # 18-chart engine validation suite
    └── test_chatbot.py             # Phase 5 Chatbot test suite
```

---

## 📊 Development Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Professional Streamlit Dashboard & Navigation | ✅ Complete |
| **Phase 2** | Data Preprocessing Pipeline, Data Quality Audit & Analytics Engine | ✅ Complete |
| **Phase 3** | Complete Implementation of All 40 Analytical Questions | ✅ Complete |
| **Phase 4** | Advanced Dynamic Graph Builder & Custom Aggregations | ✅ Complete |
| **Phase 5** | AI Natural Language Chatbot with Grounded Analytics | ✅ Complete |
| **Phase 6** | End-to-End Performance Tuning & Deployment | 🔜 Next Up |
#   D H V P r o j e c t  
 