from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException
import sys
import os

def getHeadlessDriver(url: str = None) -> webdriver.Firefox:
    """***************************************************************************

    Download page source from a given URL with a selenium driven headless firefox

    ### Parameters ###
    * url:String to query and download page source

    ### Return ###
    * Driver iwth url
    ***************************************************************************"""
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    try:
        driver = webdriver.Firefox(options=options, service_log_path=os.path.devnull)
        if url == None:
            print(f"Opening Browser")
        else:
            driver.get(url)
            print(f"creating driver for page {url}")
    except InvalidArgumentException:
        print("Bad URL")
        return driver
    except Exception as e:
        print(f"Unknown error: {e}")
        return None

    return driver
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END OF getPageSource~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def validateArgs(sys_args: dict, defaults: dict, assertions) -> None:
    """***************************************************************************

    Validates the arguments and their values. If arguments do not fit, prints
    messages indicating proper usages and exits the program.

    This implementation checks
    * write_option : must be 'w', 'a', or 'x'
    * strt

    ### Parameters ###
    * sys_args : system arguments mapped to strings

    ### Return ###
    * True if arguments fit, otherwise False
    ***************************************************************************"""

    usage_statement = f"Usage :: python {sys.argv[0]}"
    for key,val in defaults.items():
        usage_statement += f" <{key},default={val}"

    for def_key, def_val in defaults.items():
        try:
            sys_args.setdefault(def_key, def_val)
            # sys_args[def_key] = sys_args[def_key]
        except ValueError as e:
            print(
                f"value for {def_key}, {sys_args[def_key]}, is improperly formatted")
            print(usage_statement)
            sys.exit()

    try:
        assertions(sys_args, usage_statement)

    except AssertionError as e:
        print(e)
        print(usage_statement)
        sys.exit()
# END OF validateArgs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def readSysArgs(arg_names: list) -> dict:
    """***************************************************************************

    Read the system arguments and zip them into a dictionary based on the values
    provided in the arg_names. If a dict is passed, then those values are used as
    defaults. Then validates them, raising a error and quitting the program if
    the validation fails.

    Allows the possibility of using kwargs in the system arguments in the format
    <arg>=<option>

    ### Parameters ###
    *

    ### Return ###
    * mapping of system arguments to the names
    ***************************************************************************"""
    import sys
    norm_args = list()
    kwargs = list()
    for i in range(1, len(sys.argv)):
        if sys.argv[i].find("=") > -1:
            norm_args = sys.argv[1:i]
            kwargs = sys.argv[i:]
            break
        if i < len(sys.argv):
            norm_args = sys.argv[1:]

    mapped_args = dict(zip(arg_names, norm_args))
    for kwarg in kwargs:
        key, val = (kwarg.split('='))
        mapped_args[key] = val

    return mapped_args
# END OF readSysArgs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def sysArgError(message: str) -> None:
    print(message)
    print(f"Usage :: python {sys.argv[0]} <write_option: 'w', 'a', 'x'> <start index = 1> <end index = 5000>")
    sys.exit()
