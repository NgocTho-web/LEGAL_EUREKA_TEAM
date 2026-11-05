import os, sys
from pathlib import Path
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parent))
from retrieval import load,search,citation

st.set_page_config(page_title='Eureka Legal Agent',page_icon='⚖️',layout='wide')
st.title('⚖️ Eureka Legal Agent — KG + Retrieval')
st.warning('BẢN DEMO: Luật Đất đai 2013 là văn bản lịch sử, không dùng như căn cứ pháp luật hiện hành. OCR và cấu trúc vẫn có điểm chưa xác minh.')
kg_path=Path(os.getenv('LEGAL_KG_PATH','data/kg/legal_kg_matched.json'))
if not kg_path.exists():st.error(f'Chưa có KG: {kg_path}. Chạy python scripts/build_kg_match.py trước.');st.stop()
@st.cache_resource(show_spinner='Đang tải KG...')
def get_index(path,mtime):return load(path)
index=get_index(str(kg_path),kg_path.stat().st_mtime)
with st.sidebar:
 st.header('Thiết lập')
 k=st.slider('Số bằng chứng',2,10,5)
 use_llm=st.checkbox('Tạo câu trả lời bằng OpenAI (tùy chọn)',value=False)
 st.caption('Tắt OpenAI: chatbot chỉ trích xuất đoạn liên quan, không tự suy luận pháp lý.')
 st.write('KG nodes:',len(index[3]))
 st.write('Nguồn:',str(kg_path))
if 'messages' not in st.session_state:st.session_state.messages=[]
for msg in st.session_state.messages:
 with st.chat_message(msg['role']):st.markdown(msg['content'])
q=st.chat_input('Ví dụ: Điều 188 quy định điều kiện chuyển nhượng quyền sử dụng đất thế nào?')
if q:
 st.session_state.messages.append({'role':'user','content':q})
 with st.chat_message('user'):st.markdown(q)
 with st.chat_message('assistant'):
  hits=search(q,index,k)
  if not hits:answer='Không tìm thấy bằng chứng phù hợp trong KG đã nạp. Vui lòng hỏi theo số Điều hoặc cụm từ pháp luật cụ thể.'
  else:
   answer='**Các đoạn pháp luật được tìm thấy (chưa phải tư vấn pháp lý):**\n\n'
   for i,h in enumerate(hits,1):
    n=h['node'];txt=h['text'].strip();txt=txt[:1700]+('…' if len(txt)>1700 else '')
    answer+=f"**[{i}] {citation(n)}**\n\n> "+txt.replace('\n','\n> ')+"\n\n"
   if use_llm:
    try:
     from openai import OpenAI
     if not os.getenv('OPENAI_API_KEY'):raise RuntimeError('Chưa cấu hình OPENAI_API_KEY')
     evidence='\n\n'.join(f'[{i}] {citation(h["node"])}\n{h["text"][:2500]}' for i,h in enumerate(hits,1))
     client=OpenAI()
     res=client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),temperature=0,messages=[{'role':'system','content':'Bạn là trợ lý nghiên cứu văn bản lịch sử Luật Đất đai 2013. Chỉ sử dụng bằng chứng cung cấp, trích dẫn [1], [2]... đúng đoạn; không suy đoán hoặc bổ sung kiến thức bên ngoài. Nếu không đủ căn cứ, nói không đủ căn cứ. Nhắc luật 2013 không đại diện luật hiện hành và OCR chưa hoàn toàn xác minh.'},{'role':'user','content':f'Câu hỏi: {q}\n\nBằng chứng:\n{evidence}'}])
     answer=res.choices[0].message.content+'\n\n---\n**Bằng chứng nguồn:**\n\n'+ '\n\n'.join(f'[{i}] {citation(h["node"])} — {h["node"].get("source_pdf","luat_dat_dai_2013.pdf")}' for i,h in enumerate(hits,1))
    except Exception as exc:answer='Không thể gọi OpenAI ('+str(exc)+'). Hiển thị kết quả truy xuất:\n\n'+answer
  st.markdown(answer)
  st.session_state.messages.append({'role':'assistant','content':answer})
