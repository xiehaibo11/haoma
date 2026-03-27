package main

import (
	"fmt"
	"strings"

	"github.com/gocolly/colly/v2"
)

func main() {
	// Instantiate default collector
	c := colly.NewCollector(
		// Allow leisu.com domains
		colly.AllowedDomains("live.leisu.com", "h5.leisu.com", "leisu.com"),
		// Set User-Agent to look like a real browser
		colly.UserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
	)

	// On response - print first part of HTML to see structure
	c.OnResponse(func(r *colly.Response) {
		fmt.Printf("Response status: %d\n", r.StatusCode)
		fmt.Printf("Content length: %d bytes\n", len(r.Body))
		
		// Print first 2000 characters of HTML to understand structure
		body := string(r.Body)
		fmt.Println("\n--- HTML Preview (first 2000 chars) ---")
		if len(body) > 2000 {
			fmt.Println(body[:2000])
		} else {
			fmt.Println(body)
		}
		fmt.Println("\n--- End Preview ---\n")
	})

	// On title element
	c.OnHTML("title", func(e *colly.HTMLElement) {
		fmt.Printf("Page title: %q\n", e.Text)
	})

	// Try to find any text content
	c.OnHTML("body", func(e *colly.HTMLElement) {
		text := strings.TrimSpace(e.Text)
		// Extract meaningful text (filter out scripts and styles)
		lines := strings.Split(text, "\n")
		fmt.Println("--- Page Content ---")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if len(line) > 0 && len(line) < 500 {
				fmt.Println(line)
			}
		}
		fmt.Println("--- End Content ---")
	})

	// Before making a request print "Visiting ..."
	c.OnRequest(func(r *colly.Request) {
		fmt.Println("Visiting", r.URL.String())
	})

	// On error
	c.OnError(func(r *colly.Response, err error) {
		fmt.Printf("Error: %s (Status: %d)\n", err, r.StatusCode)
	})

	// Start scraping on https://live.leisu.com/detail-4244416
	c.Visit("https://live.leisu.com/detail-4244416")
}
