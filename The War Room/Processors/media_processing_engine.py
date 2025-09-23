#!/usr/bin/env python3
"""
DKI Engine - Media Processing Engine
Comprehensive video and image processing system for investigation reports
"""

import os
import sys
import json
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from voice_transcription import VoiceTranscriber

# Image and Video Processing
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image, ExifTags
except ImportError:
    Image = None
    ExifTags = None

try:
    import piexif  # EXIF helper; optional
    HAS_PIEXIF = True
except Exception:
    piexif = None
    HAS_PIEXIF = False

# Video Processing
try:
    import moviepy.editor as mp
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False
    mp = None

# Audio Processing
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    librosa = None
# Audio file fallback
try:
    import soundfile as sf  # type: ignore
    HAS_SOUNDFILE = True
except Exception:
    sf = None  # type: ignore
    HAS_SOUNDFILE = False


# Face Detection
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False
    face_recognition = None

# OCR
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None

logger = logging.getLogger(__name__)

class MediaProcessingEngine:
    """
    Comprehensive media processing engine for DKI Engine
    Handles video, image, and audio analysis for investigation reports
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.temp_dir = tempfile.mkdtemp(prefix='dki_media_')
        self.cache_dir = os.path.join(tempfile.gettempdir(), 'dki_media_cache')
        self._ensure_cache_dir()
        
        self.voice_transcriber = VoiceTranscriber()
        # Processing capabilities
        self.capabilities = {
            'video_processing': HAS_MOVIEPY,
            'image_processing': HAS_CV2,
            'face_detection': HAS_FACE_RECOGNITION,
            'ocr': HAS_TESSERACT,
            'audio_analysis': HAS_LIBROSA,
            'voice_transcription': self.voice_transcriber.is_ready()
        }
        
        # Supported formats
        self.supported_formats = {
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'],
            'audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
        }
        
        logger.info(f"Media Processing Engine initialized with capabilities: {self.capabilities}")
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def process_media_file(self, file_path: str, analysis_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single media file and extract comprehensive metadata
        
        Args:
            file_path: Path to the media file
            analysis_options: Dictionary of analysis options
            
        Returns:
            Dictionary containing processed media data
        """
        analysis_options = dict(analysis_options or {})

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        file_type = self._get_file_type(file_ext)
        
        if file_type not in ['video', 'image', 'audio']:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Generate file hash for caching
        file_hash = self._generate_file_hash(file_path)
        
        # Check cache first
        cached_result = self._get_cached_result(file_hash)
        if cached_result:
            logger.info(f"Using cached result for {file_path}")
            return cached_result
        
        # Process the file
        logger.info(f"Processing {file_type} file: {file_path}")
        
        result = {
            'file_info': self._extract_file_info(file_path),
            'file_hash': file_hash,
            'file_type': file_type,
            'processed_at': datetime.now().isoformat(),
            'analysis_options': analysis_options or {}
        }
        
        try:
            if file_type == 'image':
                result.update(self._process_image(file_path, analysis_options))
            elif file_type == 'video':
                result.update(self._process_video(file_path, analysis_options))
            elif file_type == 'audio':
                result.update(self._process_audio(file_path, analysis_options))
            
            # Cache the result
            self._cache_result(file_hash, result)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def process_media_batch(self, file_paths: List[str], analysis_options: Dict[str, Any] = None, 
                           max_workers: int = 4) -> Dict[str, Dict[str, Any]]:
        """
        Process multiple media files in parallel
        
        Args:
            file_paths: List of file paths to process
            analysis_options: Analysis options for all files
            max_workers: Maximum number of parallel workers
            
        Returns:
            Dictionary mapping file paths to processed results
        """
        analysis_options = dict(analysis_options or {})
        analysis_options.setdefault('transcribe_audio', True)

        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_media_file, path, analysis_options): path
                for path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    results[path] = {'error': str(e)}
        
        return results
    
    def _get_file_type(self, file_ext: str) -> str:
        """Determine file type from extension"""
        for file_type, extensions in self.supported_formats.items():
            if file_ext in extensions:
                return file_type
        return 'unknown'
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Generate SHA256 hash of file for caching"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_cached_result(self, file_hash: str) -> Optional[Dict]:
        """Get cached processing result"""
        cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                # Check if cache is still valid (24 hours)
                cached_time = datetime.fromisoformat(cached_data['processed_at'])
                if datetime.now() - cached_time < timedelta(hours=24):
                    return cached_data
            except Exception as e:
                logger.warning(f"Error reading cache file {cache_file}: {e}")
        return None
    
    def _cache_result(self, file_hash: str, result: Dict):
        """Cache processing result"""
        cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
    
    def _extract_file_info(self, file_path: str) -> Dict[str, Any]:
        """Extract basic file information"""
        stat = os.stat(file_path)
        return {
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': Path(file_path).suffix.lower()
        }
    
    def _process_image(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process image file"""
        result = {}
        
        try:
            # Load image
            image = Image.open(file_path)
            result['dimensions'] = {
                'width': image.width,
                'height': image.height,
                'aspect_ratio': round(image.width / image.height, 2)
            }
            result['color_mode'] = image.mode
            result['format'] = image.format
            
            # Extract EXIF data
            exif_data = self._extract_exif_data(image)
            if exif_data:
                result['exif'] = exif_data
            
            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(image, file_path)
            if thumbnail_path:
                result['thumbnail'] = thumbnail_path
            
            # OCR text extraction if enabled
            if options.get('extract_text', False) and HAS_TESSERACT:
                text = self._extract_text_from_image(image)
                if text:
                    result['extracted_text'] = text
            
            # Face detection if enabled
            if options.get('detect_faces', False) and HAS_FACE_RECOGNITION:
                faces = self._detect_faces_in_image(image)
                if faces:
                    result['faces'] = faces
            
            # Object detection if enabled
            if options.get('detect_objects', False) and HAS_CV2:
                objects = self._detect_objects_in_image(image)
                if objects:
                    result['objects'] = objects
            
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _process_video(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process video file"""
        result = {}
        
        try:
            if not HAS_MOVIEPY:
                result['error'] = "Video processing not available (moviepy not installed)"
                return result
            
            # Load video
            video = mp.VideoFileClip(file_path)
            
            result['duration'] = video.duration
            result['fps'] = video.fps
            result['dimensions'] = {
                'width': video.w,
                'height': video.h,
                'aspect_ratio': round(video.w / video.h, 2)
            }
            
            # Extract frames for analysis
            if options.get('extract_frames', True):
                frames = self._extract_video_frames(video, file_path, options.get('frame_count', 10))
                if frames:
                    result['frames'] = frames
            
            # Generate thumbnail
            thumbnail_path = self._generate_video_thumbnail(video, file_path)
            if thumbnail_path:
                result['thumbnail'] = thumbnail_path
            
            # Audio analysis if enabled
            if options.get('analyze_audio', False) and video.audio:
                audio_data = self._analyze_video_audio(video.audio, options)
                if audio_data:
                    result['audio'] = audio_data
            
            # Motion detection if enabled
            if options.get('detect_motion', False) and HAS_CV2:
                motion_data = self._detect_motion_in_video(video)
                if motion_data:
                    result['motion'] = motion_data
            
            video.close()
            
        except Exception as e:
            logger.error(f"Error processing video {file_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _process_audio(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio file"""
        result: Dict[str, Any] = {}

        try:
            audio_array = None
            sample_rate = None

            if HAS_LIBROSA:
                audio_array, sample_rate = librosa.load(file_path, sr=None, mono=False)
                samples = audio_array.shape[-1] if hasattr(audio_array, 'shape') else len(audio_array)
                result['duration'] = samples / float(sample_rate)
                result['sample_rate'] = sample_rate
                result['channels'] = 1 if getattr(audio_array, 'ndim', 1) == 1 else audio_array.shape[0]
                feature_array = librosa.to_mono(audio_array) if hasattr(librosa, 'to_mono') and getattr(audio_array, 'ndim', 1) > 1 else audio_array
            elif 'HAS_SOUNDFILE' in globals() and HAS_SOUNDFILE:
                audio_array, sample_rate = sf.read(file_path)
                samples = audio_array.shape[0] if hasattr(audio_array, 'shape') else len(audio_array)
                result['duration'] = (samples / float(sample_rate)) if sample_rate else None
                result['sample_rate'] = sample_rate
                if hasattr(audio_array, 'ndim') and audio_array.ndim > 1:
                    result['channels'] = audio_array.shape[1]
                else:
                    result['channels'] = 1
                feature_array = None
            else:
                result['warning'] = 'Audio feature extraction unavailable (librosa/soundfile not installed)'
                feature_array = None

            if HAS_LIBROSA and feature_array is not None and sample_rate:
                if options.get('analyze_audio_features', True):
                    features = self._extract_audio_features(feature_array, sample_rate)
                    if features:
                        result['audio_features'] = features

                if options.get('detect_speech', False):
                    speech_segments = self._detect_speech_segments(feature_array, sample_rate)
                    if speech_segments:
                        result['speech_segments'] = speech_segments

            if options.get('transcribe_audio', True):
                transcription = self._transcribe_audio_file(file_path, options)
                if transcription:
                    result['transcription'] = transcription
                    result['transcript'] = transcription.get('text')
                    result['transcript_language'] = transcription.get('language')
                    result['transcription_segments'] = transcription.get('segments')
                    result['transcription_model'] = transcription.get('model')
                    result['transcription_generated_at'] = transcription.get('generated_at')

        except Exception as e:
            logger.error(f"Error processing audio {file_path}: {e}")
            result['error'] = str(e)

        return result

    def _transcribe_audio_file(self, file_path: str, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        transcriber = getattr(self, 'voice_transcriber', None)
        if not transcriber or not transcriber.is_ready():
            return None

        extra: Dict[str, Any] = {}
        language = options.get('transcription_language')
        if language:
            extra['language'] = language
        temperature = options.get('transcription_temperature')
        if temperature is not None:
            extra['temperature'] = temperature

        transcription = transcriber.transcribe_file(file_path, **extra)
        if not transcription:
            return None

        return self._format_transcription(transcription, source=file_path)

    def _transcribe_audio_array(self, audio_array, sample_rate: int, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        transcriber = getattr(self, 'voice_transcriber', None)
        if not transcriber or not transcriber.is_ready():
            return None

        if not sample_rate:
            sample_rate = 16000

        extra: Dict[str, Any] = {}
        language = options.get('transcription_language')
        if language:
            extra['language'] = language
        temperature = options.get('transcription_temperature')
        if temperature is not None:
            extra['temperature'] = temperature

        transcription = transcriber.transcribe_array(audio_array, sample_rate, **extra)
        if not transcription:
            return None

        return self._format_transcription(transcription, source='video_audio_stream')

    def _format_transcription(self, transcription, source: Optional[str] = None) -> Dict[str, Any]:
        text_value = getattr(transcription, 'text', '') if transcription else ''
        language = getattr(transcription, 'language', None) if transcription else None
        segments = getattr(transcription, 'segments', []) if transcription else []
        model = getattr(transcription, 'model', None) if transcription else None

        data: Dict[str, Any] = {
            'text': text_value.strip(),
            'language': language,
            'segments': segments or [],
            'model': model,
            'source': source,
            'generated_at': datetime.now().isoformat(),
        }

        if data['text']:
            snippet = data['text'][:200].strip()
            if len(data['text']) > 200:
                snippet = snippet + '...'
            data['summary'] = snippet

        confidences = [seg.get('confidence') for seg in data['segments'] if isinstance(seg, dict) and seg.get('confidence') is not None]
        if confidences:
            try:
                data['mean_confidence'] = sum(confidences) / len(confidences)
            except Exception:
                pass

        return data

    def _extract_exif_data(self, image) -> Optional[Dict[str, Any]]:
        """Extract EXIF data from image"""
        if not HAS_PIEXIF:
            return None
        try:
            raw = (image.info.get('exif') if hasattr(image, 'info') else None) or b''
            exif_dict = piexif.load(raw)
            if not exif_dict:
                return None
            
            exif_data = {}
            
            # GPS data
            if 'GPS' in exif_dict:
                gps_data = self._extract_gps_data(exif_dict['GPS'])
                if gps_data:
                    exif_data['gps'] = gps_data
            
            # Camera data
            if '0th' in exif_dict:
                camera_data = self._extract_camera_data(exif_dict['0th'])
                if camera_data:
                    exif_data['camera'] = camera_data
            
            # DateTime
            if '0th' in exif_dict:
                datetime_data = self._extract_datetime_data(exif_dict['0th'])
                if datetime_data:
                    exif_data['datetime'] = datetime_data
            
            return exif_data if exif_data else None
            
        except Exception as e:
            logger.warning(f"Error extracting EXIF data: {e}")
            return None
    
    def _extract_gps_data(self, gps_dict: Dict) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from EXIF data"""
        if not HAS_PIEXIF:
            return None
        try:
            lat = gps_dict.get(piexif.GPSIFD.GPSLatitude)
            lat_ref = gps_dict.get(piexif.GPSIFD.GPSLatitudeRef)
            lon = gps_dict.get(piexif.GPSIFD.GPSLongitude)
            lon_ref = gps_dict.get(piexif.GPSIFD.GPSLongitudeRef)
            
            if lat and lon:
                lat_deg = self._convert_to_degrees(lat)
                lon_deg = self._convert_to_degrees(lon)
                
                if lat_ref == b'S':
                    lat_deg = -lat_deg
                if lon_ref == b'W':
                    lon_deg = -lon_deg
                
                return {
                    'latitude': lat_deg,
                    'longitude': lon_deg,
                    'coordinates': f"{lat_deg}, {lon_deg}"
                }
        except Exception as e:
            logger.warning(f"Error extracting GPS data: {e}")
        
        return None
    
    def _extract_camera_data(self, camera_dict: Dict) -> Optional[Dict[str, Any]]:
        """Extract camera information from EXIF data"""
        if not HAS_PIEXIF:
            return None
        try:
            camera_data = {}
            
            if piexif.ImageIFD.Make in camera_dict:
                camera_data['make'] = camera_dict[piexif.ImageIFD.Make].decode('utf-8')
            if piexif.ImageIFD.Model in camera_dict:
                camera_data['model'] = camera_dict[piexif.ImageIFD.Model].decode('utf-8')
            if piexif.ImageIFD.Software in camera_dict:
                camera_data['software'] = camera_dict[piexif.ImageIFD.Software].decode('utf-8')
            
            return camera_data if camera_data else None
            
        except Exception as e:
            logger.warning(f"Error extracting camera data: {e}")
            return None
    
    def _extract_datetime_data(self, datetime_dict: Dict) -> Optional[Dict[str, Any]]:
        """Extract datetime information from EXIF data"""
        if not HAS_PIEXIF:
            return None
        try:
            datetime_data = {}
            
            if piexif.ImageIFD.DateTime in datetime_dict:
                datetime_data['original'] = datetime_dict[piexif.ImageIFD.DateTime].decode('utf-8')
            if piexif.ImageIFD.DateTimeOriginal in datetime_dict:
                datetime_data['original'] = datetime_dict[piexif.ImageIFD.DateTimeOriginal].decode('utf-8')
            if piexif.ImageIFD.DateTimeDigitized in datetime_dict:
                datetime_data['digitized'] = datetime_dict[piexif.ImageIFD.DateTimeDigitized].decode('utf-8')
            
            return datetime_data if datetime_data else None
            
        except Exception as e:
            logger.warning(f"Error extracting datetime data: {e}")
            return None
    
    def _convert_to_degrees(self, value) -> float:
        """Convert GPS coordinates to decimal degrees"""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)
    
    def _generate_thumbnail(self, image, file_path: str) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            # Create thumbnail
            thumbnail_size = (200, 200)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            file_hash = self._generate_file_hash(file_path)
            thumbnail_path = os.path.join(self.cache_dir, f"{file_hash}_thumb.jpg")
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                rgb_image.save(thumbnail_path, 'JPEG', quality=85)
            else:
                image.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.warning(f"Error generating thumbnail: {e}")
            return None
    
    def _generate_video_thumbnail(self, video, file_path: str) -> Optional[str]:
        """Generate thumbnail for video"""
        try:
            # Get frame at 10% of video duration
            frame_time = video.duration * 0.1
            frame = video.get_frame(frame_time)
            
            # Convert to PIL Image
            image = Image.fromarray(frame)
            
            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(image, file_path)
            
            return thumbnail_path
            
        except Exception as e:
            logger.warning(f"Error generating video thumbnail: {e}")
            return None
    
    def _extract_text_from_image(self, image) -> Optional[str]:
        """Extract text from image using OCR"""
        try:
            if not HAS_TESSERACT:
                return None

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Configure Tesseract path on Windows if needed
            try:
                import sys as _sys
                if _sys.platform.startswith('win'):
                    from pathlib import Path as _Path
                    for p in (
                        r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
                        r'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
                    ):
                        if _Path(p).exists():
                            pytesseract.pytesseract.tesseract_cmd = p
                            break
            except Exception:
                pass

            # Extract text
            text = pytesseract.image_to_string(image)
            
            return text.strip() if text.strip() else None
            
        except Exception as e:
            logger.warning(f"Error extracting text from image: {e}")
            return None
    
    def _detect_faces_in_image(self, image) -> Optional[List[Dict[str, Any]]]:
        """Detect faces in image"""
        try:
            if not HAS_FACE_RECOGNITION:
                return None
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image_array)
            
            faces = []
            for i, (top, right, bottom, left) in enumerate(face_locations):
                faces.append({
                    'face_id': i,
                    'location': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'center': {
                        'x': (left + right) // 2,
                        'y': (top + bottom) // 2
                    }
                })
            
            return faces if faces else None
            
        except Exception as e:
            logger.warning(f"Error detecting faces: {e}")
            return None
    
    def _detect_objects_in_image(self, image) -> Optional[List[Dict[str, Any]]]:
        """Detect objects in image using OpenCV"""
        try:
            if not HAS_CV2:
                return None
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Load pre-trained model (you would need to download this)
            # For now, return a placeholder
            return [{'object': 'detection_placeholder', 'confidence': 0.0}]
            
        except Exception as e:
            logger.warning(f"Error detecting objects: {e}")
            return None
    
    def _extract_video_frames(self, video, file_path: str, frame_count: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Extract representative frames from video"""
        try:
            frames = []
            duration = video.duration
            
            # Extract frames at regular intervals
            for i in range(frame_count):
                time_point = (duration / frame_count) * i
                frame = video.get_frame(time_point)
                
                # Convert to PIL Image
                image = Image.fromarray(frame)
                
                # Generate thumbnail for frame
                thumbnail_path = self._generate_frame_thumbnail(image, file_path, i)
                
                frames.append({
                    'frame_number': i,
                    'timestamp': time_point,
                    'thumbnail': thumbnail_path
                })
            
            return frames
            
        except Exception as e:
            logger.warning(f"Error extracting video frames: {e}")
            return None
    
    def _generate_frame_thumbnail(self, image, file_path: str, frame_number: int) -> Optional[str]:
        """Generate thumbnail for video frame"""
        try:
            # Create thumbnail
            thumbnail_size = (150, 150)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            file_hash = self._generate_file_hash(file_path)
            thumbnail_path = os.path.join(self.cache_dir, f"{file_hash}_frame_{frame_number}.jpg")
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                rgb_image.save(thumbnail_path, 'JPEG', quality=85)
            else:
                image.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.warning(f"Error generating frame thumbnail: {e}")
            return None
    
    def _analyze_video_audio(self, audio_clip, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze audio from video"""
        try:
            if not HAS_LIBROSA:
                return None

            # Extract audio as numpy array
            audio_array = audio_clip.to_soundarray()
            sample_rate = getattr(audio_clip, 'fps', 0) or 0

            # Convert to mono if stereo
            if hasattr(audio_array, 'shape') and len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)

            result: Dict[str, Any] = {
                'sample_rate': sample_rate,
                'duration': (len(audio_array) / float(sample_rate)) if sample_rate else None,
                'channels': 1,
                'transcription_source': 'video_audio'
            }

            # Extract audio features
            if sample_rate:
                features = self._extract_audio_features(audio_array, sample_rate)
                if features:
                    result['audio_features'] = features

            if options.get('transcribe_audio', True):
                transcription = self._transcribe_audio_array(audio_array, sample_rate, options)
                if transcription:
                    result['transcription'] = transcription
                    result['transcript'] = transcription.get('text')
                    result['transcript_language'] = transcription.get('language')
                    result['transcription_segments'] = transcription.get('segments')
                    result['transcription_model'] = transcription.get('model')
                    result['transcription_generated_at'] = transcription.get('generated_at')

            return result

        except Exception as e:
            logger.warning(f"Error analyzing video audio: {e}")
            return None
    
    def _extract_audio_features(self, y, sr: int) -> Optional[Dict[str, Any]]:
        """Extract audio features using librosa"""
        try:
            if not HAS_LIBROSA:
                return None
            
            features = {}
            
            # Spectral features
            features['spectral_centroid'] = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
            features['spectral_rolloff'] = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
            features['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(y)))
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = [float(x) for x in np.mean(mfccs, axis=1)]
            
            # Tempo
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo)
            
            # RMS energy
            features['rms_energy'] = float(np.mean(librosa.feature.rms(y=y)))
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting audio features: {e}")
            return None
    
    def _detect_speech_segments(self, y, sr: int) -> Optional[List[Dict[str, Any]]]:
        """Detect speech segments in audio"""
        try:
            if not HAS_LIBROSA:
                return None
            
            # Simple energy-based speech detection
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)   # 10ms hop
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Threshold for speech detection
            threshold = np.mean(rms) * 0.5
            
            # Find speech segments
            speech_frames = rms > threshold
            
            # Convert frames to time segments
            segments = []
            in_speech = False
            start_time = None
            
            for i, is_speech in enumerate(speech_frames):
                time_point = i * hop_length / sr
                
                if is_speech and not in_speech:
                    start_time = time_point
                    in_speech = True
                elif not is_speech and in_speech:
                    segments.append({
                        'start': start_time,
                        'end': time_point,
                        'duration': time_point - start_time
                    })
                    in_speech = False
            
            # Handle case where speech continues to end
            if in_speech:
                segments.append({
                    'start': start_time,
                    'end': len(y) / sr,
                    'duration': len(y) / sr - start_time
                })
            
            return segments if segments else None
            
        except Exception as e:
            logger.warning(f"Error detecting speech segments: {e}")
            return None
    
    def _detect_motion_in_video(self, video) -> Optional[Dict[str, Any]]:
        """Detect motion in video using OpenCV frame differencing"""
        try:
            if not HAS_CV2:
                logger.info("OpenCV not available for motion detection")
                return {
                    'motion_detected': False,
                    'motion_regions': [],
                    'motion_intensity': 0.0,
                    'error': 'OpenCV not available'
                }
            
            import cv2
            import numpy as np
            
            # Extract frames for motion analysis
            frames = []
            frame_count = 0
            max_frames = 30  # Limit analysis to first 30 frames for performance
            
            while frame_count < max_frames:
                ret, frame = video.read()
                if not ret:
                    break
                    
                # Convert to grayscale for motion detection
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames.append(gray_frame)
                frame_count += 1
            
            if len(frames) < 2:
                return {
                    'motion_detected': False,
                    'motion_regions': [],
                    'motion_intensity': 0.0,
                    'error': 'Insufficient frames for motion analysis'
                }
            
            # Calculate frame differences
            motion_scores = []
            motion_regions = []
            
            for i in range(1, len(frames)):
                # Calculate absolute difference between consecutive frames
                diff = cv2.absdiff(frames[i-1], frames[i])
                
                # Apply threshold to get binary motion mask
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                
                # Calculate motion intensity (percentage of changed pixels)
                motion_pixels = np.sum(thresh > 0)
                total_pixels = thresh.shape[0] * thresh.shape[1]
                motion_intensity = motion_pixels / total_pixels
                motion_scores.append(motion_intensity)
                
                # Find contours for motion regions
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                frame_regions = []
                
                for contour in contours:
                    if cv2.contourArea(contour) > 100:  # Filter small noise
                        x, y, w, h = cv2.boundingRect(contour)
                        frame_regions.append({
                            'x': int(x), 'y': int(y), 
                            'width': int(w), 'height': int(h),
                            'area': int(cv2.contourArea(contour))
                        })
                
                if frame_regions:
                    motion_regions.append({
                        'frame': i,
                        'regions': frame_regions
                    })
            
            # Calculate overall motion metrics
            avg_motion_intensity = np.mean(motion_scores) if motion_scores else 0.0
            max_motion_intensity = np.max(motion_scores) if motion_scores else 0.0
            motion_detected = max_motion_intensity > 0.05  # 5% threshold
            
            return {
                'motion_detected': motion_detected,
                'motion_regions': motion_regions[:5],  # Limit to first 5 frames with motion
                'motion_intensity': float(avg_motion_intensity),
                'max_motion_intensity': float(max_motion_intensity),
                'frames_analyzed': len(frames),
                'motion_frames': len([score for score in motion_scores if score > 0.05])
            }
            
        except Exception as e:
            logger.warning(f"Error detecting motion: {e}")
            return {
                'motion_detected': False,
                'motion_regions': [],
                'motion_intensity': 0.0,
                'error': str(e)
            }
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'capabilities': self.capabilities,
            'supported_formats': self.supported_formats,
            'cache_dir': self.cache_dir,
            'temp_dir': self.temp_dir
        }


class MediaAnalysisTool:
    """
    Advanced media analysis tools for investigation purposes
    """
    
    def __init__(self, media_engine: MediaProcessingEngine):
        self.media_engine = media_engine
    
    def analyze_media_timeline(self, media_files: List[str]) -> Dict[str, Any]:
        """Analyze timeline of media files based on metadata"""
        timeline_data = []
        
        for file_path in media_files:
            try:
                result = self.media_engine.process_media_file(file_path)
                
                # Extract timestamp information
                timestamp = None
                if 'exif' in result and 'datetime' in result['exif']:
                    timestamp = result['exif']['datetime'].get('original')
                elif 'file_info' in result:
                    timestamp = result['file_info']['created']
                
                if timestamp:
                    timeline_data.append({
                        'file_path': file_path,
                        'timestamp': timestamp,
                        'file_type': result.get('file_type'),
                        'metadata': result
                    })
                    
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        # Sort by timestamp
        timeline_data.sort(key=lambda x: x['timestamp'])
        
        return {
            'timeline': timeline_data,
            'total_files': len(timeline_data),
            'date_range': {
                'start': timeline_data[0]['timestamp'] if timeline_data else None,
                'end': timeline_data[-1]['timestamp'] if timeline_data else None
            }
        }
    
    def detect_duplicate_media(self, media_files: List[str]) -> Dict[str, Any]:
        """Detect duplicate or similar media files"""
        file_hashes = {}
        duplicates = []
        
        for file_path in media_files:
            try:
                result = self.media_engine.process_media_file(file_path)
                file_hash = result.get('file_hash')
                
                if file_hash:
                    if file_hash in file_hashes:
                        duplicates.append({
                            'original': file_hashes[file_hash],
                            'duplicate': file_path,
                            'hash': file_hash
                        })
                    else:
                        file_hashes[file_hash] = file_path
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        return {
            'duplicates': duplicates,
            'unique_files': len(file_hashes),
            'total_files': len(media_files)
        }
    
    def extract_geolocation_data(self, media_files: List[str]) -> Dict[str, Any]:
        """Extract geolocation data from media files"""
        locations = []
        
        for file_path in media_files:
            try:
                result = self.media_engine.process_media_file(file_path)
                
                if 'exif' in result and 'gps' in result['exif']:
                    gps_data = result['exif']['gps']
                    locations.append({
                        'file_path': file_path,
                        'latitude': gps_data['latitude'],
                        'longitude': gps_data['longitude'],
                        'coordinates': gps_data['coordinates']
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        return {
            'locations': locations,
            'files_with_gps': len(locations),
            'total_files': len(media_files)
        }


if __name__ == "__main__":
    # Test the media processing engine
    engine = MediaProcessingEngine()
    
    # Test with a sample file (replace with actual file path)
    test_file = "test_image.jpg"
    if os.path.exists(test_file):
        result = engine.process_media_file(test_file, {
            'extract_text': True,
            'detect_faces': True,
            'detect_objects': True
        })
        print(json.dumps(result, indent=2))
    else:
        print("Test file not found. Please provide a valid media file path.")
