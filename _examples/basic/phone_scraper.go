package main

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/gocolly/colly/v2"
)

func main() {
	// Phone number regex patterns (Chinese mobile numbers)
	phonePatterns := []*regexp.Regexp{
		regexp.MustCompile(`1[3-9]\d{9}`),                                    // Standard 11-digit mobile
		regexp.MustCompile(`1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}`),              // With separators
		regexp.MustCompile(`(\+86|86)?[\s\-]?1[3-9]\d{9}`),                  // With country code
	}

	// Instantiate default collector - allow all leisu.com subdomains
	c := colly.NewCollector(
		colly.AllowedDomains("live.leisu.com", "h5.leisu.com", "m.leisu.com", "leisu.com", "www.leisu.com"),
		colly.UserAgent("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"),
		colly.MaxDepth(2),
	)

	// Store unique phone numbers
	phoneNumbers := make(map[string]bool)

	// Extract phone numbers from text
	extractPhones := func(text string) {
		for _, pattern := range phonePatterns {
			matches := pattern.FindAllString(text, -1)
			for _, match := range matches {
				// Clean the number
				cleanNumber := strings.ReplaceAll(match, " ", "")
				cleanNumber = strings.ReplaceAll(cleanNumber, "-", "")
				cleanNumber = strings.ReplaceAll(cleanNumber, "+86", "")
				cleanNumber = strings.TrimPrefix(cleanNumber, "86")
				
				if len(cleanNumber) == 11 && strings.HasPrefix(cleanNumber, "1") {
					phoneNumbers[cleanNumber] = true
				}
			}
		}
	}

	// On response - scan entire HTML
	c.OnResponse(func(r *colly.Response) {
		fmt.Printf("Response status: %d\n", r.StatusCode)
		fmt.Printf("Content length: %d bytes\n\n", len(r.Body))
		
		body := string(r.Body)
		extractPhones(body)
		
		// Print a preview of the HTML
		fmt.Println("--- HTML Preview ---")
		if len(body) > 500 {
			fmt.Println(body[:500])
		} else {
			fmt.Println(body)
		}
		fmt.Println("...")
		fmt.Println("-------------------\n")
	})

	// On any HTML element with text
	c.OnHTML("body", func(e *colly.HTMLElement) {
		extractPhones(e.Text)
	})

	// Look for tel: links
	c.OnHTML("a[href^='tel:']", func(e *colly.HTMLElement) {
		tel := strings.TrimPrefix(e.Attr("href"), "tel:")
		fmt.Printf("📞 Found tel: link -> %s\n", tel)
		extractPhones(tel)
	})

	// Look for phone containers
	c.OnHTML("[class*='phone'], [class*='tel'], [class*='mobile']", func(e *colly.HTMLElement) {
		text := strings.TrimSpace(e.Text)
		if text != "" && len(text) < 100 {
			fmt.Printf("🔍 Found phone container: %s\n", text)
			extractPhones(text)
		}
	})

	// Before making a request
	c.OnRequest(func(r *colly.Request) {
		fmt.Println("Visiting", r.URL.String())
	})

	// On error
	c.OnError(func(r *colly.Response, err error) {
		fmt.Printf("\n❌ Error: %s\n", err)
		if strings.Contains(err.Error(), "Forbidden") || strings.Contains(err.Error(), "403") {
			fmt.Println("\n⚠️  Website is blocking automated requests with WAF/anti-bot protection")
			fmt.Println("\n💡 Workarounds:")
			fmt.Println("   1. Try mobile version: https://m.leisu.com/live/detail-4244416")
			fmt.Println("   2. Use browser cookies from an authenticated session")
			fmt.Println("   3. Use headless browser (Playwright/Puppeteer)")
		}
	})

	// After scraping completes
	c.OnScraped(func(r *colly.Response) {
		fmt.Println("\n" + strings.Repeat("=", 50))
		fmt.Println("SCRAPING RESULTS")
		fmt.Println(strings.Repeat("=", 50))
		
		if len(phoneNumbers) > 0 {
			fmt.Printf("\n📱 Found %d unique phone number(s):\n\n", len(phoneNumbers))
			for phone := range phoneNumbers {
				formatted := phone[:3] + "-" + phone[3:7] + "-" + phone[7:]
				fmt.Printf("   %s\n", formatted)
			}
		} else {
			fmt.Println("\n❌ No phone numbers found in the response")
		}
	})

	// Start scraping - try mobile version first
	fmt.Println("╔════════════════════════════════════════════════╗")
	fmt.Println("║       Mobile Phone Number Scraper              ║")
	fmt.Println("╚════════════════════════════════════════════════╝")
	fmt.Println()
	
	c.Visit("https://live.leisu.com/detail-4244416")
}
