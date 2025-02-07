# Setup Conda

```bash
conda create --name auto-gen-demo python=3.12
conda env list
conda activate auto-gen-demo
```

# Install Dependencies

```bash
pip install -U "autogen-agentchat" "autogen-ext[openai,web-surfer]" "twilio" "python-dotenv" "vosk" "uvicorn[standard]" "python-multipart"

brew install ngrok

wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

```bash
git clone https://github.com/ggerganov/whisper.cpp

pip install ane_transformers
pip install openai-whisper
pip install coremltools

cd whisper.cpp

./models/download-ggml-model.sh base.en
./models/download-coreml-model.sh base.en
./models/download-ggml-model.sh small.en
./models/download-coreml-model.sh small.en
./models/download-ggml-model.sh medium.en
./models/download-coreml-model.sh medium.en
./models/download-ggml-model.sh large-v3-turbo
./models/download-coreml-model.sh large-v3-turbo

cmake -B build -DWHISPER_COREML=1
cmake --build build -j --config Release

./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav

git clone --recursive https://github.com/abdeladim-s/pywhispercpp
cd pywhispercpp
WHISPER_COREML=1 pip install .

Move files to
/Users/benferenchak/Library/Application Support/pywhispercpp/models/ggml-base.en-encoder.mlmodelc
```

# Twilio Info 

AUAU468JXQBYZFZN5D3GK5A8 

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

> ngrok http --url=promptly-alert-sparrow.ngrok-free.app 5090
