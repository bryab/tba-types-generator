from bs4 import BeautifulSoup
import bs4
import re
import json5
from tba_types_generator.url_getter import get_url
from typing import Tuple, Dict, Optional
import esprima
import jsbeautifier
import logging

logger = logging.getLogger(__name__)

HARMONY_DOC_PAT = (
    "https://docs.toonboom.com/help/harmony-{0}/scripting/script/hierarchy.js"
)
HARMONY_NAMESPACE_PAT = (
    "https://docs.toonboom.com/help/harmony-{0}/scripting/script/namespaces_dup.js"
)
SBPRO_DOC_PAT = "https://docs.toonboom.com/help/storyboard-pro-{0}/storyboard/scripting/reference/hierarchy.js"


def _group_from_labels(labels):
    if any(l in labels for l in ("read", "write")):
        return "props"
    # Note - static may be meaningful here
    if not labels or any(
        l in labels for l in ("slot", "static", "virtual", "override", "inline")
    ):
        return "slots"
    if "enum" in labels:
        return "enums"
    if "signal" in labels:
        return "signals"
    if "friend" in labels:
        return None
    if "delete" in labels:
        return None
    raise ValueError(labels)


def parse_class_page_detailed(html: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")

    class_data = {
        "name": _find_class_name(soup),
        "is_namespace": _is_namespace(soup),
        "slots": [],
        "props": [],
        "enums": [],
    }

    class_data["desc"], class_data["example"] = _find_class_desc(soup)

    contents_div = soup.find("div", {"class": "contents"})

    groups = {}

    # current_group = None
    item: bs4.element.Tag
    for item in contents_div.find_all("div", {"class": "memitem"}, recursive=False):
        labels = _sniff_div_labels(item)
        group_name = _group_from_labels(labels)
        if not group_name:  # Skip invalid items (friends for example)
            continue

        if not group_name in groups:
            groups[group_name] = []
        if group_name == "enum":
            func_data = _parse_enum_div(item)
        else:
            func_data = _parse_function_div(item)
            groups[group_name].append(func_data)

    for group_name, members in groups.items():
        if not members:
            continue
        if group_name == "constructor":
            class_data["constructor"] = members[0]
        else:
            class_data[group_name] = members
    return class_data


def get_class_hierarchy(js_url: str):
    js_str = get_url(js_url)
    data = esprima.parseScript(js_str)
    js_var = data.body[0].declarations[0]
    assert js_var.id.name == "hierarchy"
    tree = _read_elements(js_var.init.elements)
    return tree


def get_namespaces(js_url: str):
    # Note - it seems by 'namespaces' they mean global functions.
    # For this reason we just need a list of links here.
    js_str = get_url(js_url)
    data = esprima.parseScript(js_str)
    js_var = data.body[0].declarations[0]
    assert js_var.id.name == "namespaces_dup"
    tree = _read_elements(js_var.init.elements)
    return tree


def get_harmony_hierarchy_url(version):
    return HARMONY_DOC_PAT.format(version)


def get_harmony_namespace_url(version):
    return HARMONY_NAMESPACE_PAT.format(version)


def get_sbpro_hierarchy_url(version):
    return SBPRO_DOC_PAT.format(version)


def get_class_name_from_url(url):
    return re.search(r"class(\w+)\.html", url.split("/").pop()).group(1)


def get_classes(host, version_num):
    return iter_class_htmls(host, version_num)


def iter_class_htmls(host, version_num):
    if host == "harmony":
        hierarchy_url = get_harmony_hierarchy_url(version_num)
        base_url = "/".join(hierarchy_url.split("/")[:-1])
    else:
        hierarchy_url = get_sbpro_hierarchy_url(version_num)
        base_url = "/".join(hierarchy_url.split("/")[:-1])

    used_names = []  # FIXME: Multiple inheritance???
    logger.debug(f"Loading Class hierarchy from {hierarchy_url}")

    def _iter_leaf(parent_name, items):
        for item in items:
            if item.get("url", None):
                logger.debug(f"Parsing item: {item}")
                url = "{}/{}".format(base_url, item["url"])
                html = get_url(url)
                if not html:
                    logger.debug("Failed to get: {0}".format(url))
                    continue
                data = parse_class_page_detailed(html)
                if "::" in data["name"]:  # FIXME
                    continue
                if data["name"] in used_names:
                    continue
                used_names.append(data["name"])
                data["parent"] = parent_name
                data["url"] = url

                yield data
            if "members" in item:
                yield from _iter_leaf(item["name"], item["members"])

    tree = get_class_hierarchy(hierarchy_url)
    yield from _iter_leaf(None, tree)
    if host == "harmony":
        namespace_url = get_harmony_namespace_url(version_num)
        tree = get_namespaces(namespace_url)
        yield from _iter_leaf(None, tree)


DEFAULT_PARAMETER_VALUE_PAT = r"=(.+)"


def _clean_argument_name(txt):
    default_value = None
    parameter_name = None
    m = re.search(DEFAULT_PARAMETER_VALUE_PAT, txt)
    if m:
        default_value = m.group(1).strip().rstrip(",")
    m = re.search(r"(\w+)", txt)
    if m:
        parameter_name = m.group(1).strip()
    return parameter_name, default_value


FUNC_KEYWORD_PAT = r"^(?P<keyword>virtual|static) "
FUNC_NAMESPACED_NAME_PAT = r"(?:[a-z0-9_]+::)?(?P<name>[~a-z0-9_]+)$"


def _clean_function_name(txt):
    txt = txt.replace("Q_INVOKABLE", "")
    m = re.search(FUNC_KEYWORD_PAT, txt.strip())
    keyword = None
    if m:
        txt = re.sub(FUNC_KEYWORD_PAT, "", txt.strip()).strip()
        keyword = m.group("keyword")
    m = re.search(FUNC_NAMESPACED_NAME_PAT, txt.strip(), flags=re.I)
    # if m:
    func_name = m.group("name")
    txt = re.sub(FUNC_NAMESPACED_NAME_PAT, "", txt.strip(), flags=re.I).strip()
    if not txt:
        type_name = "void"
    elif " " in txt:
        # NOTE: There is a common mistake in the documentation
        # Where the actual field name is accidentally in the type
        try:
            type_name, func_name = tuple(txt.split(" "))
        except ValueError:
            logger.error("Failed to parse %s into tuple", txt)
            type_name = txt
    else:
        type_name = txt
    return type_name, func_name, keyword


def _clean_argument_desc(txt):
    return txt.lstrip(": ").strip()


# def _parse_group_name(name: str) -> str:
#     if "Constructor" in name:
#         return "constructor"
#     if "Prop" in name:
#         return "props"
#     if "Enum" in name:
#         return "enums"
#     if "Friend" in name:
#         return None
#     return "slots"


def _parse_signature_table(signature_table: bs4.element.Tag) -> Dict:
    if not signature_table:
        return {}
    func_data = {}
    for tr in signature_table.find_all("tr"):
        if td := tr.find("td", {"class": "memname"}):
            func_data["type"], func_data["name"], func_data["keyword"] = (
                _clean_function_name(td.text)
            )

        if td := tr.find("td", {"class": "paramtype"}):
            param = {}
            param["type"] = _parse_type(td.text)
            td = tr.find("td", {"class": "paramname"})

            argument_name, default_value = _clean_argument_name(td.text)
            if argument_name:
                param["name"] = argument_name
                if default_value:
                    param["default"] = default_value
                if not "params" in func_data:
                    func_data["params"] = []
                func_data["params"].append(param)
    return func_data


def _parse_example_div(e):
    example_lines = []
    for div in e.find_all("div", {"class": "line"}):
        example_lines.append(div.text)
    example = "\n".join(example_lines)
    return jsbeautifier.beautify(example)


def _parse_memdoc(doc_div: bs4.element.Tag) -> Dict:
    func_data = {}
    desc_lines = []
    for p in doc_div.find_all("p"):
        desc_line = p.text.strip()
        if desc_line:
            desc_lines.append(desc_line)
    if desc_lines:
        func_data["desc"] = "\n".join(desc_lines)

    if example_div := doc_div.find("div", {"class": "fragment"}):
        func_data["example"] = _parse_example_div(example_div)

    param_docs = []
    if params_table := doc_div.find("table", {"class": "params"}):
        for tr in params_table.find_all("tr", recursive=False):
            tds = tr.find_all("td")
            param_name_td = tds[0]
            param_name = param_name_td.text.strip()
            param_doc_td = tds[1]
            # There's sometimes a MarkdownTable that describes an Object returned by the function.
            # Attempt to get that if it exists.

            d = dict(name=param_name, desc=param_doc_td.text.strip())
            if object_schema := _find_object_schema(tr):
                d["object_schema"] = object_schema
            param_docs.append(d)
    func_data["param_docs"] = param_docs
    return func_data


def _find_object_schema(tr: bs4.element.Tag) -> Optional[dict]:
    table = tr.find("table", {"class": "markdownTable"})
    if not table:
        return None
    schema = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) != 3:
            continue
        name = tds[0].text.strip()
        typename = tds[1].text.strip()
        desc = tds[2].text.strip()
        schema.append(dict(name=name, type=typename, desc=desc))
    return schema


def _parse_enum_div(div: bs4.element.Tag) -> Dict:
    enum_data = {"name": None, "fields": []}
    enum_data.update(_parse_signature_table(div.find("table", {"class": "memname"})))
    table = div.find("table", {"class": "fieldtable"})
    for td in table.find_all("td", {"class": "fieldname"}):
        enum_data["fields"].append(td.text.strip())
    return enum_data


def _sniff_div_labels(div: bs4.element.Tag) -> str:
    """
    Determine whether this div is a slot, signal, prop, enum, etc
    """
    mlabels = div.find_all("span", {"class": "mlabel"})
    labels = [l.text.strip() for l in mlabels]
    # Note 'enum' is not usually a real label; but i want to know if an item
    # Is an enum so I have to do some digging.
    if not "enum" in labels:
        memname = div.find("td", {"class": "memname"})
        if memname and "enum" in memname.text:
            labels.append("enum")
    return labels


def _parse_function_div(div: bs4.element.Tag) -> Dict:
    func_data = {"name": None, "params": []}
    func_data.update(_parse_signature_table(div.find("table", {"class": "memname"})))

    func_data.update(_parse_memdoc(div.find("div", {"class": "memdoc"})))

    # Join the parameter documenation with the parameter dict
    for param in func_data["params"]:
        for param_doc in func_data["param_docs"]:
            if param_doc["name"] == param["name"]:
                param["desc"] = _clean_argument_desc(param_doc["desc"])
                if "object_schema" in param_doc:
                    param["object_schema"] = param_doc["object_schema"]
    del func_data["param_docs"]
    return func_data


def _find_class_name(soup: BeautifulSoup) -> str:
    div = soup.find("div", attrs={"class": "title"})
    return (
        div.find(text=True)
        .strip()
        .replace("Class Reference", "")
        .replace("Namespace Reference", "")
        .strip()
    )


def _is_namespace(soup: BeautifulSoup) -> bool:
    div = soup.find("div", attrs={"class": "title"})
    return "Namespace" in div.text


def _find_class_desc(soup: BeautifulSoup) -> Tuple[str, str]:
    desc = ""
    example = ""
    if a := soup.find("a", attrs={"id": "details"}):
        if txt := a.find_next("div", attrs={"class": "textblock"}):
            desc_lines = []
            for p in txt.find_all("p"):
                desc_lines.append(p.text.strip())
            desc = "\n".join(desc_lines)
            if e := txt.find("div", {"class": "fragment"}):
                example = _parse_example_div(e)
    return desc, example


def _parse_type(type_name):
    """
    Deprecated; this is left to downstream now,
    as there is useful information in the raw types.
    """
    return type_name.strip()


def _read_elements(elements):
    items = []
    for elem in elements:
        item = dict(name=elem.elements[0].value, url=elem.elements[1].value)
        members = elem.elements[2].elements
        if members:
            item["members"] = _read_elements(members)
        items.append(item)

    return items


# def parse_all_to_json():
#     for name, class_list_url in DOC_URLS:
#         export_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "export", name)
#         if not os.path.isdir(export_dir):
#             os.mkdir(export_dir)
#         import json

#         for data in iter_class_htmls(class_list_url):
#             json_filename = os.path.join(export_dir, "{}.json".format(data['name']))
#             with open(json_filename, "w") as f:
#                 json.dump(data, f, indent=2)
if __name__ == "__main__":
    tree = get_class_hierarchy(
        "https://docs.toonboom.com/help/harmony-22/scripting/script/hierarchy.js"
    )
    for item in tree:
        logger.debug(item["name"])
        if "members" in item:
            for subitem in item["members"]:
                logger.debug("--" + subitem["name"])
