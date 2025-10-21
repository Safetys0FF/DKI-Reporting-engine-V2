# DKI API Integration Architecture Documentation

## Overview

The DKI Report Engine now features a comprehensive API integration system that provides unified access to external services through the Data Bus architecture. This system enables any module in the DKI ecosystem to access AI services, geocoding, OSINT tools, and other external APIs through a centralized, bus-based communication system.

## Architecture Components

### 1. Central Plugin (`central_plugin.py`)

**Location**: `F:\The Central Command\Command Center\Start Menu\Run Time\central_plugin.py`

**Purpose**: The central hub that provides unified API access through the Data Bus system.

**Key Features**:
- Data Bus integration for system-wide API access
- API Manager integration for key management and rate limiting
- Smart Lookup Resolver for AI-powered services
- OSINT Engine for evidence verification
- Signal handlers for narrative generation, OSINT, and professional tools

**Core Methods**:
```python
# Bus communication
send_to_bus(signal, payload) -> Dict[str, Any]

# Narrative generation
generate_narrative(processed_data, section_id) -> Dict[str, Any]

# File storage
store_file(file_info) -> Dict[str, Any]

# Event logging
log_event(message, level) -> None
```

### 2. API Manager (`api_manager.py`)

**Location**: `F:\The Central Command\Command Center\Data Bus\api_manager.py`

**Purpose**: Manages API registrations, keys, rate limiting, and connectivity testing.

**Key Features**:
- API key management and storage
- Rate limiting and caching
- Connectivity testing for different API types
- Configuration management
- Status monitoring

**Core Methods**:
```python
# API registration
register_api(name, key, endpoint, description) -> None

# API control
toggle_api(name, enabled) -> None
is_enabled(name) -> bool

# Testing and status
test_api(name) -> Dict[str, Any]
get_api_status() -> Dict[str, Any]
get_available_apis() -> List[str]

# Rate limiting
check_rate_limit(api_name) -> bool
increment_rate_limit(api_name) -> None
```

### 3. API Configuration System

**Location**: `F:\The Central Command\Command Center\Data Bus\configs\`

**Files**:
- `api_keys.json` - API key storage
- `api_config.json` - API settings and policies

**Supported APIs**:
- OpenAI API (ChatGPT)
- Google Gemini API
- Google Maps API
- Bing Search API
- Public Records API
- WhitePages API

### 4. Data Bus Integration

**Location**: `F:\The Central Command\Command Center\Data Bus\bus_core.py`

**Purpose**: Provides the communication backbone for API signals.

**API-Related Signals**:
- `narrative.generate` - AI-powered narrative generation
- `osint.verify` - OSINT verification requests
- `geocoding.reverse` - Reverse geocoding
- `api.test` - API connectivity testing
- `api.status` - API status monitoring
- `evidence.scan` - Evidence processing with OSINT
- `mission_debrief.process_report` - Professional tools integration

## Usage Examples

### 1. Basic API Integration

```python
# Import central plugin
from central_plugin import central_plugin

# Check API status
status = central_plugin.send_to_bus("api.status", {})
print(f"API Status: {status}")

# Generate narrative using AI
narrative_result = central_plugin.generate_narrative(
    processed_data={"evidence": "sample data"},
    section_id="section_1"
)
print(f"Narrative: {narrative_result}")
```

### 2. API Manager Usage

```python
# Import API Manager
from api_manager import APIManager

# Initialize
api_manager = APIManager()

# Register new API
api_manager.register_api(
    name="custom_api",
    key="your_api_key",
    endpoint="https://api.example.com",
    description="Custom API service"
)

# Test API connectivity
result = api_manager.test_api("custom_api")
print(f"Test Result: {result}")

# Get status
status = api_manager.get_api_status()
print(f"Total APIs: {status['total_apis']}")
```

### 3. GUI Integration

The enhanced GUI includes an "API Status" tab that provides:
- Real-time API status monitoring
- Connectivity testing
- Configuration status display
- API key management interface

**Access**: Login to GUI → Navigate to "API Status" tab

## Configuration

### 1. API Keys Setup

Edit `F:\The Central Command\Command Center\Data Bus\configs\api_keys.json`:

```json
{
    "openai_api": {
        "key": "your_openai_api_key",
        "endpoint": "https://api.openai.com/v1",
        "enabled": true,
        "description": "OpenAI ChatGPT API for AI-powered narrative generation"
    },
    "google_maps_api": {
        "key": "your_google_maps_api_key",
        "endpoint": "https://maps.googleapis.com/maps/api",
        "enabled": true,
        "description": "Google Maps API for geocoding and reverse geocoding"
    }
}
```

### 2. API Configuration

Edit `F:\The Central Command\Command Center\Data Bus\configs\api_config.json`:

```json
{
    "api_settings": {
        "rate_limits": {
            "openai_api": {
                "calls_per_hour": 100,
                "calls_per_minute": 10
            }
        },
        "timeouts": {
            "default": 30,
            "openai_api": 60
        },
        "retry_settings": {
            "max_retries": 3,
            "backoff_factor": 2
        }
    }
}
```

## Signal Handlers

### 1. Narrative Generation

**Signal**: `narrative.generate`

**Payload**:
```json
{
    "section_id": "section_1",
    "processed_data": {...},
    "case_metadata": {...}
}
```

**Response**:
```json
{
    "status": "ok",
    "section_id": "section_1",
    "full_narrative": "Generated narrative text...",
    "summary": "Narrative generated for section_1"
}
```

### 2. OSINT Verification

**Signal**: `osint.verify`

**Payload**:
```json
{
    "query": "search term",
    "type": "general"
}
```

**Response**:
```json
{
    "status": "ok",
    "query": "search term",
    "verification_type": "general",
    "result": {...}
}
```

### 3. API Status

**Signal**: `api.status`

**Payload**: `{}`

**Response**:
```json
{
    "status": "ok",
    "system_status": {
        "bus_available": true,
        "api_manager_available": true,
        "smart_lookup_available": true,
        "osint_engine_available": true,
        "api_keys_loaded": true,
        "timestamp": "2025-01-26T15:30:00"
    }
}
```

## Error Handling

### 1. API Failures

The system includes comprehensive error handling:

```python
# API test failure
{
    "status": "error",
    "message": "API test failed: Connection timeout"
}

# Missing API key
{
    "status": "no_key",
    "message": "No API key configured for openai_api"
}

# Rate limit exceeded
{
    "status": "rate_limited",
    "message": "API rate limit exceeded"
}
```

### 2. Fallback Behavior

- **Provider Fallback**: If one API fails, the system tries the next provider
- **Template Fallback**: If all AI services fail, falls back to template-based generation
- **Cache Fallback**: Uses cached responses when available

## Testing

### 1. Unit Tests

Run the API integration test suite:

```bash
cd "F:\The Central Command\Command Center\UI"
python test_api_integration.py
```

### 2. GUI Testing

1. Launch the enhanced GUI
2. Navigate to "API Status" tab
3. Click "Test API Connectivity"
4. Review status display

### 3. Manual Testing

```python
# Test central plugin
from central_plugin import central_plugin

# Test API status
response = central_plugin.send_to_bus("api.status", {})
print(response)

# Test narrative generation
result = central_plugin.generate_narrative({}, "section_1")
print(result)
```

## Security Considerations

### 1. API Key Management

- API keys are stored in JSON configuration files
- Keys are not logged or exposed in error messages
- Rate limiting prevents abuse
- Caching reduces API calls

### 2. Data Privacy

- No sensitive data is sent to external APIs without encryption
- Local processing is preferred over external API calls
- Audit logging tracks all API usage

### 3. Access Control

- API access is controlled through the Data Bus system
- Section-aware execution ensures proper permissions
- User authentication required for API operations

## Performance Optimization

### 1. Caching

- API responses are cached with configurable TTL
- Cache keys are generated from request parameters
- Automatic cache expiration and cleanup

### 2. Rate Limiting

- Per-API rate limits prevent quota exhaustion
- Automatic retry with exponential backoff
- Rate limit monitoring and alerts

### 3. Async Processing

- API calls are processed asynchronously
- Non-blocking GUI operations
- Background processing for heavy operations

## Troubleshooting

### 1. Common Issues

**API Keys Not Working**:
- Check `api_keys.json` file format
- Verify API key validity
- Ensure API is enabled in configuration

**Connection Failures**:
- Check internet connectivity
- Verify API endpoints
- Review firewall settings

**Rate Limiting**:
- Check rate limit configuration
- Monitor API usage
- Implement request queuing

### 2. Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Status Monitoring

Use the GUI "API Status" tab to monitor:
- API connectivity
- Rate limit status
- Error rates
- Performance metrics

## Future Enhancements

### 1. Planned Features

- API usage analytics dashboard
- Automatic API key rotation
- Advanced caching strategies
- Multi-region API support
- API cost monitoring

### 2. Integration Opportunities

- Additional AI providers (Claude, GPT-4)
- Specialized OSINT tools
- Real-time data feeds
- Blockchain verification services

## Support

For technical support or questions about the API integration system:

1. Check the GUI "API Status" tab for current status
2. Review configuration files in `configs/` directory
3. Run the test suite to identify issues
4. Check audit logs for detailed error information

## Conclusion

The DKI API integration system provides a robust, scalable foundation for external service integration. Through the Data Bus architecture, any module in the DKI ecosystem can access AI services, geocoding, OSINT tools, and other external APIs with proper error handling, rate limiting, and security controls.

The system is designed to be:
- **Modular**: Easy to add new APIs and services
- **Reliable**: Comprehensive error handling and fallback mechanisms
- **Secure**: Proper key management and access controls
- **Performant**: Caching, rate limiting, and async processing
- **Maintainable**: Clear documentation and testing framework


