import os
import xml.etree.ElementTree as ET
import json
import requests
import concurrent.futures
import hashlib
import sys

# Parse the XML file
tree = ET.parse('gradle/verification-metadata.xml')
root = tree.getroot()

# Define the namespaces
namespaces = {
    'default': 'https://schema.gradle.org/dependency-verification'
}

# List of Maven2 URLs to query
maven_urls = [
    "https://dl.google.com/dl/android/maven2",
    "https://repo.maven.apache.org/maven2",
    "https://plugins.gradle.org/m2",
    "https://maven.google.com"
]

# List of failed Packages
failed_packages = []

# Local directory for storing artifacts
local_repo_dir = '/tmp/mvn-repo/'

# Create the local repository directory if it doesn't exist
if not os.path.exists(local_repo_dir):
    os.makedirs(local_repo_dir)

def download_artifact(_name, _group, _version, _artifact_name, _artifact_dir):
    # print the component details
    print(f"Downloading {_artifact_name} for {_group}:{_name}:{_version} from {_artifact_dir}")

    # Number of attempts
    attempts = 0

    # Iterate through Maven2 URLs
    for maven_url in maven_urls:
        # Increment the number of attempts
        attempts += 1

        # Construct the Maven2 URL for the current component
        component_url = f"{maven_url}/{_group.replace('.', '/')}/{_name}/{_version}/"

        # Construct the package URL
        package_url = component_url + _artifact_name

        print(f"Attempting to download {_artifact_name} for {_group}:{_name}:{_version} from {package_url}")

        # Download the package
        response = requests.get(package_url, stream=True)

        if response.status_code == 200:
            # Define the path to save the artifact
            artifact_path = os.path.join(_artifact_dir, _artifact_name)

            with open(output_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
            print(f"\n Downloaded '{_artifact_name}' for {_group}:{_name}:{_version} from {maven_url} to local repository. \n Repo URL: {package_url}")

            return

        else:
            print(f"\nFailed to download '{_artifact_name}' for {_group}:{_name}:{_version} from {maven_url}.")
            if attempts == len(maven_urls):
                failed_packages.append(f"{_group}:{_name}:{_version}")
                print(f"\n\nERROR: Failed to download '{_artifact_name}' for {_group}:{_name}:{_version} from all Maven2 URLs !!!!\n\n")

has_module_file = bool(sys.argv[2])

print(f"Is module file: {has_module_file}")

if not has_module_file:
    output_file = sys.argv[1]
    download_artifact(sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
else:
    #resolve the module file first
    output_file = '/tmp/module_file.module'
    download_artifact(sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[8], sys.argv[7])
    #process the component
    with open(output_file, 'r') as json_file:
        module_data = json.load(json_file)
        renaming_aliases = {}
        for variant in module_data.get('variants', []):
            for file in variant.get('files', []):
                renaming_aliases[file['name']] = file['url']

        artifact_name = sys.argv[6]
        if renaming_aliases.get(artifact_name):
            artifact_name = renaming_aliases.get(artifact_name)

        output_file = sys.argv[1]
        download_artifact(sys.argv[3], sys.argv[4], sys.argv[5], artifact_name, sys.argv[7])
