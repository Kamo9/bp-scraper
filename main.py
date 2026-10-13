import models
from database import engine, Base, get_db, session

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
import requests
import json

class Browser_data(BaseModel):
	cookies: dict;
	useragent: str;

Base.metadata.create_all(bind=engine);

app = FastAPI(title="Strange stats");

app.mount("/static", StaticFiles(directory="static"), name="static");

templates = Jinja2Templates(directory="templates");

user_data = {};

@app.post("/api/session")
async def save_session(data: Browser_data):
	user_data["cookies"] = data.cookies;
	user_data["useragent"] = data.useragent;
	return {
		"status": "success",
		"message": "Cookies saved."
	}
@app.get("/api/pull-inventories")
async def pull_inventories(db: session = Depends(get_db)):

	if("cookies" not in user_data):
		raise HTTPException(status_code=400, detail="No cookies saved, use the extension to pull cookies first.");

	headers = {
		"User-Agent": user_data["useragent"]
	};

	steamid64 = user_data["cookies"]["stack[user]"];
	# timestamps for all possible downloadable inventories are stored in the dropdown on the static part of the user's backpack page
	scraped_timestamps = [];
	stamp_url = "https://backpack.tf/profiles/"+steamid64;
	stamp_req = requests.get(stamp_url, headers=headers, cookies=user_data["cookies"]);
	stamp_soup = BeautifulSoup(stamp_req.text, "html.parser");
	for stamp in stamp_soup.find_all("option"):
		scraped_timestamps.append(stamp.get("value"));

	for saved_stamp in (db.query(models.StrangeWeapon.timestamp).filter(models.StrangeWeapon.steamid == steamid64).distinct().all()): # query to get existing timestamps
		stamp_clean = str(saved_stamp[0]);
		try:
			scraped_timestamps.remove(stamp_clean);
		except ValueError: # only happens for the inventories pulled using the "Most Recent" timestamp (no timestamp value) in the dropdown.
			continue;

	i_timestamp = 0;
	for i_timestamp in range(i_timestamp, len(scraped_timestamps)):
		current_timestamp_by_scraped_timestamps = scraped_timestamps[i_timestamp];

		inv_url = f"https://backpack.tf/_inventory/{steamid64}?time={current_timestamp_by_scraped_timestamps}&source=steam&fallback=true";

		try:
			inv_req = requests.get(inv_url, cookies=user_data["cookies"], headers=headers);
			inv_req.raise_for_status();
			inv_json = json.loads(inv_req.text);
			current_timestamp_actual = inv_json["time"]["timestamp"];
			inv_soup = BeautifulSoup(inv_json["html"], "html.parser");
			stranges_in_inv = {};
			for strange_raw in inv_soup.select(".q-440-border-11"):
				strange_string = strange_raw.attrs["data-ke1"].split(" ");
				strange_weapon = models.StrangeWeapon(
						steamid = steamid64,
						timestamp = current_timestamp_actual,
						original_id = strange_raw.attrs.get("data-original_id"),
						name = strange_raw.attrs["title"],
						strange_count_name = " ".join(strange_string[1:]),
						strange_count = int(strange_string[0].replace(",","")),
						part1_name = strange_raw.attrs.get("data-part_name_1"), 
						part1_count = int(strange_raw.attrs.get("data-part_score_1", "0").replace(",", "")),
						part2_name = strange_raw.attrs.get("data-part_name_2"), 
						part2_count = int(strange_raw.attrs.get("data-part_score_2", "0").replace(",", "")),
						part3_name = strange_raw.attrs.get("data-part_name_3"), 
						part3_count = int(strange_raw.attrs.get("data-part_score_3", "0").replace(",", "")),
					);
				db.add(strange_weapon);
				db.commit();
				db.refresh(strange_weapon);

		except requests.exceptions.HTTPError as e:
			continue;

		except IntegrityError as e:
			db.rollback();
			print(f"Unique constraint prevented the insertion, info: {e}");	
			continue;
			
		except Exception as e:
			db.rollback();
			return{
				"message": f"failure: {e}"
			}
	return {
		"message": "ok, check db"
	}
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	return templates.TemplateResponse(request, "index.html");