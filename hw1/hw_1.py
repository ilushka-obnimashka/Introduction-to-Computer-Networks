import argparse
import csv
import os
import re
import subprocess
import sys


def ping_website(target: str) -> tuple[float, float, float]:
    """
    :param target: The website to ping.
    :return result: The RTT of the website in format tuple(min-float,avg-float,max-float).
    """

    if os.name == 'posix':
        bash_ping_result = subprocess.run(['ping', '-c', '4', target], capture_output=True, text=True)
    elif os.name == 'nt':
        bash_ping_result = subprocess.run(['ping', '-n', '4', target], capture_output=True, text=True)

    if (bash_ping_result.returncode != 0):
        print(f'\u001b[31;1m ping {target} caused an error:\n',bash_ping_result.stderr,'\u001b[0m')
        return None, None, None

    pattern = r'(\d+\.\d+)\/(\d+\.\d+)\/(\d+\.\d+)'

    match = re.search(pattern, bash_ping_result.stdout)
    return tuple(map(float, match.groups()))


def extract_sites_from_txt(filename: str) -> list[str]:
    """
    :param filename: The name of the .txt file with the names sites to check RTT.
    :return result: The list of sites extracted from .txt file.
    """
    try:
        with open(filename, 'r') as file:
            site_names = []
            for line in file:
                sites_in_line = re.split(r'\s+', line.strip('\n\t\r '))
                if (sites_in_line != ['']):
                    site_names.extend(sites_in_line)
            return site_names
    except FileNotFoundError:
        print(f"\u001b[31;1m File {filename} not found. Please check this filename and restart the programm \u001b[0m")
        sys.exit(1)


def pack_data_into_csv(filename: str, column_names: list[str], data: list[tuple]) -> None:
    """
    :param filename: The name of the CSV file.
    :param data: The data to write.
    :param column_names: The names of the columns in CSV file.
    :return: None
    """

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)

        for row in data:
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(
        prog='ping_website',
        description='This program pings a website and returns the result in CSV-file. '
                    'Script input: file name with site names, file name to write the result.'
    )

    parser.add_argument('input_txt', type=str, help='input filename with site names (extension .txt)')
    parser.add_argument('output_csv', type=str, help='output filename with the result of the scripts CSV file')
    args = parser.parse_args()

    sites_names = extract_sites_from_txt(args.input_txt)

    row_results: list[tuple[str, float, float, float]] = []

    for site_name in sites_names:
        row_results.append((site_name,) + ping_website(site_name))

    pack_data_into_csv(args.output_csv, ['filename', 'min', 'avg', 'max'], row_results)


if __name__ == '__main__':    main()
