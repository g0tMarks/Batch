# Timeout Configuration for Batch Report Application

## Problem
The application was experiencing worker timeout errors when generating reports for more than 10 students. The default Gunicorn timeout (30 seconds) was insufficient for processing larger datasets.

## Solution
Multiple timeout configurations have been implemented to handle long-running report generation tasks:

### 1. Gunicorn Configuration (render.yaml)
Updated the start command in `render.yaml` with extended timeout parameters:

```yaml
startCommand: gunicorn app:app --timeout 300 --workers 2 --worker-class sync --keep-alive 5 --max-requests 1000 --max-requests-jitter 100
```

**Parameters explained:**
- `--timeout 300`: Sets worker timeout to 5 minutes (300 seconds)
- `--workers 2`: Uses 2 worker processes
- `--worker-class sync`: Uses synchronous workers (better for CPU-intensive tasks)
- `--keep-alive 5`: Keep-alive timeout of 5 seconds
- `--max-requests 1000`: Restart workers after 1000 requests
- `--max-requests-jitter 100`: Add randomness to prevent all workers restarting simultaneously

### 2. Gunicorn Configuration File (gunicorn.conf.py)
Alternative configuration file with detailed settings:

```python
timeout = 300  # 5 minutes
graceful_timeout = 300
workers = 2
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
```

### 3. Flask Application Configuration (app.py)
Added Flask-specific timeout settings:

```python
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for dynamic content
```

## Expected Results
- Report generation for 10+ students should no longer timeout
- Workers will have 5 minutes to complete processing
- Better handling of concurrent requests
- Improved stability for long-running operations

## Monitoring
Monitor the application logs for:
- Worker timeout messages
- Request processing times
- Memory usage patterns
- Worker restart frequency

## Additional Considerations
1. **Memory Usage**: Longer timeouts may increase memory usage
2. **Concurrent Users**: Consider scaling workers based on expected load
3. **Database Connections**: Ensure connection pooling is configured
4. **External API Limits**: Monitor Anthropic API rate limits

## Troubleshooting
If timeouts still occur:
1. Increase timeout value further (e.g., 600 seconds for 10 minutes)
2. Add more workers if CPU is not the bottleneck
3. Implement background job processing for very large datasets
4. Consider chunking large datasets into smaller batches 