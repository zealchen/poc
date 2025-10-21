import json
import re

def pretty_print_xml_minidom(xml_str: str, indent: int = 2) -> str:
    """
    使用 xml.dom.minidom 格式化 XML 字符串并返回格式化后的字符串。
    indent: 每层缩进的空格数
    """
    from xml.dom import minidom

    if isinstance(xml_str, bytes):
        xml_str = xml_str.decode('utf-8')

    try:
        parsed = minidom.parseString(xml_str)
        pretty = parsed.toprettyxml(indent=' ' * indent)
        # 删除多余的空白行（minidom 常会产生很多空行）
        pretty = '\n'.join([line for line in pretty.splitlines() if line.strip() != ''])
        return pretty
    except Exception as e:
        raise ValueError(f"无法解析 XML: {e}")


def expand_self_closing_tags(xml_str):
    """
    Replace all self-closing XML tags like:
      <tag attr="value" />
    with:
      <tag attr="value"></tag>
    """
    # 用正则匹配 <tag ... /> 的形式
    pattern = re.compile(r'<(\w[\w:-]*)([^>]*)/>')

    def replacer(match):
        tag = match.group(1)
        attrs = match.group(2).strip()
        # 保留属性并生成开闭标签
        if attrs:
            return f'<{tag} {attrs}></{tag}>'
        else:
            return f'<{tag}></{tag}>'

    return pattern.sub(replacer, xml_str)


if __name__ == "__main__":
    raw = "<root><child attr='1'>text<sub/></child><empty/></root>"
    with open('data.json') as fp:
        data = json.load(fp)
        # input = '<qti-gap identifier="gap3" required="false"/>'
        # qti_xml = data['qti_xml']
        qti_xml = expand_self_closing_tags(data['qti_xml'])
        # output = expand_self_closing_tags(input)
        print(qti_xml)
    # print(pretty_print_xml_minidom(qti_xml, indent=4))
