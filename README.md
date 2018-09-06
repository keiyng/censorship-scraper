# weibo-scrapper
A Web scrapper specially designed for scrapping content returned by specific search term(s) on Weibo, in real-time.
 #### Dependencies
1. Selenium
2. PyMySQL
3. PhantomJS (optional)
4. python-crontab (optional)

PhantomJS is an executable. Download link: (http://phantomjs.org/download.html)
 ## The Scrapper
 * No sign-in to Weibo is required.
* Scrape full content by expanding long posts that have been collpased by JavaScript.
* Parallel scraping with multi-threading.
* Designed to scrape content that contains TEXT ONLY. To scrape content that includes external links and media, remove or modify the filters under `scrape()` in `web_scraping.py`.
* Designed to use with a MySQL database.
* Designed to save only the meta-data that are useful for censorship verification purposes. To include additional meta-data, define selectors in `variables/element_selector.py`.
 #### How it works
1. Visits the target page with search term(s) of your choice. (http://s.weibo.com/weibo/YOUR_SEARCH_TERM_HERE&Refer=STopic_box)
2. Expand collapsible content.
3. Scrape all posts on target page.
4. Filter and save posts to database.
5. Repeat step 1 to 4 at time interval as defined in a cron job (optional).
 #### To run:
`python web_scraping.py [SEARCH TERM] [MYSQL TABLE NAME]`
 Multiple search terms are supported. Just make sure the last arguement is the table name.
Beware of CAPTCHA if too many page requests are submitted at the same time.
 ## The Checker
 This program is built with the purpose of tracking censorship on Weibo.
 ## Cron
