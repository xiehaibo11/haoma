# Configuration Reference

The scraper is configured via `config/config.yaml`. This guide explains all available options.

## Basic Configuration

### Target URL

```yaml
target:
  url: "https://live.leisu.com/detail-4244416"
```

The URL of the live stream to monitor.

### Scraping Duration

```yaml
scraping:
  duration: 300  # Run for 5 minutes
```

Set to `0` for infinite duration (until interrupted with Ctrl+C).

## Phone Patterns

Configure which phone number formats to detect:

```yaml
phone_patterns:
  - name: "china_mobile"
    pattern: "1[3-9]\\d{9}"
    enabled: true
```

### Pattern Format

- `name`: Identifier for the pattern
- `pattern`: Regular expression
- `enabled`: Whether to use this pattern

### Common Patterns

| Pattern | Regex | Description |
|---------|-------|-------------|
| China Mobile | `1[3-9]\\d{9}` | 11-digit Chinese mobile |
| With separators | `1[3-9]\\d[\\s\\-]?\\d{4}[\\s\\-]?\\d{4}` | With spaces/dashes |
| Country code | `(\\+86|86)?[\\s\\-]?1[3-9]\\d{9}` | With +86 prefix |

## Output Options

```yaml
output:
  directory: "./output"
  formats:
    csv: true
    json: true
    txt: true
  filename_prefix: "phones"
  include_context: true
  max_context_length: 100
```

### Formats

- **CSV**: Timestamped log with all metadata
- **JSON**: Structured data for programmatic use
- **TXT**: Simple list for easy reading

## Browser Settings

```yaml
browser:
  headless: true
  viewport:
    width: 1280
    height: 800
```

### Headless Mode

- `true`: Run without GUI (faster, recommended)
- `false`: Show browser window (for debugging)

## Advanced Settings

### Performance Tuning

```yaml
scraping:
  check_interval: 2      # Seconds between scans
  scroll_interval: 5     # Scroll every N iterations
  max_elements: 100      # Limit element scanning
```

Lower intervals = faster detection but higher CPU usage.

### Error Handling

```yaml
advanced:
  max_retries: 3
  retry_delay: 5
  timeout: 30
```

## Environment Variables

Override config with environment variables:

```bash
export SCRAPER_URL="https://example.com/stream"
export SCRAPER_DURATION="600"
export SCRAPER_OUTPUT="./my-output"
```

## Example Configurations

### Quick Scan

```yaml
scraping:
  duration: 60
  check_interval: 1
output:
  formats:
    csv: true
    json: false
    txt: true
```

### Long Monitoring Session

```yaml
scraping:
  duration: 3600  # 1 hour
  check_interval: 5
logging:
  progress_interval: 300  # Progress every 5 minutes
advanced:
  backup_interval: 600    # Backup every 10 minutes
```

### Minimal Output

```yaml
output:
  formats:
    csv: false
    json: false
    txt: true
  include_context: false
```

## Configuration Validation

Test your configuration:

```bash
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

If no output, the YAML is valid.
