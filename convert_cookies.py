from http.cookies import SimpleCookie
import json

input_file = "cookies.txt"       # your exported file
output_file = "chrome_cookies.json"

cookies = []
with open(input_file, "r") as f:
    for line in f:
        if not line.startswith("#") and line.strip():
            domain, _, path, secure, expiry, name, value = line.strip().split("\t")
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": int(expiry) if expiry != "0" else -1,
                "httpOnly": False,
                "secure": secure.lower() == "true",
                "sameSite": "Lax"
            })

with open(output_file, "w") as f:
    json.dump(cookies, f, indent=2)

print(f"Cookies converted and saved to {output_file}")
