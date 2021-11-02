import core.stateparser
import os
import pathlib
import jinja2
import sys
import mmap

def parse(inputfile: pathlib.WindowsPath, cpp_template, hpp_template):
    outputpath = inputfile.parent.joinpath("generated")

    print(f"parsing {str(inputfile)}")

    with open(str(inputfile), "r") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmap_file:
        if (mmap_file.find(b"@startuml")) == -1:
            return

        all_diagrams = core.stateparser.parse_data(f.read())

        outputpath.mkdir(parents=True, exist_ok=True)

        for diagram in all_diagrams:
            outputcpp = outputpath.joinpath(diagram["name"] + "_HSM.cpp")
            outputhpp = outputpath.joinpath(diagram["name"] + "_HSM.hpp")

            with open(str(outputcpp), "w") as cppout:
                cppout.writelines(cpp_template.render(diagram))
                print(f"generated {str(outputcpp)}")

            with open(str(outputhpp), "w") as hppout:
                hppout.writelines(hpp_template.render(diagram))
                print(f"generated {str(outputhpp)}")


def main():
    template = pathlib.Path(__file__).parent.resolve().joinpath("template")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template),
                             trim_blocks=True)

    cpp = env.get_template("template.cpp.jinja")
    hpp = env.get_template("template.hpp.jinja")

    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <inputfile-or-directory>")
        sys.exit(1)

    path = pathlib.Path(sys.argv[1])
    if path.is_dir():
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".puml"):
                    parse(pathlib.Path(root).joinpath(file), cpp, hpp)
    else:
        parse(path, cpp, hpp)


if __name__ == '__main__':
    main()