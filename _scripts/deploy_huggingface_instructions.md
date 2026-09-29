# Hugging Face Spaces deploy (no codemie-local GitHub)

Free persistent URL: `https://huggingface.co/spaces/YOUR_USER/epam-ai-vacancies`

## 1. Create Space (web)

1. Open https://huggingface.co/new-space
2. Name: `epam-ai-vacancies`
3. SDK: **Docker**
4. Create

## 2. Push files (terminal, one-time)

Install CLI: `pip install huggingface_hub`

```bash
cd projects/ai-native-vacancy-service
huggingface-cli login   # HF token from https://huggingface.co/settings/tokens

# Clone empty space
git clone https://huggingface.co/spaces/YOUR_USER/epam-ai-vacancies /tmp/epam-ai-vacancies-hf
cd /tmp/epam-ai-vacancies-hf

# Copy deploy bundle
cp ../../deploy/huggingface/README.md .
cp ../../Dockerfile .
cp ../../requirements.txt .
cp -r ../../service .
cp -r ../../data/jobs.json.gz data/ 2>/dev/null || mkdir -p data && cp ../../data/jobs.json.gz data/

git add .
git commit -m "EPAM AI vacancy prototype"
git push
```

Space builds in ~5 min. Set Space variable `PUBLIC_BASE_URL` to your Space URL in Settings.

## 3. Test

- `https://YOUR_USER-epam-ai-vacancies.hf.space/test`
- `https://YOUR_USER-epam-ai-vacancies.hf.space/stats`
