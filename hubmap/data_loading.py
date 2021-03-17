#!/usr/bin/env python
import subprocess


def main():
    directory = "/opt/"
    files = subprocess.check_output(f"ls {directory}", shell=True).decode().split("\n")
    tar_files = [file for file in files if ".tar.gz" in file]
    for file in tar_files:
        tar_command = f"tar -xvzf {directory}{file}"
        subprocess.run(tar_command, check=True)
    files = subprocess.check_output(f"ls", shell=True).decode().split("\n")
    csv_files = [file for file in files if ".csv" in file]
    hdf_files = [file for file in files if ".csv" in file]

    images = ["postgres", "cross-modality-query-prod"]
    images_dict = {}
    for image in images:
        base_command = f"docker ps | grep '{image}' | "
        command = base_command + "awk '{print $1}'"
        images_dict[image] = subprocess.check_output(command, shell=True).decode()

    for csv_file in csv_files:
        for image in images_dict:
            command = f"docker cp {csv_file} {images_dict[image]}:/opt/"
            subprocess.run(command, check=True)
            subprocess.run(f"rm {file}", check=True)

    for hdf_file in hdf_files:
        image = images_dict["cross-modality-query-prod"]
        command = f"docker cp {hdf_file} {image}:/opt/"
        subprocess.run(command, check=True)
        subprocess.run(f"rm {file}", check=True)

    for file in tar_files:
        command = f"rm {directory}{file}"
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
