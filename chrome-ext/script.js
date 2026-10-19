const BACKEND_URL = "http://localhost:8001"

document.getElementById("scrape-button").addEventListener("click", async () => {

	const status_div = document.getElementById("status-div");
	const progress_div = document.getElementById("progress-div");
	const steamid64 = document.getElementById("steam-id").value;
	status_div.innerText = "Pulling inventories...";

	try {
		progress_div.innerHTML = "";
		const db_timestamp_list_response = await fetch(`${BACKEND_URL}/api/get-existing-timestamps/${steamid64}`);
		db_timestamp_set = new Set((await db_timestamp_list_response.json()).timestamps);
		//The timestamps of all inventories are on the static part of backpack.tf page.

		const bp_static_page_response = await fetch(`https://backpack.tf/profiles/${steamid64}`);
		const bp_static_page = await bp_static_page_response.text();
		const parser = new DOMParser();
		const staticpage = parser.parseFromString(bp_static_page, 'text/html');
		const raw_timestamp_list = staticpage.querySelector("select#historicalview");
		const bp_timestamp_list = Array.from(raw_timestamp_list.options).map(option => Number(option.value));

		// Timestamps of invs we want to download are in the bp timestamp list and not in db timestamp set.
		timestamps = bp_timestamp_list.filter((timestamp) => {
			return (!db_timestamp_set.has(timestamp));
		});
		for(let i = 0; i < timestamps.length; i++){
			let date = new Date(timestamps[i] * 1000);

			const response = await fetch(`https://backpack.tf/_inventory/${steamid64}?time=${timestamps[i]}&source=steam&fallback=true`);
			if(response.ok){
				response_json = await response.json();
				
				progress_div.innerHTML += `<div id="progress-box-${i}">(${i+1}/${timestamps.length})
				Inventory from ${date.getDate()}-${date.getMonth()}-${date.getFullYear()}
				Trying to send...</div>`;
			}
			else{
				progress_div.innerHTML += `<div id="progress-box-${i}">(${i+1}/${timestamps.length})
				Inventory from ${date.getDate()}-${date.getMonth()}-${date.getFullYear()}
				Server error: ${response.status}, trying the next one
				</div>`;
				continue;
				console.log("THIS SHIT SHOULD NEVER SHOW UP");
			}

			const current_div = document.getElementById(`progress-box-${i}`);

			const upload_response = await fetch(`${BACKEND_URL}/api/upload-inventory`, {
				method: "POST",
				headers: {"Content-Type": "application/json"},
				body: JSON.stringify({
					"steamid64": steamid64,
					"inv_json": response_json
				})
			});
			const upload_result = await upload_response.json();
			current_div.innerHTML += `<br>${upload_result.message}`;

			progress_div.scrollTop = progress_div.scrollHeight;
		}
		
	}catch(err){
		status_div.innerText = "Error: " + err.message;
	}
});