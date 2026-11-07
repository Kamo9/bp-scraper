const BACKEND_URL = "http://localhost:8001";
let steamid64 = ""; //yes this is needed because when i pass it between functions it for some reason changes to a number and gets rounded
const item_charts = {};
const chart_contexts = {};

function show_extension(){
	document.getElementById("content-extension").classList.remove("hide");
	document.getElementById("content-display").classList.add("hide");
	document.getElementById("content-home").classList.add("hide");
}
function show_home(){
	document.getElementById("content-home").classList.remove("hide");
	document.getElementById("content-display").classList.add("hide");
	document.getElementById("content-extension").classList.add("hide");
}
function show_display(){
	document.getElementById("content-display").classList.remove("hide");
	document.getElementById("content-home").classList.add("hide");
	document.getElementById("content-extension").classList.add("hide");
}
//-- on item button click
async function display_data_for_item(original_id){
	const chart_container = document.getElementById("right-section-charts");
	const current_item_data_box = document.getElementById(`item-data-${original_id}`);
	const current_item_button = document.getElementById(`item-button-${original_id}`);

	if(current_item_data_box){ // toggling visibility of box on button click
		if(current_item_data_box.classList.contains("hide")){
			current_item_data_box.classList.remove("hide");
			current_item_button.classList.add("active-item-button");
		}else{
			current_item_data_box.classList.add("hide");
			current_item_button.classList.remove("active-item-button");
		}
	}else{
		const item_data_response = await fetch(`${BACKEND_URL}/api/fetch-item-data/${original_id}/${steamid64}`);

		const item_data_json = await item_data_response.json();

		const item_data_map = new Map(Object.entries(item_data_json.item_data));

		marker_lists = {
			item_name: item_data_json.marker_lists.name,
			custom_name: item_data_json.marker_lists.custom_name,
			custom_desc: item_data_json.marker_lists.custom_desc,
			part1_name: item_data_json.marker_lists.part1_name,
			part2_name: item_data_json.marker_lists.part2_name,
			part3_name: item_data_json.marker_lists.part3_name
		};

		const latest_timestamp = Array.from(item_data_map.keys()).pop(); // for the "Current stats:"

		current_item_button.classList.add("active-item-button");

		chart_container.insertAdjacentHTML("beforeend", 
			`<div class="item-data-box" id="item-data-${original_id}" onauxclick="display_data_for_item(${original_id})">
			<a href="https://backpack.tf/item/${original_id}" class="greenbutton bp-history-button" target="_blank">backpack.tf history link</a>
			<h3>${item_data_map.get(latest_timestamp)[0]}</h3>
			<p>Current stats: ${item_data_map.get(latest_timestamp).slice(1).join(" ")}</p>
			<canvas class="item-canvas" id="item-canvas-${original_id}"></canvas>
			</div>`
			);

		
		chart_contexts[original_id] = document.getElementById(`item-canvas-${original_id}`).getContext("2d");

		const chart_x = Array.from(item_data_map.keys()).map(timestamp => timestamp * 1000);

		const value_array = Array.from(item_data_map.values());

		const chart_main_stat = value_array.map(x => x[1]);
		const chart_part1 = value_array.map(x => x[3]);
		const chart_part2 = value_array.map(x => x[5]);
		const chart_part3 = value_array.map(x => x[7]);

		const all_datasets = [{
						data: chart_main_stat,
						label: `${item_data_map.get(latest_timestamp)[2]}`,
						backgroundColor: "#2A459A",
						borderColor: "#2A459A",
						color: "#000000",
						borderWidth: 2,
						tension: 0.1
					},
					{
						data: chart_part1,
						label: `${item_data_map.get(latest_timestamp)[4]}`,
						backgroundColor: "#81ADD5",
						borderColor: "#81ADD5",
						color: "#000000"
					},
					{
						data: chart_part2,
						label: `${item_data_map.get(latest_timestamp)[6]}`,
						backgroundColor: "#E56767",
						borderColor: "#E56767",
						color: "#000000"
					},
					{
						data: chart_part3,
						label: `${item_data_map.get(latest_timestamp)[8]}`,
						backgroundColor: "#B2F49D",
						borderColor: "#B2F49D",
						color: "#000000"
					}
					];
		const chart_datasets = all_datasets.filter(dataset => dataset && dataset.data.some(val => val !== null && val !== undefined));

		const marker_configs = {};

		marker_lists["item_name"].forEach((marker, index) => {
			const marker_key = `marker_item_name${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#FFFFFF",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Name change: ${marker.name}`,
					yAdjust: -50,
					backgroundColor: "rgba(0,0,0,0.6)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		marker_lists["custom_name"].forEach((marker, index) => {
			const marker_key = `marker_custom_name${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#EBBBE4",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Custom name change: ${marker.name}`,
					color: "#EBBBE4",
					yAdjust: -50,
					backgroundColor: "rgba(0,0,0,0.6)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		marker_lists["custom_desc"].forEach((marker, index) => {
			const marker_key = `marker_custom_desc${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#40CDC4",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Custom desc change: ${marker.name}`,
					color: "#40CDC4",
					yAdjust: -50,
					backgroundColor: "rgba(0,0,0,0.6)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		marker_lists["part1_name"].forEach((marker, index) => {
			const marker_key = `marker_part1_name${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#81ADD5",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Strange part 1 change: ${marker.name}`,
					color: "#81ADD5",
					yAdjust: -50,
					backgroundColor: "rgba(0,0,0,0.6)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		marker_lists["part2_name"].forEach((marker, index) => {
			const marker_key = `marker_part2_name${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#E56767",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Strange part 2 change: ${marker.name}`,
					color: "#E56767",
					yAdjust: -50,
					backgroundColor: "rgba(245,245,245,0)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		marker_lists["part3_name"].forEach((marker, index) => {
			const marker_key = `part3_name${index}`;
			marker_configs[marker_key] = {
				type: "line",
				borderWidth: 3,
				borderColor: "#B2F49D",
				scaleID : "x",
				value: marker.timestamp * 1000,
				label: {
					display: false,
					content: `Strange part 3 change: ${marker.name}`,
					color: "#B2F49D",
					yAdjust: -50,
					backgroundColor: "rgba(245,245,245,0)",
					font:{
						size: 10
					}
				},
				enter({chart}){
			        chart.options.plugins.annotation.annotations[marker_key].label.display = true;
			        chart.update('none');
			    },
			    leave({chart}) {
			        chart.options.plugins.annotation.annotations[marker_key].label.display = false;
			        chart.update('none');
			    }
			}
		});
		item_charts[original_id] = new Chart(chart_contexts[original_id], {
				type: "line",
				data: {
					labels: chart_x,
					datasets: chart_datasets
				},
				options:{
					scales: {
						y: {
							beginAtZero: true,
						},
						x: {
							type: "time",
							time: {
								displayFormats: {
									day: "dd-MM-yyyy"
								},
								tooltipFormat: "dd-MM-yyyy"
							},
						}
					},
					responsive: true,
					maintainAspectRatio: true,
					aspectRatio: 3.6|1,
					elements: {
						point: {
							radius: 2
						}
					},
					plugins:{
						annotation:{
							annotations: marker_configs
						}
					}
				}
			});
	}
}
//-- on "show your data" button click
document.getElementById("get-data").addEventListener("click", async () => {
	steamid64 = document.getElementById("steamid").value;
	const item_container = document.getElementById("item-buttons-container");
	const latest_checkbox_status = document.getElementById("latest-inv-checkbox").checked

	item_container.innerHTML = "";

	items_response = await fetch(`${BACKEND_URL}/api/fetch-user-items/${steamid64}?latest=${latest_checkbox_status}`);
	items_json = (await items_response.json()).items;

	items_map = new Map(Object.entries(items_json));

	items_map.forEach((value, key) => {
		item_container.insertAdjacentHTML("beforeend", `<button onclick="display_data_for_item(${key})"  style="${value[1]}" class="item-button" id="item-button-${key}">${value[0]}</button>`);
	})
});
//-- on "filter by name" button click
document.getElementById("filter-button").addEventListener("click", () => {
	const filter_by = document.getElementById("filter-text-field").value.toLowerCase();
	const buttons_container = document.getElementById("item-buttons-container");
	for(let i = 0; buttons_container.childNodes[i-1] != buttons_container.lastChild; i++){
		buttons_container.childNodes[i].classList.remove("hide");
		if(buttons_container.childNodes[i].innerText.toLowerCase().includes(filter_by)){
			buttons_container.childNodes[i].classList.remove("hide");
		}else{
			buttons_container.childNodes[i].classList.add("hide");
		}
	}
});