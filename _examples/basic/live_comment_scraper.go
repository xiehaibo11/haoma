package main

import (
	"fmt"
	"regexp"
	"strings"
	"time"

	"github.com/gocolly/colly/v2"
)

func main() {
	// Phone number regex patterns
	phonePatterns := []*regexp.Regexp{
		regexp.MustCompile(`1[3-9]\d{9}`),
		regexp.MustCompile(`1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}`),
	}

	c := colly.NewCollector(
		colly.AllowedDomains("live.leisu.com", "m.leisu.com", "leisu.com", "api.leisu.com"),
		colly.UserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
	)

	phoneNumbers := make(map[string]bool)

	extractPhones := func(text string) []string {
		var found []string
		for _, pattern := range phonePatterns {
			matches := pattern.FindAllString(text, -1)
			for _, match := range matches {
				clean := strings.ReplaceAll(match, " ", "")
				clean = strings.ReplaceAll(clean, "-", "")
				if len(clean) == 11 && strings.HasPrefix(clean, "1") && !phoneNumbers[clean] {
					phoneNumbers[clean] = true
					found = append(found, clean)
				}
			}
		}
		return found
	}

	// Look for comment/chat data in script tags
	c.OnHTML("script", func(e *colly.HTMLElement) {
		script := e.Text
		
		// Look for JSON data containing comments
		if strings.Contains(script, "comment") || strings.Contains(script, "chat") || 
		   strings.Contains(script, "message") || strings.Contains(script, "弹幕") {
			phones := extractPhones(script)
			for _, p := range phones {
				fmt.Printf("📱 Found in script: %s-%s-%s\n", p[:3], p[3:7], p[7:])
			}
		}
	})

	// Look for comments in HTML
	c.OnHTML("[class*='comment'], [class*='chat'], [class*='message'], [class*='danmu'], [class*='弹幕']", func(e *colly.HTMLElement) {
		text := strings.TrimSpace(e.Text)
		if text != "" {
			phones := extractPhones(text)
			for _, p := range phones {
				fmt.Printf("📱 Found in comment element: %s-%s-%s\n", p[:3], p[3:7], p[7:])
			}
		}
	})

	// Check all text for phone numbers
	c.OnHTML("body", func(e *colly.HTMLElement) {
		phones := extractPhones(e.Text)
		if len(phones) > 0 {
			fmt.Printf("\n✅ Total unique phone numbers found: %d\n", len(phoneNumbers))
		}
	})

	c.OnRequest(func(r *colly.Request) {
		fmt.Println("🌐 Visiting:", r.URL)
	})

	c.OnResponse(func(r *colly.Response) {
		fmt.Printf("📄 Status: %d, Size: %d bytes\n\n", r.StatusCode, len(r.Body))
		
		// Try to find API endpoints in the HTML
		body := string(r.Body)
		apiPatterns := []string{
			`api[^"']*comment[^"']*`,
			`api[^"']*chat[^"']*`,
			`ws[s]?://[^"']*`,
			`websocket[^"']*`,
		}
		
		for _, pattern := range apiPatterns {
			re := regexp.MustCompile(pattern)
			matches := re.FindAllString(body, -1)
			if len(matches) > 0 {
				fmt.Println("🔍 Potential API/WebSocket endpoints found:")
				for _, m := range matches[:min(5, len(matches))] {
					fmt.Printf("   - %s\n", m)
				}
				break
			}
		}
	})

	// Try to call common comment API patterns
	fmt.Println("╔════════════════════════════════════════════════╗")
	fmt.Println("║    Live Stream Comment Phone Scraper           ║")
	fmt.Println("╚════════════════════════════════════════════════╝")
	fmt.Println()
	fmt.Println("⚠️  Note: Real-time comments require JavaScript/WebSocket")
	fmt.Println("   This scraper checks static content only.")
	fmt.Println()

	// Visit the main page first
	c.Visit("https://live.leisu.com/detail-4244416")
	
	// Try API endpoints
	time.Sleep(1 * time.Second)
	
	// Common API patterns for live streams
	apiURLs := []string{
		"https://api.leisu.com/api/v2/match/detail?id=4244416",
		"https://api.leisu.com/api/match/comment?id=4244416",
	}
	
	for _, url := range apiURLs {
		fmt.Println("\n🔍 Trying API:", url)
		c.Visit(url)
	}

	// Print results
	fmt.Println("\n" + strings.Repeat("=", 50))
	fmt.Println("RESULTS")
	fmt.Println(strings.Repeat("=", 50))
	
	if len(phoneNumbers) > 0 {
		fmt.Printf("\n📱 Found %d phone number(s):\n\n", len(phoneNumbers))
		for phone := range phoneNumbers {
			fmt.Printf("   %s-%s-%s\n", phone[:3], phone[3:7], phone[7:])
		}
	} else {
		fmt.Println("\n❌ No phone numbers found in static content")
		fmt.Println("\n💡 For LIVE comments, you need:")
		fmt.Println("   1. Headless browser (Playwright/Selenium)")
		fmt.Println("   2. WebSocket connection to chat server")
		fmt.Println("   3. Browser DevTools to find the chat API")
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
