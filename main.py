import models
from database import engine, Base, get_db, session

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import json
from lxml import etree

Base.metadata.create_all(bind=engine);

app = FastAPI(title="bp-scraper");

app.mount("/static", StaticFiles(directory="static"), name="static");

templates = Jinja2Templates(directory="templates");

@app.get("/api/get-existing-timestamps/{steamid64}")
async def get_existing_timestamps(steamid64: str, db: session = Depends(get_db)):
	query = text("SELECT DISTINCT timestamp from weapons where steamid = :steamid64");
	try:
		query_result = db.execute(query, {"steamid64": steamid64});
		timestamps = set([row[0] for row in query_result]);

		return{
			"status": "success",
			"steamid64": steamid64,
			"timestamps": timestamps
		}
	except Exception as e:
		return{
			"status": "error",
			"message": f"Failure: {e}"
				}

@app.post("/api/upload-inventory")
async def upload_inventory(payload: dict, db: session = Depends(get_db)):
	# to not put excess weapon urls in the database. Pull existing first, if the current weapon's original_id is not in the table, add it.
	original_id_query = text("SELECT DISTINCT original_id FROM weapon_images");
	try:
		original_id_query_result = db.execute(original_id_query);
	except Exception as e:
		return{
			"status": "error",
			"message": f"Databsase failure: {e}"
		}
	existing_original_ids_in_url_table = [row[0] for row in original_id_query_result];

	steamid64 = payload.get("steamid64");
	inv_json = payload.get("inv_json");
	inv_real_timestamp = inv_json["time"]["timestamp"];
	inv_soup = BeautifulSoup(inv_json["html"], "lxml");
	for strange_raw in inv_soup.select(".q-440-border-11"):
			original_id = strange_raw.attrs.get("data-original_id");
			strange_string = strange_raw.attrs["data-ke1"].split(" ");
			strange_weapon = models.StrangeWeapon(
					steamid = steamid64,
					timestamp = inv_real_timestamp,
					original_id = original_id,
					name = strange_raw.attrs["title"],
					strange_count_name = " ".join(strange_string[1:]),
					strange_count = int(strange_string[0].replace(",","")),
					part1_name = strange_raw.attrs.get("data-part_name_1"), 
					part1_count = int(strange_raw.attrs.get("data-part_score_1", "0").replace(",", "")) if strange_raw.attrs.get("data-part_name_1") else None,
					part2_name = strange_raw.attrs.get("data-part_name_2"), 
					part2_count = int(strange_raw.attrs.get("data-part_score_2", "0").replace(",", "")) if strange_raw.attrs.get("data-part_name_2") else None,
					part3_name = strange_raw.attrs.get("data-part_name_3"), 
					part3_count = int(strange_raw.attrs.get("data-part_score_3", "0").replace(",", "")) if strange_raw.attrs.get("data-part_name_3") else None,
					custom_name = strange_raw.attrs.get("data-custom_name"),
					custom_desc = strange_raw.attrs.get("data-custom_desc")
				);
			if(original_id not in existing_original_ids_in_url_table):
				strange_image = models.WeaponImages(
					original_id = strange_raw.attrs.get("data-original_id"),
					url = strange_raw.contents[1].attrs["style"],
					)
				try:
					db.add(strange_image)
					db.commit();
					db.refresh(strange_image);
				except IntegrityError as e:
					db.rollback();
					return{
						"status": "error",
						"message": "Weapon url already in database."
					}
				except Exception as e:
					db.rollback();
					return{
						"status": "error",
						"message": f"Failure: {e}"
					}
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
async def fetch_user_items(steamid64: str, db: session = Depends(get_db), latest: bool | None = None):
	if(latest):
		query = text("""
			SELECT distinct w.original_id, w.name, wi.url, strange_count
			FROM weapons w
			LEFT JOIN weapon_images wi
			ON w.original_id = wi.original_id
			WHERE steamid = :steamid64 
			AND timestamp = (select timestamp from weapons where steamid = :steamid64 order by timestamp desc limit 1)
			ORDER BY strange_count DESC
			""");
	else:
		query = text("""
			SELECT w.original_id, max(w.name), max(wi.url), max(strange_count)
			FROM weapons w
			LEFT JOIN weapon_images wi
			ON w.original_id = wi.original_id
			WHERE steamid = :steamid64 
			GROUP BY w.original_id
			HAVING max(strange_count) > 50
			ORDER BY max(strange_count) DESC
			""");
	
	try:
		query_result = db.execute(query, {"steamid64": steamid64});

		dict_result = {};
		for row in query_result:
			dict_result[row[0]] = (row[1],row[2]);

		return{
			"status": "success",
			"items": dict_result
		}
	except Exception as e:
		return{
			"status": "error",
			"details": f"Server failure: {e}"
		}


@app.get("/api/fetch-item-data/{original_id}/{steamid64}")
async def fetch_item_data(original_id: str, steamid64: str, db: session = Depends(get_db)):
	items_query = text("""
				SELECT timestamp, name, strange_count, strange_count_name, part1_count, part1_name, part2_count, part2_name, part3_count, part3_name
				FROM weapons
				WHERE steamid = :steamid64
				AND original_id = :original_id
				ORDER BY timestamp ASC
		""");
	try:
		items_query_result = db.execute(items_query, {"steamid64": steamid64, "original_id": original_id});

		items_dict_result = {};
		for row in items_query_result:
			items_dict_result[row[0]] = [x for x in row[1:]];

		marker_items = ["name", "custom_name", "custom_desc", "part1_name", "part2_name", "part3_name"];
		marker_lists = {};
		for marker_item in marker_items:
			query = text(f"""
			SELECT min(timestamp), {marker_item}
			FROM weapons 
			WHERE steamid = :steamid64
			AND original_id = :original_id
			GROUP BY {marker_item}
			ORDER BY min(timestamp) asc
			OFFSET 1
			""");
			query_result = db.execute(query, {"steamid64": steamid64, "original_id": original_id});
			marker_lists[marker_item] = [{"timestamp": row[0], "name": row[1]} for row in query_result];

		return{
			"status": "success",
			"item_data": items_dict_result,
			"marker_lists": marker_lists

		}
	except Exception as e:
		return{
			"status": "error",
			"details": f"Server failure: {e}"
		}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
	return templates.TemplateResponse(request, "index.html");