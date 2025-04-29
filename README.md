# Lotto Max Draw Analyzer

A comprehensive Python script that scrapes, processes, and analyzes historical Lotto Max draw data from lottodatabase.com, providing insights into number frequency, common combinations, statistical trends, and visualizations.

# Features
- Data Parsing & Scraping
  - Scrapes Lotto Max results from 2009–2025 using requests and BeautifulSoup.

- Frequency & Combination Analysis
  - Identifies the most frequent numbers, pairs, triplets, and more (up to 7-number combinations).

- Yearly Trends
  - Analyzes number trends year by year with heatmaps.

- Statistical Breakdown
  - Calculates:

  - Average/Min/Max sum of numbers
  
  - Odd/Even and High/Low distributions
  
  - Number range statistics
  
  - Consecutive number pairs
  
  - Hot and cold numbers based on expected frequency

  - Number gap patterns

- Visualizations
  - Generates .png charts and heatmaps using matplotlib and seaborn.

- CSV Export
  - Saves all parsed draw data to lotto_max_draws.csv.

# Dependencies
Make sure you have the following installed:
```
pip install requests beautifulsoup4 pandas matplotlib seaborn
```
