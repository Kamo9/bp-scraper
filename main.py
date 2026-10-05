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
		raise HTTPException(status_code=400, detail="No cookies saved, user the extension to pull cookies.");
	headers = {
		"User-Agent": user_data["useragent"]
	};

	timestamps = [];
	stamp_url = "https://backpack.tf/profiles/"+user_data["cookies"]["stack[user]"];
	stamp_req = requests.get(stamp_url, headers=headers, cookies=user_data["cookies"]);
	stamp_soup = BeautifulSoup(stamp_req.text, "html.parser");
	for stamp in stamp_soup.find_all("option"):
		timestamps.append(stamp.get("value"));

	return {
		"message": timestamps
	}
@app.get("/")
async def home():
	return {
		"message": "Hello bro"
	};