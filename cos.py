import requests
import json
import browser_cookie3
from bs4 import BeautifulSoup
from pathlib import Path
# 76561198259468267

# browser_cookie3 functions to check all possible browsers for a backpack.tf cookie

print("This script uses your browser data to scrape information from your backpack.tf profile.\nMake sure you're logged in to backpack.tf on your preferred browser.\nThe process might vary based on your browser.\nFirst, the script tries to automatically grab cookies from your browser, on failure it asks you to input them yourself\nIf you're concerned about giving away your cookies, review the script.");
input("<Press enter>");
browser_cookie_funcs = [
    (browser_cookie3.firefox),
    (browser_cookie3.chrome),
    (browser_cookie3.brave),
    (browser_cookie3.edge),
    (browser_cookie3.opera),
    (browser_cookie3.librewolf),
    (browser_cookie3.chromium),
    (browser_cookie3.safari),
    (browser_cookie3.vivaldi),
    (browser_cookie3.w3m),
];

# tries to grab backpack.tf cookies from different browsers
for func in browser_cookie_funcs:
    try:
        cookies = func(domain_name='backpack.tf');
        if(len(cookies)) > 0:
            break;
    except Exception:
        continue;

steamid64 = input("input your steamid64 (backpack.tf/profiles/7656...<--THIS NUMBER):\n");

# if no cookie in browsers, user has to input cookies themselves

if not (len(cookies) > 0):
    print("failed to automatically get cookies, try again or input cookie yourself\n");
    cookies = {};
    cookies["cf_clearance"] = input("input cf_clearance:\n");
    cookies["stack[hash]"] = input("input stack[hash]:\n");
    cookies["user-id"] = input("input user-id:\n");
    cookies["stack[user]"] = steamid64;

headers = {};
headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0";
custom_user_agent = input("press enter for default or input your user-agent (type \"what's my user agent\" in google):\n");
if len(custom_user_agent) > 1:
    headers["User-Agent"] = custom_user_agent;

# get timestamps from backpack page

stamp_url = "https://backpack.tf/profiles/"+steamid64;

stamp_req = requests.get(stamp_url, cookies=cookies, headers=headers);
stamp_html = BeautifulSoup(stamp_req.text, "html.parser");

# timestamps are stored in a dropdown menu on the static part of the profile page
# the 'if not' condition is checking whether the inventory is already downloaded

timestamps = [];

for stamp in stamp_html.find_all('option'):
    candidate_timestamp = stamp.get('value');
    if not (Path(f"invs/inv{candidate_timestamp}.json").exists()):
        timestamps.append(candidate_timestamp);

if (timestamps == [] and stamp_req.status_code != 200):
    print(f"failed to get timestamps, status code: {stamp_req.status_code}");
    with open("timestampdump.html", "w", encoding="utf-8") as timestampdump:
        timestampdump.write(stamp_html.prettify());
        print("saved failed timestamp scrape to timestampdump.html");
    timestampdump.close();
    quit();

elif (timestamps == [] and stamp_req.status_code == 200):
    print("all inventories have already been downloaded");

# get inventories from every timestamp collected

i_timestamp = 0;
for i_timestamp in range(i_timestamp, len(timestamps)):
    strange_list = [];
    url = "https://backpack.tf/_inventory/"+steamid64+"?time="+timestamps[i_timestamp]+"&source=steam&fallback=true";
    try:
        inv_req = requests.get(url, cookies=cookies, headers=headers);
        inv_json = json.loads(inv_req.text);
        inv_html = BeautifulSoup(inv_json["html"], "html.parser");
        print(f"({i_timestamp}) {inv_req.status_code} {inv_json["time"]}");

        # todo check if there's a file of the current inventory and continue; if there's one

    except Exception:
        print(f"({i_timestamp}) {inv_req.status_code} request failure at timestamp: {timestamps[i_timestamp]}, trying again");
        continue;

    # selects only strange bordered items from the inventory (so elevated quality items are also included)

    for strange_raw in inv_html.select(".q-440-border-11"):
        strange_list.append(strange_raw.attrs);

    # writes raw html inventories

    #with open(f"invs/inv{timestamps[i_timestamp]}.txt", "w", encoding="utf-8") as plik:
    #    plik.write(inv_html.prettify());
    #plik.close();

    # writes json inventories with only strange items

    with open(f"invs/inv{inv_json["time"]["timestamp"]}.json", "w", encoding="utf-8") as f_json_inv:
        prettyjson = json.dumps(strange_list, indent=4);
        json_changed_dashes = prettyjson.replace("\\u2013", "-");
        f_json_inv.write(json_changed_dashes);
    f_json_inv.close();
    i_timestamp += 1;