import torch
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq, WhisperForConditionalGeneration
import os
import librosa
import numpy as np
from peft import PeftModel, PeftConfig
import traceback

class TranscriptionService:
    def __init__(self, model_path: str = "ai_models/whisper-nepali-small", tokenizer_path:str = ""):
        """
        Initialize the Whisper model and processor.
        """
        # Get the absolute path to the model directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_model_path = os.path.join(current_dir, model_path)
        
        # Define the local path to the full whisper-small model for fallback files
        small_model_dir = "ai_models/whisper-small" 
        small_model_path = os.path.join(current_dir, small_model_dir)
        print(f"Loading Whisper model from: {full_model_path}")
        if not os.path.exists(full_model_path):
             raise FileNotFoundError(f"Model directory not found at: {full_model_path}")

        # 1. Determine Device and Data Type
        # IMPORTANT: Default to CPU because MPS (Metal Performance Shaders) on Mac has bug
        force_cpu = os.getenv("WHISPER_FORCE_CPU", "true").lower() == "true"
        
        if torch.cuda.is_available():
            self.device = "cuda"
            self.torch_dtype = torch.float16
        elif not force_cpu and torch.backends.mps.is_available():
            # Only use MPS if explicitly requested, otherwise avoid due to bug
            self.device = os.getenv("WHISPER_DEVICE", "mps")
            self.torch_dtype = torch.float16 
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
            
        print(f"Using device: {self.device} with dtype: {self.torch_dtype}")
        
        # 2. Load Processor and Model
        try:
            try:
                print(f"Attempting to load processor from model path")
                self.processor = AutoProcessor.from_pretrained(full_model_path, local_files_only=True)
            except (FileNotFoundError, TypeError, Exception):
                # Fall back to the local full small model path if PEFT path is incomplete
                print(f"Local PEFT processor files incomplete. Loading from local base 'small_model_path'...")
                self.processor = AutoProcessor.from_pretrained(small_model_path, local_files_only=True)
            
            
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                full_model_path,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                local_files_only=True
            ).to(self.device)

            # base_model_name = "openai/whisper-tiny" 
            
            # print(f"Loading base model: {base_model_name}")
            # base_model = WhisperForConditionalGeneration.from_pretrained(
            #     base_model_name,
            #     # Note the change from 'torch_dtype' to 'dtype' to remove the warning
            #     dtype=self.torch_dtype, 
            #     low_cpu_mem_usage=True,
            #     use_safetensors=True
            # )

            # # 3. Load the PEFT adapter weights onto the base model
            # print(f"Loading PEFT adapters from checkpoint: {full_model_path}")
            # self.model = PeftModel.from_pretrained(
            #     base_model, 
            #     full_model_path, 
            #     device_map=self.device
            # )
            
            # Set model into evaluation mode
            self.model.eval()
            print("Model loaded successfully.")
            
        except Exception as e:
            print(f"Critical Error loading model: {e}")
            traceback.print_exc()
            raise e

    def transcribe(self, audio_path: str, language: str = None, minutes_remaining: float = 0) -> str:
        """
        Transcribe an audio file to text using manual inference loop.
        """
        print(f"Transcribing audio file: {audio_path} (Requested Language: {language})")
        
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return "[Error: Audio file not found]"
            
        try:
            # 1. Load Audio
            # librosa loads as valid float32 numpy array, resamples to 16000
            audio_data, sr = librosa.load(audio_path, sr=16000)
            duration = librosa.get_duration(y=audio_data, sr=sr)
            
            # 2. Input Validation & Normalization
            if duration < 0.1:
                return "[Audio too short]"
            
            if duration > minutes_remaining * 60:
                return "Exceeded transcription minutes limit. Please upgrade your subscription."
                
            # Normalize to [-1, 1] - important for consistent model performance
            max_val = np.abs(audio_data).max()
            if max_val > 0:
                audio_data = audio_data / max_val
                
            print(f"Audio loaded: Duration={duration:.2f}s, SR={sr}, MaxAmp={max_val:.4f}")
            
            if max_val < 0.01:
                print("Warning: Audio is nearly silent.")
                return "[Silence detected]"

            # 3. Feature Extraction
            inputs = self.processor(
                audio_data, 
                sampling_rate=16000, 
                return_tensors="pt"
            )
            
            # 4. Move to Device and Cast Type
            # Ensure inputs match the model's dtype (force float32 on MPS)
            input_features = inputs.input_features.to(device=self.device, dtype=self.torch_dtype)
            
            # 5. Prepare Generation Arguments
            gen_kwargs = {
                "max_new_tokens": 440,
                "return_timestamps": False,
                "num_beams": 1, 
                "do_sample": False,
                "repetition_penalty": 1.1, # Mild penalty to prevent "!!!!!" loops
                "task": "transcribe",
                "forced_decoder_ids": None # Important: Allow 'language' arg to generate IDs
            }
            
            # Handle Language Force Logic
            if language:
                lang_code = language.lower()
                if lang_code in ["ne", "nepali"]:
                    print("Forcing language: Nepali")
                    gen_kwargs["language"] = "nepali"
                elif lang_code in ["en", "english"]:
                    print("Forcing language: English")
                    gen_kwargs["language"] = "english"
                else:
                    print(f"Using requested language: {language}")
                    gen_kwargs["language"] = language
            else:
                 # No language specified -> Auto Detect
                 pass # 'language' key missing means auto-detect
                
            print(f"Generating with args: {gen_kwargs}")
            
            # 6. Generate Tokens
            with torch.no_grad():
                predicted_ids = self.model.generate(input_features, **gen_kwargs)
            
            # 7. Decode Tokens to Text
            text = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            text = text.strip()
            print(f"Model Raw Output: '{text}'")
            
            if not text:
                return "[No speech detected]"
                
            return text

        except Exception as e:
            print(f"Inference error: {str(e)}")
            traceback.print_exc()
            return f"[Transcription error: {str(e)}]"

# Global instance
try:
    transcription_service = TranscriptionService()
except Exception as e:
    print("Failed to initialize TranscriptionService on import.")
    transcription_service = None
