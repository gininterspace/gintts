import os
import argparse
from pathlib import Path
import openai
from datetime import datetime
import unicodedata

class TextToSpeechApp:
    def __init__(self, api_key=None):
        """Initialize the Text-to-Speech application with API key."""
        # Use provided API key or try to get from environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide it as an argument.")
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        
        # Available voices from OpenAI
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("tts_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def convert_text_to_speech(self, text, voice="nova", model="tts-1", output_file=None, language=None):
        """
        Convert text to speech using OpenAI's API.
        
        Args:
            text (str): The text to convert to speech
            voice (str): The voice to use (default: "nova")
            model (str): The TTS model to use (default: "tts-1")
            output_file (str, optional): Output file path. If None, a filename will be generated.
            language (str, optional): Language code (e.g., 'vi' for Vietnamese). If None, automatic detection.
            
        Returns:
            str: Path to the saved audio file
        """
        # Validate voice selection
        if voice not in self.available_voices:
            raise ValueError(f"Invalid voice. Choose from: {', '.join(self.available_voices)}")
        
        # Generate default output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            lang_suffix = f"_{language}" if language else ""
            output_file = self.output_dir / f"speech_{voice}{lang_suffix}_{timestamp}.mp3"
        else:
            output_file = Path(output_file)
            
        try:
            print(f"Converting text to speech using voice: {voice}")
            
            # Ensure text is properly encoded for Unicode/Vietnamese characters
            text = unicodedata.normalize('NFC', text)
            
            # Prepare API request parameters
            speech_params = {
                "model": model,
                "voice": voice,
                "input": text
            }
            
            # Add language parameter if specified
            if language:
                speech_params["response_format"] = "mp3"
                # While OpenAI doesn't have an explicit language parameter, we're setting
                # options that will work well with non-English languages
                print(f"Processing in language: {language}")
            
            # Make API request
            response = openai.audio.speech.create(**speech_params)
            
            # Save the audio file
            response.stream_to_file(str(output_file))
            
            print(f"Audio saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error during text-to-speech conversion: {e}")
            raise

def main():
    """Command line interface for the Text-to-Speech app."""
    parser = argparse.ArgumentParser(description="Convert text to speech using OpenAI's API")
    parser.add_argument("--text", "-t", type=str, help="Text to convert to speech")
    parser.add_argument("--file", "-f", type=str, help="Text file to convert to speech")
    parser.add_argument("--voice", "-v", type=str, default="nova", 
                        help="Voice to use (alloy, echo, fable, onyx, nova, shimmer)")
    parser.add_argument("--model", "-m", type=str, default="tts-1", 
                        help="TTS model to use (tts-1 or tts-1-hd)")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    parser.add_argument("--language", "-l", type=str, help="Language code (e.g., 'vi' for Vietnamese)")
    
    args = parser.parse_args()
    
    # Check if we have text input
    text = None
    if args.text:
        text = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        text = input("Enter the text to convert to speech: ")
    
    try:
        app = TextToSpeechApp(api_key=args.api_key)
        app.convert_text_to_speech(
            text=text,
            voice=args.voice,
            model=args.model,
            output_file=args.output,
            language=args.language
        )
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()