import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools, sys, threading, time

BASE_URL = "https://my.uhds.oregonstate.edu/api/jamix/item"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "x-proctorio": "1.5.25220.37"
}

DAY_NAMES = {
    0: "Thursday", 1: "Friday", 2: "Saturday",
    3: "Sunday", 4: "Monday", 5: "Tuesday", 6: "Wednesday"
}

def scrape_active_values(seed_active=13):
    params = {"active": seed_active}
    resp = requests.get(BASE_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    select = soup.find("select", {"name": "active"})
    active_values = []
    for opt in select.find_all("option"):
        value = opt.get("value")
        label = opt.text.strip()
        if value and value.isdigit():
            active_values.append((value, label))
    return active_values

def fetch_html_for_active(active_value, day):
    params = {"active": active_value, "day": day}
    resp = requests.get(BASE_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.text

def search_menu_items(html, keyword):
    soup = BeautifulSoup(html, "lxml")  # faster parser
    results = []
    for item_div in soup.find_all("div", class_="pure-g item"):
        text_to_search = ""
        name_div = item_div.find("div", class_="item_name")
        ingredients_div = item_div.find("div", class_="ingredients")
        if name_div: text_to_search += name_div.get_text()
        if ingredients_div: text_to_search += ingredients_div.get_text()
        if keyword.lower() in text_to_search.lower():
            item_name = name_div.get_text(strip=True) if name_div else "Unknown Item"
            ingredients = ingredients_div.get_text(" ", strip=True) if ingredients_div else "No ingredients listed"
            results.append((item_name, ingredients))
    return results

def run_search():
    active_values = scrape_active_values(seed_active=13)

    while True:
        # Prompt for day selection
        print("\nDay Menu:")
        print("0 = All days")
        print("1 = Sunday")
        print("2 = Monday")
        print("3 = Tuesday")
        print("4 = Wednesday")
        print("5 = Thursday")
        print("6 = Friday")
        print("7 = Saturday")
        print("x = Exit")
        print("")
        choice = input("Enter day number (or 'x' to exit): ").strip().lower()
        if choice == "x":
            print("Exiting.")
            break
        try:
            day_input = int(choice)
        except ValueError:
            print("Invalid input, try again.")
            continue

        if day_input == 0:
            days_to_fetch = list(range(7))
        else:
            mapping = {1: 3, 2: 4, 3: 5, 4: 6, 5: 0, 6: 1, 7: 2}
            days_to_fetch = [mapping.get(day_input)]
            if days_to_fetch[0] is None:
                print("Invalid day number.")
                continue

        # Fetch HTML concurrently with loading indicator
        html_results = []
        total_tasks = len(active_values) * len(days_to_fetch)
        completed = 0
        stop_spinner = False

        def spinner():
            for c in itertools.cycle(['|', '/', '-', '\\']):
                if stop_spinner:
                    break
                sys.stdout.write(f'\rFetching menus {completed}/{total_tasks} {c}')
                sys.stdout.flush()
                time.sleep(0.1)

        t = threading.Thread(target=spinner)
        t.start()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(fetch_html_for_active, value, day): (label, day)
                for value, label in active_values
                for day in days_to_fetch
            }
            for future in as_completed(futures):
                label, day = futures[future]
                try:
                    html = future.result()
                    html_results.append((label, day, html))
                except Exception as e:
                    print(f"\nError fetching {label} (day={day}): {e}")
                completed += 1

        stop_spinner = True
        t.join()
        print(f"\nFinished fetching {completed}/{total_tasks} menus.")

        # Prompt for search text
        search_text = input("Enter text to search in menu items (or leave blank to skip): ").lower()
        if not search_text:
            continue

        # Search with loading indicator
        total_tasks = len(html_results)
        completed = 0
        stop_spinner = False
        matches_all = []

        def spinner_search():
            for c in itertools.cycle(['|', '/', '-', '\\']):
                if stop_spinner:
                    break
                sys.stdout.write(f'\rSearching {completed}/{total_tasks} {c}')
                sys.stdout.flush()
                time.sleep(0.1)

        t = threading.Thread(target=spinner_search)
        t.start()

        for label, day, html in html_results:
            found = search_menu_items(html, search_text)
            if found:
                matches_all.append((label, day, found))
            completed += 1

        stop_spinner = True
        t.join()
        print(f"\nFinished searching {completed}/{total_tasks} menus.")

        # Print results
        if matches_all:
            for label, day, items in matches_all:
                print(f"\n--- Matches in {label} ({DAY_NAMES[day]}) ---")
                for name, ingredients in items:
                    print(f"Item: {name}")
                    print(f"Ingredients: {ingredients}\n")
        else:
            print("\nNo matches found.")

        # Loop back to menu again

if __name__ == "__main__":
    run_search()

