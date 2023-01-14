from typing import Dict, Iterable, List, Tuple, Union
from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException
import sys
import os

DIV_MAP = {
    "makuuchi": 1, "juryo": 2, "makushita": 3, "sandanme": 4, "jonidan": 5, "jonokuchi": 6
}


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
        driver = webdriver.Firefox(
            options=options, service_log_path=os.path.devnull)
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
    for key, val in defaults.items():
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


def validateSysArgs(kywrds: Union[List[str], None], optns: Union[None, Dict[str, str]],
                    expected_kywrds: List[str], expected_optns: Dict[str, List[str]],
                    usage_msg: str):
    """

    Validate the System arguments by comparing the provided set of keyword and
    option arguments to the expected arguments. Raises an error if any keywords
    do not match, and prints out the expected usage of the file and expected
    arguments

    ### Parameters ###
    * kywrds:   Union[List[str], None] - List of keyword arguments
    * optns:    Union[None, Dict[str, str]] - Map of options and their correlated string
    * expected_kywrds:  List[str] - List of expected keyword args
    * expected_optns:   Dict[str, str] - Map of expected options
    * usage_msg:    str - Usage message thrown with error on usage issues

    """
    if kywrds:
        for k in kywrds:
            if k not in expected_kywrds:
                raise ValueError(
                    "{} is not an appropriate keyword argument. {}"
                        .format(k, usage_msg)
                )
    else:
        if not None in expected_kywrds:
            raise ValueError(
                "Must include keyword arguments. {}"
                    .format(usage_msg)
            )

    if optns:
        for o in optns.keys():
            if o not in expected_optns.keys():
                raise ValueError(
                    "{} is not an appropriate option arg. {}"
                        .format(o, usage_msg)
                )

            if optns[o] not in expected_optns[o] and expected_optns[o] != any:
                raise ValueError(
                    "{} is not an appropriate option foroption {}. {}"
                        .format(optns[o], o, usage_msg)
                )
    else:
        if not None in expected_optns:
            raise ValueError(
                "Must include optionsal arguments. {}"
                    .format(usage_msg)
            )

# END OF validateSysArgs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def parseSysArgs(args: Iterable[str]) -> Tuple[list, dict]:
    """***************************************************************************

    Parse system arguments and return them as a map. Keyword arguments,
    delineated with "--", are stored in a list keyed to "keyword". Options are
    stored in their own map, keyed to "options", which keys the argument for
    said option by the name of the option

    ex. Keywords :: map["keyword"] = [Force, Append, ...]

    ex. Options :: map["options"] = {"FilePath": ".\helloworld.txt", "Content":
        "This is my last goodbye"}

    ### Parameters ###
    * args: Iterable[str] An iterable conataining a list of arguments

    ### Return ###
    * Dict[str, Union[list,dict]] : A map containing a list of keywords and a
        mapping of options
    ***************************************************************************"""
    keywords = list()
    options = {}

    curr_option = None

    if len(args) <= 1:
        return None, None

    for a in args[1:]:
        a = a.rstrip().lstrip()
        if len(a) == 0:
            continue
        elif curr_option:
            if a[0] == '-':
                raise ValueError(f"Argument {a} not a valid argument for the\
                    option {curr_option}")

            options[curr_option] = a
            curr_option = None
        else:
            """
            Assert that argument is either an option (ex. -A) or a keyword
            (ex. --Force). String arguments for options or keywords are handled
            above.
            """
            if a[0] != '-' or len(a) < 2:
                raise ValueError(
                    f"Argument {a} is invalid.\n Does not indiciate is neither an option, keyword, nor a parameter for an option.")

            # Arg is a keyword
            if a[0:2] == '--':
                keywords.append(a[2:].lower())
            # Arg is an Option
            else:
                curr_option = a[1:]
        # end If-Else
    # end FOR

    if curr_option:
        raise ValueError(
            f"Argument {curr_option} provided without any value for the option")

    return (keywords, options)


def sysArgError(message: str) -> None:
    print(message)
    print(
        f"Usage :: python {sys.argv[0]} <write_option: 'w', 'a', 'x'> <start index = 1> <end index = 5000>")
    sys.exit()


def tests():
    test_args = ["-A", "helloworld", "--force", ""]
    test1, test2 = parseSysArgs(test_args)
    print(test1)
    assert (test1["options"]['A'] == "helloworld")
    assert ("force" in test1["keyword"])

    try:
        test_args = ["helloworld"]
        parseSysArgs(test_args)
    except ValueError:
        print("Successful Failure")

    try:
        test_args = ["-A", "-helloworld"]
        parseSysArgs(test_args)
    except ValueError:
        print("Successful Failure")

    testValidateSysArgs()


def testValidateSysArgs():
    print("Normal test case")
    try:
        keywords = ["force", "hello"]
        expected_keywords = ["force", "hello", "append"]
        options = {"filepath": ".\\helloworld"}
        expected_options = {"filepath": [".\\helloworld"], "value": [
            "this is a value", "this is another value"]}
        validateSysArgs(keywords, options, expected_keywords,
                        expected_options, "usage message")
    except ValueError:
        print("Test failed")

    print("keyword error test case")
    try:
        keywords = ["force", "hello", "foo"]
        expected_keywords = ["force", "hello", "append"]
        options = {"filepath": ".\\helloworld"}
        expected_options = {"filepath": [any], "value": [
            "this is a value", "this is another value"]}
        validateSysArgs(keywords, options, expected_keywords,
                        expected_options, "usage message")
        print("Test did not fail properly")
    except ValueError:
        print("Test Success")

    print("Bad option test case")
    try:
        keywords = ["force", "hello"]
        expected_keywords = ["force", "hello", "append"]
        options = {"filepa": ".\\helloworld"}
        expected_options = {"filepath": [any], "value": [
            "this is a value", "this is another value"]}
        validateSysArgs(keywords, options, expected_keywords,
                        expected_options, "usage message")
        print("Test did not fail properly")
    except ValueError:
        print("Test Success")

    print("Bad value for option test case")
    try:
        keywords = ["force", "hello"]
        expected_keywords = ["force", "hello", "append"]
        options = {"value": "pooopie"}
        expected_options = {"filepath": [any], "value": [
            "this is a value", "this is another value"]}
        validateSysArgs(keywords, options, expected_keywords,
                        expected_options, "usage message")
        print("Test did not fail properly")
    except ValueError:
        print("Test Success")


if __name__ == "__main__":
    tests()
