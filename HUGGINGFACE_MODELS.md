# HuggingFace Models Research for NLP Pipeline

This document contains research findings on lightweight HuggingFace models that can be integrated into the NLP pipeline to demonstrate the plugin system's extensibility.

---

## 1. Sentiment Analysis Models

### 1.1 Multilingual Sentiment Analysis

#### `tabularisai/multilingual-sentiment-analysis`
- **URL:** https://huggingface.co/tabularisai/multilingual-sentiment-analysis
- **Task:** Text Classification (Sentiment Analysis)
- **Languages:** Multilingual (supports multiple languages)
- **Model Size:** Lightweight
- **Provider Type:** HuggingFace
- **Use Case:** Replace built-in keyword-based sentiment with ML-based sentiment
- **Advantages:** 
  - Supports multiple languages including Nepali
  - Pre-trained on multilingual data
  - Easy to integrate with existing HuggingFace adapter

#### `clapAI/roberta-large-multilingual-sentiment`
- **URL:** https://huggingface.co/clapAI/roberta-large-multilingual-sentiment
- **Task:** Text Classification (Sentiment Analysis)
- **Languages:** 16+ languages (English, Vietnamese, Chinese, French, Spanish, Portuguese, German, Italian, Russian, Japanese, Korean, Arabic, etc.)
- **Model Size:** ~500MB (RoBERTa-large)
- **Provider Type:** HuggingFace
- **Use Case:** High-accuracy multilingual sentiment analysis
- **Advantages:**
  - Supports 16+ languages
  - Fine-tuned on multilingual sentiment dataset
  - Good accuracy across languages

#### `nlptown/bert-base-multilingual-uncased-sentiment`
- **URL:** https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment
- **Task:** Text Classification (Sentiment Analysis)
- **Languages:** Multilingual (supports multiple languages)
- **Model Size:** ~110MB (BERT-base)
- **Provider Type:** HuggingFace
- **Use Case:** Lightweight multilingual sentiment analysis
- **Advantages:**
  - Small model size
  - Fast inference
  - Good for demo purposes

### 1.2 English Sentiment Analysis

#### `cardiffnlp/twitter-roberta-base-sentiment`
- **URL:** https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment
- **Task:** Text Classification (Sentiment Analysis)
- **Languages:** English
- **Model Size:** ~125MB (RoBERTa-base)
- **Provider Type:** HuggingFace
- **Use Case:** English sentiment analysis on social media text
- **Advantages:**
  - Trained on Twitter data
  - Good for informal text
  - Lightweight

#### `distilbert-base-uncased-finetuned-sst-2-english`
- **URL:** https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
- **Task:** Text Classification (Sentiment Analysis)
- **Languages:** English
- **Model Size:** ~66MB (DistilBERT)
- **Provider Type:** HuggingFace
- **Use Case:** Fast English sentiment analysis
- **Advantages:**
  - Very lightweight
  - Fast inference
  - Good accuracy

---

## 2. Named Entity Recognition (NER) Models

### 2.1 Multilingual NER

#### `Babelscape/wikineural-multilingual-ner`
- **URL:** https://huggingface.co/Babelscape/wikineural-multilingual-ner
- **Task:** Token Classification (NER)
- **Languages:** 9 languages (de, en, es, fr, it, nl, pl, pt, ru)
- **Model Size:** ~110MB (mBERT)
- **Provider Type:** HuggingFace
- **Use Case:** Multilingual named entity recognition
- **Advantages:**
  - Supports 9 languages
  - Trained on WikiNEuRal dataset
  - Good accuracy

#### `Davlan/bert-base-multilingual-cased-ner-hrl`
- **URL:** https://huggingface.co/Davlan/bert-base-multilingual-cased-ner-hrl
- **Task:** Token Classification (NER)
- **Languages:** Multilingual (high-resource languages)
- **Model Size:** ~110MB (BERT-base)
- **Provider Type:** HuggingFace
- **Use Case:** Multilingual NER for high-resource languages
- **Advantages:**
  - Supports multiple languages
  - Good accuracy
  - Lightweight

### 2.2 English NER

#### `dslim/bert-base-NER`
- **URL:** https://huggingface.co/dslim/bert-base-NER
- **Task:** Token Classification (NER)
- **Languages:** English
- **Model Size:** ~110MB (BERT-base)
- **Provider Type:** HuggingFace
- **Use Case:** English named entity recognition
- **Advantages:**
  - Trained on CoNLL-2003 dataset
  - Good accuracy
  - Lightweight

---

## 3. Text Classification Models

### 3.1 Zero-Shot Classification

#### `facebook/bart-large-mnli`
- **URL:** https://huggingface.co/facebook/bart-large-mnli
- **Task:** Zero-Shot Classification
- **Languages:** English
- **Model Size:** ~1.5GB (BART-large)
- **Provider Type:** HuggingFace
- **Use Case:** Zero-shot text classification with custom labels
- **Advantages:**
  - No training required
  - Can classify into any categories
  - Good for demo

#### `typeform/distilbert-base-uncased-mnli`
- **URL:** https://huggingface.co/typeform/distilbert-base-uncased-mnli
- **Task:** Zero-Shot Classification
- **Languages:** English
- **Model Size:** ~66MB (DistilBERT)
- **Provider Type:** HuggingFace
- **Use Case:** Lightweight zero-shot classification
- **Advantages:**
  - Very lightweight
  - Fast inference
  - Good for demo

---

## 4. Language Detection Models

### 4.1 Multilingual Language Detection

#### `papluca/xlm-roberta-base-language-detection`
- **URL:** https://huggingface.co/papluca/xlm-roberta-base-language-detection
- **Task:** Text Classification (Language Detection)
- **Languages:** 20 languages
- **Model Size:** ~278MB (XLM-RoBERTa-base)
- **Provider Type:** HuggingFace
- **Use Case:** Detect language of input text
- **Advantages:**
  - Supports 20 languages
  - Good accuracy
  - Can replace missing language_detector module

#### `facebook/fasttext-language-identification`
- **URL:** https://huggingface.co/facebook/fasttext-language-identification
- **Task:** Language Detection
- **Languages:** 176 languages
- **Model Size:** ~126MB (FastText)
- **Provider Type:** HuggingFace
- **Use Case:** Fast language detection
- **Advantages:**
  - Very fast inference
  - Supports 176 languages
  - Lightweight

---

## 5. Recommended Models for Demo

### Priority 1: Sentiment Analysis (Replace Built-in)
**Recommended:** `nlptown/bert-base-multilingual-uncased-sentiment`
- **Reason:** Lightweight (~110MB), supports multilingual including Nepali, easy to integrate
- **Integration:** Create manifest for HuggingFace provider, enable in pipeline, disable built-in sentiment

### Priority 2: Language Detection (Missing Module)
**Recommended:** `papluca/xlm-roberta-base-language-detection`
- **Reason:** Supports 20 languages, good accuracy, can replace missing language_detector module
- **Integration:** Create manifest for HuggingFace provider, enable in pipeline

### Priority 3: NER (Optional Enhancement)
**Recommended:** `Davlan/bert-base-multilingual-cased-ner-hrl`
- **Reason:** Multilingual support, good accuracy, lightweight
- **Integration:** Create manifest for HuggingFace provider, enable in pipeline alongside gazetteer-based NER

---

## 6. Integration Steps

### Step 1: Create JSON Manifest
```json
{
  "module_id": "sentiment-hf-multilingual",
  "name": "Multilingual Sentiment (HuggingFace)",
  "version": "1.0.0",
  "provider_type": "huggingface",
  "config": {
    "model": "nlptown/bert-base-multilingual-uncased-sentiment",
    "task": "sentiment-analysis",
    "device": "cpu",
    "max_length": 512
  }
}
```

### Step 2: Register Manifest
- Via web UI: Upload manifest JSON file on Modules page
- Via CLI: `python3 cli.py register manifests/sentiment_huggingface_multilingual.json`

### Step 3: Enable in Pipeline
- Via web UI: Enable on Config page
- Via CLI: `python3 cli.py enable sentiment-hf-multilingual`

### Step 4: Test Integration
- Run analysis on sample text
- Compare results with built-in sentiment
- Verify pipeline stages show HuggingFace module

---

## 7. Demo Flow

### Demo Script
1. **Start with built-in pipeline:**
   - Show normalizer → spellcheck → ner → sentiment
   - Demonstrate each module's output

2. **Show plugin system:**
   - Navigate to Modules page
   - Upload HuggingFace sentiment manifest
   - Show module registration

3. **Enable HuggingFace model:**
   - Navigate to Config page
   - Enable HuggingFace sentiment, disable built-in
   - Show pipeline reordering

4. **Run analysis again:**
   - Show different results from HuggingFace model
   - Highlight improved accuracy

5. **Show extensibility:**
   - Demonstrate how easy it is to plug in new modules
   - Show the plugin system's flexibility

---

## 8. Performance Considerations

### Model Loading
- First load: 10-30 seconds (download + load)
- Subsequent loads: 1-3 seconds (cached)
- Memory usage: 100-500MB per model

### Inference Speed
- CPU: 0.1-1 second per request
- GPU: 0.01-0.1 second per request

### Recommendations for Demo
- Pre-download models before demo
- Use CPU for demo (no GPU required)
- Test with sample inputs beforehand

---

## 9. Risk Mitigation

### Fallback Strategy
- Keep built-in sentiment as fallback
- If HuggingFace model fails, pipeline continues
- Show error handling in demo

### Network Issues
- Pre-download models to avoid network delays
- Have offline demo ready if needed

### Model Accuracy
- Test with sample inputs before demo
- Have examples where model works well
- Be prepared to explain limitations

---

## 10. Next Steps

1. **Select 1-2 models** from recommended list
2. **Create JSON manifests** for selected models
3. **Test integration** locally
4. **Document integration process** for demo
5. **Prepare demo script** with examples
6. **Pre-download models** for demo

---

## Sources

- [tabularisai/multilingual-sentiment-analysis](https://huggingface.co/tabularisai/multilingual-sentiment-analysis)
- [clapAI/roberta-large-multilingual-sentiment](https://huggingface.co/clapAI/roberta-large-multilingual-sentiment)
- [nlptown/bert-base-multilingual-uncased-sentiment](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment)
- [cardiffnlp/twitter-roberta-base-sentiment](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment)
- [distilbert-base-uncased-finetuned-sst-2-english](https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english)
- [Babelscape/wikineural-multilingual-ner](https://huggingface.co/Babelscape/wikineural-multilingual-ner)
- [Davlan/bert-base-multilingual-cased-ner-hrl](https://huggingface.co/Davlan/bert-base-multilingual-cased-ner-hrl)
- [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER)
- [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)
- [typeform/distilbert-base-uncased-mnli](https://huggingface.co/typeform/distilbert-base-uncased-mnli)
- [papluca/xlm-roberta-base-language-detection](https://huggingface.co/papluca/xlm-roberta-base-language-detection)
- [facebook/fasttext-language-identification](https://huggingface.co/facebook/fasttext-language-identification)

---

## Compatibility Rules (which models work with the plugin)

The HuggingFace adapter (`registry/adapters/huggingface.py`) loads models via
`transformers.pipeline(task, model=...)` and reads `results[0]["label"]` and
`results[0]["score"]` from the output. Compatibility therefore depends on two things:

### 1. Task / pipeline type (`config.task` in the manifest)

| Category | Tasks | Works? | Why |
|---|---|---|---|
| Classification | `text-classification`, `sentiment-analysis`, `zero-shot-classification` | Yes | Output is `[{label, score}]` |
| Token classification | `ner`, `token-classification` | Partial | Returns `entity`/`score` (no `label`); full list captured in raw output, headline label defaults to `neutral` |
| Generation / text2text | `translation`, `summarization`, `text-generation`, `text2text-generation` | No | Output is `[{generated_text}]` — no `label`/`score`, so result is dropped |

### 2. Model file format

- Must be a standard transformers model with a valid `config.json` (a `model_type` key).
- Raw checkpoints (e.g. `.pt` / `.bin` without config, custom training artifacts)
  fail to load with `Unrecognized model`. Example of a failure:
  `Sagar32/romanizedtransliterationmodel` is a raw PyTorch checkpoint, not a
  loadable pipeline model.

### Notes

- For sentiment coloring in the web UI, labels should be
  `positive` / `negative` / `neutral`.
- `nlptown/bert-base-multilingual-uncased-sentiment` (~110MB) is the proven,
  free-tier-safe sentiment example.
- `bishaldpande/Ner-xlm-roberta-base` is a working Nepali NER model
  (partial category).
