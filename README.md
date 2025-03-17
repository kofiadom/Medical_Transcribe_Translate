# Medscribe AI

Medscribe AI is a real-time medical transcription and translation application. It leverages AssemblyAI for transcription, OpenAI for text analysis and translation, and ElevenLabs for generating audio from translated text. The application is built using FastAPI and WebSocket for real-time communication.

## Features

- Real-time transcription of medical speech
- Accurate formatting and analysis of medical transcripts
- Translation of transcripts into multiple languages
- Audio generation for translated text

## Project Structure

```
Medscribe AI/
├── main.py
├── requirements.txt
├── static/
│   └── styles.css
├── templates/
│   └── index.html
└── README.md
```

### main.py

This is the main application file that sets up the FastAPI server, WebSocket connections, and handles real-time transcription, analysis, and translation.

### requirements.txt

This file lists all the dependencies required for the project.

### static/styles.css

This file contains the CSS styles for the web interface.

### templates/index.html

This file contains the HTML structure for the web interface.

## AI Tools

This project utilizes several AI tools for various functionalities:
- **AssemblyAI**: For real-time transcription of medical speech.
- **OpenAI**: For text analysis and translation.
- **ElevenLabs**: For generating audio from translated text.
- **ChatGPT**, **Claude 3.7**, **GitHub Co-pilot** : For coding assistance.

## Reasons for Choosing AI Tools

- **AssemblyAI**: Chosen for its robust real-time transcription capabilities, high accuracy in medical terminology, and ease of integration with FastAPI.
- **OpenAI**: Selected for its advanced text analysis and translation capabilities, leveraging the power of GPT-4 to ensure precise and context-aware translations.
- **ElevenLabs**: Preferred for its high-quality text-to-speech generation, providing natural-sounding audio for translated text, and seamless integration with the application.

## Security Considerations

- Ensure that your API keys are stored securely and not exposed in the codebase. Use environment variables to manage sensitive information.
- Railway ensures HTTPS hosting for secure communication.
- Regularly update dependencies to patch any security vulnerabilities.
- Implemented proper error handling to avoid exposing sensitive information in error messages. This includes:
  - Using try-except blocks to catch exceptions.
  - Logging errors using `logger.error` without exposing sensitive information.
  - Returning appropriate HTTP responses with generic error messages.

## Hosting

This application is hosted on Railway.


1. Clone the repository:

```bash
git clone https://github.com/kofiadom/Medical_Transcribe_Translate
cd Medical_Transcribe_Translate
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file in the root directory and add your API keys:

```
ASSEMBLY_AI_API_KEY=your_assemblyai_api_key
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## UI

[![3nykqfp.md.png](https://iili.io/3nykqfp.md.png)](https://freeimage.host/i/3nykqfp)

## Usage

1. Start the FastAPI server:

```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to `http://localhost:8000` to access the web interface.

3. Click the "Start Recording" button to begin real-time transcription. The transcript will be displayed in the "Real-Time Transcript" box.

4. Select a language from the dropdown to translate the transcript. The translated text will be displayed in the "Translated Transcript" box, and the audio will be generated and played.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
