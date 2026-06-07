c = open(r'D:\错题项目\services\ocr_server.py', encoding='utf-8').read()

old = 'def classify_by_ai(text, domain'
new = 'def classify_by_ai(text, domain'
# Insert keyword-first logic
old_def = old + "='all'):"
new_def = """def classify_by_ai(text, domain='all'):
    # 先用免费关键词匹配
    m=retrieve_knowledge(text, top_n=1)
    if m!='无匹配':
        parts=m.split(' > ')
        if len(parts)>=2:
            return {'subject':parts[0],'chapter':parts[1],'topics':[],'difficulty':'中等'}
    # 匹配不到才调AI"""
c = c.replace(old_def, new_def)

open(r'D:\错题项目\services\ocr_server.py', 'w', encoding='utf-8').write(c)
print('Added keyword-first classification')
