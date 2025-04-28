import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
from collections import Counter, defaultdict
from datetime import datetime


def parse_html_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    draws = []

    draw_entries = soup.find_all("div", class_="section group")

    for entry in draw_entries:
        if not entry.find("div", class_="col s_3_12"):
            continue

        date_col = entry.find("div", class_="col s_3_12")
        date_text = date_col.get_text(strip=True)

        numbers_col = entry.find("div", class_="col s_9_12")
        if not numbers_col:
            continue

        white_balls = []
        for ball in numbers_col.find_all("span", class_="white ball"):
            num = ball.get_text(strip=True)
            if num.isdigit():
                white_balls.append(int(num))

        try:
            date_obj = datetime.strptime(date_text, "%A, %B %d, %Y")
            date_str = date_obj.strftime("%Y-%m-%d")
            year = date_obj.year
        except ValueError:
            continue

        draws.append({"date": date_str, "numbers": white_balls, "year": year})

    return draws


def fetch_historical_data(start_year=2009, end_year=2025):
    all_draws = []
    base_url = "https://www.lottodatabase.com/lotto-database/canadian-lotteries/lotto-max/draw-history/"

    for year in range(start_year, end_year + 1):
        url = f"{base_url}{year}"
        print(f"Fetching data for year {year}...")

        try:
            response = requests.get(url)
            if response.status_code == 200:
                year_draws = parse_html_data(response.text)
                all_draws.extend(year_draws)
                print(f"  Found {len(year_draws)} draws for {year}")
            else:
                print(f"  Failed to fetch data for {year}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  Error fetching data for {year}: {e}")

    return all_draws


def process_pasted_data(html_content):
    draws = parse_html_data(html_content)
    print(f"Extracted {len(draws)} draws from pasted HTML")
    return draws


def analyze_frequency(draws):
    main_numbers = []

    for draw in draws:
        main_numbers.extend(draw["numbers"])

    main_freq = Counter(main_numbers)

    main_df = pd.DataFrame(
        {"number": list(main_freq.keys()), "frequency": list(main_freq.values())}
    ).sort_values(by="frequency", ascending=False)

    return {"main": main_df}


def analyze_combinations(draws, combination_size=2):
    combinations_count = Counter()

    for draw in draws:
        numbers = draw["numbers"]
        for combo in itertools.combinations(sorted(numbers), combination_size):
            combinations_count[combo] += 1

    combo_df = pd.DataFrame(
        {
            "combination": [str(combo) for combo in combinations_count.keys()],
            "frequency": list(combinations_count.values()),
        }
    ).sort_values(by="frequency", ascending=False)

    return combo_df


def analyze_by_year(draws):
    draws_by_year = defaultdict(list)
    for draw in draws:
        year = draw["year"]
        draws_by_year[year].append(draw)

    yearly_analysis = {}
    for year, year_draws in draws_by_year.items():
        yearly_analysis[year] = analyze_frequency(year_draws)["main"]

    return yearly_analysis


def calculate_additional_stats(draws):
    stats = {}

    if not draws:
        return stats

    sums = [sum(draw["numbers"]) for draw in draws]
    stats["average_sum"] = sum(sums) / len(sums)
    stats["min_sum"] = min(sums)
    stats["max_sum"] = max(sums)

    odd_counts = [sum(1 for num in draw["numbers"] if num % 2 == 1) for draw in draws]
    odd_distribution = Counter(odd_counts)
    stats["odd_even_distribution"] = {
        f"{odd} odd, {7-odd} even": count
        for odd, count in sorted(odd_distribution.items())
    }
    stats["avg_odd_numbers"] = sum(odd_counts) / len(odd_counts)

    high_counts = [sum(1 for num in draw["numbers"] if num > 25) for draw in draws]
    high_distribution = Counter(high_counts)
    stats["high_low_distribution"] = {
        f"{high} high, {7-high} low": count
        for high, count in sorted(high_distribution.items())
    }
    stats["avg_high_numbers"] = sum(high_counts) / len(high_counts)

    consecutive_counts = []
    for draw in draws:
        sorted_nums = sorted(draw["numbers"])
        consecutive = 0
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] - sorted_nums[i] == 1:
                consecutive += 1
        consecutive_counts.append(consecutive)

    consecutive_distribution = Counter(consecutive_counts)
    stats["consecutive_pairs_distribution"] = {
        f"{pairs} consecutive pairs": count
        for pairs, count in sorted(consecutive_distribution.items())
    }
    stats["avg_consecutive_pairs"] = sum(consecutive_counts) / len(consecutive_counts)

    ranges = [max(draw["numbers"]) - min(draw["numbers"]) for draw in draws]
    stats["avg_range"] = sum(ranges) / len(ranges)
    stats["min_range"] = min(ranges)
    stats["max_range"] = max(ranges)

    return stats


def find_hot_cold_numbers(freq_df, total_draws, period="all time"):
    expected_freq = total_draws * 7 / 50

    freq_df = freq_df.copy()
    freq_df["expected"] = expected_freq
    freq_df["deviation"] = (
        (freq_df["frequency"] - freq_df["expected"]) / freq_df["expected"] * 100
    )

    hot_numbers = freq_df.sort_values(by="deviation", ascending=False).head(10)
    cold_numbers = freq_df.sort_values(by="deviation", ascending=True).head(10)

    return {"period": period, "hot": hot_numbers, "cold": cold_numbers}


def find_patterns(draws):
    patterns = {}

    number_gaps = {}
    for num in range(1, 51):
        last_seen = None
        gaps = []

        for i, draw in enumerate(sorted(draws, key=lambda x: x["date"])):
            if num in draw["numbers"]:
                if last_seen is not None:
                    gaps.append(i - last_seen)
                last_seen = i

        if gaps:
            number_gaps[num] = {
                "avg_gap": sum(gaps) / len(gaps),
                "max_gap": max(gaps),
                "current_gap": (
                    len(draws) - last_seen if last_seen is not None else None
                ),
            }

    patterns["number_gaps"] = number_gaps

    return patterns


def visualize_data(
    freq_df,
    combo_df,
    triplet_df,
    quad_df,
    five_df,
    six_df,
    seven_df,
    yearly_analysis,
    stats,
):
    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="number", y="frequency", data=freq_df.head(50), color="cornflowerblue"
    )
    plt.title("Frequency of Lotto Max Numbers")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("number_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=combo_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max Number Pairs")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("pairs_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=triplet_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max Triplets")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("triplets_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=quad_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max 4-Number Combinations")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("quads_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=five_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max 5-Number Combinations")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("five_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=six_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max 6-Number Combinations")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("six_frequency.png")

    plt.figure(figsize=(15, 8))
    sns.barplot(
        x="combination", y="frequency", data=seven_df.head(20), color="cornflowerblue"
    )
    plt.title("Top 20 Most Frequent Lotto Max 7-Number Combinations")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig("seven_frequency.png")

    all_years = sorted(yearly_analysis.keys())

    all_numbers = list(range(1, 51))
    heatmap_data = pd.DataFrame(index=all_years, columns=all_numbers)

    for year in all_years:
        year_freq = yearly_analysis[year]
        year_freq_dict = dict(zip(year_freq["number"], year_freq["frequency"]))
        for num in all_numbers:
            heatmap_data.loc[year, num] = year_freq_dict.get(num, 0)

    avg_frequency = heatmap_data.mean()
    median_frequency = heatmap_data.median()
    heatmap_data.loc['Average'] = avg_frequency
    heatmap_data.loc['Median'] = median_frequency

    heatmap_data = heatmap_data.apply(pd.to_numeric)

    plt.figure(figsize=(20, 12))  # Made figure slightly taller
    sns.heatmap(heatmap_data, cmap="YlGnBu", annot=False)
    plt.title("Number Frequency by Year")
    plt.xlabel("Number")
    plt.ylabel("Year")
    plt.tight_layout()
    plt.savefig("yearly_heatmap.png")

    if "odd_even_distribution" in stats:
        plt.figure(figsize=(10, 6))
        labels = list(stats["odd_even_distribution"].keys())
        values = list(stats["odd_even_distribution"].values())
        plt.bar(labels, values, color="cornflowerblue")
        plt.title("Distribution of Odd vs Even Numbers")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("odd_even_distribution.png")


def save_to_csv(draws, filename="lotto_max_draws.csv"):
    data = []
    for draw in draws:
        row = {"date": draw["date"], "year": draw["year"]}

        for i, num in enumerate(draw["numbers"]):
            row[f"number_{i+1}"] = num

        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


def main():

    print("Fetching historical data from 2019 to 2025...")
    all_draws = fetch_historical_data(2019, 2025)

    print(f"\nTotal draws collected: {len(all_draws)}")

    print("\nAnalyzing number frequencies...")
    freq_results = analyze_frequency(all_draws)
    main_freq_df = freq_results["main"]

    print("Top 10 most frequent main numbers:")
    print(main_freq_df.head(10))

    print("\nAnalyzing number pairs...")
    combo_df = analyze_combinations(all_draws, 2)
    print("Top 10 most frequent pairs:")
    print(combo_df.head(10))

    print("\nAnalyzing combinations of 3 numbers...")
    triplet_df = analyze_combinations(all_draws, 3)
    print("Top 10 most frequent triplets:")
    print(triplet_df.head(10))

    print("\nAnalyzing combinations of 4 numbers...")
    quad_df = analyze_combinations(all_draws, 4)
    print("Top 10 most frequent 4-number combinations:")
    print(quad_df.head(10))

    print("\nAnalyzing combinations of 5 numbers...")
    five_df = analyze_combinations(all_draws, 5)
    print("Top 10 most frequent 5-number combinations:")
    print(five_df.head(10))

    print("\nAnalyzing combinations of 6 numbers...")
    six_df = analyze_combinations(all_draws, 6)
    print("Top 10 most frequent 6-number combinations:")
    print(six_df.head(10))

    print("\nAnalyzing combinations of 7 numbers...")
    seven_df = analyze_combinations(all_draws, 7)
    print("Top 10 most frequent 7-number combinations:")
    print(seven_df.head(10))

    print("\nAnalyzing by year...")
    yearly_analysis = analyze_by_year(all_draws)
    for year in sorted(yearly_analysis.keys())[-3:]:
        print(f"\nTop 10 numbers for {year}:")
        print(yearly_analysis[year].head(10))

    print("\nCalculating additional statistics...")
    stats = calculate_additional_stats(all_draws)
    for stat, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{stat}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{stat}: {value}")

    print("\nFinding hot and cold numbers...")
    hot_cold = find_hot_cold_numbers(main_freq_df, len(all_draws))
    print("\nHot numbers (most frequent compared to expected):")
    print(hot_cold["hot"][["number", "frequency", "deviation"]].to_string(index=False))
    print("\nCold numbers (least frequent compared to expected):")
    print(hot_cold["cold"][["number", "frequency", "deviation"]].to_string(index=False))

    print("\nFinding patterns in draw history...")
    patterns = find_patterns(all_draws)
    print("\nNumber gap analysis:")
    for num, gap_data in list(patterns["number_gaps"].items()):
        print(
            f"  [{num}]: Avg gap {gap_data['avg_gap']:.1f} draws, Current gap {gap_data['current_gap']}"
        )

    print("\nCreating visualizations...")
    visualize_data(
        main_freq_df,
        combo_df,
        triplet_df,
        quad_df,
        five_df,
        six_df,
        seven_df,
        yearly_analysis,
        stats,
    )

    save_to_csv(all_draws)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
