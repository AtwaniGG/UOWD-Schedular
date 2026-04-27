import json


def convert(input_path: str = "cookies.txt", output_path: str = "chrome_cookies.json") -> int:
    cookies = []
    with open(input_path, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) < 7:
                continue
            domain, _, path, secure, expiry, name, value = parts[:7]
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": int(expiry) if expiry != "0" else -1,
                "httpOnly": False,
                "secure": secure.lower() == "true",
                "sameSite": "Lax",
            })

    with open(output_path, "w") as f:
        json.dump(cookies, f, indent=2)

    return len(cookies)


if __name__ == "__main__":
    n = convert()
    print(f"Cookies converted and saved to chrome_cookies.json ({n} entries)")
