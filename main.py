import models
from database import engine, Base, get_db, session

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import requests
import json
from lxml import etree

Base.metadata.create_all(bind=engine);

app = FastAPI(title="bp-scraper");

app.mount("/static", StaticFiles(directory="static"), name="static");

templates = Jinja2Templates(directory="templates");

@app.get("/api/get-existing-timestamps/{steamid64}")
async def get_existing_timestamps(steamid64: str, db: session = Depends(get_db)):
	try:
		query = text("SELECT DISTINCT timestamp from weapons where steamid = :steamid64");
		query_result = db.execute(query, {"steamid64": steamid64});
		timestamps = set([row[0] for row in query_result]);

		return{
			"status": "success",
			"steamid64": steamid64,
			"timestamps": timestamps
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve existing timestamps from db. {e}");

@app.post("/api/upload-inventory")
async def upload_inventory(payload: dict, db: session = Depends(get_db)):
	steamid64 = payload.get("steamid64");
	inv_json = payload.get("inv_json");
	inv_real_timestamp = inv_json["time"]["timestamp"];
	inv_soup = BeautifulSoup(inv_json["html"], "lxml");
	for strange_raw in inv_soup.select(".q-440-border-11"):
			strange_string = strange_raw.attrs["data-ke1"].split(" ");
			strange_weapon = models.StrangeWeapon(
					steamid = steamid64,
					timestamp = inv_real_timestamp,
					original_id = strange_raw.attrs.get("data-original_id"),
					name = strange_raw.attrs["title"],
					strange_count_name = " ".join(strange_string[1:]),
					strange_count = int(strange_string[0].replace(",","")),
					part1_name = strange_raw.attrs.get("data-part_name_1"), 
					part1_count = int(strange_raw.attrs.get("data-part_score_1", "0").replace(",", "")) if part1_name else None,
					part2_name = strange_raw.attrs.get("data-part_name_2"), 
					part2_count = int(strange_raw.attrs.get("data-part_score_2", "0").replace(",", "")) if part2_name else None,
					part3_name = strange_raw.attrs.get("data-part_name_3"), 
					part3_count = int(strange_raw.attrs.get("data-part_score_3", "0").replace(",", "")) if part3_name else None,
				);
			try:
				db.add(strange_weapon);
				db.commit();
				db.refresh(strange_weapon);
			except IntegrityError as e:
				db.rollback();
				return{
					"status": "error",
					"message": "Inventory already in database."
				}
			except Exception as e:
				db.rollback();
				return{
					"status": "error",
					"message": f"Failure: {e}"
				}
	return{
		"status": "success",
		"message": "Successfully added."
	};
@app.get("/api/fetch-user-items/{steamid64}")
async def fetch_user_items(steamid64: str, db: session = Depends(get_db)):
	query = text("""
		SELECT distinct original_id, name 
		FROM weapons 
		WHERE steamid = :steamid64 
		AND timestamp = (select timestamp from weapons where steamid = :steamid64 order by timestamp desc limit 1)
		""");
	query_result = db.execute(query, {"steamid64": steamid64});
	dict_result = {};
	for row in query_result:
		dict_result[row[0]] = row[1];

	json_result = json.dumps(dict_result);
	return{
		"status": "success",
		"items": dict_result
	}

@app.get("/api/fetch-item-data/{original_id}")
async def fetch_item_data(original_id: str, steamid64: str, db: session = Depends(get_db)):
	query = text("""
			SELECT timestamp, name, strange_count, strange_count_name, part1_count, part1_name, part2_count, part2_name, part3_count, part3_name
			FROM weapons
			WHERE steamid = :steamid64
			AND original_id = :original_id
		""");
	query_result = db.execute(query, {"steamid64": steamid64, "original_id": original_id});
	dict_result = {};
	for row in query_result:
		dict_result[row[0]] = [x for x in row[1:]];
	return{
		"status": "success",
		"item_data": dict_result
	}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	return templates.TemplateResponse(request, "index.html");