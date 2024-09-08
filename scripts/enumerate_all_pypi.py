# # #!/usr/bin/env python3

# import pip_api
# import requests
# from bs4 import BeautifulSoup

# response = requests.get("https://pypi.org/simple/")
# soup = BeautifulSoup(response.text, "html.parser")

# packages = [link.text for link in soup.find_all("a")]

# filterd_targets = [i for i in packages if 10 <= len(i) <= 40]
# print(f"Found {len(filterd_targets)} filtered packages.")

# filterd_targets = [i for i in filterd_targets if not i[0].isdigit()]
# print(f"Found {len(filterd_targets)} additionally filtered packages.")

# with open('target_packages', 'w') as fw:
#     for package in filterd_targets:
#         pip_api.install(pip_api)
#         fw.write(f"{package}\n")