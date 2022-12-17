
from bs4 import BeautifulSoup
import re
import json5
from tba_types_generator.url_getter import get_url
import logging

logger = logging.getLogger(__name__)
HARMONY_DOC_PAT = "https://docs.toonboom.com/help/harmony-{0}/scripting/extended/index.html"
HARMONY_DOC_PAT_GLOBALS = "https://docs.toonboom.com/help/harmony-{0}/scripting/extended/global.html"


def get_classes(version_num: int):
    url = HARMONY_DOC_PAT.format(version_num)
    base_url = '/'.join(url.split('/')[:-1])
    html = get_url(url)
    classes = _parse_index(html)
    for class_data in classes:
        class_url = f"{base_url}/{class_data['url']}"
        class_html = get_url(class_url)
        class_data = _parse_class(class_html)
        class_data['url'] = class_url
        yield class_data


def get_globals(version_num: int):
    url = HARMONY_DOC_PAT_GLOBALS.format(version_num)
    html = get_url(url)
    harmony_globals = _parse_globals(html)
    return harmony_globals


def _parse_index(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    nav = soup.find('nav')

    classes = []
    for h3 in nav.find_all('h3'):
        if not h3.text in ('Classes', 'Modules'):
            continue
        ul = h3.find_next_sibling('ul')
        for li in ul.find_all('li', recursive=False):
            a = li.find('a')
            class_name = a.text.strip()
            class_url = a['href']
            classes.append(dict(name=class_name, url=class_url))
            logger.debug(f"{class_name}: {class_url}")
           # methods_ul = li.find('ul', {'class': 'slots'})
    return classes


def _parse_keyword(txt: str):
    if not txt:
        return ""
    return re.search(r"\((.+)\)", txt).group(1)


def _parse_method_name(txt: str):
    return txt.split(" ").pop()

# def _parse_signature(txt: str):
#     return


def _parse_type(txt: str):
    if txt == "Array":
        return "any[]"
    if txt == "function":
        return "(...args: any[]) => any"
    if txt == "boolean | function":
        return "boolean | (...args: any[]) => boolean"
    assert not "boolean" in txt
    # FIXME: Too lazy to write a proper parser; just check for 2d array
    match = re.search(r"Array\.\<Array\.\<(.+?)\>\>", txt)
    if match:
        return f"{match.group(1)}[][]"
    match = re.search(r"Array\.\<(.+?)\>", txt)
    if match:
        return f"{match.group(1)}[]"
    match = re.search(r"Object\.\<(.+?), (.+?)>", txt)
    if match:
        return f"{{[key: {match.group(1)}] : {match.group(2)}}}"
    return txt


def _parse_schema_table(tbody):
    fields = []
    for tr in tbody.find_all('tr', recursive=False):
        name_td = tr.find('td', {'class': 'name'}, recursive=False)
        type_td = tr.find('td', {'class': 'type'}, recursive=False)
        attr_td = tr.find(
            'td', {'class': 'attributes'}, recursive=False)
        description_td = tr.find(
            'td', {'class': 'description'}, recursive=False)
        field_name = name_td.text.strip()
        field_type = _parse_type(type_td.text.strip())
        try:
            field_desc = description_td.contents[0].text.strip()
        except IndexError:
            field_desc = ""

        field_dict = {
            'name': field_name,
            'type': field_type,
            'desc': field_desc
        }
        fields.append(field_dict)
        sub_tbody = description_td.find('tbody')
        if sub_tbody:
            field_dict['object_schema'] = _parse_schema_table(sub_tbody)
    return fields


def _parse_class(html: str):
    class_data = {
        'slots': [],
        'example': "",
        'desc': ""
    }
    soup = BeautifulSoup(html, 'html.parser')
    title_h1 = soup.find('h1', {'class': 'page-title'})
    class_name = title_h1.text.strip()
    if "/" in class_name:
        class_data['namespace'], class_data['name'] = tuple(
            class_name.split("/"))
    else:
        class_data['name'] = class_name
    article = soup.find('article')
    container_overview = article.find(
        'div', {'class': 'container-overview'}, recursive=False)
    class_desc_div = container_overview.find('div', {'class': 'description'})
    class_data['desc'] = class_desc_div.text

    for h4 in article.find_all('h4', {'class': 'name'}):
        method_id = h4['id']
        method_desc = ""
        # method_name = h4.text
        method_keyword, method_name, _, _ = tuple(
            (h.text.strip() for h in h4.contents))
        method_keyword = _parse_keyword(method_keyword)
        method_name = _parse_method_name(method_name)
        logger.debug(f"Keyword: {method_keyword}, Name: {method_name}")
        method_desc_div = h4.find_next_sibling('div', {'class': 'description'})
        if method_desc_div:
            method_desc = method_desc_div.text.strip()
        logger.debug(f"Method: {method_name}\n\t{method_desc}")

        method_dict = {
            'name': method_name,
            'keyword': method_keyword,
            'desc': method_desc,
            'params': [],
            'type': ""
        }
        class_data['slots'].append(method_dict)

        h5 = h4.find_next_sibling('h5')
        example_p = h5.find_next_sibling('p')
        if example_p:
            # example_desc = example_p.text
            example_code_pre = h5.find_next_sibling('pre')
            method_dict['example'] = example_code_pre.find('code').text
        parameters_h5 = h5.find_next_sibling('h5')

        if parameters_h5 and 'Parameters' in parameters_h5.text:
            h5 = parameters_h5
            parameters_table = parameters_h5.find_next_sibling(
                'table', {'class': 'params'})
            parameters_table_body = parameters_table.find(
                'tbody', recursive=False)
            for tr in parameters_table_body.find_all('tr', recursive=False):
                # tmp = list(tr.find_all('td'))
                name_td = tr.find('td', {'class': 'name'}, recursive=False)
                type_td = tr.find('td', {'class': 'type'}, recursive=False)
                attr_td = tr.find(
                    'td', {'class': 'attributes'}, recursive=False)
                if attr_td:
                    logger.debug(f"Atr: {attr_td}")
                description_td = tr.find(
                    'td', {'class': 'description'}, recursive=False)
                param_name = name_td.text.strip()
                param_type = _parse_type(type_td.text.strip())
                param_desc = description_td.contents[0].text.strip()
                param_dict = {
                    'name': param_name,
                    'type': param_type,
                    'desc': param_desc,
                }
                method_dict['params'].append(param_dict)
                logger.debug(
                    f"Parameter: {param_name} {param_type} {param_desc}")
                param_object_schema_tbody = description_td.find('tbody')
                if param_object_schema_tbody:
                    param_dict['object_schema'] = _parse_schema_table(
                        param_object_schema_tbody)

        return_h5 = h5.find_next_sibling('h5')
        if return_h5 and 'Returns' in return_h5.text:
            dl = return_h5.find_next_sibling('dl', {'class': 'param-type'})
            if dl:
                return_type_span = dl.find('span', {'class': 'param-type'})
                method_dict['type'] = _parse_type(
                    return_type_span.text.strip())
                assert not 'Array' in method_dict['type']
                assert not 'Object<' in method_dict['type']
    return class_data


def _parse_globals(html: str):
    """
        Only deals with interfaces
    """
    soup = BeautifulSoup(html, 'html.parser')
    harmony_globals = []
    article = soup.find('article')

    for h4 in article.find_all('h4', {'class': 'name'}):
        global_name = h4.text.strip()
        props_table = h4.find_next_sibling('table')
        tbody = props_table.find('tbody')
        schema = _parse_schema_table(tbody)

        desc_div = props_table.find_next_sibling(
            'div', {'class': 'description'})
        harmony_globals.append({
            'name': global_name,
            'object_schema': schema,
            'desc': desc_div.text.strip()
        })

    return harmony_globals
