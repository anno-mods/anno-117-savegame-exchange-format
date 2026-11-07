import sys,re
pat=re.compile(r"4974656D426F6F73745F")
n=0
st=[]
for ln,line in enumerate(open(r"x\data_raw.xml",encoding="utf-8",errors="replace")):
    s=line.strip()
    if s.startswith("</"):
        if st: st.pop()
        continue
    m=re.match(r"<([^>/ ]+)>$",s)
    if m: st.append(m.group(1)); continue
    if pat.search(s):
        n+=1
        if n<=4: print(ln,"/".join(st[-6:]),bytes.fromhex(re.search(r">([0-9A-F]+)<",s).group(1)).decode("ascii","replace"))
print(n)
