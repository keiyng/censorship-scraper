A Web scraper specially designed for Weibo's topic timeline (http://s.weibo.com/weibo/YOUR_SEARCH_TERM_HERE&Refer=STopic_box).<br />The Weibo API does not provide an endpoint to obtain data published on the topic timeline. This scraper serves as a convenient too for anyone interested in downloading data on the topic timeline automatically without limitations. No Weibo login is required. 
 ## The Scraper
* Able to scrape full content by expanding posts clipped by JavaScript.
* Parallel scraping with multi-threading.
* Only textual content is scraped by default. To scrape content that includes external links and media, modify the filters under `scrape()` in `web_scraping.py`.
* Designed to use with a MySQL database.
* To scrape additional meta-data, define selectors in `constants/element_selectors.py`.
#### Dependencies
1. Selenium
2. PyMySQL
3. PhantomJS (optional)
4. python-crontab (optional) 

PhantomJS is an executable. Download link: (http://phantomjs.org/download.html)
 #### How it works
1. Visits the target page with search term(s) of your choice.
2. Expand collapsed content.
3. Scrape all posts on target page.
4. Filter and save posts to database.
5. Repeat step 1 to 4 at time interval defined in a cron job (optional).
 #### To run:
`python web_scraping.py [SEARCH TERM] [MYSQL TABLE NAME]` <br />Multiple search terms are supported. MySQL table name must be the last argument.
 #### Check for censorship
 This project was created for the purpose of uncovering censorship on Weibo. <br /> `check.py` implements logic to decipher censorship based on the UI and the error code returned from the statuses/show API endpoint. A registered Weibo developer account is needed to obtain the access token. 
##### Dependencies
Same as the scraper, plus the requests library (http://docs.python-requests.org/en/master/)
##### To run:
`python check.py [CHECK NUMBER] [MYSQL TABLE NAME]`
