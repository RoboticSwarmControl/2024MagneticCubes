import itertools
import os.path
import subprocess
import sys
import logging

BOARD_TYPE = ["maze", "cave"]
TILES = [3, 4, 5, 6]
SIZE = [20, 30, 40]
LEFTOVER = [0, 1, 3]
GLUES = [1, 2, 3]
PROBLEM = ["fixed", "notfixed"]

print(sys.argv)

directory = sys.argv[1]
propagate = sys.argv[2:]


def main():
    logfile = "".join("".join(s.split()) for s in propagate[1:]).replace("-", "").replace("/", "")
    logging.basicConfig(filename=logfile,
                        level=logging.DEBUG)

    if not os.path.isdir(directory):
        print("first argument needs to be an input directory")
        exit(1)

    timed_out_instance_types = []

    for instance_type in itertools.product(BOARD_TYPE, TILES, SIZE,
                                           LEFTOVER, GLUES, PROBLEM):
        if any(strictly_harder(instance_type, t) for t in timed_out_instance_types):
            continue
        any_solved = False
        for filename in get_file_names(instance_type):
            logging.info("solving instance: " + filename)
            result = subprocess.run(["python", "-m", "tiltmp.run_experiment", filename] + propagate)
            if result.returncode == 0:
                logging.info("solved instance: " + filename)
                any_solved = True
            elif result.returncode == 1:
                logging.info("instance timed out: " + filename)
            elif result.returncode == 2:
                any_solved = True
                logging.info("skipping, solution file already exists")
            else:
                logging.error("something went wrong with the instance: " + filename)

        if not any_solved:
            logging.info("all instances of the type: (" + ", ".join(str(x) for x in instance_type) + ") timed out")
            # timed_out_instance_types.append(instance_type)


# true iff type 2 is strictly harder than type1
def strictly_harder(type1, type2):
    for value1, value2 in zip(type1, type2):
        if isinstance(value1, str):
            if value1 != value2:
                return False
            continue
        if value1 < value2:
            return False
    return True


def get_file_names(instance_type):
    i = 1
    while True:
        filename = os.path.join(directory, get_name(instance_type, i))
        if not os.path.isfile(filename):
            break
        yield filename
        i += 1


def get_name(instance_type, i):
    name = ""
    for x in instance_type:
        name += str(x) + "_"
    name += str(i) + ".json"
    return name


if __name__ == '__main__':
    main()
