# import pip_api
# def get_typing_supported_packages(package_names):
    # typing_supported = []
    
    # ctr = 0
    # for package in package_names:
    #     ctr += 1
    #     url = f"https://pypi.org/pypi/{package}/json"
    #     r = requests.get(url)

    #     if r.status_code == 200:
    #         data = r.json()
    #         print(data)
    #         for release in data["releases"].values():
    #             for file_info in release:
    #                 if "py.typed" in file_info["filename"] or file_info["filename"].endswith(".pyi"):
    #                     typing_supported.append(package)
    #                     print(f"[!!!] Found type supported package: {package}")
    #                     break
    #     else:
    #         print(f"#{ctr}: UNUSUAL status code from url: {url} | code: {r.status_code}")
    # return typing_supported

    # response = requests.get("https://pypi.org/simple/")
    # soup = BeautifulSoup(response.text, "html.parser")

    # packages = [link.text for link in soup.find_all("a")]
    # print(f"Found {len(packages)} packages.")

    # target_packages = get_typing_supported_packages(package_names=packages)    
    # print(f"Found {len(target_packages)} packages.")

    # with open('target_packages', 'w') as fw:
    #     for package in target_packages:
    #         fw.write(f"{package}\n")
    
    # with open('target_packages', 'r') as fp:
    #     packages_from_file = fp.readlines()
    
    # for package_name in packages_from_file:
    #     pip_api.install(package_name)
