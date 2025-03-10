# Setup 

## Conda

```bash
conda create --name auto-gen-demo python=3.12
conda env list
conda activate auto-gen-demo
```

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Download Vosk Models

```bash
mkdir -p models/vosk
cd models/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

## Setup Whisper

```bash
mkdir -p models/whisper
WHISPER_COREML=1 pip install git+https://github.com/absadiki/pywhispercpp

# Download from huggingface: https://huggingface.co/ggerganov/whisper.cpp/tree/main
# 1. ggml-large-v3-turbo.bin
# 2. ggml-large-v3-turbo-encoder.mlmodelc
```

## Ngrok

Install and start ngrok for network tunneling

```bash
brew install ngrok
ngrok http --url=promptly-alert-sparrow.ngrok-free.app 5090
```

# Twilio Info 

| Key          | Value        | 
|--------------|--------------|
| Account      | <acct-num>   |
| Phone Number | +18333709923 | 
| Auth Token   | <auth-token> |

```bash
curl -X POST https://api.twilio.com/2010-04-01/Accounts/<acct-num>/Calls.json \
  --data-urlencode "Url=http://demo.twilio.com/docs/voice.xml" \
  --data-urlencode "To=+14842744202" \
  --data-urlencode "From=+18333709923" \
  -u <acct-num>:<auth-token>
```
# Misc

# Model Comparison

| Model                       | Response T/s | Tools | Size (GB) |
|-----------------------------|--------------|-------|-----------|
| Llama3.2:3b                 | 111          | Yes   | 1.9       |
| Llama3.1:8b                 | 53           | Yes   | 4.6       |
| Llama3.3:70b-instruct-q2_K  | 6.5          | Yes   | 24.6      |
| Phi3:14b                    | 35           | No    | 7.4       |
| Phi4:14b                    | 27           | No    | 8.4       |
| Deepseek-r1:1.5b            | 135          | No    | 1         |
| Deepseek-r1:32b             | 8.6          | No    | 18.5      |
| Qwen2.5:32b                 | 15           | Yes   | 18.5      |
| Qwen2.5:32b-instruct-q5_K_M | 10           | Yes   | 21.7      |
| Qwen2.5:32b-instruct-q6_K   | 10           | Yes   | 25        |
| Qwen2.5:14b                 | 32           | Yes   | 8.4       |
| Qwen2.5:7b                  | 53           | Yes   | 4.4       |
