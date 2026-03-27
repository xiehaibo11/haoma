# Colly - AI Agent Guide

## Project Overview

Colly is a **lightning fast and elegant web scraping framework for Go** (Gophers). It provides a clean interface to write any kind of crawler, scraper, or spider. The framework is designed to extract structured data from websites for applications like data mining, data processing, or archiving.

- **Repository**: https://github.com/gocolly/colly
- **Package Path**: `github.com/gocolly/colly/v2`
- **License**: Apache License 2.0
- **Current Version**: 2.1.0

## Technology Stack

- **Language**: Go (minimum version 1.21, tested up to 1.24)
- **Build System**: Go Modules (`go.mod`)
- **Core Dependencies**:
  - `github.com/PuerkitoBio/goquery` - jQuery-like HTML manipulation
  - `github.com/antchfx/htmlquery/xmlquery` - XPath queries for HTML/XML
  - `github.com/temoto/robotstxt` - robots.txt parsing
  - `github.com/nlnwa/whatwg-url` - URL parsing (WHATWG standard)
  - `github.com/saintfish/chardet` - Character encoding detection
  - `github.com/kennygrant/sanitize` - Filename sanitization
  - `github.com/gobwas/glob` - Glob pattern matching

## Project Structure

```
d:\colly
├── colly.go              # Main Collector implementation (~1650 lines)
├── request.go            # HTTP Request type and methods
├── response.go           # HTTP Response type and methods
├── context.go            # Context for passing data between callbacks
├── htmlelement.go        # HTML element wrapper (goquery-based)
├── xmlelement.go         # XML element wrapper (xpath-based)
├── http_backend.go       # HTTP backend, rate limiting, caching
├── http_trace.go         # HTTP tracing for performance tuning
├── unmarshal.go          # Struct tag-based HTML unmarshaling
├── colly_test.go         # Main test suite (~1200 lines)
├── context_test.go       # Context tests
├── http_trace_test.go    # HTTP trace tests
├── unmarshal_test.go     # Unmarshal tests
├── xmlelement_test.go    # XML element tests
├── storage/              # Storage interface and implementations
│   └── storage.go        # Storage interface + InMemoryStorage
├── debug/                # Debugging interfaces
│   ├── debug.go          # Debugger interface and Event types
│   ├── logdebugger.go    # Log-based debugger
│   └── webdebugger.go    # Web-based debugger
├── extensions/           # Helper extensions/addons
│   ├── extensions.go
│   ├── random_user_agent.go
│   ├── referer.go
│   └── url_length_filter.go
├── queue/                # Request queue for distributed scraping
│   ├── queue.go
│   └── queue_test.go
├── proxy/                # Proxy support
│   └── proxy.go
├── _examples/            # Example implementations (24 examples)
│   ├── basic/
│   ├── queue/
│   ├── rate_limit/
│   └── ...
└── .github/workflows/    # CI/CD
    └── ci.yml
```

## Core Architecture

### The Collector

The `Collector` is the main scraping orchestrator (`colly.go`):

```go
type Collector struct {
    UserAgent              string
    Headers               *http.Header
    MaxDepth              int                    // Recursion depth limit (0 = infinite)
    MaxRequests           uint32                 // Max requests limit (0 = infinite)
    AllowedDomains        []string               // Domain whitelist
    DisallowedDomains     []string               // Domain blacklist
    DisallowedURLFilters  []*regexp.Regexp       // URL blacklist patterns
    URLFilters            []*regexp.Regexp       // URL whitelist patterns
    AllowURLRevisit       bool                   // Allow visiting same URL multiple times
    MaxBodySize           int                    // Response body size limit (default 10MB)
    CacheDir              string                 // Cache directory for GET requests
    CacheExpiration       time.Duration          // Cache file expiration
    IgnoreRobotsTxt       bool                   // Skip robots.txt check
    Async                 bool                   // Async HTTP mode
    ParseHTTPErrorResponse bool                  // Parse non-2xx responses
    DetectCharset         bool                   // Auto-detect character encoding
    CheckHead             bool                   // HEAD request before GET
    TraceHTTP             bool                   // Enable HTTP tracing
    Context               context.Context        // Request context for cancellation
    
    // Storage, callbacks, backend, etc. (private fields)
}
```

### Callback System

Colly uses a callback-based event system:

| Callback | Trigger |
|----------|---------|
| `OnRequest` | Before each request |
| `OnRequestHeaders` | Before request is sent (after headers prepared) |
| `OnResponseHeaders` | When response headers received (before body read) |
| `OnResponse` | After response received |
| `OnHTML(selector, callback)` | On matching HTML elements (CSS selector) |
| `OnXML(query, callback)` | On matching XML elements (XPath query) |
| `OnError` | On HTTP or scraping errors |
| `OnScraped` | After all parsing completed |

### Key Types

- **`Request`** (`request.go`): Represents an HTTP request with URL, headers, body, context, depth tracking
- **`Response`** (`response.go`): HTTP response with status, body, headers, trace info
- **`Context`** (`context.go`): Thread-safe key-value store for passing data between callbacks
- **`HTMLElement`** (`htmlelement.go`): Wrapper around goquery.Selection for HTML parsing
- **`XMLElement`** (`xmlelement.go`): Wrapper for XML parsing with XPath support

### Storage Interface

```go
type Storage interface {
    Init() error
    Visited(requestID uint64) error
    IsVisited(requestID uint64) (bool, error)
    Cookies(u *url.URL) string
    SetCookies(u *url.URL, cookies string)
}
```

Default implementation: `InMemoryStorage` (keeps data in memory, no persistence).

## Build and Test Commands

### Prerequisites

```bash
# Install Go 1.21 or later
# https://golang.org/dl/
```

### Build

```bash
# Download dependencies
go mod download

# Build the package
go build

# Install package
go get github.com/gocolly/colly/v2
```

### Test

```bash
# Run all tests
go test -v ./...

# Run tests with race detection
go test -race -v ./...

# Run tests with coverage
go test -race -v -coverprofile=coverage.txt -covermode=atomic ./...
```

### Linting

```bash
# Install golint
go install golang.org/x/lint/golint@latest

# Run linter
golint -set_exit_status

# Format check
gofmt -l -d ./

# Vet
go vet -v ./...
```

## Code Style Guidelines

### License Headers

Every source file must include the Apache 2.0 license header:

```go
// Copyright 2018 Adam Tauber
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
```

### Formatting

- Use `gofmt` for all Go code
- No trailing whitespace
- Use tabs for indentation (Go standard)
- Line length: practical limit, no strict enforcement

### Naming Conventions

- **Exported types/functions**: PascalCase (e.g., `Collector`, `NewCollector`)
- **Unexported types/functions**: camelCase (e.g., `htmlCallbacks`, `handleOnRequest`)
- **Interfaces**: Noun describing capability (e.g., `Storage`, `Debugger`)
- **Callbacks**: `[Event]Callback` suffix (e.g., `RequestCallback`, `HTMLCallback`)
- **Error variables**: `Err` prefix (e.g., `ErrForbiddenDomain`, `ErrMaxDepth`)

### Error Handling

Define errors as package-level variables in `colly.go`:

```go
var (
    ErrForbiddenDomain      = errors.New("Forbidden domain")
    ErrMissingURL           = errors.New("Missing URL")
    ErrMaxDepth             = errors.New("Max depth limit reached")
    ErrForbiddenURL         = errors.New("ForbiddenURL")
    ErrNoURLFiltersMatch    = errors.New("No URLFilters match")
    ErrRobotsTxtBlocked     = errors.New("URL blocked by robots.txt")
    ErrNoCookieJar          = errors.New("Cookie jar is not available")
    ErrNoPattern            = errors.New("No pattern defined in LimitRule")
    ErrEmptyProxyURL        = errors.New("Proxy URL list is empty")
    ErrAbortedAfterHeaders  = errors.New("Aborted after receiving response headers")
    ErrAbortedBeforeRequest = errors.New("Aborted before Do Request")
    ErrQueueFull            = errors.New("Queue MaxSize reached")
    ErrMaxRequests          = errors.New("Max Requests limit reached")
    ErrRetryBodyUnseekable  = errors.New("Retry Body Unseekable")
)
```

Also defines `AlreadyVisitedError` as a struct for already visited URLs.

## Testing Strategy

### Test Organization

- Main tests: `colly_test.go` (~1200 lines)
- Context tests: `context_test.go`
- HTTP trace tests: `http_trace_test.go`
- Unmarshal tests: `unmarshal_test.go`
- XML element tests: `xmlelement_test.go`
- Queue tests: `queue/queue_test.go`

### Test Patterns

Tests use `httptest.Server` for mocking HTTP:

```go
func newUnstartedTestServer() *httptest.Server {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(200)
        w.Write([]byte("hello world\n"))
    })
    // ... more handlers
    return httptest.NewServer(mux)
}
```

### Key Test Scenarios

- Basic HTTP requests and responses
- HTML/XML parsing and callbacks
- Rate limiting and concurrency
- Cookie handling
- Redirect following
- Robots.txt compliance
- Cache functionality
- Error handling
- Request/response serialization

### Running CI Locally

The CI pipeline runs:
1. `go get -a` - dependency check
2. `gofmt -l -d ./` - format check
3. `golint -set_exit_status` - lint check
4. `go vet -v ./...` - static analysis
5. `go test -race -v -coverprofile=...` - tests with race detection

## Configuration

### Environment Variables

Colly can be configured via environment variables with `COLLY_` prefix:

| Variable | Description |
|----------|-------------|
| `COLLY_ALLOWED_DOMAINS` | Comma-separated domain whitelist |
| `COLLY_CACHE_DIR` | Cache directory path |
| `COLLY_DETECT_CHARSET` | Enable charset detection (yes/1/true) |
| `COLLY_DISABLE_COOKIES` | Disable cookies |
| `COLLY_DISALLOWED_DOMAINS` | Comma-separated domain blacklist |
| `COLLY_IGNORE_ROBOTSTXT` | Ignore robots.txt (yes/1/true) |
| `COLLY_FOLLOW_REDIRECTS` | Follow redirects (yes/1/true) |
| `COLLY_MAX_BODY_SIZE` | Max body size in bytes |
| `COLLY_MAX_DEPTH` | Max crawl depth |
| `COLLY_MAX_REQUESTS` | Max number of requests |
| `COLLY_PARSE_HTTP_ERROR_RESPONSE` | Parse error responses |
| `COLLY_TRACE_HTTP` | Enable HTTP tracing |
| `COLLY_USER_AGENT` | User-Agent string |

### Collector Options

```go
c := colly.NewCollector(
    colly.AllowedDomains("example.com"),
    colly.MaxDepth(2),
    colly.Async(true),
    colly.CacheDir("./cache"),
    colly.UserAgent("MyBot/1.0"),
)
```

## Common Development Tasks

### Adding a New Callback

1. Define callback type in `colly.go`
2. Add callback slice to `Collector` struct
3. Create registration method (e.g., `OnEventName`)
4. Create handler method (e.g., `handleOnEventName`)
5. Call handler at appropriate point in request lifecycle

### Adding a Storage Backend

1. Implement `storage.Storage` interface
2. Handle `Init()`, `Visited()`, `IsVisited()`, `Cookies()`, `SetCookies()`
3. Ensure thread-safety (use mutexes)
4. Use with `collector.SetStorage(yourStorage)`

### Adding an Extension

1. Create file in `extensions/` directory
2. Implement as function taking `*colly.Collector`
3. Register callbacks as needed

Example:
```go
func MyExtension(c *colly.Collector) {
    c.OnRequest(func(r *colly.Request) {
        // Extension logic
    })
}
```

## Security Considerations

- **Robots.txt**: Respects robots.txt by default (can be disabled with `IgnoreRobotsTxt`)
- **Rate Limiting**: Built-in support via `LimitRule` to avoid overwhelming servers
- **Redirects**: Limited to 10 redirects (Go default), can be customized
- **Domain Filtering**: Whitelist/blacklist support for domains
- **URL Filtering**: Regex-based URL filtering
- **Body Size Limiting**: Default 10MB max body size
- **Secure Cookies**: Only sends secure cookies over HTTPS

## Release and Versioning

- Version stored in `VERSION` file (semantic versioning)
- Current version: 2.1.0
- v2 module path: `github.com/gocolly/colly/v2`

## Useful Resources

- **Documentation**: https://pkg.go.dev/github.com/gocolly/colly/v2
- **Examples**: `_examples/` directory contains 24 working examples
- **Website**: http://go-colly.org/
- **Issues**: https://github.com/gocolly/colly/issues

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

- **Triggers**: Push to any branch, Pull requests
- **Go versions tested**: 1.21, 1.22, 1.23, 1.24
- **Jobs**:
  - `test`: Run tests with race detection and coverage
  - `build`: Verify build succeeds
  - `codecov`: Upload coverage to Codecov

---

*This document is intended for AI coding agents working with the Colly project. For human contributors, see `CONTRIBUTING.md` and `README.md`.*
