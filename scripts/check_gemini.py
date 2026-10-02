"""Manually check server Gemini configuration without printing credentials."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings
from career_assistant import AssistantError, gemini_reply

if __name__ == '__main__':
    config = settings()
    print('Key loaded:', bool(config.get('GEMINI_API_KEY')))
    print('Model:', config.get('GEMINI_MODEL'))
    try:
        answer = gemini_reply(config, 'Give one short tip for preparing a software engineering internship portfolio.', {}, [])
        print('Gemini response:', answer)
    except AssistantError as error:
        print('Gemini check failed:', error.status, str(error))
        sys.exit(1)
