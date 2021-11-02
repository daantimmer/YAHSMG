# YAHSMG
Yet Another Hierarchical State Machine Generator

YAHSMG is build around Stefan Heinzmann's HSM and plantuml to generate C++ code.

# How to use
This has only been tested on Windows, but should work on Linux and MacOs as well.
Execute the generator python module like: `python generator <folder/file>`
When a folder is given it'll traverse all subdirectories in search for *.puml files.
For any file found it'll create a directory Generated in that file's folder and create a `<diagram nam>_HSM.hpp` and `<diagram nam>_HSM.cpp` file.
Add the `resources` folder to your include search path.

# Stefan Heinzmann's HSM
The heart of the HSM is Stefan heinzmann's HSM. This HSM has been modernized and made 'more modern C++ like'. See https://accu.org/journals/overload/12/64/heinzmann_252/ for more information.

# Things to do
- Plantuml supports generating images from any file, not only plantuml-specific files. For example you can have your plantuml diagram written in a source's header file. The diagram finder logic will now only search for `.puml` files, but a near future improvement will give the user the possibility to specify what extensions to look for.
- Create example implementations
- Create C++ unit test

# Limitations
YAHMSG currently does not support features like History/Fork/Concurrent/<<choice>>/Stereotyes/Point/Pin/Expansion features provided by plantuml. Any plantuml markup is also not supported. Some of these might be solved in later versions.