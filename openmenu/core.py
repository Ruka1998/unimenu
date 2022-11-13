from pathlib import Path
import importlib
import pkgutil
from typing import Union
from openmenu.dccs import detect_dcc, DCC
from openmenu.utils import get_json_data, get_yaml_data, getattr_recursive


def setup_config(path: Union[str, Path], dcc: DCC = None):
    """menu setup from a json or yaml file"""
    data = get_json_data(path) or get_yaml_data(path)
    return setup_dict(data, dcc)


def setup_dict(data, dcc: DCC = None):
    """menu setup from a dict"""
    dcc = dcc or detect_dcc()
    module = importlib.import_module(f'openmenu.dccs.{dcc.name}')
    return module.setup_menu(data)


def setup_module(parent_module_name, parent_menu_name='', menu_name="", function_name='main', dcc=None):
    """
    Create a menu from a folder with modules,
    automatically keep your menu up to date with all tools in that folder

    note: ensure the folder is importable and in your environment path

    Args:
    parent_module_name: the name of the module that contains all tools. e.g.: "cool_tools"
                        cool_tools
                        ├─ __init__.py   (import cool_tools)
                        ├─ tool1.py      (import cool_tools.tool1)
                        └─ tool2.py      (import cool_tools.tool2)
    parent_menu_name: the name of the parent menu to add our menu entries to
    menu_name: optional kwars to overwrite the name of the menu to create, defaults to module name
    function_name: the function name to run on the module, e.g.: 'run', defaults to 'main'
                   if empty, call the module directly
    dcc: the dcc that contains the menu. if None, will try to detect dcc
    """

    parent_module = importlib.import_module(parent_module_name)

    # create dict for every module in the folder
    # label: the name of the module
    # callback: the function to run

    # todo support recursive folders -> auto create submenus

    items = []
    for module_finder, submodule_name, ispkg in pkgutil.iter_modules(parent_module.__path__):

        # skip private modules
        if submodule_name.startswith('_'):
            continue

        # to prevent issues with late binding
        # https://stackoverflow.com/questions/3431676/creating-functions-or-lambdas-in-a-loop-or-comprehension
        # first arg might be self, e.g. operator wrapped in blender
        def callback(self=None, _submodule_name=submodule_name, _function_name=function_name, *args, **kwargs):

            # only import the module after clicking in the menu
            # so failed module imports don't break the menu setup
            submodule = module_finder.find_spec(_submodule_name).loader.load_module()

            # run the user-provided function on the module, or call the module directly
            if _function_name:
                function = getattr_recursive(submodule, _function_name)
                function()
            else:
                submodule()

        submodule_dict = {
            'label': submodule_name,
            'command': callback,  # todo ensure this also works for dccs that only support strings
        }
        items.append(submodule_dict)

    data = {}
    if parent_menu_name:
        data['parent'] = parent_menu_name
    data['items'] = [{'label': menu_name or parent_module.__name__, 'items': items}]

    # use the generated dict to set up the menu
    return setup_dict(data, dcc)


def add_item(label, command=None, parent=None, icon_name=None):
    """
    add a menu entry to the dcc menu

    Args:
        label: the label of the menu entry, defaults to None
        command: the command to run when the menu entry is clicked, defaults to None
                 some dccs support callbacks, but most use string commands
                 if None, the menu is seen as a submenu.
        parent: the parent menu name to add the entry to, defaults to None
        icon_name: the name of the icon to use, defaults to None
        todo add menu entry name support, defaults to using label, so no duplicate names currently
    """
    data = {
        "items": [
            {
                "label": label,
            }
        ]
    }
    if icon_name:
        data['items'][0]['icon'] = icon_name
    if command:
        data['items'][0]['command'] = command
    if parent:
        data['parent_menu'] = parent
    return setup_dict(data)


def breakdown():
    """remove the create menu"""
    # todo module.breakdown()
    raise NotImplementedError("not yet implemented")
