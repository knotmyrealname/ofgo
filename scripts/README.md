# Helper Scripts
Here, we are sharing a selection of helper python scripts that we utilized during development that may be useful to the end user. They should work, but they do not have any fancy input validation or thorough pytest cases and may require direct editing of filenames to maximize functionality.

## get_all_projects_by_language.py
This script searches the OSS-Fuzz `projects` directory and compiles a list of files in the format `{language}_projects.txt` in `scripts/script_output/projects_by_language`. These files have all of the projects in OSS-Fuzz filtered by the specified language listed, separated by a newline.

To run this command, simply run 
```
python get_all_projects_by_language.py
```
without any arguments. Note that if you're in the base OFGO directory, you will need to append a `scripts/` to the beginning of `get_all_projects_by_language.py`. This will also be the case for all of the following scripts.

## filter_by_projects.py
This script filters the OSS-Fuzz `projects` directory to only show specific projects, determined by the input text file, which it expects to be a new-line separated list of project names. The removed projects get put in a temporary directory, named `temp_projects`. To specify the text file, you can either directly modify the script's `source_file` parameter or specify a relative (from the perspective of the script) path to a file through a command line argument. 

If you're directly modifying the source file, you'll only have to run
```
python filter_by_projects.py
```
If you're deciding to provide command line arguments, the program expects one single argument in the form of a relative path to your file:
```
python filter_by_projects.py mylist.txt
``` 
where `mylist.txt` is in the same folder as `filter_by_projects.py`

This script also offers a cleanup option, where all projects in `temp_projects` get moved back to `projects`. To run this cleanup function, simply run the script with the argument `reset`:
```
python filter_by_projects.py reset
``` 
Note that the existence of this function means that your file cannot be named `reset`. Anything param that isn't `reset` is assumed to be a file.

## check_integration.py
This script allows you to check and see which of your dependencies are and are not currently being fuzzed by OSS-Fuzz. This script expects an input file of projects separated by newline characters, which it'll check against the list of projects in OSS-Fuzz. The checking is dumb, which will mean that the input file must have projects of the same name as in OSS-Fuzz for them to be detected as integrated. **As this script checks the live OSS-Fuzz projects directory, any changes made by** `filter_by_projects.py` **may impact the results. If you've recently ran filter_by_projects.py, we heavily recommend running**  `python filter_by_projects.py reset` **to reset the OSS-Fuzz projects directory to its initial state.**

To run this script, you can either directly modify the `source_file` parameter and run without args:
```
python check_integration.py
```
Or you can specify a relative path to an input file:
```
python check_integration.py myfile.txt
```
In this case, `myfile.txt` is in the same directory as `check_integration.py`. If it's in a different directory, you'll have to change the link to reflect the path from the script to the file.

## get_project_repositories.py

This may be the least useful script - it simply parses all of the projects in the OSS-Fuzz projects directory and gets their linked github repositories. There are no command line arguments associated with this script:
```
python get_project_repositories.py
```