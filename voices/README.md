# Qwen TTS Voice Registry

This directory stores metadata about custom Qwen voices created for the Reachy Mini apps.

## Structure

- `registry.json` - Main registry file mapping preferred names to actual voice names
- Individual voice metadata files (optional, for detailed tracking)

## Voice Registry Format

```json
{
  "version": "1.0",
  "voices": {
    "preferred_name_language": {
      "voice_name": "qwen-tts-vd-...",
      "preferred_name": "host_voice",
      "language": "en",
      "voice_prompt": "...",
      "preview_text": "...",
      "created_at": "2025-12-24T...",
      "created_by": "user@example.com"
    }
  }
}
```

## Benefits

1. **Cost Savings**: 
   - Reuses existing voices instead of creating duplicates ($0.20 per voice)
   - **Audio Caching**: Caches synthesized audio to avoid re-synthesizing ($0.13 per 10k chars)
2. **Sharing**: Can be committed to GitHub so others can reuse your voices
3. **Tracking**: Know which voices exist and when they were created
4. **API Lookup**: Automatically searches API before creating new voices

## Audio Caching

The system automatically caches synthesized audio files in `audio_cache/`:
- **Cache Key**: MD5 hash of `voice_name + text`
- **Format**: WAV files (24kHz, mono, 16-bit PCM)
- **Location**: `voices/audio_cache/{hash}.wav`
- **Benefits**: 
  - Saves $0.13 per 10,000 characters on repeated scripts
  - Instant playback for cached audio (no API call)
  - Preview audio from voice creation is also saved

**Note**: Audio cache is excluded from git (too large), but can be regenerated.

## Usage

The system automatically:
1. Checks local registry first
2. Searches Qwen API for existing voices
3. Only creates new voice if not found
4. Updates registry after creation

