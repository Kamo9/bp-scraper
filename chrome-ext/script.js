    const TARGET_DOMAIN = ".backpack.tf";
    const PARTITION_KEY_SITE = "https://backpack.tf";
    const BACKEND_URL = "http://localhost:8001/api/session";

    document.getElementById("pullbutton").addEventListener("click", async () => {
      const status_div = document.getElementById("status");
      status_div.innerText = "Pulling cookies...";

      try {
        const cookies = await chrome.cookies.getAll({ domain: TARGET_DOMAIN });
        let partitioned_cookies = [];
        try{
          partitioned_cookies = await chrome.cookies.getAll({ 
            url: "https://" + TARGET_DOMAIN, 
            partitionKey:{
              topLevelSite: PARTITION_KEY_SITE
            }
          })
        } catch (err){
          console.warn("Browser doesn't support partitioned cookies", err);
        }
        
        const cookie_map = {};
        cookies.forEach(c => cookie_map[c.name] = c.value);
        partitioned_cookies.forEach(c => cookie_map[c.name] = c.value);

        const user_agent = navigator.userAgent;

        const response = await fetch(BACKEND_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cookies: cookie_map,
            useragent: user_agent
          })
        });

        if (response.ok) {
          status_div.innerText = " Cookies properly pulled.";
        } else {
          status_div.innerText = " Server error: " + response.status;
        }
      } catch (err) {
        status_div.innerText = " Error: " + err.message;
      }
    });