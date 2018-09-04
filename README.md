# weibo-scrapper
A Web scrapper specially designed for scrapping content returned by specific search term(s) on Weibo.

An automatic way to collect data without querying the backend or API

[Target interface] (http://s.weibo.com/weibo/YOUR_SEARCH_TERM_HERE&Refer=STopic_box)

#### Dependencies
1. Selenium
2. PyMySQL
3. PhantomJS (optional)
4. python-crontab (optional)

## The Scrapper

* No sign-in to Weibo is required
* Scrape full content by expanding long posts that have been collpased
* Parallel scraping with multi-threading
* Designed for scrapping content that contains TEXT ONLY. To scrape content that includes external links and media, remove or modify the filters under `scrape()`  
* Designed for use with MySQL database.

#### To run:
`python web_scraping.py [SEARCH TERM] [MYSQL TABLE NAME]`

Multiple search terms are supported. Just make sure the last arguement is the table name.
Beware of CAPTCHA if too many page requests are submitted at the same time.

## The Checker

This program is built with the purpose of tracking censorship. 

## Cron


