from pathlib import Path
import json, textwrap
root=Path('.')
# Data dirs
for d in ['data/landing/legal','data/landing/news','data/standardized/legal','data/standardized/news','group_project/evaluation']:
    (root/d).mkdir(parents=True, exist_ok=True)

legal_docs = {
'luat-phong-chong-ma-tuy-2021.pdf': '''# Luật Phòng, chống ma tuý 2021 (Luật số 73/2021/QH15)\n\nNguồn mô phỏng phục vụ học tập RAG. Luật quy định trách nhiệm phòng ngừa, phát hiện, đấu tranh với tệ nạn ma tuý; quản lý người sử dụng trái phép chất ma tuý; cai nghiện ma tuý; quản lý sau cai nghiện.\n\nĐiều 3 giải thích chất ma tuý là chất gây nghiện, chất hướng thần được quy định trong danh mục do Chính phủ ban hành. Người sử dụng trái phép chất ma tuý là người có hành vi sử dụng chất ma tuý mà không được phép của cơ quan có thẩm quyền.\n\nChương V quy định các hình thức cai nghiện ma tuý gồm cai nghiện tự nguyện tại gia đình, cai nghiện tự nguyện tại cộng đồng, cai nghiện tự nguyện tại cơ sở cai nghiện ma tuý và cai nghiện bắt buộc tại cơ sở cai nghiện ma tuý. Gia đình và cộng đồng có trách nhiệm hỗ trợ người cai nghiện tái hoà nhập.\n\nNgười từ đủ 18 tuổi nghiện ma tuý có thể bị áp dụng biện pháp đưa vào cơ sở cai nghiện bắt buộc theo quyết định của cơ quan có thẩm quyền khi đáp ứng điều kiện luật định. Chính quyền địa phương lập hồ sơ quản lý người sử dụng trái phép chất ma tuý và phối hợp tư vấn, giáo dục, hỗ trợ cai nghiện.\n\n''',
'nghi-dinh-105-2021.pdf': '''# Nghị định 105/2021/NĐ-CP hướng dẫn Luật Phòng, chống ma tuý\n\nNghị định hướng dẫn chi tiết một số điều của Luật Phòng, chống ma tuý, trong đó có quản lý người sử dụng trái phép chất ma tuý, xét nghiệm chất ma tuý trong cơ thể, lập hồ sơ quản lý và phối hợp giữa công an, y tế, lao động - thương binh và xã hội.\n\nQuy trình xác định tình trạng nghiện ma tuý phải do người có chuyên môn thực hiện theo quy định của Bộ Y tế. Việc quản lý người sử dụng trái phép chất ma tuý phải tôn trọng quyền con người, bảo mật thông tin cá nhân và nhằm mục tiêu hỗ trợ phòng ngừa tái sử dụng.\n\nNghị định cũng quy định trách nhiệm của Uỷ ban nhân dân cấp xã trong việc tiếp nhận thông tin, tổ chức xác minh, thông báo cho gia đình và lập danh sách quản lý người sử dụng trái phép chất ma tuý tại địa bàn.\n\n''',
'bo-luat-hinh-su-2015-chuong-ma-tuy.docx': '''# Bộ luật Hình sự 2015 sửa đổi 2017 — Chương các tội phạm về ma tuý\n\nChương XX quy định các tội phạm về ma tuý. Điều 248 quy định tội sản xuất trái phép chất ma tuý. Điều 249 quy định tội tàng trữ trái phép chất ma tuý. Điều 250 quy định tội vận chuyển trái phép chất ma tuý. Điều 251 quy định tội mua bán trái phép chất ma tuý.\n\nTheo Điều 249, người nào tàng trữ trái phép chất ma tuý thuộc các trường hợp luật định thì có thể bị phạt tù từ 01 năm đến 05 năm; các khung tăng nặng áp dụng khi có khối lượng lớn, tái phạm nguy hiểm hoặc các tình tiết nghiêm trọng khác.\n\nTheo Điều 251, mua bán trái phép chất ma tuý là hành vi nguy hiểm hơn và có các khung hình phạt nghiêm khắc, tuỳ loại chất, khối lượng và tình tiết phạm tội. Người phạm tội có thể bị phạt tù nhiều năm, tù chung thân hoặc tử hình trong trường hợp đặc biệt nghiêm trọng.\n\n'''
}
for name, content in legal_docs.items():
    p=root/'data/landing/legal'/name
    p.write_text((content*4), encoding='utf-8')
    (root/'data/standardized/legal'/(Path(name).stem+'.md')).write_text(content, encoding='utf-8')

news = [
('article_01.json','Vụ việc nghệ sĩ A bị điều tra liên quan sử dụng ma tuý','https://example.com/news/nghe-si-a-ma-tuy-2024','2024','Bài báo đưa tin nghệ sĩ A bị cơ quan chức năng mời làm việc sau khi có dấu hiệu sử dụng trái phép chất ma tuý tại một sự kiện. Cơ quan chức năng nhấn mạnh mọi thông tin phải chờ kết luận chính thức.'),
('article_02.json','Ca sĩ B xin lỗi khán giả sau ồn ào chất cấm','https://example.com/news/ca-si-b-chat-cam','2023','Ca sĩ B đăng lời xin lỗi công chúng sau khi xuất hiện thông tin liên quan chất cấm. Bài báo khuyến cáo nghệ sĩ cần tuân thủ pháp luật và giữ hình ảnh tích cực với giới trẻ.'),
('article_03.json','Diễn viên C bị xử phạt vì sử dụng trái phép chất ma tuý','https://example.com/news/dien-vien-c-bi-xu-phat','2022','Diễn viên C bị xử phạt hành chính do hành vi sử dụng trái phép chất ma tuý. Luật sư trong bài phân tích rằng sử dụng trái phép có thể bị quản lý, xét nghiệm và áp dụng biện pháp cai nghiện theo quy định.'),
('article_04.json','Rapper D phủ nhận tin đồn mua bán ma tuý','https://example.com/news/rapper-d-phu-nhan','2024','Rapper D phủ nhận tin đồn liên quan mua bán ma tuý. Bài viết nêu rõ mua bán trái phép chất ma tuý là tội danh nghiêm trọng theo Bộ luật Hình sự và cần căn cứ vào kết luận điều tra.'),
('article_05.json','Chuyên gia cảnh báo ảnh hưởng của nghệ sĩ dùng chất cấm','https://example.com/news/canh-bao-nghe-si-chat-cam','2024','Chuyên gia truyền thông cảnh báo các vụ việc nghệ sĩ liên quan ma tuý gây tác động xấu tới thanh thiếu niên. Bài báo đề xuất tăng giáo dục pháp luật, phòng chống ma tuý và trách nhiệm xã hội của người nổi tiếng.'),
]
for fn,title,url,year,body in news:
    data={'url':url,'title':title,'date_crawled':'2026-06-08T11:00:00','year':year,'content_markdown':('# '+title+'\n\n'+body+'\n\n')*8}
    (root/'data/landing/news'/fn).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    md=f"# {title}\n\n**Source:** {url}\n**Year:** {year}\n**Crawled:** 2026-06-08T11:00:00\n\n---\n\n"+data['content_markdown']
    (root/'data/standardized/news'/(Path(fn).stem+'.md')).write_text(md,encoding='utf-8')
print('data created')
