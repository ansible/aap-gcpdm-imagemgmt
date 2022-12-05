import os
import json
from io import StringIO
import sys
import base64


def env_set(env_var, default):
    if env_var in os.environ:
        return os.environ[env_var]
    elif os.path.exists(env_var) and os.path.getsize(env_var) > 0:
        with open(env_var, "r") as env_file:
            var = env_file.read().strip()
            env_file.close()
        return var
    else:
        return default


def gatherAssets(snapshot_path, snapshot_date):
    return_code = False
    resource_map = {}
    image_name = ""
    for dirname in next(os.walk(snapshot_path))[1]:
        object_storage = ""
        account_copied_to = ""
        account_destined_for = ""
        try:
            full_path="{}/{}/gcp-machine-image-manifest.json".format(snapshot_path,dirname)
            with open(full_path, "r") as a_file:
                resource_text = a_file.read()
                resource_map = json.loads(resource_text)
                image_name = resource_map["builds"][0]["artifact_id"]
            # print("full_path: {}".format(full_path))
        except:
            try:
                full_path="{}/{}/gcp-machine-image-manifest_{}.json".format(snapshot_path,dirname,snapshot_date)
                with open(full_path, "r") as a_file:
                    resource_text = a_file.read()
                    resource_map = json.loads(resource_text)
                    image_name = resource_map["builds"][0]["artifact_id"]
                # print("full_path: {}".format(full_path))
            except:
                print("Didn't find the image created in {}/{}!".format(snapshot_path,dirname))
        try:
            full_path="{}/{}/gcp_project_id.txt".format(snapshot_path,dirname)
            with open(full_path, "r") as a_file:
                account_copied_to = a_file.read().strip()
            # print("    sub-build {} account copied to: {}".format(dirname,account_copied_to))
        except:
            account_copied_to = 'gc-ansible-cloud'
            print("Didn't find the gcp project stuff for sub-build {}, assuming '{}'".format(dirname,account_copied_to))
        try:
            full_path="{}/{}/destination_project_id.txt".format(snapshot_path,dirname)
            with open(full_path, "r") as a_file:
                account_destined_for = a_file.read().strip()
            # print("account destined for: {}".format(account_destined_for))
        except:
            print("Didn't find the destination gcp project ID for sub-build {}, assuming {}".format(dirname,account_copied_to))
            account_destined_for = account_copied_to
        try:
            full_path="{}/{}/object-storage.out".format(snapshot_path,dirname)
            with open(full_path, "r") as a_file:
                object_storage = a_file.read().strip()
            # print("account destined for: {}".format(account_destined_for))
        except:
            print("No object storage exists for sub-build {}.".format(dirname));
        if (account_destined_for != account_copied_to) & (image_name != ""):
            print("Copying sub-build {} image {} to {} since account_destined_for is {} and account_copied_to is {}.".format(dirname,image_name, account_destined_for,account_copied_to,account_destined_for))
        if (account_destined_for != account_copied_to) & (object_storage != ""):
            print("Copying sub-build {} zip   {} to {}".format(dirname,object_storage, account_destined_for))
        return_code = True
    return return_code


def main():

    # Reorient stdout to a string so we can capture it
    tmp_stdout = sys.stdout
    string_stdout = StringIO()
    sys.stdout = string_stdout

    # Assumes a credentials file has been laid down thusly
    #os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "{}/.aws/credentials".format(os.getcwd())

    # Prime the stdout pump - we seem to lose the first line otherwise
    print()

    snapshot_path = env_set("INPUT_SNAPSHOT_PATH", "")
    snapshot_date = env_set("INPUT_SNAPSHOT_DATE", "")
    log_filename = env_set("INPUT_LOG_FILENAME", "promotetoprod.log")
    prod_store_bucket = env_set("INPUT_GCP_PROD_STORAGE_BUCKET", "aap-aoc-code-assets")

    success = gatherAssets(snapshot_path, snapshot_date)

    # Reorient stdout back to normal, dump out what it was, and return value to action
    sys.stdout = tmp_stdout
    with open(log_filename, "a") as out_file:
        out_file.write(string_stdout.getvalue())
        out_file.close()
    exit(not success)


if __name__ == "__main__":
    main()
