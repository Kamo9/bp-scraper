from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
from pydantic import BaseModel
import requests
import json

class Browser_data(BaseModel):
	cookies: dict;
	useragent: str;

app = FastAPI(title="Strange stats");

user_data = {};

@app.post("/api/session")
async def save_session(data: Browser_data):
	user_data["cookies"] = data.cookies;
	user_data["useragent"] = data.useragent;
	return {
		"status": "success",
		"message": "Cookies saved."
	}
@app.get("/api/inventory")
async def get_inventory():
	if("cookies" not in user_data):
		raise HTTPException(status_code=400, detail="No cookies saved, use the extension to pull cookies first.");
	headers = {
		"User-Agent": user_data["useragent"]
	};

	steamid64 = user_data["cookies"]["stack[user]"];
	timestamps = [];
	saved_inventories = {};

	stamp_url = "https://backpack.tf/profiles/"+steamid64;
	stamp_req = requests.get(stamp_url, headers=headers, cookies=user_data["cookies"]);
	stamp_soup = BeautifulSoup(stamp_req.text, "html.parser");
	for stamp in stamp_soup.find_all("option"):
		timestamps.append(stamp.get("value"));

	i_timestamp = 0;
	for i_timestamp in range(i_timestamp, 2):
		inv_url = "https://backpack.tf/_inventory/"+steamid64+"?time="+timestamps[i_timestamp]+"&source=steam&fallback=true";
		try:
			inv_req = requests.get(inv_url, cookies=user_data["cookies"], headers=headers);
			inv_json = json.loads(inv_req.text);
			inv_soup = BeautifulSoup(inv_json["html"], "html.parser");
			stranges_in_inv = {};
			for strange_raw in inv_soup.select(".q-440-border-11"):
				strange_string = strange_raw.attrs["data-ke1"].split(" ");
				strange_weapon = {																	#short names to save space
				"n": strange_raw.attrs["title"], 													#n - name
				"str_c": int(strange_string[0].replace(",","")),									#str_c - strange count
				"str_c_n": " ".join(strange_string[1:]),											#stc_c_n - strange count name
				"p1_n": strange_raw.attrs.get("data-part_name_1"), 									#part 1 name
				"p1_c": int(strange_raw.attrs.get("data-part_score_1", "0").replace(",", "")),		#part 2 count
				"p2_n": strange_raw.attrs.get("data-part_name_2"),									#etc..
				"p2_c": int(strange_raw.attrs.get("data-part_score_2", "0").replace(",", "")),
				"p3_n": strange_raw.attrs.get("data-part_name_3"),
				"p3_c": int(strange_raw.attrs.get("data-part_score_3", "0").replace(",", ""))
				};
				stranges_in_inv[strange_raw.attrs["data-original_id"]] = strange_weapon;
			saved_inventories[timestamps[i_timestamp]] = stranges_in_inv;
			
		except Exception as e:
			return{
				"message": f"failure: {e}"
			}
	return {
		"message": saved_inventories
	}
@app.get("/")
async def home():
	return {
		"message": "Hi bro"
	};