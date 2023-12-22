import requests
import json
import os
import multiprocessing as mp
import lzma
import pickle
import const
import get_pr_links


def collect_metadata(url, filepath, readin=False):
    """
    # this is for PR and build metadata
    url to request the data
    filename to write and store the requested data
    readin = True means returning requested or stored data
    """
    info = {}
    if not os.path.exists(filepath):
        print(f"REQUESTING {url}")
        try:
            html_response = requests.get(url=url, headers=const.GENERAL_HEADERS)
            info = json.loads(html_response.text)
            with open(filepath, "w") as outf:
                json.dump(info, outf, indent=2)
            print(filepath, "collected")
        except Exception as e:
            print(f"ERROR GETTING {url}")
    else:
        if readin:
            info = json.load(open(filepath))
    return info


def collect_testdata(url, filepath):
    """
    # this is for testdata, REQUIRE COMPRESSING
    url to request the data
    filename to write and store the requested data
    """
    if not os.path.exists(filepath) and not os.path.exists(filepath+".zip"):
        print(f"REQUESTING {url}")
        try:
            html_response = requests.get(url=url, headers=const.GENERAL_HEADERS, timeout=30)
            info = json.loads(html_response.text)
            with open(filepath, "w") as outf:
                json.dump(info, outf, indent=2)
            print(filepath, "collected")
        except Exception as e:
            print(f"ERROR GETTING {url}")
            # utility.record_failed_attempt(url, filepath)


def compress_testdata(filepath):
    if  os.path.exists(filepath) and not os.path.exists(filepath+".zip"):
        print("COMPRESSING ", filepath)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        dest_dir = os.path.dirname(filepath)
        zip_name = os.path.basename(filepath)
        os.chdir(dest_dir)
        os.system(f"zip {zip_name}.zip {zip_name}")
        os.system(f"rm {zip_name}")
        os.chdir(current_dir)


def collect_console_output(console_file, console_query_url, overwrite=False):
    if not os.path.exists(console_file) or overwrite:
        print("REQUESTING", console_query_url)
        try:
            html_response = requests.get(url=console_query_url, headers=const.GENERAL_HEADERS, timeout=30)
            if html_response.status_code == requests.codes.ok:
                with lzma.open(console_file, "wb") as outf:
                    pickle.dump(html_response.text, outf)
                print(console_file, "collected")
            else:
                print(f"ERROR GETTING {console_query_url}")
        except:
            print(f"ERROR GETTING {console_query_url}")

def get_pr_data(project, pr, pr_url):
    # create per pr folder on testdata
    prdir = os.path.join(const.testdir, project, "PR", pr)
    os.makedirs(prdir, exist_ok=True)

    # get pr meta infomation
    meta_query_url = pr_url+"api/json"
    meta_file = f"{prdir}/meta.json"
    info = collect_metadata(meta_query_url, meta_file, readin=True)

    # get all the build info of this PR if the link valid
    if len(info) > 0 and "builds" in info:
        build_urls = [[x["number"], x["url"]] for x in info["builds"]]
        # get build level infomation
        for build_number, build_url in build_urls:
            print("\nPROCESSING ", build_url)
            build_query_url = build_url + "api/json"
            build_file = f"{prdir}/build{build_number}.json"
            build_info = collect_metadata(build_query_url, build_file, readin=True)

            # collect both failed and successful build (successful build is for transition features)
            # only collect test data if there is test result for this build
            if len(build_info) > 0 and "actions" in build_info:
                for action in build_info["actions"]:
                    if "urlName" in action and action["urlName"] == "testReport":
                        # if "failCount" in action and action["failCount"] > 0:
                        test_query_url = build_url + "testReport/api/json"
                        test_file = f"{prdir}/testReport_build{build_number}.json"
                        collect_testdata(test_query_url, test_file)
                        compress_testdata(test_file)
        
                        # get raw console output so that we can get the trunk sha this build is based on
                        console_file = f"{prdir}/console_build{build_number}.txt.xz"
                        console_query_url = build_url + "consoleText"
                        collect_console_output(console_file, console_query_url)
    

def get_pr_for_project(project, parallel=True):
    # create PR dir for each project
    prdir = os.path.join(const.testdir, project, "PR")
    os.makedirs(prdir, exist_ok=True)

    prs = get_pr_links.get_all_prs(project)
    
    if parallel:
        pool = mp.Pool(mp.cpu_count())
        pool.starmap(get_pr_data, [(project, name, url) for name, url in prs.items()])
    else:
        for name, url in prs.items():
            get_pr_data(project, name, url)


if __name__ == "__main__":
    for project in const.PROJECTS:
        get_pr_for_project(project, parallel=True)
    pass