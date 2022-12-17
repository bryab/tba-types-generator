
from bs4 import BeautifulSoup
import re
import json5
from tba_types_generator.url_getter import get_url
import logging

logger = logging.getLogger(__name__)
HARMONY_DOC_PAT = "https://docs.toonboom.com/help/harmony-{0}/scripting/extended/index.html"


def get_classes(version_num: int):
    url = HARMONY_DOC_PAT.format(version_num)
    base_url = '/'.join(url.split('/')[:-1])
    html = get_url(url)
    classes = _parse_index(html)
    for class_data in classes:
        class_url = f"{base_url}/{class_data['url']}"
        class_html = get_url(class_url)
        yield class_data


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

# def _parse_signature(txt: str):
#     return

# def _parse_method_type(txt: str):
#     return re.search(r"\{(.+)\}").group(1)


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
        field_type = type_td.text.strip()
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
        logger.debug(f"Keyword: {method_keyword}, Name: {method_name}")
        method_desc_div = h4.find_next_sibling('div', {'class': 'description'})
        if method_desc_div:
            method_desc = method_desc_div.text.strip()
        logger.debug(f"Method: {method_name}\n\t{method_desc}")

        method_dict = {
            'name': method_name,
            'keyword': method_keyword,
            'desc': method_desc,
        }
        class_data['slots'].append(method_dict)

        h5 = h4.find_next_sibling('h5')
        example_p = h5.find_next_sibling('p')
        if example_p:
            example_desc = example_p.text
            example_code_pre = h5.find_next_sibling('pre')
            method_dict['example'] = example_code_pre.find('code').text
        parameters_h5 = h5.find_next_sibling('h5')
        params_list = []

        if parameters_h5 and 'Parameters' in parameters_h5.text:
            method_dict['params'] = []
            parameters_table = parameters_h5.find_next_sibling(
                'table', {'class': 'params'})
            parameters_table_body = parameters_table.find(
                'tbody', recursive=False)
            for tr in parameters_table_body.find_all('tr', recursive=False):
                tmp = list(tr.find_all('td'))
                name_td = tr.find('td', {'class': 'name'}, recursive=False)
                type_td = tr.find('td', {'class': 'type'}, recursive=False)
                attr_td = tr.find(
                    'td', {'class': 'attributes'}, recursive=False)
                description_td = tr.find(
                    'td', {'class': 'description'}, recursive=False)
                param_name = name_td.text.strip()
                param_type = type_td.text.strip()
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
    return class_data


# if __name__ == "__main__":
#     url = HARMONY_DOC_PAT.format(21)
#     base_url = '/'.join(url.split('/')[:-1])
#     html = get_url(url)
#     classes = _parse_index(html)
#     for class_data in classes:
#         class_url = f"{base_url}/{class_data['url']}"
#         class_html = get_url(class_url)
#         class_data.update(_parse_class(class_html))

#     for class_data in classes:
#         logger.debug(json5.dumps(class_data, indent=4))
